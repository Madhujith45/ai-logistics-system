# app/order_service.py

"""
Order service — fetches and mutates orders from the database.
No hardcoded order data; everything is read from SQLite / PostgreSQL.
"""

from datetime import datetime, timedelta

from app.database import SessionLocal


def get_order(order_id: str) -> dict | None:
    """
    Look up an order by its string order_id.
    Returns a dict compatible with the policy engine, or None.
    """
    from app.models import Order

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return None

        shipped_statuses = {"Shipped", "Out for Delivery", "Delivered"}

        # Compute return_deadline from delivery_date + return_window_days
        return_window_days = order.return_window_days or 7
        return_deadline = None
        if order.delivery_date:
            try:
                d = datetime.strptime(order.delivery_date, "%Y-%m-%d")
                return_deadline = (d + timedelta(days=return_window_days)).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        return {
            "order_id": order.order_id,
            "customer_name": order.customer_name,
            "product_name": order.product_name or "your item",
            "payment_mode": order.payment_mode,
            "order_status": order.status,
            "status": order.status,
            "shipped": order.status in shipped_statuses,
            "delivery_date": order.delivery_date,
            "price": order.price,
            "return_window_days": return_window_days,
            "return_deadline": return_deadline,
        }
    finally:
        db.close()


def cancel_order(order_id: str) -> dict:
    """
    Cancel an order in the database if it hasn't shipped yet.
    """
    from app.models import Order

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"success": False, "message": "Order not found"}

        shipped_statuses = {"Shipped", "Out for Delivery", "Delivered"}
        if order.status in shipped_statuses:
            return {"success": False, "message": "Order already shipped. Cannot cancel."}

        order.status = "Cancelled"
        db.commit()
        return {"success": True, "message": "Order cancelled successfully"}
    except Exception:
        db.rollback()
        return {"success": False, "message": "Failed to cancel order"}
    finally:
        db.close()

