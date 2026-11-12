"""Create all tables and the admin user. Usage: python database/init_db.py  (run from project root)
For PostgreSQL you can alternatively run database/schema.sql with psql."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app import create_app
from backend.extensions import db
from backend.models import User

app = create_app()
with app.app_context():
    db.create_all()
    email, pw = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if email and pw and not User.query.filter_by(email=email.lower()).first():
        u = User(full_name="Administrator", email=email.lower(), phone="0000000000", role="admin")
        u.set_password(pw); db.session.add(u); db.session.commit(); print("Admin created:", email)
    print("Database ready.")
