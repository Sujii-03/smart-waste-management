from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db

CATEGORIES = ("plastic", "paper", "metal", "glass", "organic")
STATUSES = ("pending", "approved", "completed", "cancelled")

def _now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="user")
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)
    classifications = db.relationship("WasteClassification", backref="user", cascade="all, delete-orphan")
    requests = db.relationship("CollectionRequest", backref="user", cascade="all, delete-orphan")
    __table_args__ = (db.CheckConstraint("role IN ('user','admin')", name="ck_user_role"),)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class WasteClassification(db.Model):
    __tablename__ = "waste_classifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = db.Column(db.String(255), nullable=False)
    waste_category = db.Column(db.String(20), nullable=False, index=True)
    confidence_score = db.Column(db.Float, nullable=False)
    disposal_recommendation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False, index=True)
    __table_args__ = (
        db.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_conf_range"),
        db.CheckConstraint("waste_category IN ('plastic','paper','metal','glass','organic')", name="ck_class_cat"),
    )

class CollectionRequest(db.Model):
    __tablename__ = "collection_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    waste_category = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # kg
    pickup_address = db.Column(db.Text, nullable=False)
    pickup_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(12), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)
    history = db.relationship("CollectionHistory", backref="request", cascade="all, delete-orphan")
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_qty_positive"),
        db.CheckConstraint("status IN ('pending','approved','completed','cancelled')", name="ck_req_status"),
        db.CheckConstraint("waste_category IN ('plastic','paper','metal','glass','organic')", name="ck_req_cat"),
    )

class CollectionHistory(db.Model):
    __tablename__ = "collection_history"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("collection_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(12), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, nullable=False)

class Admin(db.Model):
    """Spec-required table. Web admin login uses users.role='admin'; this is for a separate ops account."""
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
