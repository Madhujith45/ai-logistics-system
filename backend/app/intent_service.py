# app/intent_service.py

import spacy
from app.config import MODEL_PATH, STATUS_THRESHOLD, CANCELLATION_THRESHOLD

# Load model once at startup
nlp = spacy.load(MODEL_PATH)

def classify_intent(text: str):
    doc = nlp(text)
    intent = max(doc.cats, key=doc.cats.get)
    confidence = doc.cats[intent]

    # Apply different thresholds
    if intent == "ORDER_CANCELLATION":
        threshold = CANCELLATION_THRESHOLD
    else:
        threshold = STATUS_THRESHOLD

    if confidence < threshold:
        return {
            "intent": "ESCALATE_TO_HUMAN",
            "confidence": confidence,
            "auto_processed": False
        }

    return {
        "intent": intent,
        "confidence": confidence,
        "auto_processed": True
    }
