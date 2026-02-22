import pandas as pd

df = pd.read_csv("logistics_dataset.csv")

# Find smallest class count
min_count = df["intent"].value_counts().min()

balanced_df = (
    df.groupby("intent")
      .apply(lambda x: x.sample(min_count, random_state=42))
      .reset_index(drop=True)
)

print("Balanced Distribution:")
print(balanced_df["intent"].value_counts())

balanced_df.to_csv("balanced_logistics_dataset.csv", index=False)

print("\nSaved as balanced_logistics_dataset.csv")
