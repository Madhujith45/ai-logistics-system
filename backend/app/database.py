# app/database.py

"""
MongoDB Atlas data layer for LogiAI.

This module keeps the same public helpers used by the rest of the app,
while adding production-focused helpers for policies, user risk flags,
and return/refund orchestration.
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from datetime import datetime
from typing import Any

import certifi
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.database import Database

from app.config import (
    MONGODB_DB_NAME,
    MONGODB_TLS_ALLOW_INVALID_CERTS,
    MONGODB_TLS_CA_FILE,
    MONGODB_TLS_DISABLE,
    MONGODB_URI,
)

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db: Database | None = None

# Backward compatibility symbols for legacy SQLAlchemy imports.
Base = object
SessionLocal = None

DEFAULT_RETURN_THRESHOLD = 5


STATUS_DISPLAY_MAP = {
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


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        mongo_kwargs: dict[str, Any] = {
            "serverSelectionTimeoutMS": 3000,
            "connectTimeoutMS": 3000,
            "socketTimeoutMS": 5000,
            "retryWrites": True,
            "appname": "logiai-local",
        }

        uri_lower = MONGODB_URI.lower()
        uses_tls = (
            not MONGODB_TLS_DISABLE
            and (MONGODB_URI.startswith("mongodb+srv://") or "tls=true" in uri_lower)
        )

        if uses_tls:
            mongo_kwargs["tls"] = True
            mongo_kwargs["tlsCAFile"] = MONGODB_TLS_CA_FILE or certifi.where()
            mongo_kwargs["tlsAllowInvalidCertificates"] = MONGODB_TLS_ALLOW_INVALID_CERTS

        _client = MongoClient(
            MONGODB_URI,
            **mongo_kwargs,
        )
    return _client


def mongo_connection_status() -> dict[str, Any]:
    """Return lightweight MongoDB connectivity status for diagnostics."""
    try:
        get_mongo_client().admin.command("ping")
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_database() -> Database:
    global _db
    if _db is None:
        _db = get_mongo_client()[MONGODB_DB_NAME]
    return _db


def get_collection(name: str):
    return get_database()[name]


def get_db():
    """FastAPI dependency compatibility hook."""
    yield get_database()


def _next_sequence(name: str) -> int:
    counters = get_collection("counters")
    doc = counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc.get("value", 1))


def init_db() -> None:
    """Initialize MongoDB indexes and baseline policies."""
    try:
        db = get_database()

        # Users
        # Backfill missing user_id values to keep unique user_id index safe.
        db.users.update_many(
            {
                "$or": [{"user_id": {"$exists": False}}, {"user_id": None}],
                "id": {"$type": "number"},
            },
            [{"$set": {"user_id": "$id"}}],
        )

        db.users.create_index([("id", ASCENDING)], unique=True)
        db.users.create_index(
            [("user_id", ASCENDING)],
            unique=True,
            partialFilterExpression={"user_id": {"$type": "number"}},
        )
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
        db.users.create_index([("google_sub", ASCENDING)], unique=True, sparse=True)
        db.users.create_index([("flagged", ASCENDING)])

        # Orders
        db.orders.create_index([("order_id", ASCENDING)], unique=True)
        db.orders.create_index([("user_id", ASCENDING)])
        db.orders.create_index([("status", ASCENDING)])
        db.orders.create_index([("delivery_date", ASCENDING)])

        # Tickets
        db.tickets.create_index([("ticket_id", ASCENDING)], unique=True)
        db.tickets.create_index([("user_id", ASCENDING)])
        db.tickets.create_index([("created_at", DESCENDING)])

        # Policies / returns / uploads / refunds / pickups / claims
        db.policies.create_index([("category", ASCENDING)], unique=True)

        db.returns.create_index([("order_id", ASCENDING)])
        db.returns.create_index([("user_id", ASCENDING)])
        db.returns.create_index([("status", ASCENDING)])
        db.returns.create_index([("verification_status", ASCENDING)])

        db.uploads.create_index([("order_id", ASCENDING)])
        db.uploads.create_index([("verification_status", ASCENDING)])

        db.refunds.create_index([("order_id", ASCENDING)])
        db.refunds.create_index([("status", ASCENDING)])
        db.refunds.create_index([("updated_at", DESCENDING)])

        db.pickups.create_index([("order_id", ASCENDING)])
        db.pickups.create_index([("status", ASCENDING)])

        db.claims.create_index([("order_id", ASCENDING)])
        db.claims.create_index([("status", ASCENDING)])

        default_policies = [
            {
                "category": "electronics",
                "return_days": 7,
                "replacement_allowed": True,
                "refund_allowed": True,
                "video_required": True,
                "technician_inspection": True,
                "non_returnable": False,
            },
            {
                "category": "amazon_devices",
                "return_days": 7,
                "replacement_allowed": True,
                "refund_allowed": False,
                "video_required": True,
                "technician_inspection": False,
                "non_returnable": False,
            },
            {
                "category": "digital_products",
                "return_days": 3,
                "replacement_allowed": False,
                "refund_allowed": True,
                "video_required": False,
                "technician_inspection": False,
                "non_returnable": True,
            },
            {
                "category": "amazon_bazaar",
                "return_days": 5,
                "replacement_allowed": False,
                "refund_allowed": True,
                "video_required": False,
                "technician_inspection": False,
                "non_returnable": False,
            },
            {
                "category": "fashion",
                "return_days": 10,
                "replacement_allowed": True,
                "refund_allowed": True,
                "video_required": False,
                "technician_inspection": False,
                "non_returnable": False,
            },
            {
                "category": "non_returnable",
                "return_days": 0,
                "replacement_allowed": False,
                "refund_allowed": False,
                "video_required": True,
                "technician_inspection": False,
                "non_returnable": True,
            },
            {
                "category": "default",
                "return_days": 7,
                "replacement_allowed": True,
                "refund_allowed": True,
                "video_required": True,
                "technician_inspection": False,
                "non_returnable": False,
            },
        ]

        for policy in default_policies:
            db.policies.update_one(
                {"category": policy["category"]},
                {"$setOnInsert": policy},
                upsert=True,
            )

        get_mongo_client().admin.command("ping")
        logger.info("MongoDB initialized successfully.")
    except Exception as exc:
        logger.warning("MongoDB initialization skipped: %s", exc)


def get_policy_by_category(category: str | None) -> dict[str, Any]:
    category_key = (category or "default").strip().lower()
    policies = get_collection("policies")
    policy = policies.find_one({"category": category_key})
    if policy:
        return policy
    fallback = policies.find_one({"category": "default"})
    if fallback:
        return fallback
    return {
        "category": "default",
        "return_days": 7,
        "replacement_allowed": True,
        "refund_allowed": True,
        "video_required": True,
        "technician_inspection": False,
        "non_returnable": False,
    }


def user_exists(user_id: int | None) -> bool:
    if user_id is None:
        return False
    return get_collection("users").count_documents({"id": user_id}, limit=1) > 0


def order_exists(order_id: str | None) -> bool:
    if not order_id:
        return False
    return get_collection("orders").count_documents({"order_id": order_id}, limit=1) > 0


def ensure_user_profile(user_id: int | None, name: str | None = None) -> None:
    if user_id is None:
        return
    users = get_collection("users")
    users.update_one(
        {"id": user_id},
        {
            "$setOnInsert": {
                "id": user_id,
                "user_id": user_id,
                "username": f"user_{user_id}",
                "name": name or f"User {user_id}",
                "email": None,
                "hashed_password": "",
                "role": "user",
                "return_count": 0,
                "flagged": False,
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


def increment_return_count(user_id: int | None, threshold: int = DEFAULT_RETURN_THRESHOLD) -> dict[str, Any]:
    if user_id is None:
        return {"return_count": 0, "flagged": False}

    ensure_user_profile(user_id)
    users = get_collection("users")
    updated = users.find_one_and_update(
        {"id": user_id},
        {"$inc": {"return_count": 1}, "$set": {"updated_at": datetime.utcnow()}},
        return_document=ReturnDocument.AFTER,
    )

    count = int(updated.get("return_count", 0)) if updated else 0
    flagged = count > threshold
    if flagged:
        users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "flagged": True,
                    "risk_reason": "High return frequency",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    return {"return_count": count, "flagged": flagged}


def _serialize_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket_id": ticket.get("ticket_id"),
        "text": ticket.get("user_query"),
        "order_id": ticket.get("order_id"),
        "intent": ticket.get("intent_detected"),
        "confidence": ticket.get("confidence"),
        "status": ticket.get("status"),
        "message": ticket.get("ai_response"),
        "timestamp": ticket.get("created_at").isoformat() if ticket.get("created_at") else None,
        "user_id": ticket.get("user_id"),
        "escalation_reason": ticket.get("escalation_reason"),
        "admin_decision": ticket.get("admin_decision"),
    }


def _serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user.get("id"),
        "user_id": user.get("user_id", user.get("id")),
        "name": user.get("name") or user.get("username"),
        "email": user.get("email") or user.get("username"),
        "role": user.get("role", "user"),
        "return_count": user.get("return_count", 0),
        "flagged": bool(user.get("flagged", False)),
        "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
    }


def _serialize_order(order: dict[str, Any]) -> dict[str, Any]:
    raw_status = str(order.get("status", ""))
    display_status = STATUS_DISPLAY_MAP.get(raw_status.lower(), raw_status)

    return {
        "order_id": order.get("order_id"),
        "user_id": order.get("user_id"),
        "customer_name": order.get("customer_name"),
        "product_name": order.get("product_name") or order.get("product") or "your item",
        "product": order.get("product") or order.get("product_name"),
        "category": order.get("category", "default"),
        "price": order.get("price"),
        "payment_mode": order.get("payment_mode"),
        "order_status": display_status,
        "status": display_status,
        "raw_status": raw_status,
        "origin": order.get("origin"),
        "destination": order.get("destination"),
        "order_date": order.get("order_date"),
        "expected_delivery": order.get("expected_delivery"),
        "delivery_date": order.get("delivery_date"),
        "return_window_days": order.get("return_window_days", 7),
        "refund_status": order.get("refund_status"),
        "combined_shipment": bool(order.get("combined_shipment", False)),
        "items": order.get("items", []),
        "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
    }


def create_ticket(data: dict[str, Any]) -> dict[str, Any]:
    now = datetime.utcnow()
    tickets = get_collection("tickets")

    ticket = {
        "ticket_id": str(uuid.uuid4())[:8].upper(),
        "user_query": data["text"],
        "order_id": data.get("order_id") or None,
        "intent_detected": data["intent"],
        "confidence": data.get("confidence"),
        "status": data.get("status", "PENDING_ADMIN"),
        "ai_response": data.get("message", ""),
        "user_id": data.get("user_id"),
        "escalation_reason": data.get("escalation_reason"),
        "admin_decision": data.get("admin_decision"),
        "created_at": now,
    }

    tickets.insert_one(ticket)
    return _serialize_ticket(ticket)


def get_all_tickets() -> list[dict[str, Any]]:
    rows = get_collection("tickets").find().sort("created_at", DESCENDING)
    return [_serialize_ticket(row) for row in rows]


def get_pending_tickets() -> list[dict[str, Any]]:
    rows = (
        get_collection("tickets")
        .find({"status": "PENDING_ADMIN"})
        .sort("created_at", DESCENDING)
    )
    return [_serialize_ticket(row) for row in rows]


def update_ticket(ticket_id: str, status: str, message: str):
    tickets = get_collection("tickets")
    updated = tickets.find_one_and_update(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "status": status,
                "ai_response": message,
                "admin_decision": status,
                "updated_at": datetime.utcnow(),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        return None
    return _serialize_ticket(updated)


def get_ticket_by_id(ticket_id: str):
    ticket = get_collection("tickets").find_one({"ticket_id": ticket_id})
    if not ticket:
        return None
    return _serialize_ticket(ticket)


def get_tickets_by_user(user_id: int) -> list[dict[str, Any]]:
    rows = (
        get_collection("tickets")
        .find({"user_id": user_id})
        .sort("created_at", DESCENDING)
    )
    return [_serialize_ticket(row) for row in rows]


def create_user(
    name: str,
    email: str,
    password_hash: str | None,
    role: str = "user",
    auth_provider: str = "local",
    google_sub: str | None = None,
):
    users = get_collection("users")
    now = datetime.utcnow()

    existing = users.find_one({"$or": [{"email": email}, {"username": email}]})
    if existing:
        return _serialize_user(existing)

    user_id = _next_sequence("users")
    user_doc = {
        "id": user_id,
        "user_id": user_id,
        "username": email,
        "name": name,
        "email": email,
        "hashed_password": password_hash,
        "auth_provider": auth_provider,
        "google_sub": google_sub,
        "role": role.lower(),
        "return_count": 0,
        "flagged": False,
        "created_at": now,
    }
    users.insert_one(user_doc)
    return _serialize_user(user_doc)


def get_user_by_email(email: str):
    user = get_collection("users").find_one({"$or": [{"email": email}, {"username": email}]})
    if not user:
        return None
    return {
        "id": user.get("id"),
        "user_id": user.get("user_id", user.get("id")),
        "name": user.get("name") or user.get("username"),
        "email": user.get("email") or user.get("username"),
        "password_hash": user.get("hashed_password"),
        "auth_provider": user.get("auth_provider", "local"),
        "role": user.get("role", "user"),
        "return_count": user.get("return_count", 0),
        "flagged": bool(user.get("flagged", False)),
    }


def get_user_by_username(username: str):
    user = get_collection("users").find_one({"username": username})
    if not user:
        return None
    return {
        "id": user.get("id"),
        "user_id": user.get("user_id", user.get("id")),
        "name": user.get("name") or user.get("username"),
        "username": user.get("username"),
        "email": user.get("email") or user.get("username"),
        "password_hash": user.get("hashed_password"),
        "auth_provider": user.get("auth_provider", "local"),
        "role": user.get("role", "user"),
        "return_count": user.get("return_count", 0),
        "flagged": bool(user.get("flagged", False)),
    }


def get_user_by_id(user_id: int):
    user = get_collection("users").find_one({"id": user_id})
    if not user:
        return None
    return _serialize_user(user)


def get_all_orders() -> list[dict[str, Any]]:
    rows = get_collection("orders").find().sort("created_at", DESCENDING)
    return [_serialize_order(row) for row in rows]


def get_orders_by_user(user_id: int) -> list[dict[str, Any]]:
    rows = get_collection("orders").find({"user_id": user_id}).sort("created_at", DESCENDING)
    return [_serialize_order(row) for row in rows]


def assign_orders_to_user(user_id: int) -> int:
    result = get_collection("orders").update_many(
        {"$or": [{"user_id": None}, {"user_id": {"$exists": False}}]},
        {"$set": {"user_id": user_id, "updated_at": datetime.utcnow()}},
    )
    return int(result.modified_count)


def save_conversation_message(user_id, session_id, ticket_id, sender, message, intent=None):
    return None


def get_conversation_by_ticket(ticket_id: str) -> list[dict[str, Any]]:
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return []
    return [
        {"sender": "user", "message": ticket["text"], "timestamp": ticket["timestamp"]},
        {
            "sender": "bot",
            "message": ticket["message"],
            "intent": ticket["intent"],
            "timestamp": ticket["timestamp"],
        },
    ]


def get_user_conversations(user_id: int) -> list[dict[str, Any]]:
    tickets = get_tickets_by_user(user_id)
    conversations: list[dict[str, Any]] = []
    for t in tickets:
        conversations.append(
            {
                "sender": "user",
                "message": t["text"],
                "timestamp": t["timestamp"],
                "ticket_id": t["ticket_id"],
            }
        )
        conversations.append(
            {
                "sender": "bot",
                "message": t["message"],
                "intent": t["intent"],
                "timestamp": t["timestamp"],
                "ticket_id": t["ticket_id"],
            }
        )
    return conversations


def store_upload_with_binary(
    order_id: str,
    filename: str,
    video_data: bytes,
    verification_status: str = "pending",
    content_type: str | None = None,
) -> dict[str, Any]:
    """Store upload evidence with binary video data in MongoDB."""
    uploads = get_collection("uploads")
    doc = {
        "order_id": order_id,
        "filename": filename,
        "video_data": video_data,  # Store as binary in Mongo
        "content_type": content_type or "application/octet-stream",
        "video_size": len(video_data),
        "verification_status": verification_status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = uploads.insert_one(doc)
    return {
        "upload_id": str(result.inserted_id),
        "order_id": order_id,
        "filename": filename,
        "verification_status": verification_status,
        "size_bytes": len(video_data),
    }


def get_uploads_for_order(order_id: str) -> list[dict[str, Any]]:
    """Get all uploads for an order (without binary data in response)."""
    uploads = get_collection("uploads")
    rows = uploads.find({"order_id": order_id}, {"video_data": 0})  # Exclude binary data
    return [
        {
            "upload_id": str(doc.get("_id")),
            "order_id": doc.get("order_id"),
            "filename": doc.get("filename"),
            "verification_status": doc.get("verification_status"),
            "size_bytes": doc.get("video_size", 0),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        }
        for doc in rows
    ]


def get_upload_binary(upload_id: str) -> bytes | None:
    """Retrieve binary video data from upload."""
    from bson import ObjectId
    
    uploads = get_collection("uploads")
    try:
        doc = uploads.find_one({"_id": ObjectId(upload_id)})
        if doc:
            return doc.get("video_data")
    except Exception:
        pass
    return None


def get_upload_file(upload_id: str) -> dict[str, Any] | None:
    """Retrieve upload file with metadata and binary bytes by upload id."""
    from bson import ObjectId

    uploads = get_collection("uploads")
    try:
        doc = uploads.find_one({"_id": ObjectId(upload_id)})
        if not doc:
            return None

        video_data = doc.get("video_data")
        if not video_data:
            return None

        filename = doc.get("filename") or "proof.mp4"
        inferred_type, _ = mimetypes.guess_type(filename)
        resolved_type = doc.get("content_type") or inferred_type or "application/octet-stream"

        return {
            "upload_id": str(doc.get("_id")),
            "filename": filename,
            "content_type": resolved_type,
            "video_data": bytes(video_data),
            "size_bytes": doc.get("video_size", len(video_data)),
        }
    except Exception:
        return None
