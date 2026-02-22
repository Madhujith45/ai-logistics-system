import csv
import random

data = []

# ==============================
# ORDER_STATUS (200)
# ==============================

order_status_samples = [
    "Where is my order",
    "Track my shipment",
    "Check order status",
    "Has my parcel been dispatched",
    "Is my package out for delivery",
    "Track order ID 12345",
    "Where is my courier",
    "Shipment tracking please",
    "Live tracking update",
    "Has it reached my city",
    "Current status of my parcel",
    "When will my package arrive",
    "Is it still in transit",
    "Track my delivery now",
    "Give me tracking details",
    "Order progress update",
    "Has it left the warehouse",
    "Where exactly is my shipment",
    "Delivery tracking information",
    "Track my recent purchase"
]

# Add noisy variations
def add_noise(text):
    variations = [
        text.lower(),
        text.upper(),
        text + "???",
        text.replace("my", ""),
        text + " please",
        text + " asap",
        "pls " + text,
        text.replace("order", "package"),
    ]
    return random.choice(variations)

for _ in range(200):
    base = random.choice(order_status_samples)
    data.append((add_noise(base), "ORDER_STATUS"))

# ==============================
# ORDER_CANCELLATION (200)
# ==============================

cancel_samples = [
    "I don't want this anymore",
    "I dont want this anymore",
    "I changed my mind",
    "I no longer need this",
    "Please stop this order",
    "I don't need this now",
    "Take this back",
    "Cancel it",
    "Stop this order",
    "I don’t want the package",
    "I don’t need it anymore",
    "Remove this purchase",
    "Stop it",
    "I don't want it",
    "End this order",
    "Cancel my order",
    "I want to cancel this shipment",
    "Stop my delivery",
    "Abort my purchase",
    "Cancel immediately",
    "Do not ship this order",
    "I changed my mind cancel it",
    "Terminate this order",
    "Delete my order",
    "Withdraw my order",
    "Cancel before dispatch",
    "Call off my shipment",
    "Cancel my recent purchase",
    "Please void the order",
    "Cancel delivery request",
    "Stop the dispatch",
    "Remove this order",
    "Cancel order as soon as possible",
    "Stop my package from shipping",
    "I no longer want this order"
]

for _ in range(200):
    base = random.choice(cancel_samples)
    data.append((add_noise(base), "ORDER_CANCELLATION"))

# ==============================
# UNKNOWN (200)
# ==============================

unknown_samples = [
    "I want a refund",
    "Refund not received",
    "Package damaged",
    "Very bad service",
    "Money not credited",
    "Product defective",
    "Courier was rude",
    "How do I contact support",
    "Payment failed",
    "I need help",
    "Hello",
    "Good morning",
    "What is your return policy",
    "Wrong item delivered",
    "Delivery was late",
    "I am unhappy with service",
    "Need refund details",
    "Complaint about delivery",
    "Why is refund delayed",
    "Talk to human agent"
]

for _ in range(200):
    base = random.choice(unknown_samples)
    data.append((add_noise(base), "UNKNOWN"))

# Shuffle dataset
random.shuffle(data)

# Write CSV
with open("logistics_training_data_v2.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["utterance", "intent"])
    writer.writerows(data)

print("600 sample dataset (v2) created successfully")
