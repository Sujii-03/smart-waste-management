from functools import wraps
from flask import session, jsonify
from backend.extensions import db
from backend.models import User

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not current_user():
            return jsonify(error="Authentication required"), 401
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u: return jsonify(error="Authentication required"), 401
        if u.role != "admin": return jsonify(error="Admin access required"), 403
        return f(*a, **k)
    return w
