import spacy
from spacy.util import minibatch
import pandas as pd
import random
from spacy.training.example import Example
from sklearn.model_selection import train_test_split

# -----------------------------
# 1️⃣ Load Dataset
# -----------------------------
df = pd.read_csv("logistics_training_data_clean.csv")




print("Dataset shape:", df.shape)
print("\nIntent distribution:")
print(df["intent"].value_counts())

# -----------------------------
# 2️⃣ Train-Test Split
# -----------------------------
train_texts, test_texts, train_labels, test_labels = train_test_split(
    df["utterance"],
    df["intent"],
    test_size=0.2,
    random_state=42,
    stratify=df["intent"]
)

print("\nTrain size:", len(train_texts))
print("Test size:", len(test_texts))

# -----------------------------
# 3️⃣ Load Pretrained Model
# -----------------------------
nlp = spacy.load("en_core_web_sm")

# Remove existing textcat if present
if "textcat" in nlp.pipe_names:
    nlp.remove_pipe("textcat")

# Add fresh textcat layer
textcat = nlp.add_pipe("textcat", last=True)

# Add labels
labels = df["intent"].unique()
for label in labels:
    textcat.add_label(label)

# -----------------------------
# 4️⃣ Convert to spaCy Format
# -----------------------------
def create_examples(texts, labels_series):
    examples = []
    unique_labels = df["intent"].unique()

    for text, label in zip(texts, labels_series):
        cats = {l: 0 for l in unique_labels}
        cats[label] = 1
        examples.append((text, {"cats": cats}))

    return examples


train_data = create_examples(train_texts, train_labels)
test_data = create_examples(test_texts, test_labels)

# -----------------------------
# 5️⃣ Training Loop (Mini-batch)
# -----------------------------
optimizer = nlp.initialize()

for epoch in range(15):
    random.shuffle(train_data)
    losses = {}

    batches = minibatch(train_data, size=8)

    for batch in batches:
        examples = []
        for text, annotations in batch:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            examples.append(example)

        nlp.update(examples, sgd=optimizer, losses=losses)

    print(f"Epoch {epoch+1}, Loss: {losses}")

# -----------------------------
# 6️⃣ Evaluation
# -----------------------------
correct = 0
total = 0

for text, annotations in test_data:
    doc = nlp(text)
    predicted = max(doc.cats, key=doc.cats.get)
    actual = [k for k, v in annotations["cats"].items() if v == 1][0]

    if predicted == actual:
        correct += 1
    total += 1

accuracy = correct / total
print(f"\nTest Accuracy: {accuracy:.2f}")

# -----------------------------
# 7️⃣ Save Model
# -----------------------------
nlp.to_disk("trained_logistics_model")
print("\nModel saved as 'trained_logistics_model'")
