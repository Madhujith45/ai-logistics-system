# app/seed_data.py

"""MongoDB demo seeder for LogiAI."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.auth import get_password_hash
from app.database import create_ticket, create_user, get_collection, get_user_by_email

logger = logging.getLogger(__name__)

USERS = [
    {
        "username": "admin",
        "name": "Admin",
        "email": "admin@logiai.com",
        "password": "admin123",
        "role": "admin",
    },
    {
        "username": "rahul@logiai.com",
        "name": "Rahul Sharma",
        "email": "rahul@logiai.com",
        "password": "rahul123",
        "role": "user",
    },
    {
        "username": "priya@logiai.com",
        "name": "Priya Patel",
        "email": "priya@logiai.com",
        "password": "priya123",
        "role": "user",
    },
    {
        "username": "amit@logiai.com",
        "name": "Amit Verma",
        "email": "amit@logiai.com",
        "password": "amit123",
        "role": "user",
    },
]

SAMPLE_ORDERS = [
    {
        "order_id": "ORD-1001",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "iPhone 15 Pro Max",
        "product": "iPhone 15 Pro Max",
        "category": "electronics",
        "price": 159900,
        "payment_mode": "prepaid",
        "status": "processing",
        "origin": "Mumbai Warehouse",
        "destination": "Delhi, India",
        "order_date": "2026-02-28",
        "expected_delivery": "2026-03-08",
        "delivery_date": None,
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-1003",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "Samsung Galaxy S24 Ultra",
        "product": "Samsung Galaxy S24 Ultra",
        "category": "electronics",
        "price": 129999,
        "payment_mode": "prepaid",
        "status": "delivered",
        "origin": "Hyderabad Warehouse",
        "destination": "Pune, India",
        "order_date": "2026-02-16",
        "expected_delivery": "2026-02-20",
        "delivery_date": "2026-02-20",
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-1004",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "Nike Air Zoom Pegasus 41",
        "product": "Nike Air Zoom Pegasus 41",
        "category": "fashion",
        "price": 7499,
        "payment_mode": "cod",
        "status": "delivered",
        "origin": "Chennai Hub",
        "destination": "Delhi, India",
        "order_date": "2026-03-12",
        "expected_delivery": "2026-03-16",
        "delivery_date": "2026-03-16",
        "return_window_days": 10,
    },
    {
        "order_id": "ORD-1005",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "Apple Watch Series 10",
        "product": "Apple Watch Series 10",
        "category": "electronics",
        "price": 45999,
        "payment_mode": "prepaid",
        "status": "processing",
        "origin": "Mumbai Warehouse",
        "destination": "Delhi, India",
        "order_date": "2026-03-17",
        "expected_delivery": "2026-03-21",
        "delivery_date": None,
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-2002",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Dyson V15 Vacuum Cleaner",
        "product": "Dyson V15 Vacuum Cleaner",
        "category": "electronics",
        "price": 62900,
        "payment_mode": "prepaid",
        "status": "delivered",
        "origin": "Mumbai Warehouse",
        "destination": "Nashik, India",
        "order_date": "2026-02-10",
        "expected_delivery": "2026-02-15",
        "delivery_date": "2026-02-14",
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-2003",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Amazon Bazaar Wooden Shelf",
        "product": "Amazon Bazaar Wooden Shelf",
        "category": "amazon_bazaar",
        "price": 3899,
        "payment_mode": "prepaid",
        "status": "delivered",
        "origin": "Ahmedabad Warehouse",
        "destination": "Surat, India",
        "order_date": "2026-03-05",
        "expected_delivery": "2026-03-10",
        "delivery_date": "2026-03-10",
        "return_window_days": 5,
    },
    {
        "order_id": "ORD-2004",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "E-Book Subscription (Digital)",
        "product": "E-Book Subscription (Digital)",
        "category": "digital_products",
        "price": 899,
        "payment_mode": "prepaid",
        "status": "delivered",
        "origin": "Digital Fulfillment",
        "destination": "Surat, India",
        "order_date": "2026-03-17",
        "expected_delivery": "2026-03-17",
        "delivery_date": "2026-03-17",
        "return_window_days": 3,
    },
    {
        "order_id": "ORD-2005",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Kindle Paperwhite 2025",
        "product": "Kindle Paperwhite 2025",
        "category": "electronics",
        "price": 15999,
        "payment_mode": "prepaid",
        "status": "shipped",
        "origin": "Chennai Hub",
        "destination": "Surat, India",
        "order_date": "2026-03-16",
        "expected_delivery": "2026-03-20",
        "delivery_date": None,
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-3003",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "Samsung 55 OLED TV",
        "product": "Samsung 55 OLED TV",
        "category": "electronics",
        "price": 134990,
        "payment_mode": "prepaid",
        "status": "ordered",
        "origin": "Delhi Warehouse",
        "destination": "Bhopal, India",
        "order_date": "2026-03-10",
        "expected_delivery": "2026-03-14",
        "delivery_date": None,
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-3004",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "Sony WH-1000XM5 Headphones",
        "product": "Sony WH-1000XM5 Headphones",
        "category": "electronics",
        "price": 29990,
        "payment_mode": "prepaid",
        "status": "delivered",
        "origin": "Hyderabad Warehouse",
        "destination": "Bhopal, India",
        "order_date": "2026-03-10",
        "expected_delivery": "2026-03-14",
        "delivery_date": "2026-03-14",
        "return_window_days": 7,
    },
    {
        "order_id": "ORD-3005",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "Gaming Chair Pro X",
        "product": "Gaming Chair Pro X",
        "category": "non_returnable",
        "price": 14999,
        "payment_mode": "prepaid",
        "status": "delivered",
        "origin": "Delhi Warehouse",
        "destination": "Bhopal, India",
        "order_date": "2026-03-08",
        "expected_delivery": "2026-03-12",
        "delivery_date": "2026-03-12",
        "return_window_days": 0,
    },
    {
        "order_id": "ORD-3006",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "LogiAI Smart Speaker",
        "product": "LogiAI Smart Speaker",
        "category": "electronics",
        "price": 9999,
        "payment_mode": "prepaid",
        "status": "out for delivery",
        "origin": "Delhi Warehouse",
        "destination": "Bhopal, India",
        "order_date": "2026-03-17",
        "expected_delivery": "2026-03-18",
        "delivery_date": None,
        "return_window_days": 7,
    },
]


DEMO_TICKETS = [
    {
        "text": "Where is my order ORD-1001?",
        "order_id": "ORD-1001",
        "intent": "TRACK_ORDER",
        "confidence": 0.96,
        "status": "AUTO_RESOLVED",
        "message": "Your order ORD-1001 is currently processing.",
        "user_email": "rahul@logiai.com",
    },
    {
        "text": "I want a refund for ORD-2002",
        "order_id": "ORD-2002",
        "intent": "REFUND_REQUEST",
        "confidence": 0.93,
        "status": "PENDING_ADMIN",
        "message": "Refund request captured and pending policy check.",
        "user_email": "priya@logiai.com",
    },
    {
        "text": "Cancel my order ORD-1005",
        "order_id": "ORD-1005",
        "intent": "CANCEL_ORDER",
        "confidence": 0.95,
        "status": "AUTO_RESOLVED",
        "message": "Cancellation request captured and processed.",
        "user_email": "rahul@logiai.com",
    },
    {
        "text": "My order ORD-3006 is still not right, please cancel",
        "order_id": "ORD-3006",
        "intent": "CANCEL_ORDER",
        "confidence": 0.88,
        "status": "PENDING_ADMIN",
        "message": "Order is already out for delivery. Cancellation needs review.",
        "user_email": "amit@logiai.com",
    },
    {
        "text": "I received a damaged product for ORD-3004",
        "order_id": "ORD-3004",
        "intent": "DAMAGED_PRODUCT",
        "confidence": 0.92,
        "status": "PENDING_ADMIN",
        "message": "Damage report received. Please upload proof for verification.",
        "user_email": "amit@logiai.com",
    },
    {
        "text": "Wrong item received for ORD-2003",
        "order_id": "ORD-2003",
        "intent": "MISMATCH_PRODUCT",
        "confidence": 0.9,
        "status": "PENDING_ADMIN",
        "message": "Mismatch report received. Upload proof for verification.",
        "user_email": "priya@logiai.com",
    },
    {
        "text": "Refund for ORD-2003",
        "order_id": "ORD-2003",
        "intent": "REFUND_REQUEST",
        "confidence": 0.9,
        "status": "PENDING_ADMIN",
        "message": "Refund request captured. Return window may be expired.",
        "user_email": "priya@logiai.com",
    },
    {
        "text": "Return request for ORD-3005",
        "order_id": "ORD-3005",
        "intent": "REFUND_REQUEST",
        "confidence": 0.87,
        "status": "PENDING_ADMIN",
        "message": "Non-returnable category requires damage proof or exception review.",
        "user_email": "amit@logiai.com",
    },
]


def seed_all() -> None:
    try:
        users_col = get_collection("users")
        orders_col = get_collection("orders")

        email_to_user_id: dict[str, int] = {}

        for u in USERS:
            existing = get_user_by_email(u["email"])
            if existing:
                email_to_user_id[u["email"]] = existing["id"]
                continue

            created = create_user(
                name=u["name"],
                email=u["email"],
                password_hash=get_password_hash(u["password"]),
                role=u["role"],
            )

            # Keep admin login backward-compatible with username="admin"
            if u["username"] == "admin":
                users_col.update_one(
                    {"id": created["id"]},
                    {"$set": {"username": "admin"}},
                )

            email_to_user_id[u["email"]] = created["id"]
            logger.info("Seeded user: %s", u["email"])

        for order in SAMPLE_ORDERS:
            exists = orders_col.find_one({"order_id": order["order_id"]})
            if exists:
                continue

            payload = {
                **order,
                "user_id": email_to_user_id.get(order["owner_email"]),
                "created_at": datetime.utcnow(),
            }
            orders_col.insert_one(payload)

        ticket_count = get_collection("tickets").count_documents({})
        if ticket_count == 0:
            tickets_col = get_collection("tickets")
            for idx, t in enumerate(DEMO_TICKETS):
                user_id = email_to_user_id.get(t["user_email"])
                created_at = datetime.utcnow() - timedelta(minutes=(idx + 1) * 10)
                tickets_col.insert_one(
                    {
                        "ticket_id": f"DEMO-{idx + 1:03d}",
                        "user_query": t["text"],
                        "order_id": t["order_id"],
                        "intent_detected": t["intent"],
                        "confidence": t["confidence"],
                        "status": t["status"],
                        "ai_response": t["message"],
                        "user_id": user_id,
                        "escalation_reason": t.get("escalation_reason"),
                        "admin_decision": None,
                        "created_at": created_at,
                    }
                )

        logger.info("MongoDB seed verification complete.")
    except Exception as exc:
        logger.warning("Seed skipped: MongoDB not reachable or not configured yet (%s)", exc)
