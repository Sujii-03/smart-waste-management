from datetime import date
from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models import CollectionRequest, CollectionHistory, CATEGORIES
from backend.utils.auth import login_required, current_user

bp = Blueprint("collections", __name__, url_prefix="/api/collections")

def to_dict(r):
    return {"id": r.id, "category": r.waste_category, "quantity": r.quantity, "address": r.pickup_address,
            "pickup_date": r.pickup_date.isoformat(), "status": r.status, "created_at": r.created_at.isoformat()}

def log_status(req, status):
    req.status = status
    db.session.add(CollectionHistory(request_id=req.id, status=status))

@bp.post("")
@login_required
def create():
    d = request.get_json(silent=True) or {}
    errors = {}
    cat = (d.get("category") or "").lower()
    if cat not in CATEGORIES: errors["category"] = "Invalid category"
    try:
        qty = float(d.get("quantity"))
        if not 0 < qty <= 10000: raise ValueError
    except (TypeError, ValueError): errors["quantity"] = "Quantity must be between 0 and 10000 kg"; qty = 0
    addr = (d.get("address") or "").strip()
    if not 5 <= len(addr) <= 500: errors["address"] = "Address must be 5-500 characters"
    try:
        pd = date.fromisoformat(d.get("pickup_date") or "")
        if pd < date.today(): errors["pickup_date"] = "Pickup date cannot be in the past"
    except ValueError: errors["pickup_date"] = "Invalid date (use YYYY-MM-DD)"; pd = None
    if errors: return jsonify(error="Validation failed", fields=errors), 400
    r = CollectionRequest(user_id=current_user().id, waste_category=cat, quantity=qty, pickup_address=addr, pickup_date=pd)
    db.session.add(r); db.session.flush(); log_status(r, "pending"); db.session.commit()
    return jsonify(request=to_dict(r)), 201

@bp.get("")
@login_required
def mine():
    rows = CollectionRequest.query.filter_by(user_id=current_user().id).order_by(CollectionRequest.created_at.desc()).all()
    return jsonify(items=[to_dict(r) for r in rows])

@bp.get("/<int:rid>/history")
@login_required
def timeline(rid):
    r = db.session.get(CollectionRequest, rid)
    if not r or r.user_id != current_user().id: return jsonify(error="Not found"), 404
    return jsonify(items=[{"status": h.status, "updated_at": h.updated_at.isoformat()}
                          for h in sorted(r.history, key=lambda h: h.updated_at)])

@bp.post("/<int:rid>/cancel")
@login_required
def cancel(rid):
    r = db.session.get(CollectionRequest, rid)
    if not r or r.user_id != current_user().id: return jsonify(error="Not found"), 404
    if r.status != "pending": return jsonify(error="Only pending requests can be cancelled"), 409
    log_status(r, "cancelled"); db.session.commit()
    return jsonify(request=to_dict(r))
