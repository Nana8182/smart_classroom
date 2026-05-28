import os
import sys
import json
import base64
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response as FlaskResponse

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
from config import (
    CLOUD_ATTENDANCE_URL,
    API_SECRET,
    REQUEST_TIMEOUT,
)

app = Flask(__name__)

# ── Paths ─────────────────────────────────────────────
BASE_DIR        = os.path.dirname(__file__)
STUDENTS_FILE   = os.path.join(BASE_DIR, "students.json")
SESSION_FILE    = os.path.join(BASE_DIR, "session.json")
SNAPSHOT_DIR    = os.path.join(BASE_DIR, "snapshots")

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ── Load registered students ──────────────────────────
def load_students():
    if not os.path.exists(STUDENTS_FILE):
        print(f"WARNING: {STUDENTS_FILE} not found. No roster loaded.")
        return []
    with open(STUDENTS_FILE) as f:
        return json.load(f)

# ── Session persistence ───────────────────────────────
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            return json.load(f)
    return {}

def save_session(data: dict):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

registered_students = load_students()
present_students    = load_session()   # { name: { timestamp, snapshot_filename } }

# ── Auth helper ───────────────────────────────────────
def authorized(req) -> bool:
    return req.headers.get("X-Secret-Key") == API_SECRET

# ── Routes ────────────────────────────────────────────

@app.route("/attendance", methods=["POST"])
def attendance():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    student  = data.get("student", "").strip()
    timestamp = data.get("timestamp", "").strip()
    image_b64 = data.get("snapshot", "")
    snapshot_filename = data.get("snapshot_filename", "")

    if not student or not timestamp:
        return jsonify({"error": "Missing student or timestamp"}), 400

    if student not in present_students:

        # ── Save snapshot image ───────────────────────
        saved_filename = None
        if image_b64 and snapshot_filename:
            try:
                img_bytes      = base64.b64decode(image_b64)
                saved_filename = f"{student}_{datetime.now().strftime('%H%M%S')}.jpg"
                img_path       = os.path.join(SNAPSHOT_DIR, saved_filename)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
            except Exception as e:
                print(f"Snapshot save error: {e}")
                saved_filename = None

        present_students[student] = {
            "timestamp":         timestamp,
            "snapshot_filename": saved_filename,
        }
        save_session(present_students)

        print(f"\n✓ Marked present: {student} at {timestamp}")

        # ── Forward to cloud ──────────────────────────
        cloud_payload = {
            "student":           student,
            "timestamp":         timestamp,
            "status":            "Present",
            "snapshot_filename": saved_filename,
        }
        try:
            requests.post(
                CLOUD_ATTENDANCE_URL,
                json=cloud_payload,
                headers={"X-Secret-Key": API_SECRET},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.ConnectionError:
            print("Cloud server unreachable — will retry on next event.")
        except requests.exceptions.Timeout:
            print("Cloud server timed out.")

    return _build_status_response(), 200


@app.route("/status", methods=["GET"])
def status():
    return _build_status_response(), 200


@app.route("/snapshot/<filename>")
def snapshot(filename):
    """Serve a face snapshot image."""
    return send_from_directory(SNAPSHOT_DIR, filename)


@app.route("/reset", methods=["POST"])
def reset():
    """Clear today's session (call at start of each class)."""
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    present_students.clear()
    save_session(present_students)
    return jsonify({"message": "Session reset."}), 200

from flask import Response as FlaskResponse

def _build_status_response() -> FlaskResponse:
    absent = [s for s in registered_students if s not in present_students]
    return jsonify({
        "present_students": present_students,
        "absent_students":  absent,
        "occupancy":        len(present_students),
        "last_updated":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)