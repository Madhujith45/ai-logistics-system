# app/order_service.py

# -----------------------------------
# Realistic Mock Order Database
# -----------------------------------

mock_orders = {
    "123": {
        "order_id": "123",
        "customer_name": "Rahul Sharma",
        "product_name": "iPhone 13",
        "payment_mode": "UPI",
        "order_status": "Processing",
        "status": "Processing",
        "shipped": False,
        "delivery_date": None,
        "price": 59999,
        "return_window_days": 7,
    },
    "456": {
        "order_id": "456",
        "customer_name": "Priya Patel",
        "product_name": "Samsung Galaxy S23",
        "payment_mode": "CARD",
        "order_status": "Shipped",
        "status": "Shipped",
        "shipped": True,
        "delivery_date": None,
        "price": 74999,
        "return_window_days": 7,
    },
    "789": {
        "order_id": "789",
        "customer_name": "Amit Verma",
        "product_name": "Sony WH-1000XM5 Headphones",
        "payment_mode": "COD",
        "order_status": "Delivered",
        "status": "Delivered",
        "shipped": True,
        "delivery_date": "2026-02-20",
        "price": 29990,
        "return_window_days": 7,
    },
    "1001": {
        "order_id": "1001",
        "customer_name": "Neha Gupta",
        "product_name": "MacBook Air M2",
        "payment_mode": "NET_BANKING",
        "order_status": "Delivered",
        "status": "Delivered",
        "shipped": True,
        "delivery_date": "2026-01-10",
        "price": 114990,
        "return_window_days": 7,
    },
    "1002": {
        "order_id": "1002",
        "customer_name": "Vikram Singh",
        "product_name": "Nike Air Max 270",
        "payment_mode": "WALLET",
        "order_status": "Placed",
        "status": "Placed",
        "shipped": False,
        "delivery_date": None,
        "price": 12995,
        "return_window_days": 7,
    },
    "1003": {
        "order_id": "1003",
        "customer_name": "Ananya Reddy",
        "product_name": "Kindle Paperwhite",
        "payment_mode": "UPI",
        "order_status": "Out for Delivery",
        "status": "Out for Delivery",
        "shipped": True,
        "delivery_date": None,
        "price": 13999,
        "return_window_days": 7,
    },
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
    order["order_status"] = "Cancelled"
    return {"success": True, "message": "Order cancelled successfully"}
