import os

# ── Fog ──────────────────────────────────────────────
FOG_HOST = os.environ.get("FOG_HOST", "127.0.0.1")
FOG_PORT = int(os.environ.get("FOG_PORT", 5001))
FOG_SERVER_URL = f"http://{FOG_HOST}:{FOG_PORT}/attendance"
FOG_STATUS_URL = f"http://{FOG_HOST}:{FOG_PORT}/status"

# ── Cloud ─────────────────────────────────────────────
CLOUD_BASE_URL = os.environ.get(
    "CLOUD_BASE_URL", "https://YOUR-RENDER-URL.onrender.com"
)
CLOUD_ATTENDANCE_URL = f"{CLOUD_BASE_URL}/cloud_attendance"
CLOUD_ANALYTICS_URL  = f"{CLOUD_BASE_URL}/analytics"

# ── Shared secret (set same value on all machines) ───
API_SECRET = os.environ.get("ATTENDANCE_SECRET", "change-me-in-production")

# ── Edge paths ────────────────────────────────────────
ENCODINGS_FILE  = os.environ.get("ENCODINGS_FILE",  "encodings.pkl")
KNOWN_FACES_DIR = os.environ.get("KNOWN_FACES_DIR", "known_faces")

# ── Request timeout (seconds) ────────────────────────
REQUEST_TIMEOUT = 5