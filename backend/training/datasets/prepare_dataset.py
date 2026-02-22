import pandas as pd

# Load original dataset
df = pd.read_csv("NLPdatasetai.csv")

# Keep only logistics-related intents
selected_intents = [
    "track_order",
    "delivery_period",
    "delivery_options",
    "cancel_order",
    "change_shipping_address",
    "payment_issue",
    "check_refund_policy",
    "get_refund",
    "track_refund",
    "complaint"
]

filtered_df = df[df["intent"].isin(selected_intents)]

print("Filtered Shape:", filtered_df.shape)
print("\nIntent Distribution:")
print(filtered_df["intent"].value_counts())

# Save new dataset
filtered_df.to_csv("logistics_dataset.csv", index=False)

print("\nSaved as logistics_dataset.csv")
