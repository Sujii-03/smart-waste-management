import re
from flask import Blueprint, request, session, jsonify
from sqlalchemy.exc import IntegrityError
from backend.extensions import db
from backend.models import User
from backend.utils.auth import current_user, login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^\+?[0-9]{7,15}$")

def _public(u):
    return {"id": u.id, "full_name": u.full_name, "email": u.email, "phone": u.phone, "role": u.role}

@bp.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    name = (d.get("full_name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    phone = (d.get("phone") or "").strip()
    pw, pw2 = d.get("password") or "", d.get("confirm_password") or ""
    errors = {}
    if len(name) < 2: errors["full_name"] = "Full name is required"
    if not EMAIL.match(email): errors["email"] = "Invalid email"
    if not PHONE.match(phone): errors["phone"] = "Invalid phone number"
    if len(pw) < 8: errors["password"] = "Password must be at least 8 characters"
    if pw != pw2: errors["confirm_password"] = "Passwords do not match"
    if errors: return jsonify(error="Validation failed", fields=errors), 400
    u = User(full_name=name, email=email, phone=phone, role="user")
    u.set_password(pw)
    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Email already registered"), 409
    return jsonify(user=_public(u)), 201

@bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    u = User.query.filter_by(email=(d.get("email") or "").strip().lower()).first()
    if not u or not u.check_password(d.get("password") or ""):
        return jsonify(error="Invalid email or password"), 401
    csrf = session.get("csrf"); session.clear()
    session["csrf"] = csrf; session["user_id"] = u.id
    return jsonify(user=_public(u))

@bp.post("/logout")
def logout():
    csrf = session.get("csrf"); session.clear()
    if csrf: session["csrf"] = csrf
    return jsonify(message="Logged out")

@bp.get("/me")
@login_required
def me():
    return jsonify(user=_public(current_user()))
