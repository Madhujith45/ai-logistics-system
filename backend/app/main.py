# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.auth import authenticate_user, create_access_token, decode_token
from app.schemas import ChatRequest
from app.intent_service import classify_intent
from app.policy_engine import handle_cancellation
from app.order_service import get_order
from app.database import (
    create_ticket,
    get_all_tickets,
    get_pending_tickets,
    update_ticket
)

# -----------------------------------
# App Initialization
# -----------------------------------

app = FastAPI(title="LogiAI - Logistics AI Backend")

# -----------------------------------
# CORS CONFIGURATION (FIXED)
# -----------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",                      # Local frontend
        "https://ai-logistics-system.vercel.app"     # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# OAuth2 Scheme
# -----------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# -----------------------------------
# Health Check
# -----------------------------------

@app.get("/health")
def health():
    return {"status": "OK"}

# -----------------------------------
# LOGIN
# -----------------------------------

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"]
    }

# -----------------------------------
# TOKEN VALIDATION DEPENDENCY
# -----------------------------------

def require_admin(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return payload

# -----------------------------------
# MAIN CHAT ENDPOINT
# -----------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    result = classify_intent(request.text)

    intent = result["intent"]
    confidence = result["confidence"]
    auto_processed = result["auto_processed"]

    message = ""
    success_flag = auto_processed

    if intent == "ESCALATE_TO_HUMAN":
        message = "Your request has been escalated to a human agent."
        success_flag = False

    elif intent == "ORDER_CANCELLATION":
        if not request.order_id:
            message = "Order ID is required for cancellation."
            success_flag = False
        else:
            cancellation_result = handle_cancellation(request.order_id)
            message = cancellation_result["message"]
            success_flag = cancellation_result["success"]

    elif intent == "ORDER_STATUS":
        if not request.order_id:
            message = "Order ID is required to check status."
            success_flag = False
        else:
            order = get_order(request.order_id)
            if not order:
                message = "Order not found."
                success_flag = False
            else:
                message = f"Your order status is: {order['status']}"
                success_flag = True

    else:
        message = "Could not process your request."
        success_flag = False

    ticket_status = "AUTO_RESOLVED" if success_flag else "PENDING_ADMIN"

    ticket = create_ticket({
        "text": request.text,
        "order_id": request.order_id,
        "intent": intent,
        "confidence": confidence,
        "status": ticket_status,
        "message": message
    })

    return {
        "ticket_id": ticket["ticket_id"],
        "intent": intent,
        "confidence": confidence,
        "status": ticket_status,
        "message": message
    }

# -----------------------------------
# ADMIN ROUTES (PROTECTED)
# -----------------------------------

@app.get("/tickets")
def all_tickets(payload=Depends(require_admin)):
    return get_all_tickets()

@app.get("/escalations")
def escalations(payload=Depends(require_admin)):
    return get_pending_tickets()

@app.post("/admin/approve/{ticket_id}")
def approve_ticket(ticket_id: str, payload=Depends(require_admin)):
    ticket = update_ticket(ticket_id, "APPROVED", "Approved by admin.")
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.post("/admin/reject/{ticket_id}")
def reject_ticket(ticket_id: str, payload=Depends(require_admin)):
    ticket = update_ticket(ticket_id, "REJECTED", "Rejected by admin.")
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/admin/metrics")
def admin_metrics(payload=Depends(require_admin)):
    tickets = get_all_tickets()

    total = len(tickets)
    auto_resolved = sum(1 for t in tickets if t["status"] == "AUTO_RESOLVED")
    pending = sum(1 for t in tickets if t["status"] == "PENDING_ADMIN")
    approved = sum(1 for t in tickets if t["status"] == "APPROVED")
    rejected = sum(1 for t in tickets if t["status"] == "REJECTED")

    avg_confidence = (
        sum(t["confidence"] for t in tickets) / total
        if total else 0
    )

    escalation_rate = (pending / total) * 100 if total else 0

    return {
        "total_tickets": total,
        "auto_resolved": auto_resolved,
        "pending_escalations": pending,
        "approved": approved,
        "rejected": rejected,
        "average_confidence": round(avg_confidence, 3),
        "escalation_rate_percent": round(escalation_rate, 2)
    }