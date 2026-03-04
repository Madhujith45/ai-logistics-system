# app/database.py

"""
Database engine, session factory, and CRUD operations for LogiAI.

Architecture notes:
    - Uses SQLAlchemy ORM with SQLite (development).
    - Swap DATABASE_URL to a PostgreSQL connection string for production
      without changing any business logic.
    - All models are defined in app/models.py.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid
import logging

from app.config import DATABASE_URL

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Engine & Session
# ──────────────────────────────────────────────

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Enable foreign-key enforcement for SQLite
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


# ──────────────────────────────────────────────
# Dependency for FastAPI route injection
# ──────────────────────────────────────────────

def get_db():
    """Yield a DB session and close it when the request is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────
# Initialise tables (called once at startup)
# ──────────────────────────────────────────────

def init_db():
    """Import models so they register with Base, then create all tables."""
    from app.models import User, Order, Ticket  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")


# ──────────────────────────────────────────────
# Serialisation helpers
# ──────────────────────────────────────────────

def serialize_ticket(ticket):
    """Convert a Ticket ORM object to a frontend-compatible dict."""
    return {
        "ticket_id": ticket.ticket_id,
        "text": ticket.user_query,
        "order_id": ticket.order_id,
        "intent": ticket.intent_detected,
        "confidence": ticket.confidence,
        "status": ticket.status,
        "message": ticket.ai_response,
        "timestamp": ticket.created_at.isoformat() if ticket.created_at else None,
        "user_id": ticket.user_id,
        "escalation_reason": ticket.escalation_reason,
        "admin_decision": ticket.admin_decision,
    }


def serialize_user(user):
    """Convert a User ORM object to a dict."""
    return {
        "id": user.id,
        "name": user.name or user.username,
        "email": user.email or user.username,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def serialize_order(order):
    """Convert an Order ORM object to a dict."""
    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "product_name": order.product_name,
        "price": order.price,
        "payment_mode": order.payment_mode,
        "order_status": order.status,
        "status": order.status,
        "origin": order.origin,
        "destination": order.destination,
        "expected_delivery": order.expected_delivery,
        "delivery_date": order.delivery_date,
        "return_window_days": order.return_window_days,
        "refund_status": order.refund_status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


# ──────────────────────────────────────────────
# CRUD — Tickets
# ──────────────────────────────────────────────

def create_ticket(data: dict) -> dict:
    from app.models import Ticket, Order, User

    db = SessionLocal()
    try:
        # Only set order_id FK if the order actually exists in DB
        order_id = data.get("order_id") or None
        if order_id:
            exists = db.query(Order).filter(Order.order_id == order_id).first()
            if not exists:
                order_id = None

        # Only set user_id FK if the user actually exists in DB
        user_id = data.get("user_id")
        if user_id:
            exists = db.query(User).filter(User.id == user_id).first()
            if not exists:
                user_id = None

        ticket = Ticket(
            ticket_id=str(uuid.uuid4())[:8],
            user_query=data["text"],
            order_id=order_id,
            intent_detected=data["intent"],
            confidence=data["confidence"],
            status=data["status"],
            ai_response=data["message"],
            user_id=user_id,
            escalation_reason=data.get("escalation_reason"),
            admin_decision=data.get("admin_decision"),
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return serialize_ticket(ticket)
    finally:
        db.close()


def get_all_tickets() -> list:
    from app.models import Ticket

    db = SessionLocal()
    try:
        tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
        return [serialize_ticket(t) for t in tickets]
    finally:
        db.close()


def get_pending_tickets() -> list:
    from app.models import Ticket

    db = SessionLocal()
    try:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.status == "PENDING_ADMIN")
            .order_by(Ticket.created_at.desc())
            .all()
        )
        return [serialize_ticket(t) for t in tickets]
    finally:
        db.close()


def update_ticket(ticket_id: str, status: str, message: str):
    from app.models import Ticket

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return None

        ticket.status = status
        ticket.ai_response = message
        ticket.admin_decision = status
        db.commit()
        db.refresh(ticket)
        return serialize_ticket(ticket)
    finally:
        db.close()


def get_ticket_by_id(ticket_id: str):
    from app.models import Ticket

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return None
        return serialize_ticket(ticket)
    finally:
        db.close()


def get_tickets_by_user(user_id: int) -> list:
    from app.models import Ticket

    db = SessionLocal()
    try:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.user_id == user_id)
            .order_by(Ticket.created_at.desc())
            .all()
        )
        return [serialize_ticket(t) for t in tickets]
    finally:
        db.close()


# ──────────────────────────────────────────────
# CRUD — Users
# ──────────────────────────────────────────────

def create_user(name: str, email: str, password_hash: str, role: str = "user"):
    from app.models import User

    db = SessionLocal()
    try:
        user = User(
            username=email,           # email doubles as the unique username
            hashed_password=password_hash,
            role=role,
            name=name,
            email=email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return serialize_user(user)
    finally:
        db.close()


def get_user_by_email(email: str):
    from app.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.email == email) | (User.username == email)
        ).first()
        if not user:
            return None
        return {
            "id": user.id,
            "name": user.name or user.username,
            "email": user.email or user.username,
            "password_hash": user.hashed_password,
            "role": user.role,
        }
    finally:
        db.close()


def get_user_by_username(username: str):
    from app.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return {
            "id": user.id,
            "name": user.name or user.username,
            "username": user.username,
            "email": user.email or user.username,
            "password_hash": user.hashed_password,
            "role": user.role,
        }
    finally:
        db.close()


def get_user_by_id(user_id: int):
    from app.models import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return serialize_user(user)
    finally:
        db.close()


# ──────────────────────────────────────────────
# CRUD — Orders
# ──────────────────────────────────────────────

def get_all_orders() -> list:
    from app.models import Order

    db = SessionLocal()
    try:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
        return [serialize_order(o) for o in orders]
    finally:
        db.close()


def get_orders_by_user(user_id: int) -> list:
    from app.models import Order

    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.user_id == user_id).all()
        return [serialize_order(o) for o in orders]
    finally:
        db.close()


def assign_orders_to_user(user_id: int) -> int:
    """Assign unowned orders to a newly registered user."""
    from app.models import Order

    db = SessionLocal()
    try:
        unowned = db.query(Order).filter(Order.user_id.is_(None)).all()
        for order in unowned:
            order.user_id = user_id
        db.commit()
        return len(unowned)
    except Exception:
        db.rollback()
        return 0
    finally:
        db.close()


# ──────────────────────────────────────────────
# Conversation-style helpers (backwards compat)
# ──────────────────────────────────────────────

def save_conversation_message(user_id, session_id, ticket_id, sender, message, intent=None):
    """No-op kept for backward compatibility.
    All query/response data is now stored directly in the Tickets table."""
    return None


def get_conversation_by_ticket(ticket_id: str) -> list:
    """Reconstruct conversation from the ticket record itself."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return []
    return [
        {"sender": "user", "message": ticket["text"], "timestamp": ticket["timestamp"]},
        {"sender": "bot", "message": ticket["message"], "intent": ticket["intent"], "timestamp": ticket["timestamp"]},
    ]


def get_user_conversations(user_id: int) -> list:
    """Return all tickets for this user formatted as conversation entries."""
    tickets = get_tickets_by_user(user_id)
    conversations = []
    for t in tickets:
        conversations.append({"sender": "user", "message": t["text"], "timestamp": t["timestamp"], "ticket_id": t["ticket_id"]})
        conversations.append({"sender": "bot", "message": t["message"], "intent": t["intent"], "timestamp": t["timestamp"], "ticket_id": t["ticket_id"]})
    return conversations