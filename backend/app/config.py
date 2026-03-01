# app/config.py

"""
Central configuration for the LogiAI backend.

To switch from SQLite to PostgreSQL, change DATABASE_URL:
    DATABASE_URL = "postgresql://user:pass@host:5432/logistics_db"
"""

# ── Database ──────────────────────────────────
DATABASE_URL = "sqlite:///./logistics.db"

# ── NLP Model ─────────────────────────────────
MODEL_PATH = "models/trained_logistics_model_v3"

# ── Confidence thresholds ─────────────────────
STATUS_THRESHOLD = 0.85
CANCELLATION_THRESHOLD = 0.90

# ── System flags ──────────────────────────────
AUTO_APPROVE_CANCELLATION = True
