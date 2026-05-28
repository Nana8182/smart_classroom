import cv2
import face_recognition
import pickle
import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
from config import ENCODINGS_FILE, KNOWN_FACES_DIR

# ── Sanitize name input ───────────────────────────────
raw_name = input("Enter student name: ").strip()
student_name = re.sub(r"[^\w\s-]", "", raw_name).strip()
if not student_name:
    print("Invalid name. Exiting.")
    sys.exit(1)

# ── Ensure directories exist ──────────────────────────
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
student_dir = os.path.join(KNOWN_FACES_DIR, student_name)
os.makedirs(student_dir, exist_ok=True)

# ── Load existing encodings ───────────────────────────
if os.path.exists(ENCODINGS_FILE):
    with open(ENCODINGS_FILE, "rb") as f:
        saved = pickle.load(f)
    known_encodings = saved["encodings"]
    known_names     = saved["names"]
else:
    known_encodings = []
    known_names     = []

# ── Capture loop ──────────────────────────────────────
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera. Exiting.")
    sys.exit(1)

count = 0
TARGET = 5
print(f"Capturing {TARGET} images for '{student_name}'. Press Q to quit early.")

try:
    while count < TARGET:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Camera read error — retrying...")
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        display = frame.copy()

        if len(face_locations) > 0:
            face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]

            image_path = os.path.join(student_dir, f"{count}.jpg")
            cv2.imwrite(image_path, frame)

            known_encodings.append(face_encoding)
            known_names.append(student_name)
            count += 1
            print(f"  Captured {count}/{TARGET}")

            top, right, bottom, left = face_locations[0]
            cv2.rectangle(display, (left, top), (right, bottom), (0, 200, 100), 2)
            cv2.putText(
                display, f"Captured {count}/{TARGET}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 100), 2
            )
            cv2.imshow("Registration", display)
            cv2.waitKey(600)
        else:
            cv2.putText(
                display, "No face detected",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 80, 200), 2
            )

        cv2.imshow("Registration", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Quit early.")
            break

finally:
    cap.release()
    cv2.destroyAllWindows()

# ── Save updated encodings ────────────────────────────
if count > 0:
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump({"encodings": known_encodings, "names": known_names}, f)
    print(f"Registration complete. {count} images saved for '{student_name}'.")
else:
    print("No images captured. Encodings not updated.")