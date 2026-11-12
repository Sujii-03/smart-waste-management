import io, os, tempfile
os.environ.update(SECRET_KEY="test-secret", DATABASE_URL="sqlite:///:memory:", UPLOAD_FOLDER=tempfile.mkdtemp())
import pytest
from PIL import Image
from backend.app import create_app
from backend.extensions import db
from backend.models import User

@pytest.fixture()
def app():
    a = create_app(); a.config["TESTING"] = True
    with a.app_context():
        db.create_all(); yield a; db.session.remove(); db.drop_all()

@pytest.fixture()
def client(app): return app.test_client()

def post(c, url, **kw):
    tok = c.get("/api/auth/csrf").json["token"]
    return c.post(url, headers={"X-CSRF-Token": tok}, **kw)

def patch(c, url, **kw):
    tok = c.get("/api/auth/csrf").json["token"]
    return c.patch(url, headers={"X-CSRF-Token": tok}, **kw)

def make_user(email="a@b.com", role="user", pw="password123"):
    u = User(full_name="Test User", email=email, phone="1234567890", role=role); u.set_password(pw)
    db.session.add(u); db.session.commit(); return u

def login(c, email="a@b.com", pw="password123"):
    return post(c, "/api/auth/login", json={"email": email, "password": pw})

def png_bytes():
    b = io.BytesIO(); Image.new("RGB", (32, 32), "green").save(b, "PNG"); b.seek(0); return b
