# app/schemas.py

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    order_id: Optional[str] = Field(default=None, min_length=3, max_length=40)
    # New optional fields (backward compatible — not required)
    user_id: Optional[int] = None
    session_id: Optional[str] = Field(default=None, max_length=120)
    return_reason: Optional[str] = Field(default=None, max_length=250)


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    message: str
    auto_processed: bool


# -----------------------------------
# User Registration / Login Schemas
# -----------------------------------

class UserRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=100)


class UserLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=100)


class UserGoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20)


class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str


class ReturnRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=40)
    reason: str = Field(min_length=3, max_length=250)  # e.g., "damaged", "defective", "wrong_item"
    user_id: Optional[int] = None
    refund_type: Optional[str] = Field(default=None, max_length=30)
    partial_items: Optional[list[str]] = None
    condition: Optional[str] = Field(default=None, max_length=50)  # "damaged", "defective", "not_as_described", etc.


class ReturnReasonsResponse(BaseModel):
    """Amazon-style return reason options"""
    reasons: list[str] = [
        "Item Defective or Doesn't Work",
        "Item Arrived Damaged",
        "Item Not as Described or Expected",
        "Wrong Item Received",
        "Missing Parts or Accessories",
        "Better Price Found",
        "No Longer Needed",
        "Changed Mind",
    ]
    require_proof: dict[str, bool] = {
        "Item Defective or Doesn't Work": True,
        "Item Arrived Damaged": True,
        "Item Not as Described or Expected": True,
        "Wrong Item Received": False,
        "Missing Parts or Accessories": True,
        "Better Price Found": False,
        "No Longer Needed": False,
        "Changed Mind": False,
    }


class RefundOptionsRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=40)


class PickupRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=40)
    reschedule_date: Optional[str] = Field(default=None, max_length=20)


class CancelOrderRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=40)
    user_id: Optional[int] = None
    partial_items: Optional[list[str]] = None
    combined_shipment: Optional[bool] = False
    reason: Optional[str] = Field(default=None, max_length=100)  # "item_not_needed", "found_cheaper", etc.


class CancelReasonsResponse(BaseModel):
    """Amazon-style cancellation reason options"""
    reasons: list[str] = [
        "Item no longer needed",
        "Found a cheaper alternative",
        "Delivery time too long",
        "Changed my mind",
        "Ordered by mistake",
        "Item out of stock elsewhere",
        "Other reason",
    ]
