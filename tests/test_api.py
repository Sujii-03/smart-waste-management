from datetime import date, timedelta
from tests.conftest import post, patch, make_user, login, png_bytes
from backend.services import classifier

REG = {"full_name": "Jane Doe", "email": "jane@x.com", "phone": "+911234567890",
       "password": "password123", "confirm_password": "password123"}

def test_register_login_flow(client):
    assert post(client, "/api/auth/register", json=REG).status_code == 201
    assert post(client, "/api/auth/register", json=REG).status_code == 409          # duplicate email
    assert post(client, "/api/auth/register", json={**REG, "email": "bad"}).status_code == 400
    assert post(client, "/api/auth/register", json={**REG, "email": "n@x.com", "confirm_password": "zzz"}).status_code == 400
    assert login(client, "jane@x.com", "wrong").status_code == 401
    assert login(client, "jane@x.com").status_code == 200
    assert client.get("/api/auth/me").json["user"]["email"] == "jane@x.com"

def test_csrf_required(client):
    assert client.post("/api/auth/login", json={}).status_code == 403

def test_auth_required(client):
    assert client.get("/api/collections").status_code == 401
    assert client.get("/api/stats/admin").status_code == 401

def test_collection_lifecycle_and_admin(client, app):
    make_user(); make_user("root@x.com", "admin")
    login(client)
    good = {"category": "plastic", "quantity": 2.5, "address": "12 Green Street", "pickup_date": (date.today() + timedelta(days=2)).isoformat()}
    r = post(client, "/api/collections", json=good); assert r.status_code == 201
    rid = r.json["request"]["id"]
    assert post(client, "/api/collections", json={**good, "pickup_date": "2000-01-01"}).status_code == 400
    assert post(client, "/api/collections", json={**good, "quantity": -1}).status_code == 400
    assert post(client, "/api/collections", json={**good, "category": "lava"}).status_code == 400
    assert client.get("/api/admin/users").status_code == 403                          # normal user blocked
    post(client, "/api/auth/logout"); login(client, "root@x.com")
    assert patch(client, f"/api/admin/requests/{rid}", json={"status": "completed"}).status_code == 409  # must approve first
    assert patch(client, f"/api/admin/requests/{rid}", json={"status": "approved"}).status_code == 200
    assert patch(client, f"/api/admin/requests/{rid}", json={"status": "completed"}).status_code == 200
    s = client.get("/api/stats/admin").json
    assert s["requests"] == 1 and s["completed"] == 1 and s["users"] == 2
    assert client.get("/api/admin/reports/requests.csv").status_code == 200
    assert client.get("/api/admin/reports/requests.xlsx").status_code == 200

def test_classify_without_model_returns_503(client, monkeypatch):
    make_user(); login(client)
    monkeypatch.setattr(classifier, "MODEL_PATH", "/nonexistent.keras")
    r = post(client, "/api/classify", data={"image": (png_bytes(), "x.png")}, content_type="multipart/form-data")
    assert r.status_code == 503

def test_classify_flow_with_stubbed_model(client, monkeypatch):
    make_user(); login(client)
    monkeypatch.setattr(classifier, "predict", lambda path: ("metal", 0.91))  # stub: tests the plumbing, not the AI
    r = post(client, "/api/classify", data={"image": (png_bytes(), "x.png")}, content_type="multipart/form-data")
    assert r.status_code == 201 and r.json["result"]["category"] == "metal"
    assert client.get("/api/stats/user").json["by_category"]["metal"] == 1
    assert client.get(r.json["result"]["image_url"]).status_code == 200

def test_classify_rejects_bad_files(client):
    make_user(); login(client)
    for name, data in [("x.txt", b"hello"), ("x.png", b"not really a png"), ("x.gif", png_bytes().read())]:
        import io
        r = post(client, "/api/classify", data={"image": (io.BytesIO(data), name)}, content_type="multipart/form-data")
        assert r.status_code == 400
