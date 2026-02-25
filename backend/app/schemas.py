# app/schemas.py

from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    text: str
    order_id: Optional[str] = None
    # New optional fields (backward compatible — not required)
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    return_reason: Optional[str] = None


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    message: str
    auto_processed: bool


# -----------------------------------
# User Registration / Login Schemas
# -----------------------------------

class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
