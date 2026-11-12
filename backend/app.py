import os, click
from flask import Flask, jsonify
from backend.config import Config
from backend.extensions import db, migrate

def create_app():
    app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)
    from backend import models  # noqa: registers models for migrations
    migrate.init_app(app, db)

    from backend.routes import auth, classify, collections, stats, admin
    for m in (auth, classify, collections, stats, admin):
        app.register_blueprint(m.bp)

    from backend.routes import pages
    app.register_blueprint(pages.bp)

    import secrets
    from flask import request, session
    @app.get("/api/auth/csrf")
    def csrf():
        session.setdefault("csrf", secrets.token_urlsafe(32))
        return jsonify(token=session["csrf"])

    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.path.startswith("/api/"):
            tok = session.get("csrf")
            if not tok or not secrets.compare_digest(tok, request.headers.get("X-CSRF-Token", "")):
                return jsonify(error="Invalid or missing CSRF token"), 403

    @app.get("/api/health")
    def health(): return jsonify(status="ok")

    @app.errorhandler(413)
    def too_big(_): return jsonify(error="File too large"), 413
    @app.errorhandler(404)
    def nf(_): return jsonify(error="Not found"), 404

    @app.cli.command("init-db")
    def init_db():
        """Create tables (dev shortcut)."""
        db.create_all(); click.echo("Tables created.")

    @app.cli.command("create-admin")
    def create_admin():
        """Create admin user from ADMIN_EMAIL / ADMIN_PASSWORD env vars."""
        email, pw = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
        if not email or not pw: raise click.ClickException("Set ADMIN_EMAIL and ADMIN_PASSWORD")
        if models.User.query.filter_by(email=email.lower()).first():
            return click.echo("Admin already exists.")
        u = models.User(full_name="Administrator", email=email.lower(), phone="0000000000", role="admin")
        u.set_password(pw); db.session.add(u); db.session.commit()
        click.echo("Admin created.")
    return app
