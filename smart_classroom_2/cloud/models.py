from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AttendanceRecord(db.Model):  # type: ignore[name-defined]
    __tablename__ = "attendance_records"

    id                = db.Column(db.Integer, primary_key=True)
    student           = db.Column(db.String(120), nullable=False)
    timestamp         = db.Column(db.String(30),  nullable=False)
    status            = db.Column(db.String(20),  nullable=False, default="Present")
    snapshot_filename = db.Column(db.String(200), nullable=True)
    created_at        = db.Column(db.DateTime,    default=datetime.utcnow)

    def __init__(self, student: str, timestamp: str, status: str = "Present",
                 snapshot_filename: str | None = None):
        self.student           = student
        self.timestamp         = timestamp
        self.status            = status
        self.snapshot_filename = snapshot_filename

    def to_dict(self):
        return {
            "id":                self.id,
            "student":           self.student,
            "timestamp":         self.timestamp,
            "status":            self.status,
            "snapshot_filename": self.snapshot_filename,
            "created_at":        self.created_at.isoformat(),
        }