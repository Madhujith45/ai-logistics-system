# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.auth import (
    authenticate_user, create_access_token, decode_token,
    authenticate_customer, create_user_token, get_current_user,
    get_password_hash,
)
from app.schemas import ChatRequest, UserRegisterRequest, UserLoginRequest
from app.intent_service import classify_intent
from app.policy_engine import handle_cancellation, apply_policy
from app.order_service import get_order
from app.response_generator import generate_professional_response
from app.database import (
    init_db,
    create_ticket,
    get_all_tickets,
    get_pending_tickets,
    update_ticket,
    get_ticket_by_id,
    get_tickets_by_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_orders_by_user,
    get_all_orders,
    save_conversation_message,
    get_conversation_by_ticket,
    get_user_conversations,
    assign_orders_to_user,
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
# Startup: initialise database + seed
# -----------------------------------

@app.on_event("startup")
def on_startup():
    init_db()
    from app.seed_data import seed_all
    seed_all()


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
        data={"sub": user["username"], "role": user["role"], "user_id": user.get("user_id")}
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

    # Step 1: Classify intent (enhanced with categorized intents)
    result = classify_intent(request.text)

    intent = result["intent"]
    confidence = result["confidence"]
    auto_processed = result["auto_processed"]

    message = ""
    success_flag = auto_processed
    ticket_status = "ESCALATED"
    order = None
    escalation_reason = None

    # Step 1b: Handle greetings — auto-resolve without escalation
    GREETINGS = {"hi", "hey", "hello", "hii", "hiii", "heyy", "yo", "sup", "good morning", "good afternoon", "good evening"}
    if request.text.strip().lower() in GREETINGS:
        message = (
            "👋 Hello! Welcome to LogiAI Support.\n\n"
            "I can help you with:\n"
            "• 📦 Track your order\n"
            "• ❌ Cancel an order\n"
            "• 💳 Request a refund\n\n"
            "Just type your query or provide your Order ID to get started!"
        )
        intent = "GREETING"
        ticket_status = "AUTO_RESOLVED"
        success_flag = True

    # Step 2: Fetch order if order_id is provided
    if request.order_id:
        order = get_order(request.order_id)

    # Step 3: Apply the enhanced policy engine if we have an order
    if intent == "GREETING":
        pass  # Already handled above

    elif order and intent in [
        "TRACK_ORDER", "CANCEL_ORDER", "REFUND_REQUEST",
        "DAMAGED_PRODUCT", "MISMATCH_PRODUCT"
    ]:
        policy_result = apply_policy(intent, order, confidence=confidence, return_reason=getattr(request, 'return_reason', None))
        message = generate_professional_response(intent, policy_result, order)
        ticket_status = policy_result.get("status", "ESCALATED")
        success_flag = policy_result.get("auto_processed", False)
        escalation_reason = policy_result.get("escalation_reason")

    else:
        # ------- ORIGINAL LOGIC (preserved for backward compat) -------
        if intent == "ESCALATE_TO_HUMAN" or intent == "GENERAL_QUERY":
            message = (
                "Thank you for reaching out to LogiAI Support. "
                "We were unable to automatically process your request. "
                "Your query has been escalated to a support specialist. "
                "Our team will respond within 24 hours."
            )
            success_flag = False
            escalation_reason = "Low confidence or general query"

        elif intent in ["ORDER_CANCELLATION", "CANCEL_ORDER"]:
            if not request.order_id:
                message = "To process your cancellation request, please provide your Order ID."
                ticket_status = "IN_PROGRESS"  # Bot is handling — not escalated
            else:
                cancellation_result = handle_cancellation(request.order_id)
                message = cancellation_result["message"]
                success_flag = cancellation_result["success"]

        elif intent in ["ORDER_STATUS", "TRACK_ORDER"]:
            if not request.order_id:
                message = "To track your order, please provide your Order ID."
                ticket_status = "IN_PROGRESS"  # Bot is handling — not escalated
            else:
                fetched_order = get_order(request.order_id)
                if not fetched_order:
                    message = "We couldn't find an order with that ID. Please double-check and try again."
                    success_flag = False
                else:
                    product_name = fetched_order.get("product_name", "your item")
                    status_val = fetched_order.get("order_status", fetched_order.get("status", "Unknown"))
                    message = f"Your order for {product_name} is currently: {status_val}."
                    success_flag = True

        elif intent == "REFUND_REQUEST":
            if not request.order_id:
                message = "To process your refund request, please provide your Order ID."
                ticket_status = "IN_PROGRESS"  # Bot is handling — not escalated
            else:
                fetched_order = get_order(request.order_id)
                if not fetched_order:
                    message = "We couldn't find an order with that ID. Please double-check and try again."
                    success_flag = False
                else:
                    policy_result = apply_policy(intent, fetched_order, confidence=confidence, return_reason=getattr(request, 'return_reason', None))
                    message = generate_professional_response(intent, policy_result, fetched_order)
                    ticket_status = policy_result.get("status", "ESCALATED")
                    success_flag = policy_result.get("auto_processed", False)
                    escalation_reason = policy_result.get("escalation_reason")

        elif intent in ["DAMAGED_PRODUCT", "MISMATCH_PRODUCT"]:
            if not request.order_id:
                label = "damaged product" if intent == "DAMAGED_PRODUCT" else "wrong/mismatched product"
                message = f"We're sorry to hear you received a {label}. To proceed, please provide your Order ID so we can look up your order."
                ticket_status = "IN_PROGRESS"  # Bot is handling — not escalated
            else:
                fetched_order = get_order(request.order_id)
                if not fetched_order:
                    message = "We couldn't find an order with that ID. Please double-check and try again."
                    success_flag = False
                else:
                    policy_result = apply_policy(intent, fetched_order, confidence=confidence, return_reason=getattr(request, 'return_reason', None))
                    message = generate_professional_response(intent, policy_result, fetched_order)
                    ticket_status = policy_result.get("status", "ESCALATED")
                    success_flag = policy_result.get("auto_processed", False)
                    escalation_reason = policy_result.get("escalation_reason")

        else:
            message = (
                "Thank you for contacting LogiAI Support. "
                "We were unable to automatically process your request. "
                "Your query has been escalated to a support specialist who will respond within 24 hours."
            )
            success_flag = False
            escalation_reason = "Unrecognized intent"

        # Only override ticket_status if it wasn't already set (e.g. IN_PROGRESS)
        if ticket_status == "ESCALATED":
            ticket_status = "AUTO_RESOLVED" if success_flag else "ESCALATED"

    # Step 4: Map ticket_status — ensure backward compatible values
    db_status = ticket_status
    if ticket_status == "ESCALATED":
        db_status = "PENDING_ADMIN"

    # Step 5: Resolve user_id
    user_id = getattr(request, 'user_id', None)

    # Step 6: Create ticket (AI query log)
    ticket = create_ticket({
        "text": request.text,
        "order_id": request.order_id,
        "intent": intent,
        "confidence": confidence,
        "status": db_status,
        "message": message,
        "user_id": user_id,
        "escalation_reason": escalation_reason,
    })

    # Step 7: Return backward-compatible response
    return {
        "ticket_id": ticket["ticket_id"],
        "intent": intent,
        "confidence": confidence,
        "status": db_status,
        "message": message
    }

# -----------------------------------
# PUBLIC ROUTES
# -----------------------------------

@app.get("/track/{order_id}")
def track_order_public(order_id: str):
    """Public order tracking — no login required."""
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order["order_id"],
        "status": order["order_status"],
        "product_name": order.get("product_name", "N/A"),
        "customer_name": order.get("customer_name", "N/A"),
        "origin": order.get("origin"),
        "destination": order.get("destination"),
        "expected_delivery": order.get("expected_delivery"),
        "delivery_date": order.get("delivery_date"),
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

@app.get("/admin/orders")
def admin_orders(payload=Depends(require_admin)):
    """Get all orders for admin dashboard."""
    return get_all_orders()


@app.get("/admin/metrics")
def admin_metrics(payload=Depends(require_admin)):
    tickets = get_all_tickets()
    orders = get_all_orders()

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

    # Intent distribution for pie chart
    intent_counts = {}
    for t in tickets:
        intent = t.get("intent", "UNKNOWN")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    intent_distribution = [
        {"name": k.replace("_", " ").title(), "value": v}
        for k, v in intent_counts.items()
    ]

    # Order stats
    total_orders = len(orders)
    active_shipments = sum(1 for o in orders if o["status"] in ["Processing", "Shipped", "Out for Delivery"])
    delivered_orders = sum(1 for o in orders if o["status"] == "Delivered")
    cancelled_orders = sum(1 for o in orders if o["status"] == "Cancelled")

    return {
        "total_tickets": total,
        "auto_resolved": auto_resolved,
        "pending_escalations": pending,
        "approved": approved,
        "rejected": rejected,
        "average_confidence": round(avg_confidence, 3),
        "escalation_rate_percent": round(escalation_rate, 2),
        "intent_distribution": intent_distribution,
        "total_orders": total_orders,
        "active_shipments": active_shipments,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
    }


# -----------------------------------
# USER REGISTRATION & LOGIN (NEW)
# -----------------------------------

@app.post("/user/register")
def user_register(req: UserRegisterRequest):
    """Register a new customer user."""
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    password_hash = get_password_hash(req.password)
    user = create_user(
        name=req.name,
        email=req.email,
        password_hash=password_hash,
        role="USER",
    )

    # Assign sample orders to the new user so they have purchase history
    assign_orders_to_user(user["id"])

    token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": user["id"],
            "name": user["name"],
            "role": user["role"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "name": user["name"],
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        }
    }


@app.post("/user/login")
def user_login(req: UserLoginRequest):
    """Login for customer users."""
    user = authenticate_customer(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_user_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "name": user["name"],
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        }
    }


@app.get("/user/profile")
def user_profile(token: str = Depends(oauth2_scheme)):
    """Get current user profile from token."""
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )
    user_id = payload.get("user_id")
    if user_id:
        user = get_user_by_id(user_id)
        if user:
            return user
    # Fallback for admin tokens
    return {
        "id": None,
        "name": payload.get("sub", "Admin"),
        "email": payload.get("sub"),
        "role": payload.get("role", "admin"),
    }


@app.get("/user/orders")
def user_orders(token: str = Depends(oauth2_scheme)):
    """Get purchase history for the logged-in user."""
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        return []
    return get_orders_by_user(user_id)


@app.get("/user/tickets")
def user_tickets(token: str = Depends(oauth2_scheme)):
    """Get all tickets for the logged-in user."""
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        return []
    return get_tickets_by_user(user_id)


@app.get("/user/conversations")
def user_conversations(token: str = Depends(oauth2_scheme)):
    """Get all conversation history for the logged-in user."""
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        return []
    return get_user_conversations(user_id)


# -----------------------------------
# ADMIN ENHANCED ROUTES (NEW, appended)
# -----------------------------------

@app.get("/admin/ticket/{ticket_id}")
def admin_ticket_detail(ticket_id: str, payload=Depends(require_admin)):
    """Get full ticket details including conversation history for admin review."""
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Attach conversation history
    conversation = get_conversation_by_ticket(ticket_id)
    ticket["conversation"] = conversation

    # Attach order details if available
    if ticket.get("order_id"):
        order = get_order(ticket["order_id"])
        if order:
            ticket["order_details"] = order

    return ticket


@app.post("/admin/resolve/{ticket_id}")
def admin_resolve_ticket(ticket_id: str, payload=Depends(require_admin)):
    """Mark a ticket as resolved by admin."""
    ticket = update_ticket(
        ticket_id,
        "RESOLVED",
        "This ticket has been reviewed and resolved by our support team."
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket