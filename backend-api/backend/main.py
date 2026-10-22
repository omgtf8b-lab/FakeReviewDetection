from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
import extended_models
from routers import workspace
from routers import integrations
from routers import product_links
from config import settings
from database import Base, engine
from routers import auth, users, products, reviews, predictions, statistics, admin, product_verification
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    from database import SessionLocal
    from extended_models import Setting
    from ml.predictor import predictor
    with SessionLocal() as db:
        active = db.get(Setting, 'active_model')
        if active:
            settings.model_path = active.value
            predictor.reload()
    yield


app = FastAPI(
    title=settings.app_name,
    version="3.0.0",
    openapi_tags=[
        {"name": "Hệ thống", "description": "Kiểm tra trạng thái API và cơ sở dữ liệu."},
        {"name": "Xác thực", "description": "Đăng ký, đăng nhập và JWT."},
        {"name": "Người dùng", "description": "Thông tin và quản lý tài khoản."},
        {"name": "Sản phẩm", "description": "Quản lý sản phẩm và tạo dữ liệu QR."},
        {"name": "Xác thực sản phẩm", "description": "Tra cứu nguồn gốc sản phẩm bằng mã sản phẩm hoặc QR."},
        {"name": "Đánh giá", "description": "Quản lý đánh giá sản phẩm."},
        {"name": "Phát hiện đánh giá giả", "description": "Phân tích review bằng mô hình ML/NLP và xem lịch sử dự đoán."},
        {"name": "Thống kê", "description": "Thống kê dữ liệu đánh giá và phát hiện giả."},
        {"name": "Quản trị", "description": "Các chức năng dành cho quản trị viên/kỹ sư."},
    ],
    description=(
        "Backend phục vụ hệ thống Phát hiện đánh giá sản phẩm giả (Fake Review Detection). "
        "Bao gồm xác thực JWT, quản lý sản phẩm/đánh giá, dự đoán ML, lịch sử và thống kê."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Hệ thống"], summary="Thông tin API")
def root():
    return {"message": "API Phát hiện đánh giá sản phẩm giả đang hoạt động", "docs": "/docs", "version": app.version}


@app.get("/health", tags=["Hệ thống"], summary="Kiểm tra API")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/health/db", tags=["Hệ thống"], summary="Kiểm tra kết nối cơ sở dữ liệu")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "error", "database": "unavailable"}


app.include_router(auth.router)
app.include_router(auth.legacy_router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(predictions.router)
app.include_router(statistics.router)
app.include_router(admin.router)
app.include_router(product_verification.router)
app.include_router(product_verification.page_router)
app.include_router(workspace.router)
app.include_router(integrations.router)
app.include_router(product_links.router)
