import spacy
import pandas as pd
import random
from spacy.training.example import Example
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Load dataset
df = pd.read_csv("final_training_dataset_v3.csv")

# Train-test split
train_texts, test_texts, train_labels, test_labels = train_test_split(
    df["utterance"],
    df["intent"],
    test_size=0.2,
    random_state=42,
    stratify=df["intent"]
)

# Create blank model
nlp = spacy.blank("en")
textcat = nlp.add_pipe("textcat")

labels = ["ORDER_STATUS", "ORDER_CANCELLATION", "UNKNOWN"]
for label in labels:
    textcat.add_label(label)

def create_examples(texts, labels_list):
    examples = []
    for text, label in zip(texts, labels_list):
        cats = {l: 0 for l in labels}
        cats[label] = 1
        examples.append((text, {"cats": cats}))
    return examples

train_data = create_examples(train_texts, train_labels)
test_data = create_examples(test_texts, test_labels)

optimizer = nlp.initialize()

# Training loop
for epoch in range(20):
    random.shuffle(train_data)
    losses = {}
    for text, annotations in train_data:
        example = Example.from_dict(nlp.make_doc(text), annotations)
        nlp.update([example], sgd=optimizer, losses=losses, drop=0.3)
    print(f"Epoch {epoch+1}, Loss: {losses}")

# Evaluation
y_true = []
y_pred = []

for text, annotations in test_data:
    doc = nlp(text)
    predicted = max(doc.cats, key=doc.cats.get)
    actual = [k for k, v in annotations["cats"].items() if v == 1][0]

    y_true.append(actual)
    y_pred.append(predicted)

print("\nClassification Report:")
print(classification_report(y_true, y_pred))

nlp.to_disk("trained_logistics_model_v3")
print("\nModel saved as trained_logistics_model_v3")
