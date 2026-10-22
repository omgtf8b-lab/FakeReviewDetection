import os
from pathlib import Path
import tempfile

DB = Path(os.environ.get("TEST_DATABASE_PATH") or str(Path(tempfile.mkdtemp(prefix="fake-review-tests-")) / "test.db")).resolve()
if DB.exists():
    raise RuntimeError("Use a new disposable TEST_DATABASE_PATH; existing databases are never deleted.")
os.environ["DATABASE_URL"] = "sqlite:///" + DB.as_posix()
os.environ["SECRET_KEY"] = "test-secret-for-local"

from fastapi.testclient import TestClient
import main
import models
from database import SessionLocal


def test_full_flow():
    with TestClient(main.app) as client:
        assert client.get("/health").status_code == 200
        r = client.post("/api/auth/register", json={"email": "buyer@example.com", "password": "Password123"})
        assert r.status_code == 201
        buyer = client.post("/api/auth/login", json={"email": "buyer@example.com", "password": "Password123"}).json()
        buyer_headers = {"Authorization": f"Bearer {buyer['access_token']}"}

        with SessionLocal() as db:
            seller = models.User(email="seller@example.com", password_hash=main.auth.hash_password("Password123"), role="seller")
            admin = models.User(email="admin@example.com", password_hash=main.auth.hash_password("Password123"), role="admin")
            db.add_all([seller, admin])
            db.commit()

        seller_login = client.post("/api/auth/login", json={"email": "seller@example.com", "password": "Password123"}).json()
        seller_headers = {"Authorization": f"Bearer {seller_login['access_token']}"}
        product = client.post("/api/products", headers=seller_headers, json={"name": "Tai nghe Demo", "category": "Electronics", "price": 499000, "description": "Demo"})
        assert product.status_code == 201
        product_id = product.json()["id"]
        product_code = product.json()["product_code"]
        assert product.json()["is_verified"] is False

        # Tra cứu trước khi admin duyệt: có dữ liệu nhưng chưa xác minh.
        verification = client.post("/api/product-verification/verify", json={"identifier": product_code})
        assert verification.status_code == 200
        assert verification.json()["status"] == "unverified"

        admin_login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "Password123"}).json()
        admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}
        approve = client.patch(f"/api/admin/products/{product_id}/verification", headers=admin_headers, json={"verification_status": "verified", "verification_note": "Demo: đã đối chiếu dữ liệu nguồn."})
        assert approve.status_code == 200
        assert approve.json()["is_verified"] is True

        verification = client.post("/api/product-verification/verify", json={"identifier": product_code})
        assert verification.status_code == 200
        assert verification.json()["verified"] is True
        assert verification.json()["product"]["product_code"] == product_code

        page = client.get("/xac-thuc-san-pham", params={"identifier": product_code})
        assert page.status_code == 200
        assert "Xác thực sản phẩm" in page.text
        assert product_code in page.text

        qr_data = client.get(f"/api/products/{product_id}/qr").json()
        assert qr_data["product_code"] == product_code
        assert "/xac-thuc-san-pham" in qr_data["verification_url"]
        qr_payload = qr_data["qr_payload"]
        qr_verification = client.post("/api/product-verification/verify", json={"identifier": qr_payload})
        assert qr_verification.status_code == 200
        assert qr_verification.json()["verified"] is True
        assert client.get(f"/api/products/{product_id}/qr/image").status_code == 200
        assert client.post("/api/product-verification/verify", json={"identifier": "SP-NOT-EXIST"}).json()["status"] == "not_found"

        order = client.post('/api/workspace/purchases', headers=buyer_headers, json={'product_id': product_id, 'quantity': 1})
        assert order.status_code == 200
        assert client.patch(f"/api/workspace/purchases/{order.json()['id']}", headers=seller_headers, json={'status': 'completed'}).status_code == 200
        review = client.post("/api/reviews", headers=buyer_headers, json={"product_id": product_id, "rating": 5, "content": "Sản phẩm quá tuyệt vời, rất hài lòng, mua ngay"})
        assert review.status_code == 201
        assert review.json()["prediction"]["predicted_label"] in {"fake", "real"}
        review_id = review.json()["id"]

        assert client.get(f"/api/reviews/{review_id}").status_code == 200
        assert client.get("/api/predictions/history/me", headers=buyer_headers).status_code == 200
        assert client.post("/api/predictions/analyze", json={"content": "Dùng 3 tháng rồi, pin ổn."}).status_code == 200

        assert client.get("/api/statistics/overview", headers=admin_headers).status_code == 200
        assert client.get("/api/admin/reviews", headers=admin_headers).status_code == 200

        assert client.post("/api/products", json={"name": "X", "price": 1}).status_code == 401
        assert client.post("/api/reviews", headers=buyer_headers, json={"product_id": product_id, "rating": 5, "content": "Test user_id"}).status_code == 201

    main.engine.dispose()
    if DB.exists():
        DB.unlink()
