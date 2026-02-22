# app/policy_engine.py

from app.order_service import cancel_order

def handle_cancellation(order_id: str):
    result = cancel_order(order_id)
    return result
