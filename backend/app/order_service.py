# app/order_service.py

# Mock order database
mock_orders = {
    "123": {"status": "Processing", "shipped": False},
    "456": {"status": "Shipped", "shipped": True},
    "789": {"status": "Delivered", "shipped": True},
}

def get_order(order_id: str):
    return mock_orders.get(order_id)

def cancel_order(order_id: str):
    order = get_order(order_id)
    if not order:
        return {"success": False, "message": "Order not found"}

    if order["shipped"]:
        return {"success": False, "message": "Order already shipped. Cannot cancel."}

    order["status"] = "Cancelled"
    return {"success": True, "message": "Order cancelled successfully"}
