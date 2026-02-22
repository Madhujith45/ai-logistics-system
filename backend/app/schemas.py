# app/schemas.py

from pydantic import BaseModel

class ChatRequest(BaseModel):
    text: str
    order_id: str | None = None

class ChatResponse(BaseModel):
    intent: str
    confidence: float
    message: str
    auto_processed: bool
