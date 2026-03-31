# app/refund_service.py

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.database import get_collection

logger = logging.getLogger(__name__)

REFUND_STATUS_TRANSITIONS = {
    "initiated": {"processing", "failed"},
    "processing": {"completed", "failed"},
    "completed": set(),
    "failed": {"processing"},
}


def get_refund_options(payment_mode: str) -> list[str]:
    mode = (payment_mode or "").strip().lower()
    if mode in {"cod", "cash_on_delivery"}:
        return ["bank", "wallet", "coupon"]
    return ["original", "wallet", "coupon"]


def get_refund_timeline(refund_type: str) -> str:
    refund_type = (refund_type or "").strip().lower()
    if refund_type == "wallet":
        return "within 4 hours"
    if refund_type in {"bank", "upi", "card"}:
        return "up to 5 days"
    if refund_type == "cheque":
        return "up to 10 days"
    if refund_type == "coupon":
        return "instant"
    if refund_type == "original":
        return "up to 5 days"
    return "timeline depends on provider"


def _can_transition(current: str, target: str) -> bool:
    current_key = (current or "initiated").lower()
    target_key = (target or "").lower()
    return target_key in REFUND_STATUS_TRANSITIONS.get(current_key, set())


def get_latest_refund(order_id: str) -> dict[str, Any] | None:
    return get_collection("refunds").find_one({"order_id": order_id}, sort=[("created_at", -1)])


def create_refund_record(
    order_id: str,
    amount: float,
    refund_type: str,
    user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.utcnow()
    payload: dict[str, Any] = {
        "order_id": order_id,
        "user_id": user_id,
        "refund_type": refund_type,
        "amount": float(amount or 0),
        "status": "initiated",
        "timeline": get_refund_timeline(refund_type),
        "failure_reason": None,
        "created_at": now,
        "updated_at": now,
        "status_history": [{"status": "initiated", "at": now}],
    }
    if metadata:
        payload["metadata"] = metadata

    get_collection("refunds").insert_one(payload)
    return payload


def update_refund_status(order_id: str, new_status: str, failure_reason: str | None = None) -> dict[str, Any]:
    refunds = get_collection("refunds")
    latest = refunds.find_one({"order_id": order_id}, sort=[("created_at", -1)])

    if not latest:
        return {
            "success": False,
            "message": "No refund found for this order.",
        }

    current_status = str(latest.get("status", "initiated")).lower()
    target_status = str(new_status).lower()

    if current_status == target_status:
        return {
            "success": True,
            "message": "Refund already in requested status.",
            "refund": latest,
        }

    if not _can_transition(current_status, target_status):
        return {
            "success": False,
            "message": f"Invalid refund status transition: {current_status} -> {target_status}",
            "refund": latest,
        }

    now = datetime.utcnow()
    update_doc: dict[str, Any] = {
        "status": target_status,
        "updated_at": now,
    }

    if target_status == "failed":
        update_doc["failure_reason"] = failure_reason or "Refund processing failed"

    updated = refunds.find_one_and_update(
        {"_id": latest["_id"]},
        {
            "$set": update_doc,
            "$push": {"status_history": {"status": target_status, "at": now}},
        },
        return_document=True,
    )

    return {
        "success": True,
        "message": f"Refund moved to {target_status}.",
        "refund": updated,
    }


def process_refund(
    order: dict,
    selected_refund_type: str | None = None,
    verification_status: str | None = None,
) -> dict:
    """
    Evaluate refund eligibility based on order status and verification state.
    """
    order_status = str(order.get("raw_status", order.get("status", ""))).lower()
    product_name = order.get("product_name", "your item")
    payment_mode = order.get("payment_mode", "prepaid")

    if order_status != "delivered":
        return {
            "eligible": False,
            "message": (
                f"Refund for {product_name} is not available because order status is "
                f"'{order.get('status', order_status)}'."
            ),
            "refund_options": [],
            "timeline": None,
            "decision": "Not Eligible",
        }

    if verification_status in {"pending", "rejected"}:
        return {
            "eligible": False,
            "message": "Refund is blocked until damage verification is completed.",
            "refund_options": [],
            "timeline": None,
            "decision": "Blocked",
        }

    options = get_refund_options(payment_mode)
    chosen = (selected_refund_type or options[0]).lower()
    if chosen not in options:
        chosen = options[0]

    return {
        "eligible": True,
        "message": (
            f"Refund for {product_name} is eligible. Available options: {', '.join(options)}. "
            f"Selected option: {chosen}."
        ),
        "refund_options": options,
        "selected_refund_type": chosen,
        "timeline": get_refund_timeline(chosen),
        "decision": "Eligible",
    }
