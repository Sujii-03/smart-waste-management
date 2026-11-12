from collections import Counter
from flask import Blueprint, jsonify
from sqlalchemy import func
from backend.extensions import db
from backend.models import WasteClassification, CollectionRequest, User, CATEGORIES
from backend.utils.auth import login_required, admin_required, current_user

bp = Blueprint("stats", __name__, url_prefix="/api/stats")

def _monthly(rows):
    c = Counter(r.strftime("%Y-%m") for (r,) in rows)
    return [{"month": m, "count": c[m]} for m in sorted(c)]

def _by_cat(q):
    got = dict(q.group_by(WasteClassification.waste_category).with_entities(
        WasteClassification.waste_category, func.count()).all())
    return {c: got.get(c, 0) for c in CATEGORIES}

@bp.get("/user")
@login_required
def user_stats():
    uid = current_user().id
    q = WasteClassification.query.filter_by(user_id=uid)
    cats = _by_cat(q)
    dates = db.session.query(WasteClassification.created_at).filter(WasteClassification.user_id == uid).all()
    return jsonify(total=sum(cats.values()), by_category=cats, monthly=_monthly(dates))

@bp.get("/admin")
@admin_required
def admin_stats():
    cr = CollectionRequest
    by_status = dict(db.session.query(cr.status, func.count()).group_by(cr.status).all())
    cdates = db.session.query(WasteClassification.created_at).all()
    rdates = db.session.query(cr.created_at).all()
    cats = _by_cat(WasteClassification.query)
    return jsonify(users=User.query.count(), classifications=sum(cats.values()),
                   requests=cr.query.count(), pending=by_status.get("pending", 0),
                   completed=by_status.get("completed", 0), by_status=by_status,
                   by_category=cats, monthly_classifications=_monthly(cdates), monthly_requests=_monthly(rdates))
