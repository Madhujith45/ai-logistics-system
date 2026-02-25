from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, text as sa_text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import uuid
import logging
import json

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./tickets.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# -----------------------------------
# User Model (Multi-user support)
# -----------------------------------

class UserAccount(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="USER")
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------------
# Order Model (Purchase history)
# -----------------------------------

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    product_name = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    payment_mode = Column(String, nullable=True)
    order_status = Column(String, nullable=True)
    order_date = Column(String, nullable=True)
    delivery_date = Column(String, nullable=True)
    return_deadline = Column(String, nullable=True)
    refund_status = Column(String, nullable=True)


# -----------------------------------
# Ticket Model
# -----------------------------------

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True, index=True)
    text = Column(String, nullable=False)
    order_id = Column(String, nullable=True)
    intent = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    # Extended columns
    payment_mode = Column(String, nullable=True)
    order_status = Column(String, nullable=True)
    delivery_date = Column(String, nullable=True)
    refund_status = Column(String, nullable=True)
    return_window_days = Column(Integer, nullable=True, default=7)
    # New columns for enhanced features
    user_id = Column(Integer, nullable=True)
    escalation_reason = Column(String, nullable=True)
    conversation_history = Column(Text, nullable=True)
    admin_decision = Column(String, nullable=True)
    return_reason = Column(String, nullable=True)


# -----------------------------------
# Conversation Model (Chat history per user)
# -----------------------------------

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String, nullable=True, index=True)
    ticket_id = Column(String, nullable=True)
    sender = Column(String, nullable=False)  # "user" or "bot"
    message = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# -----------------------------------
# Safe Migration: Add new columns
# -----------------------------------

def _safe_add_column(table_name: str, column_name: str, column_type: str, default=None):
    """Append a column to a table if it does not already exist."""
    try:
        with engine.connect() as conn:
            ddl = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default is not None:
                ddl += f" DEFAULT {default}"
            conn.execute(sa_text(ddl))
            conn.commit()
            logger.info(f"Added column '{column_name}' to {table_name} table.")
    except Exception:
        # Column likely already exists — safe to ignore
        pass


# Tickets table migrations
_safe_add_column("tickets", "payment_mode", "TEXT")
_safe_add_column("tickets", "order_status", "TEXT")
_safe_add_column("tickets", "delivery_date", "TEXT")
_safe_add_column("tickets", "refund_status", "TEXT")
_safe_add_column("tickets", "return_window_days", "INTEGER", default=7)
_safe_add_column("tickets", "user_id", "INTEGER")
_safe_add_column("tickets", "escalation_reason", "TEXT")
_safe_add_column("tickets", "conversation_history", "TEXT")
_safe_add_column("tickets", "admin_decision", "TEXT")
_safe_add_column("tickets", "return_reason", "TEXT")


# -----------------------------------
# Helper: Serialize
# -----------------------------------

def serialize_ticket(ticket):
    data = {
        "ticket_id": ticket.ticket_id,
        "text": ticket.text,
        "order_id": ticket.order_id,
        "intent": ticket.intent,
        "confidence": ticket.confidence,
        "status": ticket.status,
        "message": ticket.message,
        "timestamp": ticket.timestamp.isoformat()
    }
    # Append new fields if present (backward compatible)
    if ticket.payment_mode is not None:
        data["payment_mode"] = ticket.payment_mode
    if ticket.order_status is not None:
        data["order_status"] = ticket.order_status
    if ticket.delivery_date is not None:
        data["delivery_date"] = ticket.delivery_date
    if ticket.refund_status is not None:
        data["refund_status"] = ticket.refund_status
    if ticket.return_window_days is not None:
        data["return_window_days"] = ticket.return_window_days
    # New fields
    if ticket.user_id is not None:
        data["user_id"] = ticket.user_id
    if ticket.escalation_reason is not None:
        data["escalation_reason"] = ticket.escalation_reason
    if ticket.conversation_history is not None:
        try:
            data["conversation_history"] = json.loads(ticket.conversation_history)
        except (json.JSONDecodeError, TypeError):
            data["conversation_history"] = ticket.conversation_history
    if ticket.admin_decision is not None:
        data["admin_decision"] = ticket.admin_decision
    if ticket.return_reason is not None:
        data["return_reason"] = ticket.return_reason
    return data


def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def serialize_order(order):
    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "product_name": order.product_name,
        "price": order.price,
        "payment_mode": order.payment_mode,
        "order_status": order.order_status,
        "order_date": order.order_date,
        "delivery_date": order.delivery_date,
        "return_deadline": order.return_deadline,
        "refund_status": order.refund_status,
    }


def serialize_conversation(conv):
    return {
        "id": conv.id,
        "user_id": conv.user_id,
        "session_id": conv.session_id,
        "ticket_id": conv.ticket_id,
        "sender": conv.sender,
        "message": conv.message,
        "intent": conv.intent,
        "timestamp": conv.timestamp.isoformat() if conv.timestamp else None,
    }


# -----------------------------------
# CRUD Operations: Tickets
# -----------------------------------

def create_ticket(data):
    db = SessionLocal()
    try:
        # Serialize conversation history to JSON if it's a list
        conv_hist = data.get("conversation_history")
        if isinstance(conv_hist, (list, dict)):
            conv_hist = json.dumps(conv_hist)

        ticket = Ticket(
            ticket_id=str(uuid.uuid4())[:8],
            text=data["text"],
            order_id=data.get("order_id"),
            intent=data["intent"],
            confidence=data["confidence"],
            status=data["status"],
            message=data["message"],
            payment_mode=data.get("payment_mode"),
            order_status=data.get("order_status"),
            delivery_date=data.get("delivery_date"),
            refund_status=data.get("refund_status"),
            return_window_days=data.get("return_window_days", 7),
            user_id=data.get("user_id"),
            escalation_reason=data.get("escalation_reason"),
            conversation_history=conv_hist,
            admin_decision=data.get("admin_decision"),
            return_reason=data.get("return_reason"),
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return serialize_ticket(ticket)
    finally:
        db.close()


def get_all_tickets():
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).order_by(Ticket.timestamp.desc()).all()
        return [serialize_ticket(t) for t in tickets]
    finally:
        db.close()


def get_pending_tickets():
    db = SessionLocal()
    try:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.status == "PENDING_ADMIN")
            .order_by(Ticket.timestamp.desc())
            .all()
        )
        return [serialize_ticket(t) for t in tickets]
    finally:
        db.close()


def update_ticket(ticket_id, status, message):
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

        if not ticket:
            return None

        ticket.status = status
        ticket.message = message
        ticket.admin_decision = status
        db.commit()
        db.refresh(ticket)

        return serialize_ticket(ticket)
    finally:
        db.close()


def get_ticket_by_id(ticket_id):
    """Get a single ticket by ID with full details for admin review."""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return None
        return serialize_ticket(ticket)
    finally:
        db.close()


def get_tickets_by_user(user_id):
    """Get all tickets for a specific user."""
    db = SessionLocal()
    try:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.user_id == user_id)
            .order_by(Ticket.timestamp.desc())
            .all()
        )
        return [serialize_ticket(t) for t in tickets]
    finally:
        db.close()


# -----------------------------------
# CRUD Operations: Users
# -----------------------------------

def create_user(name, email, password_hash, role="USER"):
    db = SessionLocal()
    try:
        user = UserAccount(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return serialize_user(user)
    finally:
        db.close()


def get_user_by_email(email):
    db = SessionLocal()
    try:
        user = db.query(UserAccount).filter(UserAccount.email == email).first()
        if not user:
            return None
        # Return raw data including hash for auth verification
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role,
        }
    finally:
        db.close()


def get_user_by_id(user_id):
    db = SessionLocal()
    try:
        user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
        if not user:
            return None
        return serialize_user(user)
    finally:
        db.close()


# -----------------------------------
# CRUD Operations: Orders (DB-backed)
# -----------------------------------

def create_order_record(data):
    db = SessionLocal()
    try:
        order = Order(
            order_id=data["order_id"],
            user_id=data.get("user_id"),
            product_name=data.get("product_name"),
            price=data.get("price"),
            payment_mode=data.get("payment_mode"),
            order_status=data.get("order_status"),
            order_date=data.get("order_date"),
            delivery_date=data.get("delivery_date"),
            return_deadline=data.get("return_deadline"),
            refund_status=data.get("refund_status"),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return serialize_order(order)
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def get_orders_by_user(user_id):
    db = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.user_id == user_id).all()
        return [serialize_order(o) for o in orders]
    finally:
        db.close()


# -----------------------------------
# CRUD Operations: Conversations
# -----------------------------------

def save_conversation_message(user_id, session_id, ticket_id, sender, message, intent=None):
    """Save a single message to conversation history."""
    db = SessionLocal()
    try:
        conv = Conversation(
            user_id=user_id,
            session_id=session_id,
            ticket_id=ticket_id,
            sender=sender,
            message=message,
            intent=intent,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return serialize_conversation(conv)
    finally:
        db.close()


def get_conversation_by_session(session_id):
    """Get full conversation for a session."""
    db = SessionLocal()
    try:
        convos = (
            db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.timestamp.asc())
            .all()
        )
        return [serialize_conversation(c) for c in convos]
    finally:
        db.close()


def get_conversation_by_ticket(ticket_id):
    """Get full conversation for a ticket (for admin review)."""
    db = SessionLocal()
    try:
        convos = (
            db.query(Conversation)
            .filter(Conversation.ticket_id == ticket_id)
            .order_by(Conversation.timestamp.asc())
            .all()
        )
        return [serialize_conversation(c) for c in convos]
    finally:
        db.close()


def get_user_conversations(user_id):
    """Get all conversations for a user."""
    db = SessionLocal()
    try:
        convos = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.timestamp.desc())
            .all()
        )
        return [serialize_conversation(c) for c in convos]
    finally:
        db.close()


# -----------------------------------
# Seed default orders into DB
# -----------------------------------

def _seed_default_orders():
    """Seed mock orders into the orders table if they don't exist."""
    from app.order_service import mock_orders
    db = SessionLocal()
    try:
        for oid, odata in mock_orders.items():
            exists = db.query(Order).filter(Order.order_id == oid).first()
            if not exists:
                delivery = odata.get("delivery_date")
                return_deadline = None
                if delivery:
                    try:
                        dd = datetime.strptime(delivery, "%Y-%m-%d")
                        return_deadline = (dd + timedelta(days=7)).strftime("%Y-%m-%d")
                    except Exception:
                        pass
                order = Order(
                    order_id=oid,
                    user_id=None,
                    product_name=odata.get("product_name"),
                    price=odata.get("price"),
                    payment_mode=odata.get("payment_mode"),
                    order_status=odata.get("order_status"),
                    order_date=None,
                    delivery_date=delivery,
                    return_deadline=return_deadline,
                    refund_status=None,
                )
                db.add(order)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def assign_orders_to_user(user_id):
    """Assign unowned mock orders to a newly registered user so they have order history."""
    db = SessionLocal()
    try:
        unowned = db.query(Order).filter(Order.user_id == None).all()
        for order in unowned:
            order.user_id = user_id
        db.commit()
        return len(unowned)
    except Exception:
        db.rollback()
        return 0
    finally:
        db.close()


_seed_default_orders()