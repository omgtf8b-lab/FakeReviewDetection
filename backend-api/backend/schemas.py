from datetime import date, datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Role = Literal["buyer", "seller", "admin", "engineer"]
Label = Literal["real", "fake", "pending"]
VerificationStatus = Literal["verified", "not_found", "unverified", "revoked"]


class UserAuth(BaseModel):
    email: EmailStr = Field(description="Email đăng nhập")
    password: str = Field(min_length=8, max_length=128, description="Mật khẩu tối thiểu 8 ký tự")


class UserCreate(UserAuth):
    role: Role = "buyer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255, description="Tên sản phẩm")
    product_code: Optional[str] = Field(default=None, min_length=3, max_length=80, description="Mã sản phẩm; bỏ trống để hệ thống tự tạo")
    brand: Optional[str] = Field(default=None, max_length=150)
    sku: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    price: float = Field(gt=0)
    description: Optional[str] = Field(default=None, max_length=10000)
    manufacturer: Optional[str] = Field(default=None, max_length=255, description="Nhà sản xuất")
    origin: Optional[str] = Field(default=None, max_length=255, description="Xuất xứ")
    batch_number: Optional[str] = Field(default=None, max_length=100, description="Số lô")
    production_date: Optional[date] = Field(default=None, description="Ngày sản xuất")
    expiry_date: Optional[date] = Field(default=None, description="Ngày hết hạn")
    official_source_url: Optional[str] = Field(default=None, max_length=1000, description="Nguồn chính thức")
    verification_note: Optional[str] = Field(default=None, max_length=5000, description="Ghi chú xác minh")

    @field_validator("product_code", "sku", "batch_number", mode="before")
    @classmethod
    def strip_optional_codes(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None


class RoleUpdate(BaseModel):
    role: Role


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    product_code: Optional[str] = Field(default=None, min_length=3, max_length=80)
    brand: Optional[str] = Field(default=None, max_length=150)
    sku: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    price: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=10000)
    manufacturer: Optional[str] = Field(default=None, max_length=255)
    origin: Optional[str] = Field(default=None, max_length=255)
    batch_number: Optional[str] = Field(default=None, max_length=100)
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None
    official_source_url: Optional[str] = Field(default=None, max_length=1000)
    verification_note: Optional[str] = Field(default=None, max_length=5000)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_code: str
    name: str
    image_url: Optional[str] = None
    stock: Optional[int] = None
    sale_status: str = 'active'
    brand: Optional[str]
    sku: Optional[str]
    category: Optional[str]
    price: float
    description: Optional[str]
    manufacturer: Optional[str]
    origin: Optional[str]
    batch_number: Optional[str]
    production_date: Optional[date]
    expiry_date: Optional[date]
    official_source_url: Optional[str]
    verification_note: Optional[str]
    is_verified: bool
    verification_status: str
    shop_id: int
    created_at: datetime


class ReviewCreate(BaseModel):
    product_id: int = Field(gt=0)
    rating: float = Field(ge=1, le=5)
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Nội dung đánh giá không được rỗng")
        return value


class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(default=None, ge=1, le=5)
    content: Optional[str] = Field(default=None, min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: Optional[str]):
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Nội dung không được rỗng")
        return value


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    review_id: int
    predicted_label: str
    fake_probability: float
    real_probability: float
    confidence_score: float
    explanation: Optional[str]
    model_name: str
    model_version: str
    created_at: datetime


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    user_id: int
    author_name: Optional[str] = None
    effective_label: Optional[str] = None
    moderation_label: Optional[str] = None
    rating: float
    content: str
    created_at: datetime
    prediction: Optional[PredictionResponse] = None


class PredictionRequest(BaseModel):
    review_id: int = Field(gt=0)


class PredictionDirectRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class PredictionDirectResponse(BaseModel):
    predicted_label: str
    fake_probability: float
    real_probability: float
    confidence_score: float
    explanation: Optional[str]
    model_name: str
    model_version: str


class PaginatedProducts(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


class PaginatedReviews(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int


class StatisticsOverview(BaseModel):
    total_users: int
    total_products: int
    total_reviews: int
    total_predictions: int
    fake_reviews: int
    real_reviews: int
    pending_reviews: int
    fake_percentage: float


class MyStatisticsOverview(BaseModel):
    total_products: int
    my_reviews: int
    my_predictions: int
    my_fake_reviews: int
    my_real_reviews: int
    my_pending_reviews: int
    my_fake_percentage: float


class ProductStatistics(BaseModel):
    product_id: int
    total_reviews: int
    fake_reviews: int
    real_reviews: int
    average_rating: float
    fake_percentage: float


class ProductVerificationResponse(BaseModel):
    verified: bool
    status: VerificationStatus
    message: str
    query: str
    source: str = "Cơ sở dữ liệu sản phẩm đã đăng ký"
    product: Optional[ProductResponse] = None
    qr_payload: Optional[str] = None


class ProductVerificationRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=300, description="Mã sản phẩm hoặc dữ liệu lấy từ QR")


class ProductVerificationUpdate(BaseModel):
    verification_status: Literal["verified", "pending", "revoked"]
    verification_note: Optional[str] = Field(default=None, max_length=5000)


class QRCodeResponse(BaseModel):
    product_id: int
    product_code: str
    qr_payload: str
    verification_url: str


class MessageResponse(BaseModel):
    message: str

ReportReason = Literal["fake", "spam", "misleading", "inappropriate", "other"]


class ReviewReportCreate(BaseModel):
    reason: ReportReason = Field(description="Lý do báo cáo đánh giá")
    description: Optional[str] = Field(default=None, max_length=1000, description="Mô tả chi tiết lý do báo cáo")
    detail: Optional[str] = Field(default=None, max_length=1000, description="Alias tương thích ngược với Mobile nếu gửi detail")

    @field_validator("reason", mode="before")
    @classmethod
    def map_legacy_reasons(cls, value: Any):
        if value == "abuse":
            return "inappropriate"
        return value

    @model_validator(mode="before")
    @classmethod
    def handle_detail_and_legacy_codes(cls, data: Any):
        if isinstance(data, dict):
            if "detail" in data and ("description" not in data or data["description"] is None):
                data["description"] = data["detail"]
            if data.get("reason") == "abuse":
                data["reason"] = "inappropriate"
        return data


class ReviewReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    review_id: int
    reporter_user_id: int
    reason: str
    description: Optional[str] = None
    status: str
    created_at: datetime

