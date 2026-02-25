# app/refund_service.py

from datetime import datetime, timedelta


def process_refund(order: dict) -> dict:
    """
    Process refund based on order status, delivery date, and payment mode.

    Returns a structured dict with:
        - eligible: bool
        - message: str
        - refund_method: str or None
        - store_credit_available: bool
        - store_credit_bonus: str or None
    """

    order_status = order.get("order_status", order.get("status", ""))
    product_name = order.get("product_name", "your item")
    payment_mode = order.get("payment_mode", "CARD")
    delivery_date_str = order.get("delivery_date")
    return_window_days = order.get("return_window_days", 7)

    # --------------------------------------------------
    # Rule 1: Cannot refund if not delivered
    # --------------------------------------------------
    if order_status.upper() not in ["DELIVERED"]:
        return {
            "eligible": False,
            "message": (
                f"Refund for {product_name} cannot be initiated at this time. "
                f"Your order is currently '{order_status}'. "
                "Refunds are only available after delivery is confirmed."
            ),
            "refund_method": None,
            "store_credit_available": False,
            "store_credit_bonus": None,
        }

    # --------------------------------------------------
    # Rule 2: Check return window
    # --------------------------------------------------
    within_window = True
    if delivery_date_str:
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d")
            days_since = (datetime.utcnow() - delivery_date).days
            within_window = days_since <= return_window_days
        except (ValueError, TypeError):
            within_window = True  # be lenient on bad data

    # --------------------------------------------------
    # Rule 3: Payment-mode based refund method
    # --------------------------------------------------
    refund_method_map = {
        "UPI": "your original UPI ID",
        "CARD": "your original credit/debit card",
        "COD": "your registered bank account (bank transfer required)",
        "WALLET": "your wallet balance",
        "NET_BANKING": "your bank account via NEFT",
    }
    refund_method = refund_method_map.get(payment_mode.upper(), "your original payment method")

    if within_window:
        # Full refund + store credit option
        message = (
            f"Great news! Your refund request for {product_name} is eligible. "
            f"You can choose one of the following options:\n\n"
            f"1. Full refund to {refund_method} (5-7 business days)\n"
            f"2. Instant store credit with a 5% bonus — available immediately for your next purchase\n\n"
            f"Please select your preferred refund option below."
        )
        return {
            "eligible": True,
            "message": message,
            "refund_method": refund_method,
            "store_credit_available": True,
            "store_credit_bonus": "5%",
        }
    else:
        # Outside return window — store credit only
        message = (
            f"Your refund request for {product_name} falls outside the {return_window_days}-day return window. "
            f"However, we can offer you store credit for the full amount, "
            f"which can be used towards any future purchase.\n\n"
            f"Would you like to proceed with store credit?"
        )
        return {
            "eligible": True,
            "message": message,
            "refund_method": None,
            "store_credit_available": True,
            "store_credit_bonus": None,
        }
