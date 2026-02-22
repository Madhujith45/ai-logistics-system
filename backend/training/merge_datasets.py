import pandas as pd

hf = pd.read_csv("hf_mapped_3_intents.csv")

# Notice the path fix here 👇
synthetic = pd.read_csv("AI_DATASETS/logistics_training_data_v2.csv")

combined = pd.concat([hf, synthetic], ignore_index=True)

print("Combined Distribution:")
print(combined["intent"].value_counts())

combined.to_csv("final_training_dataset_v3.csv", index=False)

print("\nSaved as final_training_dataset_v3.csv")
