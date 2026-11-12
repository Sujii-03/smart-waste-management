import os, uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory, abort
from PIL import Image, UnidentifiedImageError
from backend.extensions import db
from backend.models import WasteClassification
from backend.utils.auth import login_required, current_user
from backend.services import classifier
from backend.services.disposal import recommendation

bp = Blueprint("classify", __name__, url_prefix="/api/classify")
ALLOWED = {"JPEG": ".jpg", "PNG": ".png"}

def to_dict(c):
    return {"id": c.id, "category": c.waste_category, "confidence": round(c.confidence_score * 100, 1),
            "recommendation": c.disposal_recommendation, "image_url": f"/api/classify/image/{c.id}",
            "created_at": c.created_at.isoformat()}

@bp.post("")
@login_required
def classify():
    f = request.files.get("image")
    if not f or not f.filename: return jsonify(error="No image uploaded"), 400
    if os.path.splitext(f.filename.lower())[1] not in (".jpg", ".jpeg", ".png"):
        return jsonify(error="Only JPG, JPEG and PNG files are allowed"), 400
    try:  # validate real content, not just the extension
        img = Image.open(f.stream); fmt = img.format; img.verify(); f.stream.seek(0); img = Image.open(f.stream)
        if fmt not in ALLOWED: raise UnidentifiedImageError()
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        return jsonify(error="File is not a valid JPG/PNG image"), 400
    name = uuid.uuid4().hex + ALLOWED[fmt]
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
    img.convert("RGB").save(path)  # re-encode: strips EXIF/metadata and embedded payloads
    try:
        cat, conf = classifier.predict(path)
    except classifier.ModelNotAvailable as e:
        os.remove(path); return jsonify(error=str(e)), 503
    c = WasteClassification(user_id=current_user().id, image_path=name, waste_category=cat,
                            confidence_score=conf, disposal_recommendation=recommendation(cat))
    db.session.add(c); db.session.commit()
    return jsonify(result=to_dict(c)), 201

@bp.get("/history")
@login_required
def history():
    rows = (WasteClassification.query.filter_by(user_id=current_user().id)
            .order_by(WasteClassification.created_at.desc()).limit(100).all())
    return jsonify(items=[to_dict(c) for c in rows])

@bp.get("/image/<int:cid>")
@login_required
def image(cid):
    c = db.session.get(WasteClassification, cid) or abort(404)
    u = current_user()
    if c.user_id != u.id and u.role != "admin": abort(403)
    return send_from_directory(os.path.abspath(current_app.config["UPLOAD_FOLDER"]), c.image_path)
