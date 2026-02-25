# app/intent_service.py

import spacy
from app.config import MODEL_PATH, STATUS_THRESHOLD, CANCELLATION_THRESHOLD

nlp = None  # Do not load at import time

# -----------------------------------
# Categorized Intent Mapping
# -----------------------------------

INTENT_CATEGORIES = {
    "ORDER_STATUS": "TRACK_ORDER",
    "TRACK_ORDER": "TRACK_ORDER",
    "ORDER_CANCELLATION": "CANCEL_ORDER",
    "CANCEL_ORDER": "CANCEL_ORDER",
    "REFUND_REQUEST": "REFUND_REQUEST",
    "REFUND": "REFUND_REQUEST",
    "DAMAGED_PRODUCT": "DAMAGED_PRODUCT",
    "DAMAGE": "DAMAGED_PRODUCT",
    "MISMATCH_PRODUCT": "MISMATCH_PRODUCT",
    "MISMATCH": "MISMATCH_PRODUCT",
    "GENERAL_QUERY": "GENERAL_QUERY",
}

# Keyword-based fallback classifier for intents not in the spaCy model
KEYWORD_PATTERNS = {
    "TRACK_ORDER": ["track", "where is", "status", "order status", "delivery status", "shipping status", "where's my", "when will"],
    "CANCEL_ORDER": ["cancel", "cancellation", "abort", "stop order", "don't want"],
    "REFUND_REQUEST": ["refund", "money back", "return money", "reimburse", "cashback", "get my money"],
    "DAMAGED_PRODUCT": ["damaged", "broken", "defective", "not working", "cracked", "torn", "faulty"],
    "MISMATCH_PRODUCT": ["wrong product", "wrong item", "mismatch", "different product", "not what i ordered", "incorrect item", "wrong color", "wrong size"],
}


def get_nlp():
    global nlp
    if nlp is None:
        nlp = spacy.load(MODEL_PATH)
    return nlp


def _keyword_classify(text: str):
    """Fallback keyword-based classification for extended intents."""
    text_lower = text.lower()
    for intent, keywords in KEYWORD_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                return intent
    return None


def _normalize_intent(raw_intent: str) -> str:
    """Map raw model intent labels to the categorized intent system."""
    return INTENT_CATEGORIES.get(raw_intent, raw_intent)


# Known policy-engine intents
KNOWN_INTENTS = {"TRACK_ORDER", "CANCEL_ORDER", "REFUND_REQUEST", "DAMAGED_PRODUCT", "MISMATCH_PRODUCT", "GENERAL_QUERY"}

# High-priority keywords — if these appear, they override the model's guess
# because users explicitly saying "refund" or "cancel" should never be misclassified
HIGH_PRIORITY_KEYWORDS = {
    "REFUND_REQUEST": ["refund", "money back", "reimburse", "return money", "get my money"],
    "CANCEL_ORDER": ["cancel", "cancellation", "abort order"],
    "DAMAGED_PRODUCT": ["damaged", "broken", "defective", "cracked", "faulty"],
    "MISMATCH_PRODUCT": ["wrong product", "wrong item", "mismatch", "not what i ordered", "incorrect item"],
}


def classify_intent(text: str):
    model = get_nlp()
    doc = model(text)

    raw_intent = max(doc.cats, key=doc.cats.get)
    confidence = doc.cats[raw_intent]

    # Normalize to categorized intent
    intent = _normalize_intent(raw_intent)

    if intent == "CANCEL_ORDER" or raw_intent == "ORDER_CANCELLATION":
        threshold = CANCELLATION_THRESHOLD
    else:
        threshold = STATUS_THRESHOLD

    # STEP 1: Check high-priority keywords FIRST
    # If the user explicitly says "refund", "cancel", "damaged" etc.,
    # trust the keyword over the model — these are unambiguous signals
    text_lower = text.lower()
    for kw_intent, keywords in HIGH_PRIORITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                # Only override if the model predicted a DIFFERENT intent
                if intent != kw_intent:
                    return {
                        "intent": kw_intent,
                        "confidence": round(max(confidence, 0.88), 4),
                        "auto_processed": True
                    }

    # STEP 2: If model returns a known intent with good confidence, use it
    if intent in KNOWN_INTENTS and confidence >= threshold:
        return {
            "intent": intent,
            "confidence": round(confidence, 4),
            "auto_processed": True
        }

    # STEP 3: General keyword fallback for lower confidence
    keyword_intent = _keyword_classify(text)
    if keyword_intent:
        effective_confidence = max(confidence, 0.85) if keyword_intent == intent else 0.85
        return {
            "intent": keyword_intent,
            "confidence": round(effective_confidence, 4),
            "auto_processed": True
        }

    # STEP 4: If model confidence is high but intent is unknown
    if confidence >= threshold:
        return {
            "intent": intent,
            "confidence": round(confidence, 4),
            "auto_processed": False
        }

    return {
        "intent": "GENERAL_QUERY",
        "confidence": round(confidence, 4),
        "auto_processed": False
    }