import cv2
import face_recognition
import pickle
import requests
import base64
import os
import sys
import numpy as np
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
from config import ENCODINGS_FILE, FOG_SERVER_URL, API_SECRET, REQUEST_TIMEOUT

# ── Load encodings ────────────────────────────────────
if not os.path.exists(ENCODINGS_FILE):
    print(f"Encodings file not found: {ENCODINGS_FILE}")
    sys.exit(1)

with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names     = data["names"]

if not known_encodings:
    print("No encodings found. Please run register.py first.")
    sys.exit(1)

# ── Snapshot output dir ───────────────────────────────
SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

attendance_log = set()

# ── Camera ────────────────────────────────────────────
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera. Exiting.")
    sys.exit(1)

print("Starting recognition system... Press Q to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Camera read error — retrying...")
            continue

        rgb_frame      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):

            # Best-match using face distance
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_idx  = int(np.argmin(distances))
            name      = "Unknown"

            if distances[best_idx] < 0.50:
                name = known_names[best_idx]

                if name not in attendance_log:
                    attendance_log.add(name)

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # ── Crop face and encode as base64 ────────
                    top, right, bottom, left = face_location
                    padding = 20
                    top    = max(0, top - padding)
                    left   = max(0, left - padding)
                    bottom = min(frame.shape[0], bottom + padding)
                    right  = min(frame.shape[1], right + padding)
                    crop   = frame[top:bottom, left:right]

                    snapshot_filename = f"{name}_{datetime.now().strftime('%H%M%S')}.jpg"
                    snapshot_path     = os.path.join(SNAPSHOT_DIR, snapshot_filename)
                    cv2.imwrite(snapshot_path, crop)

                    _, buffer    = cv2.imencode(".jpg", crop)
                    image_b64    = base64.b64encode(buffer.tobytes()).decode("utf-8")

                    payload = {
                        "student":   name,
                        "timestamp": timestamp,
                        "snapshot":  image_b64,
                        "snapshot_filename": snapshot_filename,
                    }

                    print(f"\n→ Sending attendance for {name} at {timestamp}")

                    try:
                        response = requests.post(
                            FOG_SERVER_URL,
                            json=payload,
                            headers={"X-Secret-Key": API_SECRET},
                            timeout=REQUEST_TIMEOUT,
                        )
                        print("Fog response:", response.json())
                    except requests.exceptions.ConnectionError:
                        print("Fog server unreachable — event logged locally only.")
                    except requests.exceptions.Timeout:
                        print("Fog server timed out.")

            # ── Draw bounding box ─────────────────────
            top, right, bottom, left = face_location
            color = (0, 200, 100) if name != "Unknown" else (0, 80, 200)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(
                frame, name,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2
            )

        cv2.imshow("Edge Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()