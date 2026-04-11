# app/main.py

import importlib
import logging
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.auth import (
    authenticate_customer,
    authenticate_user,
    create_access_token,
    create_user_token,
    decode_token,
    get_current_user,
    get_password_hash,
)
from app.config import BACKEND_CORS_ORIGINS
from app.database import (
    assign_orders_to_user,
    create_ticket,
    create_user,
    get_all_orders,
    get_all_tickets,
    get_conversation_by_ticket,
    get_orders_by_user,
    get_pending_tickets,
    get_ticket_by_id,
    get_tickets_by_user,
    mongo_connection_status,
    get_uploads_for_order,
    get_upload_binary,
    get_upload_file,
    get_user_by_email,
    get_user_by_id,
    get_user_conversations,
    init_db,
    order_exists,
    store_upload_with_binary,
    update_ticket,
    user_exists,
)
from app.intent_service import classify_intent
from app.order_service import get_order
from app.pickup_service import create_pickup
from app.policy_engine import (
    apply_policy,
    check_return_eligibility,
    get_refund_options_for_order,
    handle_cancellation,
    register_video_upload,
    request_return,
    schedule_pickup,
)
from app.response_generator import generate_professional_response
from app.schemas import (
    CancelOrderRequest,
    CancelReasonsResponse,
    ChatRequest,
    PickupRequest,
    RefundOptionsRequest,
    ReturnRequest,
    ReturnReasonsResponse,
    UserGoogleLoginRequest,
    UserLoginRequest,
    UserRegisterRequest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LogiAI - Logistics AI Backend")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_logging_middleware(request: Request, call_next):
    logger.info("api_request method=%s path=%s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("api_error path=%s error=%s", request.url.path, exc)
        raise
    logger.info("api_response path=%s status=%s", request.url.path, response.status_code)
    return response


@app.on_event("startup")
def on_startup():
    init_db()
    from app.seed_data import seed_all

    seed_all()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()


def is_greeting_message(text: str) -> bool:
    cleaned = re.sub(r"\(\s*order\s*[:#-]?[^)]*\)", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", cleaned).lower()
    normalized = " ".join(cleaned.split())

    if not normalized:
        return False

    greeting_keywords = {
        "hi",
        "hey",
        "hello",
        "hii",
        "hiii",
        "heyy",
        "yo",
        "sup",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
    }
    service_keywords = {
        "track",
        "status",
        "cancel",
        "refund",
        "return",
        "damaged",
        "broken",
        "wrong",
        "mismatch",
        "delivery",
        "where is",
        "order",
    }

    has_greeting = any(kw in normalized for kw in greeting_keywords)
    has_service_intent = any(kw in normalized for kw in service_keywords)

    return has_greeting and not has_service_intent


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    status_doc = mongo_connection_status()
    if status_doc.get("ok"):
        return {"status": "OK", "database": "connected"}
    raise HTTPException(
        status_code=503,
        detail={
            "status": "DEGRADED",
            "database": "unreachable",
            "error": status_doc.get("error"),
        },
    )


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
    except Exception as exc:
        logger.exception("login_failed username=%s error=%s", form_data.username, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable. Please try again.",
        )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "user_id": user.get("user_id")}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
    }


def require_admin(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return payload


@app.post("/chat")
def chat(request: ChatRequest):
    # Auto-fix Order ID if it's missing the prefix (e.g. "1004" -> "ORD-1004")
    if request.order_id and request.order_id.isdigit():
        request.order_id = f"ORD-{request.order_id}"

    result = classify_intent(request.text)

    intent = result["intent"]
    confidence = result["confidence"]
    auto_processed = result["auto_processed"]

    message = ""
    success_flag = auto_processed
    ticket_status = "ESCALATED"
    escalation_reason = None
    policy_result: dict = {}

    if is_greeting_message(request.text):
        message = (
            "Hello! Welcome to LogiAI Support.\n\n"
            "I can help you with tracking, cancellation, refund, return, and damage issues.\n"
            "Share your query with order ID to continue."
        )
        intent = "GREETING"
        ticket_status = "AUTO_RESOLVED"
        success_flag = True
    else:
        if request.order_id:
            if not order_exists(request.order_id):
                message = "Order not found. Verify order ID and try again."
                success_flag = False
                ticket_status = "ESCALATED"
                escalation_reason = "order_not_found"
            else:
                order = get_order(request.order_id)
                if order and intent in {
                    "TRACK_ORDER",
                    "CANCEL_ORDER",
                    "REFUND_REQUEST",
                    "DAMAGED_PRODUCT",
                    "MISMATCH_PRODUCT",
                }:
                    policy_result = apply_policy(
                        intent,
                        order,
                        confidence=confidence,
                        return_reason=request.return_reason,
                    )
                    message = generate_professional_response(intent, policy_result, order)
                    ticket_status = policy_result.get("status", "ESCALATED")
                    success_flag = policy_result.get("auto_processed", False)
                    escalation_reason = policy_result.get("reason")
                else:
                    message = "Please provide a valid order query intent."
                    success_flag = False
        else:
            if intent in {"TRACK_ORDER", "CANCEL_ORDER", "REFUND_REQUEST", "DAMAGED_PRODUCT", "MISMATCH_PRODUCT"}:
                message = "Please provide your order ID to continue."
                ticket_status = "IN_PROGRESS"
                success_flag = False
            else:
                message = (
                    "Your query is escalated to support specialist. "
                    "We will respond within 24 hours."
                )
                success_flag = False
                escalation_reason = "general_query"

    if ticket_status == "ESCALATED":
        db_status = "PENDING_ADMIN"
    else:
        db_status = ticket_status if ticket_status != "ESCALATED" else "PENDING_ADMIN"

    user_id = request.user_id
    if user_id is not None and not user_exists(user_id):
        logger.warning("chat_request invalid user_id=%s", user_id)
        user_id = None

    ticket = create_ticket(
        {
            "text": request.text,
            "order_id": request.order_id,
            "intent": intent,
            "confidence": confidence,
            "status": db_status,
            "message": message,
            "user_id": user_id,
            "escalation_reason": escalation_reason,
        }
    )

    return {
        "ticket_id": ticket["ticket_id"],
        "intent": intent,
        "confidence": confidence,
        "status": db_status,
        "message": message,
        "decision": policy_result.get("decision"),
        "eligibility": policy_result.get("eligibility"),
        "reason": policy_result.get("reason"),
        "next_steps": policy_result.get("next_steps", []),
        "refund_options": policy_result.get("refund_options", []),
        "pickup": policy_result.get("pickup"),
        "a_to_z": policy_result.get("a_to_z"),
    }


@app.get("/track/{order_id}")
def track_order_public(order_id: str):
    try:
        order = get_order(order_id)
    except Exception as exc:
        logger.exception("track_order_public_failed order_id=%s error=%s", order_id, exc)
        raise HTTPException(status_code=503, detail="Tracking service temporarily unavailable")

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


@app.get("/check-return/{order_id}")
def check_return(order_id: str):
    try:
        return check_return_eligibility(order_id)
    except Exception as exc:
        logger.exception("check_return_failed order_id=%s error=%s", order_id, exc)
        raise HTTPException(status_code=500, detail="Failed to evaluate return eligibility")


@app.post("/request-return")
def create_return(req: ReturnRequest):
    if req.user_id is not None and not user_exists(req.user_id):
        raise HTTPException(status_code=404, detail="user_id not found")

    if not order_exists(req.order_id):
        raise HTTPException(status_code=404, detail="order_id not found")

    try:
        return request_return(
            order_id=req.order_id,
            reason=req.reason,
            user_id=req.user_id,
            refund_type=req.refund_type,
            partial_items=req.partial_items,
        )
    except Exception as exc:
        logger.exception("request_return_failed order_id=%s error=%s", req.order_id, exc)
        raise HTTPException(status_code=500, detail="Failed to create return request")


@app.post("/upload-proof")
def upload_proof(order_id: str = Form(...), file: UploadFile = File(...)):
    # Auto-prefix if user provided just the digits
    if order_id and order_id.isdigit():
        order_id = f"ORD-{order_id}"

    if not order_exists(order_id):
        raise HTTPException(status_code=404, detail="order_id not found")

    try:
        # Read file into memory
        video_data = file.file.read()
        if not video_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Store in MongoDB with binary data
        upload_record = store_upload_with_binary(
            order_id=order_id,
            filename=file.filename or "proof",
            video_data=video_data,
            verification_status="pending",
            content_type=file.content_type,
        )

        # Register video upload in returns collection
        return register_video_upload(order_id=order_id, video_url=upload_record["upload_id"])
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("upload_proof_failed order_id=%s error=%s", order_id, exc)
        raise HTTPException(status_code=500, detail="Failed to store uploaded proof")


@app.post("/refund-options")
def refund_options(req: RefundOptionsRequest):
    if not order_exists(req.order_id):
        raise HTTPException(status_code=404, detail="order_id not found")
    return get_refund_options_for_order(req.order_id)


@app.post("/schedule-pickup")
def schedule_pickup_endpoint(req: PickupRequest):
    if not order_exists(req.order_id):
        raise HTTPException(status_code=404, detail="order_id not found")
    return schedule_pickup(req.order_id, req.reschedule_date)


@app.post("/cancel-order")
def cancel_order_endpoint(req: CancelOrderRequest):
    if req.user_id is not None and not user_exists(req.user_id):
        raise HTTPException(status_code=404, detail="user_id not found")
    if not order_exists(req.order_id):
        raise HTTPException(status_code=404, detail="order_id not found")

    return handle_cancellation(
        order_id=req.order_id,
        user_id=req.user_id,
        partial_items=req.partial_items,
        combined_shipment=bool(req.combined_shipment),
        cancellation_reason=req.reason,
    )


@app.get("/return-reasons")
def get_return_reasons():
    """Get Amazon-style return reason options and which ones require proof."""
    return {
        "reasons": [
            "Item Defective or Doesn't Work",
            "Item Arrived Damaged",
            "Item Not as Described or Expected",
            "Wrong Item Received",
            "Missing Parts or Accessories",
            "Better Price Found",
            "No Longer Needed",
            "Changed Mind",
        ],
        "proof_required": {
            "Item Defective or Doesn't Work": True,
            "Item Arrived Damaged": True,
            "Item Not as Described or Expected": True,
            "Wrong Item Received": False,
            "Missing Parts or Accessories": True,
            "Better Price Found": False,
            "No Longer Needed": False,
            "Changed Mind": False,
        },
    }


@app.get("/cancel-reasons")
def get_cancel_reasons():
    """Get Amazon-style cancellation reason options."""
    return {
        "reasons": [
            "Item no longer needed",
            "Found a cheaper alternative",
            "Delivery time too long",
            "Changed my mind",
            "Ordered by mistake",
            "Item out of stock elsewhere",
            "Other reason",
        ],
    }


@app.get("/uploads/{order_id}")
def get_order_uploads(order_id: str):
    """Get all uploaded proof files for an order (user/admin view)."""
    if not order_exists(order_id):
        raise HTTPException(status_code=404, detail="order_id not found")
    
    uploads = get_uploads_for_order(order_id)
    return {
        "order_id": order_id,
        "uploads": uploads,
        "total": len(uploads),
    }


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

    avg_confidence = sum((t.get("confidence") or 0) for t in tickets) / total if total else 0
    escalation_rate = (pending / total) * 100 if total else 0

    intent_counts = {}
    for t in tickets:
        intent = t.get("intent", "UNKNOWN")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    intent_distribution = [{"name": k.replace("_", " ").title(), "value": v} for k, v in intent_counts.items()]

    total_orders = len(orders)
    active_shipments = sum(
        1
        for o in orders
        if str(o.get("status", "")).lower() in {"processing", "shipped", "out for delivery", "refuse delivery"}
    )
    delivered_orders = sum(1 for o in orders if str(o.get("status", "")).lower() == "delivered")
    cancelled_orders = sum(
        1 for o in orders if str(o.get("status", "")).lower() in {"cancelled", "partially cancelled"}
    )

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


@app.post("/user/register")
def user_register(req: UserRegisterRequest):
    normalized_email = req.email.strip().lower()
    existing = get_user_by_email(normalized_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    password_hash = get_password_hash(req.password)
    user = create_user(
        name=req.name.strip(),
        email=normalized_email,
        password_hash=password_hash,
        role="USER",
        auth_provider="local",
    )

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
        },
    }


@app.post("/user/login")
def user_login(req: UserLoginRequest):
    try:
        user = authenticate_customer(req.email.strip().lower(), req.password)
    except Exception as exc:
        logger.exception("user_login_failed email=%s error=%s", req.email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable. Please try again.",
        )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

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
        },
    }


@app.post("/user/google-login")
def user_google_login(req: UserGoogleLoginRequest):
    try:
        google_requests_mod = importlib.import_module("google.auth.transport.requests")
        google_id_token_mod = importlib.import_module("google.oauth2.id_token")
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login dependency is missing on server.",
        )

    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured on server.",
        )

    try:
        idinfo = google_id_token_mod.verify_oauth2_token(
            req.credential,
            google_requests_mod.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        logger.exception("google_login_verify_failed error=%s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential.")

    email = str(idinfo.get("email", "")).strip().lower()
    if not email or not idinfo.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email is not verified.")

    name = str(idinfo.get("name") or email.split("@")[0]).strip()
    google_sub = str(idinfo.get("sub") or "").strip()

    user = get_user_by_email(email)
    if not user:
        user = create_user(
            name=name,
            email=email,
            password_hash=None,
            role="user",
            auth_provider="google",
            google_sub=google_sub or None,
        )
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
        },
    }


@app.get("/user/profile")
def user_profile(token: str = Depends(oauth2_scheme)):
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user_id = payload.get("user_id")
    if user_id:
        user = get_user_by_id(user_id)
        if user:
            return user

    return {
        "id": None,
        "name": payload.get("sub", "Admin"),
        "email": payload.get("sub"),
        "role": payload.get("role", "admin"),
    }


@app.get("/user/orders")
def user_orders(token: str = Depends(oauth2_scheme)):
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        return []
    return get_orders_by_user(user_id)


@app.get("/user/tickets")
def user_tickets(token: str = Depends(oauth2_scheme)):
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        return []
    return get_tickets_by_user(user_id)


@app.get("/user/conversations")
def user_conversations(token: str = Depends(oauth2_scheme)):
    payload = get_current_user(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        return []
    return get_user_conversations(user_id)


@app.get("/admin/ticket/{ticket_id}")
def admin_ticket_detail(ticket_id: str, payload=Depends(require_admin)):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    conversation = get_conversation_by_ticket(ticket_id)
    ticket["conversation"] = conversation

    if ticket.get("order_id"):
        order = get_order(ticket["order_id"])
        if order:
            ticket["order_details"] = order

    return ticket


@app.post("/admin/resolve/{ticket_id}")
def admin_resolve_ticket(ticket_id: str, payload=Depends(require_admin)):
    ticket = update_ticket(ticket_id, "RESOLVED", "This ticket has been reviewed and resolved by support.")
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/admin/returns/{order_id}")
def admin_view_return(order_id: str, payload=Depends(require_admin)):
    """Admin view: Get return request details with all uploaded evidence."""
    if not order_exists(order_id):
        raise HTTPException(status_code=404, detail="order_id not found")

    from app.database import get_collection

    returns = get_collection("returns")
    return_doc = returns.find_one({"order_id": order_id}, sort=[("created_at", -1)])

    if not return_doc:
        return {
            "order_id": order_id,
            "return_request": None,
            "uploads": [],
            "message": "No return request found for this order.",
        }

    # Get all uploads for this order
    uploads = get_uploads_for_order(order_id)

    # Build response with return details
    return {
        "order_id": order_id,
        "return_request": {
            "status": return_doc.get("status"),
            "reason": return_doc.get("reason"),
            "verification_status": return_doc.get("verification_status"),
            "created_at": return_doc.get("created_at").isoformat() if return_doc.get("created_at") else None,
            "user_id": return_doc.get("user_id"),
            "video_uploaded": bool(return_doc.get("video_uploaded", False)),
            "reviewer_note": return_doc.get("reviewer_note"),
        },
        "uploads": uploads,
        "total_uploads": len(uploads),
    }


@app.post("/admin/returns/{order_id}/verify")
def admin_verify_return(order_id: str, verification_status: str, reviewer_note: str = "", payload=Depends(require_admin)):
    """Admin action: Approve or reject return request with notes."""
    if not order_exists(order_id):
        raise HTTPException(status_code=404, detail="order_id not found")

    from app.policy_engine import update_damage_verification

    try:
        result = update_damage_verification(
            order_id=order_id,
            verification_status=verification_status.lower(),
            reviewer_note=reviewer_note or None,
        )
        return {
            "success": result["success"],
            "message": result.get("message", "Verification status updated."),
            "verification_status": result.get("verification_status"),
            "return_status": result.get("return_status"),
            "reviewer": payload.get("sub"),
            "reviewed_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.exception("admin_verify_return_failed order_id=%s error=%s", order_id, exc)
        raise HTTPException(status_code=500, detail="Failed to verify return")


@app.get("/admin/uploads/{order_id}")
def admin_view_uploads(order_id: str, payload=Depends(require_admin)):
    """Admin view: Get all uploaded evidence for an order with metadata."""
    if not order_exists(order_id):
        raise HTTPException(status_code=404, detail="order_id not found")

    uploads = get_uploads_for_order(order_id)
    return {
        "order_id": order_id,
        "uploads": uploads,
        "total": len(uploads),
        "reviewed_by": payload.get("sub"),
    }


@app.get("/admin/uploads/{upload_id}/download")
def admin_download_upload(upload_id: str, payload=Depends(require_admin)):
    """Admin action: Download/view uploaded proof file."""
    try:
        video_data = get_upload_binary(upload_id)
        if not video_data:
            raise HTTPException(status_code=404, detail="Upload not found")

        return {
            "upload_id": upload_id,
            "data": video_data.hex(),  # Return as hex for JSON compatibility
            "size_bytes": len(video_data),
            "note": "Use hex decoder to convert back to binary for playback",
            "accessed_by": payload.get("sub"),
            "accessed_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("admin_download_upload_failed upload_id=%s error=%s", upload_id, exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve upload")


@app.get("/admin/uploads/{upload_id}/file")
def admin_stream_upload(upload_id: str, payload=Depends(require_admin)):
    """Admin action: Stream uploaded proof file for inline preview/playback."""
    upload = get_upload_file(upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    headers = {
        "Content-Disposition": f"inline; filename={upload['filename']}",
        "X-Admin-Viewer": payload.get("sub") or "admin",
    }
    return StreamingResponse(
        iter([upload["video_data"]]),
        media_type=upload["content_type"],
        headers=headers,
    )
