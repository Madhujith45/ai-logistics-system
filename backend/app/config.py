# app/config.py

"""
Central configuration for the LogiAI backend.
"""

import os
from pathlib import Path


def _load_env_file() -> None:
	env_path = Path(__file__).resolve().parents[1] / ".env"
	if not env_path.exists():
		return

	for line in env_path.read_text(encoding="utf-8").splitlines():
		entry = line.strip()
		if not entry or entry.startswith("#") or "=" not in entry:
			continue
		key, value = entry.split("=", 1)
		os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


def _env_bool(name: str, default: bool = False) -> bool:
	value = os.getenv(name)
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
	value = os.getenv(name)
	if not value:
		return default
	items = [item.strip() for item in value.split(",")]
	return [item for item in items if item]


def _env_required(name: str) -> str:
	value = os.getenv(name, "").strip()
	if not value:
		raise ValueError(f"{name} is not set")
	return value

# ── Database (MongoDB Atlas) ──────────────────
MONGODB_URI = _env_required("MONGODB_URI")
MONGODB_DB_NAME = _env_required("MONGODB_DB_NAME")
MONGODB_TLS_CA_FILE = os.getenv("MONGODB_TLS_CA_FILE", "")
MONGODB_TLS_ALLOW_INVALID_CERTS = _env_bool("MONGODB_TLS_ALLOW_INVALID_CERTS", False)
MONGODB_TLS_DISABLE = _env_bool("MONGODB_TLS_DISABLE", False)

# ── NLP Model ─────────────────────────────────
MODEL_PATH = "models/trained_logistics_model_v3"

# ── Confidence thresholds ─────────────────────
STATUS_THRESHOLD = 0.85
CANCELLATION_THRESHOLD = 0.90

# ── System flags ──────────────────────────────
AUTO_APPROVE_CANCELLATION = True

# ── API / CORS ───────────────────────────────
DEFAULT_CORS_ORIGINS = [
	"http://localhost:3000",
	"https://ai-logistics-system.vercel.app",
	"https://ai-logistics-system-madhujith45s-projects.vercel.app",
	"https://logiai.vercel.app",
]
BACKEND_CORS_ORIGINS = _env_list("BACKEND_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
