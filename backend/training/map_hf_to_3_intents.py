import pandas as pd

df = pd.read_csv("hf_ecommerce_support_train.csv")

def map_intent(category):
    if category in [
        "Order Delivery Issues",
        "Pickup and Shipping",
        "Order Confirmation and Status",
        "Delivery Process",
        "Availability of Faster Delivery Options",
        "Standard Shipping Speeds and Delivery Charges",
        "Product Availability for Shipping",
        "Expedited Delivery"
    ]:
        return "ORDER_STATUS"
    
    elif category == "Order Cancellation":
        return "ORDER_CANCELLATION"
    
    else:
        return "UNKNOWN"

df["intent"] = df["issue_category"].apply(map_intent)

# We need actual text input — use 'conversation' column
df_final = df[["conversation", "intent"]]
df_final.rename(columns={"conversation": "utterance"}, inplace=True)

print(df_final["intent"].value_counts())

df_final.to_csv("hf_mapped_3_intents.csv", index=False)

print("Mapped dataset saved as hf_mapped_3_intents.csv")
