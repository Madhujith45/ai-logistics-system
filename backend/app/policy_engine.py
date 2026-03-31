# app/policy_engine.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from app.database import (
    get_collection,
    get_policy_by_category,
    increment_return_count,
    order_exists,
    user_exists,
)
from app.order_service import cancel_order, get_order
from app.pickup_service import create_pickup, get_pickup_status, reschedule_pickup
from app.refund_service import (
    create_refund_record,
    get_latest_refund,
    get_refund_options,
    get_refund_timeline,
    process_refund,
)

logger = logging.getLogger(__name__)

DAMAGE_KEYWORDS = {
    "damaged",
    "broken",
    "defective",
    "wrong item",
    "missing parts",
    "scratched",
    "crushed",
    "leakage",
    "not as described",
}


def _today() -> datetime:
    return datetime.utcnow()


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _build_decision(
    *,
    decision: str,
    eligibility: bool,
    reason: str,
    next_steps: list[str],
    message: str,
    refund_options: list[str] | None = None,
    pickup: dict[str, Any] | None = None,
    status: str = "AUTO_RESOLVED",
    auto_processed: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "decision": decision,
        "eligibility": eligibility,
        "reason": reason,
        "next_steps": next_steps,
        "refund_options": refund_options or [],
        "pickup": pickup,
        "message": message,
        "status": status,
        "auto_processed": auto_processed,
    }
    if extra:
        response.update(extra)
    return response


def _is_damage_reason(reason: str | None, intent: str | None = None) -> bool:
    reason_l = (reason or "").strip().lower()
    if intent in {"DAMAGED_PRODUCT", "MISMATCH_PRODUCT"}:
        return True
    return any(keyword in reason_l for keyword in DAMAGE_KEYWORDS)


def _compute_return_eligibility(order: dict, policy: dict) -> tuple[bool, str]:
    delivery_date = _parse_date(order.get("delivery_date"))
    return_days = int(policy.get("return_days", order.get("return_window_days", 7)))

    if not delivery_date:
        return False, "Order is not delivered yet. Return can start only after delivery confirmation."

    if delivery_date.date() > _today().date():
        return False, "Delivery date is in the future. Return request is not allowed yet."

    deadline = delivery_date + timedelta(days=return_days)

    if _today() <= deadline:
        if delivery_date.date() == _today().date():
            return True, "Eligible for same-day return initiation within policy window."
        return True, f"Eligible. Return window is open until {deadline.strftime('%Y-%m-%d')}."

    return False, f"Not eligible. Return window expired on {deadline.strftime('%Y-%m-%d')}."


def _latest_return(order_id: str) -> dict[str, Any] | None:
    return get_collection("returns").find_one({"order_id": order_id}, sort=[("created_at", -1)])


def _a_to_z_eligibility(order: dict, return_doc: dict[str, Any] | None = None) -> dict[str, Any]:
    expected_delivery = _parse_date(order.get("expected_delivery"))
    delivered = str(order.get("raw_status", order.get("status", ""))).lower() == "delivered"

    reasons: list[str] = []

    if expected_delivery and not delivered and _today() > expected_delivery + timedelta(days=3):
        reasons.append("Order not delivered after expected date + 3 days")

    latest_refund = get_latest_refund(order.get("order_id"))
    if latest_refund and latest_refund.get("status") != "completed":
        refund_updated_at = latest_refund.get("updated_at") or latest_refund.get("created_at") or _today()
        if _today() > refund_updated_at + timedelta(days=7):
            reasons.append("Refund not received within expected timeline")

    if return_doc:
        seller_contacted_at = return_doc.get("seller_contacted_at")
        seller_responded_at = return_doc.get("seller_responded_at")
        if seller_contacted_at and not seller_responded_at:
            start = seller_contacted_at if isinstance(seller_contacted_at, datetime) else _today()
            if _today() > start + timedelta(hours=48):
                reasons.append("Seller did not respond within 48 hours")

    if not reasons:
        return {
            "eligible": False,
            "reason": "A-to-Z guarantee conditions are not met.",
            "claim_status": None,
            "resolution_eta": None,
        }

    claims = get_collection("claims")
    existing = claims.find_one({"order_id": order.get("order_id")}, sort=[("created_at", -1)])
    if existing:
        claim_status = existing.get("status", "pending")
    else:
        claim = {
            "order_id": order.get("order_id"),
            "user_id": order.get("user_id"),
            "status": "pending",
            "reasons": reasons,
            "created_at": _today(),
            "updated_at": _today(),
            "appeal_until": (_today() + timedelta(days=30)).strftime("%Y-%m-%d"),
        }
        claims.insert_one(claim)
        claim_status = "pending"

    return {
        "eligible": True,
        "reason": "; ".join(reasons),
        "claim_status": claim_status,
        "resolution_eta": "up to 7 days",
    }


def _validate_order_user(order_id: str, user_id: int | None = None) -> tuple[dict | None, str | None]:
    if not order_exists(order_id):
        return None, "Order not found"

    order = get_order(order_id)
    if not order:
        return None, "Order not found"

    effective_user_id = user_id if user_id is not None else order.get("user_id")
    if effective_user_id is not None and not user_exists(effective_user_id):
        return None, "User not found"

    if user_id is not None and order.get("user_id") not in (None, user_id):
        return None, "Order does not belong to provided user"

    return order, None


def check_return_eligibility(order_id: str) -> dict:
    order, error = _validate_order_user(order_id)
    if error:
        return _build_decision(
            decision="Not Eligible",
            eligibility=False,
            reason=error,
            next_steps=["Verify order_id and retry."],
            message=error,
            status="ESCALATED",
            auto_processed=False,
        )

    policy = get_policy_by_category(order.get("category"))
    eligible, reason = _compute_return_eligibility(order, policy)

    return _build_decision(
        decision="Eligible" if eligible else "Not Eligible",
        eligibility=eligible,
        reason=reason,
        next_steps=[
            "Proceed with /request-return if eligible.",
            "Contact support if you need policy exception review.",
        ],
        message=reason,
        extra={
            "order_id": order_id,
            "category": policy.get("category", "default"),
            "return_days": int(policy.get("return_days", 7)),
        },
    )


def request_return(
    order_id: str,
    reason: str,
    user_id: int | None = None,
    refund_type: str | None = None,
    partial_items: list[str] | None = None,
) -> dict:
    order, error = _validate_order_user(order_id, user_id)
    if error:
        return _build_decision(
            decision="Rejected",
            eligibility=False,
            reason=error,
            next_steps=["Provide valid order_id and user_id."],
            message=error,
            status="ESCALATED",
            auto_processed=False,
            extra={"success": False, "order_id": order_id},
        )

    policy = get_policy_by_category(order.get("category"))
    damage_case = _is_damage_reason(reason)
    non_returnable = bool(policy.get("non_returnable", False))

    if non_returnable and not damage_case:
        msg = "This category is non-returnable unless item is damaged/defective/incorrect."
        return _build_decision(
            decision="Not Eligible",
            eligibility=False,
            reason=msg,
            next_steps=["Raise damage/defect claim with proof if applicable."],
            message=msg,
            status="ESCALATED",
            auto_processed=False,
            extra={"success": False, "order_id": order_id},
        )

    eligible, eligibility_reason = _compute_return_eligibility(order, policy)
    if not eligible:
        return _build_decision(
            decision="Not Eligible",
            eligibility=False,
            reason=eligibility_reason,
            next_steps=["Contact support for exception handling."],
            message=eligibility_reason,
            status="ESCALATED",
            auto_processed=False,
            extra={"success": False, "order_id": order_id},
        )

    returns = get_collection("returns")
    effective_user = user_id if user_id is not None else order.get("user_id")

    verification_status = "pending" if damage_case else "verified"
    return_status = "pending_verification" if damage_case else "approved"

    return_doc = {
        "order_id": order_id,
        "user_id": effective_user,
        "reason": reason,
        "status": return_status,
        "verification_status": verification_status,
        "partial_items": partial_items or [],
        "request_date": _today().strftime("%Y-%m-%d"),
        "created_at": _today(),
        "updated_at": _today(),
        "seller_contacted_at": _today(),
        "seller_responded_at": None,
    }
    returns.insert_one(return_doc)

    abuse = increment_return_count(effective_user)
    pickup = None
    refund_details = None

    if damage_case:
        message = (
            f"I'm sorry to hear that your order arrived damaged! 📹\n\n"
            f"To process your damage claim, please upload a clear video or photo showing:\n"
            f"• The damaged packaging\n"
            f"• The damaged product\n\n"
            f"Click the 📹 upload button above to submit your proof. Our team will review it within 24 hours."
        )
        next_steps = [
            "Click the 📹 upload button to submit damage proof video/photo",
            "Our team reviews and confirms within 24 hours",
            "Replacement or refund is processed immediately",
        ]
        decision = "Pending Verification"
        final_status = "ESCALATED"
        auto_processed = False
    else:
        pickup = create_pickup(order_id)

        if bool(policy.get("replacement_allowed", True)) and bool(order.get("item_available", True)):
            message = "Replacement approved and pickup scheduled."
            decision = "Eligible"
            next_steps = [
                "Keep item ready in original condition.",
                "Pickup partner will collect the parcel.",
                "Replacement shipment will be triggered after pickup scan.",
            ]
        else:
            options = get_refund_options(order.get("payment_mode", "prepaid"))
            selected = (refund_type or options[0]).lower()
            if selected not in options:
                selected = options[0]
            refund_doc = create_refund_record(
                order_id=order_id,
                amount=float(order.get("price", 0) or 0),
                refund_type=selected,
                user_id=effective_user,
                metadata={"source": "return_request"},
            )
            refund_details = {
                "status": refund_doc.get("status"),
                "refund_type": selected,
                "timeline": refund_doc.get("timeline"),
            }
            message = "Return approved. Refund initiated based on selected refund type."
            decision = "Eligible"
            next_steps = [
                "Keep item ready for reverse pickup.",
                "Track refund status from initiated -> processing -> completed.",
            ]

        final_status = "AUTO_RESOLVED"
        auto_processed = True

    logger.info(
        "return_requested order_id=%s user_id=%s damage_case=%s eligible=%s",
        order_id,
        effective_user,
        damage_case,
        eligible,
    )

    return _build_decision(
        decision=decision,
        eligibility=True,
        reason=eligibility_reason,
        next_steps=next_steps,
        refund_options=get_refund_options(order.get("payment_mode", "prepaid")),
        pickup=pickup,
        message=message,
        status=final_status,
        auto_processed=auto_processed,
        extra={
            "success": True,
            "order_id": order_id,
            "return_status": return_status,
            "verification_status": verification_status,
            "video_required": damage_case,
            "refund": refund_details,
            "abuse_detection": abuse,
        },
    )


def register_video_upload(order_id: str, video_url: str) -> dict:
    order, error = _validate_order_user(order_id)
    if error:
        return _build_decision(
            decision="Rejected",
            eligibility=False,
            reason=error,
            next_steps=["Provide valid order_id."],
            message=error,
            status="ESCALATED",
            auto_processed=False,
            extra={"success": False, "order_id": order_id},
        )

    returns = get_collection("returns")
    latest_return = _latest_return(order_id)

    if not latest_return:
        return _build_decision(
            decision="Rejected",
            eligibility=False,
            reason="No return request found for this order.",
            next_steps=["Create return request first using /request-return."],
            message="No return request found for this order.",
            status="ESCALATED",
            auto_processed=False,
            extra={"success": False, "order_id": order_id},
        )

    # Note: Binary video data is already stored by store_upload_with_binary() in main.py
    # We just need to update the returns collection with the upload reference
    returns.update_one(
        {"_id": latest_return["_id"]},
        {
            "$set": {
                "video_url": video_url,
                "video_uploaded": True,
                "verification_status": "pending",
                "status": "pending_verification",
                "updated_at": _today(),
            }
        },
    )

    return _build_decision(
        decision="Pending Verification",
        eligibility=True,
        reason="Damage proof uploaded. Verification is pending.",
        next_steps=[
            "Wait for quality verification.",
            "Refund remains blocked until verification is completed.",
        ],
        message="Proof uploaded successfully.",
        status="ESCALATED",
        auto_processed=False,
        extra={
            "success": True,
            "order_id": order_id,
            "verification_status": "pending",
            "video_url": video_url,
        },
    )


def update_damage_verification(order_id: str, verification_status: str, reviewer_note: str | None = None) -> dict:
    returns = get_collection("returns")
    latest_return = _latest_return(order_id)
    if not latest_return:
        return {"success": False, "message": "No return request found."}

    status = verification_status.lower().strip()
    if status not in {"verified", "rejected", "pending"}:
        return {"success": False, "message": "Invalid verification status."}

    new_return_status = latest_return.get("status", "pending_verification")
    if status == "verified":
        new_return_status = "approved"
    elif status == "rejected":
        new_return_status = "rejected"

    returns.update_one(
        {"_id": latest_return["_id"]},
        {
            "$set": {
                "verification_status": status,
                "status": new_return_status,
                "reviewer_note": reviewer_note,
                "updated_at": _today(),
            }
        },
    )

    if status == "verified":
        create_pickup(order_id)

    return {
        "success": True,
        "order_id": order_id,
        "verification_status": status,
        "return_status": new_return_status,
    }


def get_refund_options_for_order(order_id: str) -> dict:
    order, error = _validate_order_user(order_id)
    if error:
        return {
            "success": False,
            "order_id": order_id,
            "reason": error,
            "refund_options": [],
            "timelines": {},
        }

    latest_return = _latest_return(order_id)
    verification_status = latest_return.get("verification_status") if latest_return else None

    options = get_refund_options(order.get("payment_mode", "prepaid"))
    blocked = verification_status in {"pending", "rejected"}

    return {
        "success": True,
        "order_id": order_id,
        "payment_mode": order.get("payment_mode"),
        "refund_options": options,
        "timelines": {opt: get_refund_timeline(opt) for opt in options},
        "blocked": blocked,
        "block_reason": (
            "Damage verification pending/rejected. Refund is blocked."
            if blocked
            else None
        ),
    }


def schedule_pickup(order_id: str, reschedule_date: str | None = None) -> dict:
    if reschedule_date:
        result = reschedule_pickup(order_id, reschedule_date)
    else:
        result = create_pickup(order_id)

    if not result.get("success"):
        return {
            "success": False,
            "reason": result.get("message", "Unable to schedule pickup."),
            "pickup": get_pickup_status(order_id),
        }

    return {
        "success": True,
        "message": result.get("message", "Pickup scheduled."),
        "pickup": get_pickup_status(order_id),
    }


def handle_cancellation(
    order_id: str,
    user_id: int | None = None,
    partial_items: list[str] | None = None,
    combined_shipment: bool = False,
    cancellation_reason: str | None = None,
):
    return cancel_order(
        order_id=order_id,
        user_id=user_id,
        partial_items=partial_items,
        combined_shipment=combined_shipment,
        cancellation_reason=cancellation_reason,
    )


def apply_policy(intent: str, order: dict, confidence: float = 1.0, return_reason: str | None = None) -> dict:
    order_id = order.get("order_id")
    reason_text = return_reason or ""

    logger.info("policy_eval intent=%s order_id=%s confidence=%.4f", intent, order_id, confidence)

    if intent == "TRACK_ORDER":
        latest_return = _latest_return(order_id)
        a_to_z = _a_to_z_eligibility(order, latest_return)
        status_text = order.get("status", "Unknown")

        return _build_decision(
            decision="Eligible",
            eligibility=True,
            reason="Tracking status resolved.",
            next_steps=["Monitor updates in dashboard."],
            message=f"Order {order_id} is currently '{status_text}'.",
            refund_options=[],
            pickup=get_pickup_status(order_id),
            extra={"a_to_z": a_to_z},
        )

    if intent == "CANCEL_ORDER":
        result = handle_cancellation(order_id=order_id, user_id=order.get("user_id"))
        return _build_decision(
            decision=result.get("decision", "Processed"),
            eligibility=bool(result.get("success", False)),
            reason=result.get("message", "Cancellation processed."),
            next_steps=[result.get("next_steps", "")],
            message=result.get("message", "Cancellation processed."),
            status="AUTO_RESOLVED" if result.get("success") else "ESCALATED",
            auto_processed=bool(result.get("success")),
        )

    if intent == "REFUND_REQUEST":
        latest_return = _latest_return(order_id)
        verification_status = latest_return.get("verification_status") if latest_return else None
        refund_eval = process_refund(order, verification_status=verification_status)

        return _build_decision(
            decision=refund_eval.get("decision", "Processed"),
            eligibility=bool(refund_eval.get("eligible", False)),
            reason="Refund policy evaluated.",
            next_steps=[
                "Use /refund-options to choose payout mode.",
                "If return is required, create /request-return.",
            ],
            message=refund_eval.get("message", "Refund evaluated."),
            refund_options=refund_eval.get("refund_options", []),
            status="AUTO_RESOLVED" if refund_eval.get("eligible") else "ESCALATED",
            auto_processed=bool(refund_eval.get("eligible")),
        )

    if intent in {"DAMAGED_PRODUCT", "MISMATCH_PRODUCT"}:
        outcome = request_return(
            order_id=order_id,
            reason=reason_text or "damaged item",
            user_id=order.get("user_id"),
        )
        return outcome

    return _build_decision(
        decision="Escalated",
        eligibility=False,
        reason="Intent requires manual support handling.",
        next_steps=["Support specialist will respond within 24 hours."],
        message="Query escalated to support specialist.",
        status="ESCALATED",
        auto_processed=False,
    )
