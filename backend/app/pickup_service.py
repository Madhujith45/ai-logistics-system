# app/pickup_service.py

from __future__ import annotations

import logging
from datetime import datetime

from app.database import get_collection
from app.order_service import get_order

logger = logging.getLogger(__name__)

MAX_PICKUP_ATTEMPTS = 3


def _serialize_pickup(doc: dict | None) -> dict | None:
    if not doc:
        return None

    result = {k: v for k, v in doc.items() if k != "_id"}
    for key in ("created_at", "updated_at", "completed_at"):
        if isinstance(result.get(key), datetime):
            result[key] = result[key].isoformat()

    history = result.get("attempt_history")
    if isinstance(history, list):
        normalized = []
        for item in history:
            entry = dict(item)
            if isinstance(entry.get("at"), datetime):
                entry["at"] = entry["at"].isoformat()
            normalized.append(entry)
        result["attempt_history"] = normalized

    return result


def _latest_pickup(order_id: str):
    return get_collection("pickups").find_one({"order_id": order_id}, sort=[("created_at", -1)])


def create_pickup(order_id: str, reschedule_date: str | None = None) -> dict:
    order = get_order(order_id)
    if not order:
        return {
            "success": False,
            "order_id": order_id,
            "status": "failed",
            "attempts": 0,
            "message": "Order not found.",
        }

    pickups = get_collection("pickups")
    existing = _latest_pickup(order_id)

    if existing:
        attempts = int(existing.get("attempts", 0))
        status = str(existing.get("status", "scheduled")).lower()

        if status in {"scheduled", "completed"}:
            return {
                "success": True,
                "order_id": order_id,
                "status": status,
                "attempts": attempts,
                "message": "Pickup already exists for this order.",
            }

        if attempts >= MAX_PICKUP_ATTEMPTS:
            pickups.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "auto_cancelled": True,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return {
                "success": False,
                "order_id": order_id,
                "status": "failed",
                "attempts": attempts,
                "message": "Pickup auto-cancelled after maximum failed attempts.",
            }

    payload = {
        "order_id": order_id,
        "status": "scheduled",
        "attempts": int(existing.get("attempts", 0)) if existing else 0,
        "reschedule_date": reschedule_date,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    pickups.insert_one(payload)

    return {
        "success": True,
        "order_id": order_id,
        "status": "scheduled",
        "attempts": payload["attempts"],
        "message": "Pickup scheduled successfully.",
    }


def register_pickup_attempt(order_id: str, success: bool, failure_reason: str | None = None) -> dict:
    pickups = get_collection("pickups")
    pickup = _latest_pickup(order_id)

    if not pickup:
        return {
            "success": False,
            "message": "Pickup not found for this order.",
        }

    attempts = int(pickup.get("attempts", 0)) + 1
    now = datetime.utcnow()

    if success:
        updated = pickups.find_one_and_update(
            {"_id": pickup["_id"]},
            {
                "$set": {
                    "status": "completed",
                    "attempts": attempts,
                    "completed_at": now,
                    "updated_at": now,
                },
                "$push": {
                    "attempt_history": {
                        "at": now,
                        "result": "completed",
                    }
                },
            },
            return_document=True,
        )
        return {
            "success": True,
            "message": "Pickup completed successfully.",
            "pickup": _serialize_pickup(updated),
        }

    failed_status = "failed" if attempts >= MAX_PICKUP_ATTEMPTS else "scheduled"
    updated = pickups.find_one_and_update(
        {"_id": pickup["_id"]},
        {
            "$set": {
                "status": failed_status,
                "attempts": attempts,
                "failure_reason": failure_reason,
                "updated_at": now,
                "auto_cancelled": attempts >= MAX_PICKUP_ATTEMPTS,
            },
            "$push": {
                "attempt_history": {
                    "at": now,
                    "result": "failed",
                    "reason": failure_reason,
                }
            },
        },
        return_document=True,
    )

    msg = "Pickup attempt failed."
    if attempts >= MAX_PICKUP_ATTEMPTS:
        msg = "Pickup auto-cancelled after 3 failed attempts."

    return {
        "success": True,
        "message": msg,
        "pickup": _serialize_pickup(updated),
    }


def reschedule_pickup(order_id: str, reschedule_date: str | None) -> dict:
    pickups = get_collection("pickups")
    pickup = _latest_pickup(order_id)

    if not pickup:
        return create_pickup(order_id=order_id, reschedule_date=reschedule_date)

    attempts = int(pickup.get("attempts", 0))
    if attempts >= MAX_PICKUP_ATTEMPTS:
        return {
            "success": False,
            "message": "Cannot reschedule. Maximum pickup attempts reached.",
        }

    updated = pickups.find_one_and_update(
        {"_id": pickup["_id"]},
        {
            "$set": {
                "status": "scheduled",
                "reschedule_date": reschedule_date,
                "updated_at": datetime.utcnow(),
            }
        },
        return_document=True,
    )

    return {
        "success": True,
        "message": "Pickup rescheduled successfully.",
        "pickup": _serialize_pickup(updated),
    }


def get_pickup_status(order_id: str) -> dict | None:
    return _serialize_pickup(_latest_pickup(order_id))
