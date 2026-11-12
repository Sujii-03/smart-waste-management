import csv, io
from flask import Blueprint, request, jsonify, Response, send_file
from openpyxl import Workbook
from backend.extensions import db
from backend.models import User, CollectionRequest, WasteClassification, STATUSES
from backend.routes.collections import to_dict as req_dict, log_status
from backend.utils.auth import admin_required, current_user

bp = Blueprint("admin", __name__, url_prefix="/api/admin")
FLOW = {"pending": {"approved", "cancelled"}, "approved": {"completed", "cancelled"}, "completed": set(), "cancelled": set()}

@bp.get("/users")
@admin_required
def users():
    return jsonify(items=[{"id": u.id, "full_name": u.full_name, "email": u.email, "phone": u.phone,
                           "role": u.role, "created_at": u.created_at.isoformat()}
                          for u in User.query.order_by(User.id).all()])

@bp.patch("/users/<int:uid>")
@admin_required
def set_role(uid):
    role = (request.get_json(silent=True) or {}).get("role")
    u = db.session.get(User, uid)
    if not u: return jsonify(error="Not found"), 404
    if role not in ("user", "admin"): return jsonify(error="Invalid role"), 400
    if u.id == current_user().id: return jsonify(error="You cannot change your own role"), 400
    u.role = role; db.session.commit()
    return jsonify(message="Updated")

@bp.delete("/users/<int:uid>")
@admin_required
def delete_user(uid):
    u = db.session.get(User, uid)
    if not u: return jsonify(error="Not found"), 404
    if u.id == current_user().id: return jsonify(error="You cannot delete yourself"), 400
    db.session.delete(u); db.session.commit()
    return jsonify(message="Deleted")

@bp.get("/requests")
@admin_required
def requests_all():
    q = CollectionRequest.query
    s = request.args.get("status")
    if s in STATUSES: q = q.filter_by(status=s)
    out = []
    for r in q.order_by(CollectionRequest.created_at.desc()).all():
        d = req_dict(r); d["user"] = r.user.full_name; d["email"] = r.user.email; out.append(d)
    return jsonify(items=out)

@bp.patch("/requests/<int:rid>")
@admin_required
def update_request(rid):
    new = (request.get_json(silent=True) or {}).get("status")
    r = db.session.get(CollectionRequest, rid)
    if not r: return jsonify(error="Not found"), 404
    if new not in FLOW[r.status]:
        return jsonify(error=f"Cannot change status from {r.status} to {new}"), 409
    log_status(r, new); db.session.commit()
    return jsonify(request=req_dict(r))

def _safe(v):  # neutralise spreadsheet formula injection
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s

def _dataset(kind):
    if kind == "users":
        return ["id", "full_name", "email", "phone", "role", "created_at"], [
            [u.id, u.full_name, u.email, u.phone, u.role, u.created_at] for u in User.query.all()]
    if kind == "classifications":
        return ["id", "user_id", "category", "confidence", "created_at"], [
            [c.id, c.user_id, c.waste_category, round(c.confidence_score, 4), c.created_at]
            for c in WasteClassification.query.all()]
    if kind == "requests":
        return ["id", "user_id", "category", "quantity_kg", "address", "pickup_date", "status", "created_at"], [
            [r.id, r.user_id, r.waste_category, r.quantity, r.pickup_address, r.pickup_date, r.status, r.created_at]
            for r in CollectionRequest.query.all()]
    return None

@bp.get("/reports/<kind>.<fmt>")
@admin_required
def report(kind, fmt):
    data = _dataset(kind)
    if not data or fmt not in ("csv", "xlsx"): return jsonify(error="Unknown report"), 404
    head, rows = data
    rows = [[_safe(v) for v in r] for r in rows]
    if fmt == "csv":
        buf = io.StringIO(); w = csv.writer(buf); w.writerow(head); w.writerows(rows)
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={kind}.csv"})
    wb = Workbook(); ws = wb.active; ws.append(head)
    for r in rows: ws.append(r)
    b = io.BytesIO(); wb.save(b); b.seek(0)
    return send_file(b, as_attachment=True, download_name=f"{kind}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
