# app/seed_data.py

"""
Demo data seeder for LogiAI.

Populates the database with:
    - 1 admin user
    - 3 customer users with unique order histories
    - 15 realistic orders across all statuses
    - Idempotent — safe to call on every startup.

Credentials:
    Admin  : admin / admin123
    User 1 : rahul@logiai.com / rahul123
    User 2 : priya@logiai.com / priya123
    User 3 : amit@logiai.com  / amit123
"""

import logging
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.auth import get_password_hash

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────

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

# ──────────────────────────────────────────────
# Orders  (owner_email links to the user above)
# ──────────────────────────────────────────────

SAMPLE_ORDERS = [
    # ── Rahul Sharma's orders ──
    {
        "order_id": "ORD-1001",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "iPhone 15 Pro Max",
        "price": 159900,
        "payment_mode": "UPI",
        "status": "Processing",
        "origin": "Mumbai Warehouse",
        "destination": "Delhi, India",
        "expected_delivery": "2026-03-08",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-1002",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "Sony WH-1000XM5 Headphones",
        "price": 29990,
        "payment_mode": "CARD",
        "status": "Shipped",
        "origin": "Chennai Hub",
        "destination": "Bangalore, India",
        "expected_delivery": "2026-03-04",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-1003",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "Samsung Galaxy S24 Ultra",
        "price": 129999,
        "payment_mode": "NET_BANKING",
        "status": "Delivered",
        "origin": "Hyderabad Warehouse",
        "destination": "Pune, India",
        "expected_delivery": "2026-02-20",
        "delivery_date": "2026-02-20",
    },
    {
        "order_id": "ORD-1004",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "Nike Air Max 270",
        "price": 12995,
        "payment_mode": "COD",
        "status": "Placed",
        "origin": "Kolkata Hub",
        "destination": "Lucknow, India",
        "expected_delivery": "2026-03-12",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-1005",
        "owner_email": "rahul@logiai.com",
        "customer_name": "Rahul Sharma",
        "product_name": "MacBook Air M3",
        "price": 114990,
        "payment_mode": "CARD",
        "status": "Delivered",
        "origin": "Delhi Warehouse",
        "destination": "Jaipur, India",
        "expected_delivery": "2026-01-12",
        "delivery_date": "2026-01-10",
    },

    # ── Priya Patel's orders ──
    {
        "order_id": "ORD-2001",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "iPad Air (M2)",
        "price": 69900,
        "payment_mode": "UPI",
        "status": "Out for Delivery",
        "origin": "Ahmedabad Warehouse",
        "destination": "Surat, India",
        "expected_delivery": "2026-02-28",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-2002",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Dyson V15 Vacuum Cleaner",
        "price": 62900,
        "payment_mode": "CARD",
        "status": "Delivered",
        "origin": "Mumbai Warehouse",
        "destination": "Nashik, India",
        "expected_delivery": "2026-02-15",
        "delivery_date": "2026-02-14",
    },
    {
        "order_id": "ORD-2003",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Kindle Paperwhite (2025)",
        "price": 15999,
        "payment_mode": "WALLET",
        "status": "Processing",
        "origin": "Chennai Hub",
        "destination": "Coimbatore, India",
        "expected_delivery": "2026-03-06",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-2004",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Levi's 501 Original Jeans",
        "price": 4999,
        "payment_mode": "COD",
        "status": "Shipped",
        "origin": "Bangalore Hub",
        "destination": "Mysore, India",
        "expected_delivery": "2026-03-03",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-2005",
        "owner_email": "priya@logiai.com",
        "customer_name": "Priya Patel",
        "product_name": "Boat Airdopes 141",
        "price": 1299,
        "payment_mode": "UPI",
        "status": "Delivered",
        "origin": "Delhi Warehouse",
        "destination": "Chandigarh, India",
        "expected_delivery": "2026-01-25",
        "delivery_date": "2026-01-24",
    },

    # ── Amit Verma's orders ──
    {
        "order_id": "ORD-3001",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "Dell XPS 15 Laptop",
        "price": 164990,
        "payment_mode": "NET_BANKING",
        "status": "Delivered",
        "origin": "Hyderabad Warehouse",
        "destination": "Vizag, India",
        "expected_delivery": "2026-02-18",
        "delivery_date": "2026-02-17",
    },
    {
        "order_id": "ORD-3002",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "PlayStation 5 Slim",
        "price": 49990,
        "payment_mode": "CARD",
        "status": "Shipped",
        "origin": "Mumbai Warehouse",
        "destination": "Indore, India",
        "expected_delivery": "2026-03-05",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-3003",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "Samsung 55\" OLED TV",
        "price": 134990,
        "payment_mode": "NET_BANKING",
        "status": "Placed",
        "origin": "Delhi Warehouse",
        "destination": "Bhopal, India",
        "expected_delivery": "2026-03-14",
        "delivery_date": None,
    },
    {
        "order_id": "ORD-3004",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "JBL Flip 6 Speaker",
        "price": 11999,
        "payment_mode": "UPI",
        "status": "Delivered",
        "origin": "Kolkata Hub",
        "destination": "Patna, India",
        "expected_delivery": "2026-02-05",
        "delivery_date": "2026-02-04",
    },
    {
        "order_id": "ORD-3005",
        "owner_email": "amit@logiai.com",
        "customer_name": "Amit Verma",
        "product_name": "Adidas Ultraboost 23",
        "price": 16999,
        "payment_mode": "WALLET",
        "status": "Out for Delivery",
        "origin": "Bangalore Hub",
        "destination": "Kochi, India",
        "expected_delivery": "2026-02-28",
        "delivery_date": None,
    },
]

# ──────────────────────────────────────────────
# Demo Tickets (pre-populated for admin dashboard)
# ──────────────────────────────────────────────

SAMPLE_TICKETS = [
    {
        "user_query": "Where is my order ORD-1001?",
        "order_id": "ORD-1001",
        "intent_detected": "TRACK_ORDER",
        "confidence": 0.96,
        "status": "AUTO_RESOLVED",
        "ai_response": "📦 Your order ORD-1001 (iPhone 15 Pro Max) is currently being **Processing** 🛠️.\n\n📍 Route: Mumbai Warehouse → Delhi, India\n📅 Expected Delivery: 2026-03-08",
        "owner_email": "rahul@logiai.com",
        "minutes_ago": 5,
    },
    {
        "user_query": "I want to cancel order ORD-1002",
        "order_id": "ORD-1002",
        "intent_detected": "CANCEL_ORDER",
        "confidence": 0.94,
        "status": "AUTO_RESOLVED",
        "ai_response": "✅ Your order **ORD-1002** (Samsung Galaxy S24 Ultra) has been **cancelled** successfully.\n\n💰 Refund of ₹134999 will be credited to your Credit Card within 5-7 business days.",
        "owner_email": "rahul@logiai.com",
        "minutes_ago": 12,
    },
    {
        "user_query": "Track my order ORD-2001",
        "order_id": "ORD-2001",
        "intent_detected": "TRACK_ORDER",
        "confidence": 0.98,
        "status": "AUTO_RESOLVED",
        "ai_response": "📦 Your order ORD-2001 (MacBook Air M3) is currently **Shipped** 🚛.\n\n📍 Route: Delhi Warehouse → Jaipur, India\n📅 Expected Delivery: 2026-03-05",
        "owner_email": "priya@logiai.com",
        "minutes_ago": 25,
    },
    {
        "user_query": "I received a damaged product for ORD-2004",
        "order_id": "ORD-2004",
        "intent_detected": "DAMAGED_PRODUCT",
        "confidence": 0.91,
        "status": "PENDING_ADMIN",
        "ai_response": "I'm sorry to hear about the damaged product. Your case has been escalated to our support team for immediate review.",
        "escalation_reason": "Damaged product reported — requires admin verification",
        "owner_email": "priya@logiai.com",
        "minutes_ago": 40,
    },
    {
        "user_query": "Where is ORD-3001?",
        "order_id": "ORD-3001",
        "intent_detected": "TRACK_ORDER",
        "confidence": 0.95,
        "status": "AUTO_RESOLVED",
        "ai_response": "📦 Your order ORD-3001 (Sony WH-1000XM5) is **Out for Delivery** 🚚.\n\n📍 Route: Chennai Hub → Hyderabad, India\n📅 Expected Delivery: 2026-02-28",
        "owner_email": "amit@logiai.com",
        "minutes_ago": 55,
    },
    {
        "user_query": "I want a refund for ORD-3004",
        "order_id": "ORD-3004",
        "intent_detected": "REFUND_REQUEST",
        "confidence": 0.92,
        "status": "AUTO_RESOLVED",
        "ai_response": "✅ Your refund request for **ORD-3004** (JBL Flip 6 Speaker) has been approved.\n\n💰 Refund of ₹11999 will be credited to your UPI account within 3-5 business days.",
        "owner_email": "amit@logiai.com",
        "minutes_ago": 70,
    },
    {
        "user_query": "Cancel ORD-2003 please",
        "order_id": "ORD-2003",
        "intent_detected": "CANCEL_ORDER",
        "confidence": 0.93,
        "status": "PENDING_ADMIN",
        "ai_response": "❌ Sorry, your order **ORD-2003** (Dyson V15 Detect) is already **Out for Delivery** and cannot be cancelled at this stage.",
        "escalation_reason": "Cancellation denied — order already out for delivery",
        "owner_email": "priya@logiai.com",
        "minutes_ago": 90,
    },
    {
        "user_query": "I got the wrong item in ORD-1004",
        "order_id": "ORD-1004",
        "intent_detected": "MISMATCH_PRODUCT",
        "confidence": 0.89,
        "status": "PENDING_ADMIN",
        "ai_response": "I'm sorry about the wrong item. Your complaint has been escalated to our team for investigation and resolution.",
        "escalation_reason": "Product mismatch reported — requires admin review",
        "owner_email": "rahul@logiai.com",
        "minutes_ago": 120,
    },
    {
        "user_query": "What is the status of ORD-3005?",
        "order_id": "ORD-3005",
        "intent_detected": "TRACK_ORDER",
        "confidence": 0.97,
        "status": "AUTO_RESOLVED",
        "ai_response": "📦 Your order ORD-3005 (Adidas Ultraboost 23) is **Out for Delivery** 🚚.\n\n📍 Route: Bangalore Hub → Kochi, India\n📅 Expected Delivery: 2026-02-28",
        "owner_email": "amit@logiai.com",
        "minutes_ago": 150,
    },
    {
        "user_query": "Track ORD-1003",
        "order_id": "ORD-1003",
        "intent_detected": "TRACK_ORDER",
        "confidence": 0.96,
        "status": "AUTO_RESOLVED",
        "ai_response": "📦 Your order ORD-1003 (Sony PlayStation 5) has been **Delivered** 📦✅.\n\n📍 Delivered to: Chennai, India\n📅 Delivered on: 2026-02-15",
        "owner_email": "rahul@logiai.com",
        "minutes_ago": 180,
    },
]


# ──────────────────────────────────────────────
# Seed function
# ──────────────────────────────────────────────

def seed_all():
    """Insert seed data if the tables are empty. Idempotent."""
    from app.models import User, Order, Ticket

    db = SessionLocal()
    try:
        # ── Seed all users ────────────────────
        email_to_user_id: dict[str, int] = {}

        for udata in USERS:
            user = db.query(User).filter(User.username == udata["username"]).first()
            if not user:
                user = User(
                    username=udata["username"],
                    name=udata["name"],
                    email=udata["email"],
                    hashed_password=get_password_hash(udata["password"]),
                    role=udata["role"],
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Seeded user: {udata['username']}")
            email_to_user_id[udata["email"]] = user.id

        # ── Seed orders ──────────────────────
        for odata in SAMPLE_ORDERS:
            exists = db.query(Order).filter(Order.order_id == odata["order_id"]).first()
            if exists:
                continue

            owner_id = email_to_user_id.get(odata["owner_email"])

            order = Order(
                order_id=odata["order_id"],
                customer_name=odata["customer_name"],
                product_name=odata["product_name"],
                price=odata["price"],
                payment_mode=odata["payment_mode"],
                status=odata["status"],
                origin=odata["origin"],
                destination=odata["destination"],
                expected_delivery=odata["expected_delivery"],
                delivery_date=odata["delivery_date"],
                return_window_days=7,
                user_id=owner_id,
            )
            db.add(order)

        db.commit()

        # ── Seed demo tickets ────────────────
        existing_tickets = db.query(Ticket).count()
        if existing_tickets == 0:
            now = datetime.utcnow()
            for tdata in SAMPLE_TICKETS:
                owner_id = email_to_user_id.get(tdata["owner_email"])
                ticket = Ticket(
                    ticket_id=f"DEMO-{SAMPLE_TICKETS.index(tdata)+1:03d}",
                    user_query=tdata["user_query"],
                    order_id=tdata["order_id"],
                    intent_detected=tdata["intent_detected"],
                    confidence=tdata["confidence"],
                    status=tdata["status"],
                    ai_response=tdata["ai_response"],
                    user_id=owner_id,
                    escalation_reason=tdata.get("escalation_reason"),
                    admin_decision=None,
                    created_at=now - timedelta(minutes=tdata["minutes_ago"]),
                )
                db.add(ticket)
            db.commit()
            logger.info(f"Seeded {len(SAMPLE_TICKETS)} demo tickets.")

        logger.info("Seed data verified / inserted. "
                     f"{len(USERS)} users, {len(SAMPLE_ORDERS)} orders.")

    except Exception as e:
        db.rollback()
        logger.error(f"Seed error: {e}")
    finally:
        db.close()
