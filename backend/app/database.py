from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid

DATABASE_URL = "sqlite:///./tickets.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


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


Base.metadata.create_all(bind=engine)


# -----------------------------------
# Helper: Serialize
# -----------------------------------

def serialize_ticket(ticket):
    return {
        "ticket_id": ticket.ticket_id,
        "text": ticket.text,
        "order_id": ticket.order_id,
        "intent": ticket.intent,
        "confidence": ticket.confidence,
        "status": ticket.status,
        "message": ticket.message,
        "timestamp": ticket.timestamp.isoformat()
    }


# -----------------------------------
# CRUD Operations
# -----------------------------------

def create_ticket(data):
    db = SessionLocal()
    try:
        ticket = Ticket(
            ticket_id=str(uuid.uuid4())[:8],
            text=data["text"],
            order_id=data.get("order_id"),
            intent=data["intent"],
            confidence=data["confidence"],
            status=data["status"],
            message=data["message"],
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
        db.commit()
        db.refresh(ticket)

        return serialize_ticket(ticket)
    finally:
        db.close()