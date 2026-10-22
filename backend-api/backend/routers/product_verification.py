from html import escape
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import models
import schemas
from config import settings
from database import get_db

router = APIRouter(prefix="/api/product-verification", tags=["Xác thực sản phẩm"])
page_router = APIRouter(tags=["Xác thực sản phẩm"])


def _normalize_identifier(identifier: str) -> str:
    value = identifier.strip()
    # QR nội bộ: FAKE-REVIEW|PRODUCT|<MÃ>
    if "|PRODUCT|" in value:
        value = value.split("|PRODUCT|", 1)[1].strip()
    # QR dạng URL: .../xac-thuc-san-pham?identifier=<MÃ>
    if value.startswith(("http://", "https://")):
        try:
            query = parse_qs(urlparse(value).query)
            value = query.get("identifier", [value])[0].strip()
        except Exception:
            pass
    return value


def _find_product(identifier: str, db: Session):
    normalized = _normalize_identifier(identifier)
    product = db.query(models.Product).filter(models.Product.product_code == normalized).first()
    if product:
        return product, normalized
    # Hỗ trợ nhập ID số, thuận tiện cho demo.
    if normalized.isdigit():
        product = db.query(models.Product).filter(models.Product.id == int(normalized)).first()
    # Hỗ trợ nhập SKU nếu có.
    if not product:
        product = db.query(models.Product).filter(models.Product.sku == normalized).first()
    return product, normalized


def _build_verification_response(identifier: str, db: Session):
    product, normalized = _find_product(identifier, db)
    if not product:
        return {
            "verified": False,
            "status": "not_found",
            "message": "Không tìm thấy mã sản phẩm trong cơ sở dữ liệu đăng ký. Hệ thống chưa thể xác minh sản phẩm này.",
            "query": normalized,
        }

    if product.verification_status == "revoked":
        return {
            "verified": False,
            "status": "revoked",
            "message": "Mã sản phẩm đã bị thu hồi xác thực bởi quản trị viên.",
            "query": normalized,
            "product": product,
            "qr_payload": f"FAKE-REVIEW|PRODUCT|{product.product_code}",
        }

    if not product.is_verified or product.verification_status != "verified":
        return {
            "verified": False,
            "status": "unverified",
            "message": "Có thông tin sản phẩm nhưng mã này chưa được quản trị viên xác nhận là nguồn chính thức.",
            "query": normalized,
            "product": product,
            "qr_payload": f"FAKE-REVIEW|PRODUCT|{product.product_code}",
        }

    return {
        "verified": True,
        "status": "verified",
        "message": "Đã tìm thấy và xác minh sản phẩm trong cơ sở dữ liệu nguồn chính thức.",
        "query": normalized,
        "product": product,
        "qr_payload": f"FAKE-REVIEW|PRODUCT|{product.product_code}",
    }


@router.post(
    "/verify",
    response_model=schemas.ProductVerificationResponse,
    summary="Xác thực sản phẩm bằng mã hoặc dữ liệu QR",
    description=(
        "Nhận mã sản phẩm, ID số, SKU hoặc chuỗi lấy từ QR. Nếu bản ghi đã được quản trị viên "
        "xác nhận nguồn chính thức, API trả về thông tin gốc và trạng thái xác minh."
    ),
)
def verify_product(payload: schemas.ProductVerificationRequest, db: Session = Depends(get_db)):
    return _build_verification_response(payload.identifier, db)


@router.get(
    "/verify",
    response_model=schemas.ProductVerificationResponse,
    summary="Tra cứu sản phẩm bằng mã, SKU hoặc QR",
)
def verify_product_by_query(
    identifier: str = Query(..., min_length=1, max_length=300, description="Mã sản phẩm, SKU hoặc dữ liệu quét từ QR"),
    db: Session = Depends(get_db),
):
    return _build_verification_response(identifier, db)


def _status_ui(result: dict) -> tuple[str, str]:
    if result["status"] == "verified":
        return "ĐÃ XÁC MINH", "verified"
    if result["status"] == "revoked":
        return "ĐÃ THU HỒI XÁC MINH", "revoked"
    if result["status"] == "unverified":
        return "CHƯA XÁC MINH", "unverified"
    return "KHÔNG TÌM THẤY", "not-found"


@page_router.get(
    "/xac-thuc-san-pham",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def verification_page(
    identifier: str = Query(..., min_length=1, max_length=300),
    db: Session = Depends(get_db),
):
    # Route được map dưới dạng /xac-thuc-san-pham nhờ router prefix ../ trong FastAPI,
    # nhưng để tránh phụ thuộc cơ chế path normalization, main.py cũng đăng ký alias.
    result = _build_verification_response(identifier, db)
    label, css = _status_ui(result)
    product = result.get("product")

    if product:
        product_html = f"""
        <div class=\"grid\">
          <div><span>Mã sản phẩm</span><strong>{escape(product.product_code)}</strong></div>
          <div><span>Tên sản phẩm</span><strong>{escape(product.name)}</strong></div>
          <div><span>Thương hiệu</span><strong>{escape(product.brand or '—')}</strong></div>
          <div><span>SKU</span><strong>{escape(product.sku or '—')}</strong></div>
          <div><span>Nhà sản xuất</span><strong>{escape(product.manufacturer or '—')}</strong></div>
          <div><span>Xuất xứ</span><strong>{escape(product.origin or '—')}</strong></div>
          <div><span>Số lô</span><strong>{escape(product.batch_number or '—')}</strong></div>
          <div><span>Ngày sản xuất</span><strong>{escape(str(product.production_date or '—'))}</strong></div>
          <div><span>Hạn sử dụng</span><strong>{escape(str(product.expiry_date or '—'))}</strong></div>
        </div>
        """
    else:
        product_html = "<p class=\"empty\">Không có thông tin sản phẩm tương ứng trong cơ sở dữ liệu đăng ký.</p>"

    return HTMLResponse(f"""
    <!doctype html>
    <html lang=\"vi\">
    <head>
      <meta charset=\"utf-8\">
      <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
      <title>Xác thực sản phẩm</title>
      <style>
        body{{font-family:Arial,sans-serif;background:#f5f7fb;margin:0;color:#1f2937}}
        .wrap{{max-width:760px;margin:40px auto;padding:20px}}
        .card{{background:white;border-radius:18px;padding:28px;box-shadow:0 10px 35px rgba(0,0,0,.08)}}
        h1{{margin-top:0}} .badge{{display:inline-block;padding:8px 14px;border-radius:999px;font-weight:700;margin:8px 0 18px}}
        .verified{{background:#dcfce7;color:#166534}} .unverified{{background:#fef3c7;color:#92400e}}
        .revoked,.not-found{{background:#fee2e2;color:#991b1b}}
        .grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:20px}}
        .grid div{{background:#f8fafc;padding:14px;border-radius:12px}} .grid span{{display:block;font-size:12px;color:#64748b;margin-bottom:5px}}
        .grid strong{{font-size:15px}} .note{{padding:14px;border-left:4px solid #94a3b8;background:#f8fafc;margin-top:18px}}
        .empty{{color:#64748b}} @media(max-width:600px){{.grid{{grid-template-columns:1fr}} .wrap{{margin:10px auto}}}}
      </style>
    </head>
    <body><div class=\"wrap\"><div class=\"card\">
      <h1>Xác thực sản phẩm</h1>
      <div class=\"badge {css}\">{label}</div>
      <p>{escape(result['message'])}</p>
      {product_html}
      <div class=\"note\"><strong>Lưu ý:</strong> Không tìm thấy mã trong cơ sở dữ liệu chỉ có nghĩa là hệ thống chưa xác minh được sản phẩm; không nên dùng riêng tín hiệu này để kết luận pháp lý rằng sản phẩm chắc chắn là hàng giả.</div>
    </div></div></body></html>
    """)
