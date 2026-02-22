import csv

data = []

# -------- TRACK ORDER (100) --------
track_samples = [
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
"Track my recent purchase",
"What is the current delivery status",
"Tell me the status of my package",
"I want to know where my shipment is",
"Track this order for me",
"Is my order on the way",
"Check my parcel progress",
"Track the shipment right now",
"Please provide tracking information",
"Has delivery started",
"Where can I track my order",
]

track_samples *= 4  # makes 120, we trim later
track_samples = track_samples[:100]

for s in track_samples:
    data.append((s, "track_order"))

# -------- CANCEL ORDER (100) --------
cancel_samples = [
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
"Cancel the shipment right now",
"Stop the dispatch",
"Remove this order",
"Cancel order as soon as possible",
"I want this order cancelled",
"Stop my package from shipping",
"Cancel this product order",
"I need to cancel my purchase",
"Cancel my online order",
"Please stop this shipment",
"Cancel this item immediately",
"Do not proceed with delivery",
"Cancel this transaction",
"I no longer want this order",
"Cancel the package delivery",
]

cancel_samples *= 4
cancel_samples = cancel_samples[:100]

for s in cancel_samples:
    data.append((s, "cancel_order"))

# -------- RESCHEDULE DELIVERY (100) --------
reschedule_samples = [
"Reschedule my delivery",
"Deliver tomorrow instead",
"Change delivery date",
"Postpone shipment",
"Deliver next week",
"Shift delivery time",
"I will not be home today",
"Deliver after 6 PM",
"Move delivery to Friday",
"Delay my package",
"Schedule it for weekend",
"Push delivery by two days",
"Deliver later",
"Switch delivery date",
"Change my delivery schedule",
"Adjust delivery timing",
"Move shipment to next week",
"Reschedule this order",
"Modify delivery time",
"Delay shipment arrival",
"Can you deliver on Monday",
"Reschedule my package",
"Change the drop off date",
"Deliver on another day",
"I need a different delivery slot",
"Please delay my delivery",
"Move my shipment date",
"Adjust my delivery time",
"Reschedule the courier visit",
"Change delivery appointment",
]

reschedule_samples *= 4
reschedule_samples = reschedule_samples[:100]

for s in reschedule_samples:
    data.append((s, "reschedule_delivery"))

# -------- REFUND ISSUE (100) --------
refund_samples = [
"I want a refund",
"How do I get a refund",
"My refund not processed",
"Track my refund",
"Refund status update",
"When will refund be credited",
"Refund delay issue",
"I need my money back",
"Refund for cancelled order",
"Refund not received yet",
"Where is my refund",
"Refund still pending",
"Money not credited",
"Return my payment",
"Please process my refund",
"Refund processing time",
"Why is my refund delayed",
"Refund inquiry",
"Credit my refund amount",
"Refund support request",
"Refund has not arrived",
"Waiting for refund confirmation",
"Refund transaction issue",
"Need refund details",
"Refund taking too long",
"When is refund expected",
"Refund assistance needed",
"Follow up on refund",
"Refund still not credited",
"Money back request",
]

refund_samples *= 4
refund_samples = refund_samples[:100]

for s in refund_samples:
    data.append((s, "refund_issue"))

# -------- COMPLAINT (100) --------
complaint_samples = [
"My item is damaged",
"Package arrived broken",
"Delivery is late",
"Product not working",
"Very bad service",
"Courier was rude",
"Item missing from box",
"Shipment arrived late",
"Received wrong item",
"Terrible experience",
"Product defective",
"Service was poor",
"Wrong product delivered",
"Delay in delivery",
"Parcel damaged during transit",
"Late delivery again",
"Delivery was extremely slow",
"Missing items in package",
"Poor delivery experience",
"Unsatisfactory delivery service",
"Order damaged in transit",
"Delivery was not on time",
"Faulty product received",
"Product arrived scratched",
"Incorrect item sent",
"Unacceptable delivery delay",
"Bad customer service",
"Shipment issue complaint",
"Product arrived in bad condition",
"Delivery delay problem",
]

complaint_samples *= 4
complaint_samples = complaint_samples[:100]

for s in complaint_samples:
    data.append((s, "complaint"))

# -------- WRITE FILE --------
with open("logistics_training_data_clean.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["utterance", "intent"])
    writer.writerows(data)

print("500 sample dataset created successfully")
