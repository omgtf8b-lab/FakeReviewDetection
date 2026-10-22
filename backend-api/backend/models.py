from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="buyer", index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    # Mã định danh chính dùng cho nhập tay và QR xác thực sản phẩm.
    product_code = Column(String(80), unique=True, index=True, nullable=False, default="PENDING")
    name = Column(String(255), nullable=False, index=True)
    brand = Column(String(150), nullable=True, index=True)
    sku = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    manufacturer = Column(String(255), nullable=True)
    origin = Column(String(255), nullable=True)
    batch_number = Column(String(100), nullable=True, index=True)
    production_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    official_source_url = Column(String(1000), nullable=True)
    verification_note = Column(Text, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False, index=True)
    verification_status = Column(String(20), nullable=False, default="pending", index=True)
    shop_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    shop = relationship("User", back_populates="products")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    predictions = relationship(
        "Prediction",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="Prediction.created_at.desc()",
    )

    @property
    def prediction(self):
        return self.predictions[0] if self.predictions else None


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_label_created", "predicted_label", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_label = Column(String(20), nullable=False, index=True)
    fake_probability = Column(Float, nullable=False)
    real_probability = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    review = relationship("Review", back_populates="predictions")

class ReviewReport(Base):
    __tablename__ = "review_reports"
    __table_args__ = (
        UniqueConstraint("review_id", "reporter_user_id", name="uq_review_reports_review_reporter"),
    )

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    review = relationship("Review")
    reporter = relationship("User")

