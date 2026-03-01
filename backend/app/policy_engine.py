# app/policy_engine.py

from app.order_service import cancel_order, get_order
from app.refund_service import process_refund
from app.config import STATUS_THRESHOLD, CANCELLATION_THRESHOLD


# -----------------------------------
# Confidence Thresholds for Auto-Resolution
# -----------------------------------

INTENT_CONFIDENCE_THRESHOLDS = {
    "TRACK_ORDER": STATUS_THRESHOLD,
    "CANCEL_ORDER": CANCELLATION_THRESHOLD,
    "REFUND_REQUEST": 0.88,
    "DAMAGED_PRODUCT": 0.85,
    "MISMATCH_PRODUCT": 0.85,
    "GENERAL_QUERY": 0.80,
}

# High-value threshold for extra scrutiny
HIGH_VALUE_THRESHOLD = 50000  # Orders above this get escalated


def handle_cancellation(order_id: str):
    """Original cancellation handler — preserved for backward compatibility."""
    result = cancel_order(order_id)
    return result


# -----------------------------------
# Enhanced Policy Engine
# -----------------------------------

def apply_policy(intent: str, order: dict, confidence: float = 1.0, return_reason: str = None) -> dict:
    """
    Central policy engine that routes to the correct handler
    based on classified intent. Includes confidence-based automation.

    Returns a structured result dict:
        - message: str
        - status: "AUTO_RESOLVED" | "ESCALATED"
        - auto_processed: bool
        - escalation_reason: str or None
    """

    product_name = order.get("product_name", "your item")
    order_status = order.get("order_status", order.get("status", "Unknown"))
    order_id = order.get("order_id", "N/A")
    price = order.get("price", 0)

    # Step 1: Check confidence threshold for the intent
    threshold = INTENT_CONFIDENCE_THRESHOLDS.get(intent, STATUS_THRESHOLD)
    low_confidence = confidence < threshold

    # Step 2: Check if high-value order needs extra scrutiny
    is_high_value = price and price > HIGH_VALUE_THRESHOLD

    # ---- TRACK ORDER ----
    if intent == "TRACK_ORDER":
        result = _handle_tracking(order)
        # Tracking is always auto-resolved regardless of confidence
        return result

    # ---- CANCEL ORDER ----
    if intent == "CANCEL_ORDER":
        result = _handle_cancellation_policy(order)
        # If low confidence on cancellation, escalate instead
        if low_confidence and result.get("auto_processed"):
            result["status"] = "ESCALATED"
            result["auto_processed"] = False
            result["escalation_reason"] = f"Low confidence ({round(confidence * 100, 1)}%) for cancellation request"
            result["message"] = (
                f"We've received your cancellation request for order #{order_id}. "
                f"Your request requires additional review by our support team. "
                f"A specialist will process this within 24 hours."
            )
        return result

    # ---- REFUND REQUEST ----
    if intent == "REFUND_REQUEST":
        result = _handle_refund(order)
        # Escalate high-value refunds or low confidence
        if is_high_value and result.get("auto_processed"):
            result["status"] = "ESCALATED"
            result["auto_processed"] = False
            result["escalation_reason"] = f"High-value refund (₹{price:,.0f}) requires admin approval"
            result["message"] += (
                f"\n\nNote: Due to the order value (₹{price:,.0f}), your refund request "
                f"has been forwarded to our senior support team for expedited processing."
            )
        elif low_confidence:
            result["status"] = "ESCALATED"
            result["auto_processed"] = False
            result["escalation_reason"] = f"Low confidence ({round(confidence * 100, 1)}%) for refund request"
        return result

    # ---- DAMAGED PRODUCT ----
    if intent == "DAMAGED_PRODUCT":
        return _handle_damage(order, return_reason=return_reason)

    # ---- MISMATCH PRODUCT ----
    if intent == "MISMATCH_PRODUCT":
        return _handle_mismatch(order, return_reason=return_reason)

    # ---- GENERAL QUERY / FALLBACK ----
    return {
        "message": (
            "Thank you for reaching out to LogiAI Support. "
            "We were unable to automatically process your request. "
            "Your query has been escalated to a support specialist. "
            "Our team will respond within 24 hours."
        ),
        "status": "ESCALATED",
        "auto_processed": False,
        "escalation_reason": "General query or unrecognized intent",
    }


def _handle_tracking(order: dict) -> dict:
    product_name = order.get("product_name", "your item")
    order_status = order.get("order_status", order.get("status", "Unknown"))
    order_id = order.get("order_id", "N/A")
    delivery_date = order.get("delivery_date")

    status_messages = {
        "Placed": (
            f"📤 Order Dispatched!\n\n"
            f"Your order #{order_id} for {product_name} has been placed and is being prepared for dispatch.\n"
            f"📦 We'll notify you once it ships."
        ),
        "Processing": (
            f"🛠 Order Processing\n\n"
            f"Your order #{order_id} for {product_name} is currently being processed.\n"
            f"⏳ Expected dispatch within 1–2 business days."
        ),
        "Shipped": (
            f"🚛 In Transit\n\n"
            f"Your order #{order_id} for {product_name} has been shipped and is on its way!\n"
            f"📧 You will receive tracking details via email shortly."
        ),
        "Out for Delivery": (
            f"🚚 Out for Delivery!\n\n"
            f"Great news! Your order #{order_id} for {product_name} is out for delivery.\n"
            f"📍 It will arrive today — please ensure someone is available to receive it."
        ),
        "Delivered": (
            f"📦 Delivered Successfully!\n\n"
            f"Your order #{order_id} for {product_name} was delivered on {delivery_date or 'a recent date'}.\n"
            f"✅ We hope you enjoy your purchase! If you have any concerns, feel free to reach out."
        ),
        "Cancelled": (
            f"❌ Order Cancelled\n\n"
            f"Your order #{order_id} for {product_name} has been cancelled.\n"
            f"💳 If a payment was made, a refund will be initiated within 5–7 business days.\n"
            f"If you did not request this, please contact our support team immediately."
        ),
    }

    message = status_messages.get(
        order_status,
        f"Your order #{order_id} for {product_name} is currently in '{order_status}' status. Please check back later for updates."
    )

    return {
        "message": message,
        "status": "AUTO_RESOLVED",
        "auto_processed": True,
        "escalation_reason": None,
    }


def _handle_cancellation_policy(order: dict) -> dict:
    product_name = order.get("product_name", "your item")
    order_status = order.get("order_status", order.get("status", "Unknown"))
    order_id = order.get("order_id", "N/A")

    # Cancellable statuses
    if order_status.upper() in ["PROCESSING", "PLACED"]:
        cancel_result = cancel_order(order_id)
        if cancel_result["success"]:
            return {
                "message": (
                    f"Your order #{order_id} for {product_name} has been successfully cancelled. "
                    f"Any payment made will be refunded within 5-7 business days."
                ),
                "status": "AUTO_RESOLVED",
                "auto_processed": True,
                "escalation_reason": None,
            }
        else:
            return {
                "message": cancel_result["message"],
                "status": "ESCALATED",
                "auto_processed": False,
                "escalation_reason": "Cancellation failed: " + cancel_result["message"],
            }

    # Non-cancellable statuses
    if order_status.upper() in ["SHIPPED", "OUT FOR DELIVERY", "OUT_FOR_DELIVERY"]:
        return {
            "message": (
                f"We're sorry, but your order #{order_id} for {product_name} is already "
                f"'{order_status}' and cannot be cancelled at this stage. "
                f"You may initiate a return after delivery if needed."
            ),
            "status": "ESCALATED",
            "auto_processed": False,
            "escalation_reason": f"Order already {order_status} — cancellation denied",
        }

    if order_status.upper() == "DELIVERED":
        return {
            "message": (
                f"Your order #{order_id} for {product_name} has already been delivered. "
                f"Cancellation is no longer available. Please initiate a return or refund request instead."
            ),
            "status": "ESCALATED",
            "auto_processed": False,
            "escalation_reason": "Order already delivered — cancellation not possible",
        }

    return {
        "message": (
            f"We are unable to process the cancellation for order #{order_id} at this time. "
            f"Your request has been escalated to our support team."
        ),
        "status": "ESCALATED",
        "auto_processed": False,
        "escalation_reason": f"Unknown order status: {order_status}",
    }


def _handle_refund(order: dict) -> dict:
    refund_result = process_refund(order)
    status = "AUTO_RESOLVED" if refund_result["eligible"] else "ESCALATED"
    escalation_reason = None if refund_result["eligible"] else "Refund not eligible based on policy"
    return {
        "message": refund_result["message"],
        "status": status,
        "auto_processed": refund_result["eligible"],
        "refund_details": refund_result,
        "escalation_reason": escalation_reason,
    }


def _handle_damage(order: dict, return_reason: str = None) -> dict:
    product_name = order.get("product_name", "your item")
    order_id = order.get("order_id", "N/A")

    # Build reason-specific messaging
    reason_detail = ""
    if return_reason:
        reason_map = {
            "damaged_packaging": "damaged packaging",
            "product_defective": "a defective product",
            "product_broken": "a broken product",
        }
        reason_detail = f" regarding {reason_map.get(return_reason, return_reason)}"

    return {
        "message": (
            f"We are truly sorry to hear that your {product_name} (Order #{order_id}) arrived damaged{reason_detail}. "
            f"A replacement request has been initiated for your order. "
            f"Please upload images of the damaged product via the support portal within 48 hours "
            f"to help us expedite the process. Our team will review and confirm the replacement within 24 hours."
        ),
        "status": "ESCALATED",
        "auto_processed": False,
        "escalation_reason": f"Damaged product report{reason_detail}",
    }


def _handle_mismatch(order: dict, return_reason: str = None) -> dict:
    product_name = order.get("product_name", "your item")
    order_id = order.get("order_id", "N/A")

    reason_detail = ""
    if return_reason:
        reason_map = {
            "wrong_item": "a completely wrong item",
            "wrong_color": "the wrong color",
            "wrong_size": "the wrong size",
        }
        reason_detail = f" — specifically, {reason_map.get(return_reason, return_reason)}"

    return {
        "message": (
            f"We apologize for the inconvenience. It appears you received a different item "
            f"instead of {product_name} (Order #{order_id}){reason_detail}. "
            f"A replacement process has been initiated. Please upload images of the received item "
            f"via the support portal within 48 hours. "
            f"Once verified, we will ship the correct product to you at no additional cost."
        ),
        "status": "ESCALATED",
        "auto_processed": False,
        "escalation_reason": f"Product mismatch report{reason_detail}",
    }
