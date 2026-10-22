"""Nâng cấp database cũ lên schema hiện tại mà không xóa dữ liệu."""
from datetime import datetime
import secrets

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
import models


def add_column_if_missing(table: str, column: str, ddl: str):
    inspector = inspect(engine)
    if not inspector.has_table(table):
        return
    columns = {c["name"] for c in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
    print(f"Đã thêm cột {table}.{column}")


def migrate_user_columns():
    # Thêm các cột tài khoản mới nếu database cũ chưa có.
    add_column_if_missing("users", "is_active", "BOOLEAN NOT NULL DEFAULT TRUE")


def migrate_product_columns():
    # Các cột mới đều có thể thêm dạng nullable trước để giữ dữ liệu cũ.
    additions = {
        "product_code": "VARCHAR(80)",
        "brand": "VARCHAR(150)",
        "sku": "VARCHAR(100)",
        "manufacturer": "VARCHAR(255)",
        "origin": "VARCHAR(255)",
        "batch_number": "VARCHAR(100)",
        "production_date": "DATE",
        "expiry_date": "DATE",
        "official_source_url": "VARCHAR(1000)",
        "verification_note": "TEXT",
        "is_verified": "BOOLEAN DEFAULT FALSE",
        "verification_status": "VARCHAR(20) DEFAULT 'pending'",
    }
    for column, ddl in additions.items():
        add_column_if_missing("products", column, ddl)

    inspector = inspect(engine)
    if not inspector.has_table("products"):
        return
    db: Session = SessionLocal()
    try:
        products = db.query(models.Product).all()
        for product in products:
            if not product.product_code or product.product_code == "PENDING":
                product.product_code = f"SP-{datetime.now():%Y%m%d}-{secrets.token_hex(4).upper()}"
            if not product.verification_status:
                product.verification_status = "pending"
            if product.is_verified is None:
                product.is_verified = False
        db.commit()
        print(f"Đã cập nhật mã sản phẩm cho {len(products)} sản phẩm.")
    finally:
        db.close()


def migrate_legacy_predictions():
    inspector = inspect(engine)
    if not inspector.has_table("reviews"):
        return
    review_columns = {c["name"] for c in inspector.get_columns("reviews")}
    legacy_cols = {"predicted_label", "confidence_score", "explanation"}
    if not legacy_cols.issubset(review_columns):
        return

    db: Session = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT id, predicted_label, confidence_score, explanation
            FROM reviews
            WHERE predicted_label IS NOT NULL
              AND predicted_label <> 'pending'
        """)).mappings().all()
        copied = 0
        for row in rows:
            exists = db.query(models.Prediction).filter(models.Prediction.review_id == row["id"]).first()
            if exists:
                continue
            label = str(row["predicted_label"]).lower()
            if label in {"giả", "fake", "spam"}:
                label = "fake"
            elif label in {"thật", "real", "genuine"}:
                label = "real"
            else:
                continue
            confidence = float(row["confidence_score"] or 0.5)
            fake_probability = confidence if label == "fake" else 1 - confidence
            real_probability = 1 - fake_probability
            db.add(models.Prediction(
                review_id=row["id"],
                predicted_label=label,
                fake_probability=round(fake_probability, 4),
                real_probability=round(real_probability, 4),
                confidence_score=round(confidence, 4),
                explanation=row["explanation"],
                model_name="legacy-keyword",
                model_version="legacy",
            ))
            copied += 1
        db.commit()
        print(f"Đã chuyển {copied} kết quả dự đoán cũ sang bảng predictions.")
    finally:
        db.close()


def main():
    # Tạo bảng mới nếu database chưa có.
    Base.metadata.create_all(bind=engine)
    migrate_user_columns()
    migrate_product_columns()
    migrate_legacy_predictions()
    print("Migration hoàn tất.")


if __name__ == "__main__":
    main()
