import os
import sys
from datetime import datetime, date
from flask import Flask, request, jsonify
from models import db, AttendanceRecord

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))
from config import API_SECRET

app = Flask(__name__)

# ── Database ──────────────────────────────────────────
# On Render: set DATABASE_URL environment variable to your
# Render PostgreSQL internal connection string.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///attendance.db")

# Render gives postgres:// — SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"]        = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ── Auth helper ───────────────────────────────────────
def authorized(req) -> bool:
    return req.headers.get("X-Secret-Key") == API_SECRET

# ── Routes ────────────────────────────────────────────

@app.route("/cloud_attendance", methods=["POST"])
def cloud_attendance():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    student   = data.get("student", "").strip()
    timestamp = data.get("timestamp", "").strip()
    status    = data.get("status", "Present").strip()
    snapshot_filename = data.get("snapshot_filename")

    if not student or not timestamp:
        return jsonify({"error": "Missing student or timestamp"}), 400

    record = AttendanceRecord(
        student=student,
        timestamp=timestamp,
        status=status,
        snapshot_filename=snapshot_filename,
    )
    db.session.add(record)
    db.session.commit()

    print(f"Stored: {student} — {timestamp}")

    return jsonify({
        "message":      "Attendance stored",
        "total_records": AttendanceRecord.query.count(),
    }), 201


@app.route("/analytics", methods=["GET"])
def analytics():
    # Optional ?date=YYYY-MM-DD filter; defaults to today
    date_str = request.args.get("date", date.today().isoformat())

    records = AttendanceRecord.query.filter(
    AttendanceRecord.timestamp.startswith(date_str)  # type: ignore[union-attr]
    ).order_by(AttendanceRecord.created_at).all()

    unique_students = list({r.student for r in records})

    # Per-student breakdown
    per_student = {}
    for r in records:
        if r.student not in per_student:
            per_student[r.student] = {
                "first_seen":        r.timestamp,
                "snapshot_filename": r.snapshot_filename,
                "status":            r.status,
            }

    # Total records across all time (for history chart)
    all_records = AttendanceRecord.query.order_by(
        AttendanceRecord.created_at
    ).all()

    # Daily attendance counts for chart
    daily_counts: dict[str, int] = {}
    for r in all_records:
        day = r.timestamp[:10]
        daily_counts[day] = daily_counts.get(day, 0) + 1

    return jsonify({
        "date":                    date_str,
        "students_present_today":  len(unique_students),
        "unique_students":         unique_students,
        "per_student":             per_student,
        "attendance_history":      [r.to_dict() for r in all_records],
        "daily_counts":            daily_counts,
        "total_records_all_time":  len(all_records),
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200
    
@app.route("/reset_db", methods=["POST"])
def reset_db():
    if not authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        db.session.query(AttendanceRecord).delete()
        db.session.commit()
        return jsonify({"message": "All records deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
