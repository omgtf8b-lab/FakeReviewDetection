import secrets
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import io

import models
import schemas
from auth import require_roles, get_current_user
from database import get_db
from config import settings

router = APIRouter(prefix="/api/products", tags=["Sản phẩm"])


def _generate_product_code() -> str:
    return f"SP-{datetime.now():%Y%m%d}-{secrets.token_hex(4).upper()}"


def _ensure_unique_product_code(db: Session, requested: str | None) -> str:
    code = requested.strip() if requested else _generate_product_code()
    if db.query(models.Product).filter(models.Product.product_code == code).first():
        if requested:
            raise HTTPException(status_code=409, detail="Mã sản phẩm đã tồn tại")
        return _ensure_unique_product_code(db, None)
    return code


@router.post("", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED,
             summary="Đăng ký sản phẩm chính hãng")
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("seller", "admin")),
):
    if product.expiry_date and product.production_date and product.expiry_date < product.production_date:
        raise HTTPException(status_code=422, detail="Ngày hết hạn không được trước ngày sản xuất")
    code = _ensure_unique_product_code(db, product.product_code)
    payload = product.model_dump(exclude={"product_code"})
    new_product = models.Product(product_code=code, **payload, shop_id=current_user.id)
    db.add(new_product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Không thể tạo sản phẩm vì dữ liệu bị trùng")
    db.refresh(new_product)
    return new_product


@router.get("", response_model=schemas.PaginatedProducts, summary="Tra cứu danh sách sản phẩm")
def get_all_products(
    search: str | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Product)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                models.Product.name.ilike(term),
                models.Product.description.ilike(term),
                models.Product.product_code.ilike(term),
                models.Product.brand.ilike(term),
            )
        )
    if category:
        query = query.filter(models.Product.category == category)
    total = query.count()
    items = (
        query.order_by(models.Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{product_id}", response_model=schemas.ProductResponse, summary="Xem thông tin sản phẩm")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    return product


@router.put("/{product_id}", response_model=schemas.ProductResponse, summary="Cập nhật thông tin sản phẩm")
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    if product.shop_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa sản phẩm này")
    values = payload.model_dump(exclude_unset=True)
    if "product_code" in values and values["product_code"] != product.product_code:
        if db.query(models.Product).filter(models.Product.product_code == values["product_code"]).first():
            raise HTTPException(status_code=409, detail="Mã sản phẩm đã tồn tại")
    new_production_date = values.get("production_date", product.production_date)
    new_expiry_date = values.get("expiry_date", product.expiry_date)
    if new_expiry_date and new_production_date and new_expiry_date < new_production_date:
        raise HTTPException(status_code=422, detail="Ngày hết hạn không được trước ngày sản xuất")
    for key, value in values.items():
        setattr(product, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", response_model=schemas.MessageResponse, summary="Xóa sản phẩm")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    if product.shop_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa sản phẩm này")
    db.delete(product)
    db.commit()
    return {"message": "Xóa sản phẩm thành công"}


@router.get("/{product_id}/qr", response_model=schemas.QRCodeResponse, summary="Lấy dữ liệu QR của sản phẩm")
def get_product_qr_data(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    payload = f"FAKE-REVIEW|PRODUCT|{product.product_code}"
    verification_url = f"{settings.verification_base_url}/xac-thuc-san-pham?identifier={quote(product.product_code)}"
    return {
        "product_id": product.id,
        "product_code": product.product_code,
        "qr_payload": payload,
        "verification_url": verification_url,
    }


@router.get("/{product_id}/qr/image", summary="Tạo ảnh QR cho sản phẩm")
def get_product_qr_image(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    try:
        import qrcode
    except ImportError:
        raise HTTPException(status_code=500, detail="Chưa cài thư viện qrcode. Hãy chạy pip install -r requirements.txt")
    verification_url = f"{settings.verification_base_url}/xac-thuc-san-pham?identifier={quote(product.product_code)}"
    image = qrcode.make(verification_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png", headers={"Content-Disposition": f'inline; filename="QR-{product.product_code}.png"'})
