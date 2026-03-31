# app/order_service.py

"""Mongo-backed order service with production cancellation handling."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from app.database import get_collection

logger = logging.getLogger(__name__)

ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{3,40}$")


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _normalize_status(raw_status: str) -> str:
    status_map = {
        "ordered": "Ordered",
        "placed": "Placed",
        "processing": "Processing",
        "shipped": "Shipped",
        "out for delivery": "Out for Delivery",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
        "partial_cancelled": "Partially Cancelled",
        "cancellation_requested": "Cancellation Requested",
        "refuse_delivery": "Refuse Delivery",
    }
    return status_map.get(raw_status.lower(), raw_status)


def validate_order_id(order_id: str) -> bool:
    return bool(order_id and ORDER_ID_PATTERN.match(order_id))


def get_order(order_id: str) -> dict | None:
    if not validate_order_id(order_id):
        return None

    try:
        order = get_collection("orders").find_one({"order_id": order_id})
    except Exception as exc:
        logger.warning("get_order_failed order_id=%s error=%s", order_id, exc)
        return None

    if not order:
        return None

    return_window_days = int(order.get("return_window_days", 7))
    delivery_date = order.get("delivery_date")
    return_deadline = None

    delivered_at = _parse_date(delivery_date)
    if delivered_at:
        return_deadline = (delivered_at + timedelta(days=return_window_days)).strftime("%Y-%m-%d")

    raw_status = str(order.get("status", "ordered"))
    status = _normalize_status(raw_status)
    shipped_statuses = {"shipped", "out for delivery", "delivered"}

    return {
        "order_id": order.get("order_id"),
        "customer_name": order.get("customer_name"),
        "product_name": order.get("product_name") or order.get("product") or "your item",
        "product": order.get("product") or order.get("product_name") or "your item",
        "category": order.get("category", "default"),
        "payment_mode": order.get("payment_mode", "prepaid"),
        "order_status": status,
        "status": status,
        "raw_status": raw_status,
        "shipped": raw_status.lower() in shipped_statuses,
        "delivery_date": order.get("delivery_date"),
        "expected_delivery": order.get("expected_delivery"),
        "order_date": order.get("order_date"),
        "origin": order.get("origin"),
        "destination": order.get("destination"),
        "price": order.get("price", 0),
        "return_window_days": return_window_days,
        "return_deadline": return_deadline,
        "user_id": order.get("user_id"),
        "items": order.get("items", []),
        "combined_shipment": bool(order.get("combined_shipment", False)),
    }


def cancel_order(
    order_id: str,
    user_id: int | None = None,
    partial_items: list[str] | None = None,
    combined_shipment: bool = False,
    cancellation_reason: str | None = None,
) -> dict:
    orders = get_collection("orders")

    if not validate_order_id(order_id):
        return {
            "success": False,
            "decision": "Rejected",
            "message": "Invalid order_id format.",
            "next_steps": "Provide a valid order ID.",
        }

    order = orders.find_one({"order_id": order_id})
    if not order:
        return {
            "success": False,
            "decision": "Rejected",
            "message": "Order not found.",
            "next_steps": "Verify order ID and try again.",
        }

    if user_id is not None and order.get("user_id") not in (None, user_id):
        return {
            "success": False,
            "decision": "Rejected",
            "message": "Order does not belong to the specified user.",
            "next_steps": "Use the logged-in user account for cancellation.",
        }

    raw_status = str(order.get("status", "")).lower()

    # Combined-shipment edge case: cannot immediately cancel one item after pack/ship.
    if combined_shipment or bool(order.get("combined_shipment", False)):
        if raw_status in {"shipped", "out for delivery"}:
            orders.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": "refuse_delivery",
                        "cancellation_mode": "combined_shipment",
                        "cancellation_reason": cancellation_reason,
                        "cancellation_requested_at": datetime.utcnow(),
                    }
                },
            )
            return {
                "success": True,
                "decision": "Refuse Delivery",
                "message": "Combined shipment is already dispatched; mark as refuse delivery.",
                "next_steps": "Refuse package on delivery. Return/refund starts after carrier scan.",
            }

    if raw_status in {"ordered", "placed", "processing"}:
        update_doc: dict[str, object] = {
            "cancellation_requested_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "cancellation_reason": cancellation_reason,
        }

        if partial_items:
            update_doc["status"] = "partial_cancelled"
            update_doc["partial_cancel_items"] = partial_items
            decision = "Partially Cancelled"
            message = "Selected items are cancelled successfully."
        else:
            update_doc["status"] = "cancelled"
            decision = "Cancelled"
            message = "Order cancelled successfully."

        orders.update_one({"order_id": order_id}, {"$set": update_doc})
        return {
            "success": True,
            "decision": decision,
            "message": message,
            "next_steps": "Refund initiation starts immediately for prepaid orders.",
        }

    if raw_status in {"shipped", "out for delivery"}:
        orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "refuse_delivery",
                    "cancellation_reason": cancellation_reason,
                    "cancellation_requested_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return {
            "success": True,
            "decision": "Refuse Delivery",
            "message": "Order is already shipped; cancellation is converted to refuse delivery.",
            "next_steps": "Refuse package at delivery. Refund is processed after return scan.",
        }

    if raw_status == "delivered":
        return {
            "success": False,
            "decision": "Rejected",
            "message": "Delivered orders cannot be cancelled.",
            "next_steps": "Create a return/refund request instead.",
        }

    if raw_status in {"cancelled", "partial_cancelled", "refuse_delivery"}:
        return {
            "success": True,
            "decision": "No Change",
            "message": f"Order is already in '{raw_status}' state.",
            "next_steps": "No additional cancellation action required.",
        }

    logger.warning("Unsupported cancellation state order_id=%s status=%s", order_id, raw_status)
    return {
        "success": False,
        "decision": "Rejected",
        "message": "Cancellation is not supported for current order state.",
        "next_steps": "Contact support for manual review.",
    }
