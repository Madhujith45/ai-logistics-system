# app/models.py

"""
SQLAlchemy ORM Models for LogiAI Logistics System.

Tables:
    - Users     : System users (admin / customer)
    - Orders    : Customer orders with tracking info
    - Tickets   : AI query logs linking users, orders, and NLP output

Designed for SQLite in development; swap DATABASE_URL to
PostgreSQL in production without changing business logic.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ──────────────────────────────────────────────
# Users Table
# ──────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Extra fields for frontend compatibility (name / email)
    name = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=True, index=True)

    # Relationships
    orders = relationship("Order", back_populates="user", lazy="select")
    tickets = relationship("Ticket", back_populates="user", lazy="select")

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"


# ──────────────────────────────────────────────
# Orders Table
# ──────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(100), nullable=True)
    origin = Column(String(100), nullable=True)
    destination = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="Processing")
    expected_delivery = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign key to Users
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Additional business-logic fields used by policy / refund engines
    product_name = Column(String(200), nullable=True)
    price = Column(Float, nullable=True)
    payment_mode = Column(String(50), nullable=True)
    delivery_date = Column(String(50), nullable=True)
    return_window_days = Column(Integer, default=7)
    refund_status = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    tickets = relationship("Ticket", back_populates="order", lazy="select")

    def __repr__(self):
        return f"<Order id={self.id} order_id={self.order_id!r} status={self.status!r}>"


# ──────────────────────────────────────────────
# Tickets Table  (AI Query Logs)
# ──────────────────────────────────────────────

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(20), unique=True, nullable=False, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"), nullable=True)

    # Core log fields
    user_query = Column(Text, nullable=False)
    intent_detected = Column(String(50), nullable=False)
    ai_response = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Metadata
    escalation_reason = Column(String(255), nullable=True)
    admin_decision = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="tickets")
    order = relationship("Order", back_populates="tickets")

    def __repr__(self):
        return f"<Ticket id={self.id} ticket_id={self.ticket_id!r} intent={self.intent_detected!r}>"
