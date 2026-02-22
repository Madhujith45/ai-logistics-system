# app/intent_service.py

import spacy
from app.config import MODEL_PATH, STATUS_THRESHOLD, CANCELLATION_THRESHOLD

nlp = None  # Do not load at import time


def get_nlp():
    global nlp
    if nlp is None:
        nlp = spacy.load(MODEL_PATH)
    return nlp


def classify_intent(text: str):
    model = get_nlp()
    doc = model(text)

    intent = max(doc.cats, key=doc.cats.get)
    confidence = doc.cats[intent]

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