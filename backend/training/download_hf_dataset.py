from datasets import load_dataset
import pandas as pd

print("Downloading dataset...")

dataset = load_dataset("rjac/e-commerce-customer-support-qa")

print(dataset)

# Convert train split to pandas
df = pd.DataFrame(dataset["train"])

print("Columns:", df.columns)
print("Number of rows:", len(df))

# Save as CSV
df.to_csv("hf_ecommerce_support_train.csv", index=False)

print("Dataset saved as hf_ecommerce_support_train.csv")
