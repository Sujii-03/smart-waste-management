import os
from flask import Blueprint, render_template, redirect, url_for
from backend.utils.auth import current_user

bp = Blueprint("pages", __name__)

@bp.app_context_processor
def inject():
    return {"user": current_user(), "contact_email": os.getenv("CONTACT_EMAIL", "support@example.com")}

def public(name):
    def view():
        u = current_user()
        if u and name in ("login", "register"):
            return redirect(url_for("pages.admin" if u.role == "admin" else "pages.dashboard"))
        return render_template(f"{name}.html")
    view.__name__ = name
    return view

def private(name, admin=False):
    def view():
        u = current_user()
        if not u: return redirect(url_for("pages.login"))
        if admin and u.role != "admin": return redirect(url_for("pages.dashboard"))
        return render_template(f"{name}.html")
    view.__name__ = name
    return view

for n, path in [("index", "/"), ("login", "/login"), ("register", "/register"), ("forgot", "/forgot"),
                ("about", "/about"), ("contact", "/contact")]:
    bp.add_url_rule(path, n, public(n))
for n in ("dashboard", "classify", "collect", "history"):
    bp.add_url_rule(f"/{n}", n, private(n))
bp.add_url_rule("/admin", "admin", private("admin", admin=True))
