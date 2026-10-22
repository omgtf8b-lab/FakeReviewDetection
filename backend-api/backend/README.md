# API Phát hiện đánh giá sản phẩm giả + Xác thực sản phẩm

Backend FastAPI cho khóa luận **Phát hiện đánh giá sản phẩm giả (Fake Review Detection)**, đồng thời có module **xác thực sản phẩm bằng mã sản phẩm hoặc mã QR**.

## 1. Các tầng chức năng

- **Xác thực**: đăng ký, đăng nhập, JWT Bearer.
- **Người dùng**: hồ sơ, quản lý trạng thái, vai trò.
- **Sản phẩm**: CRUD, mã sản phẩm, thông tin thương hiệu/xuất xứ/nhà sản xuất/lô.
- **Xác thực sản phẩm**: nhập mã hoặc chuỗi quét QR để tra cứu bản ghi nguồn.
- **QR**: sinh payload QR và ảnh QR để demo.
- **Đánh giá**: CRUD, tự động chạy dự đoán sau khi tạo/sửa.
- **Phát hiện review giả**: TF-IDF + Logistic Regression, xác suất Fake/Real, confidence, giải thích đặc trưng.
- **Lịch sử dự đoán**: lưu từng lần phân tích.
- **Thống kê**: tổng review, fake/real, tỷ lệ fake, rating.
- **Quản trị**: quản lý review, đổi vai trò, xác nhận/thu hồi sản phẩm.

## 2. Cài đặt trên Windows

```cmd
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
```

Copy `.env.example` thành `.env`, sau đó sửa thông tin PostgreSQL và `SECRET_KEY`.

Ví dụ:

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg2://postgres:MAT_KHAU@localhost:5432/fake_review_db
SECRET_KEY=mot-chuoi-bi-mat-dai-it-nhat-32-ky-tu
VERIFICATION_BASE_URL=http://127.0.0.1:8000
```

## 3. Chạy API

```cmd
uvicorn main:app --reload
```

Swagger tiếng Việt:

```text
http://127.0.0.1:8000/docs
```

## 4. Tạo admin

```cmd
python seed_admin.py --email admin@example.com --password AdminPassword123
```

## 5. Luồng xác thực sản phẩm bằng QR / mã sản phẩm

```text
Người dùng quét QR hoặc nhập mã sản phẩm
                    ↓
             Product Verification API
                    ↓
        Tìm trong CSDL sản phẩm đăng ký
              ↙                  ↘
          Không có             Có bản ghi
             ↓                     ↓
      Chưa xác minh         Kiểm tra trạng thái
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
                 Verified                  Pending/Revoked
                    ↓                           ↓
          Hiện thông tin gốc          Cảnh báo/chưa xác minh
```

### API tra cứu

```text
POST /api/product-verification/verify
GET  /api/product-verification/verify?identifier=SP-...
```

Body POST:

```json
{
  "identifier": "SP-20260924-A1B2C3D4"
}
```

Có thể truyền thẳng chuỗi QR:

```text
FAKE-REVIEW|PRODUCT|SP-20260924-A1B2C3D4
```

Khi tìm thấy bản ghi đã được admin xác nhận, API trả về:

- Mã sản phẩm
- Tên
- Thương hiệu
- SKU
- Nhà sản xuất
- Xuất xứ
- Số lô
- Ngày sản xuất/hạn sử dụng
- Nguồn chính thức
- Trạng thái xác minh

### Sinh QR

```text
GET /api/products/{product_id}/qr
GET /api/products/{product_id}/qr/image
```

QR chứa payload dạng:

```text
FAKE-REVIEW|PRODUCT|<MÃ SẢN PHẨM>
```

Frontend/mobile chỉ cần quét QR, lấy chuỗi và gửi chuỗi đó tới `/api/product-verification/verify`.

> Lưu ý nghiệp vụ: **không tìm thấy mã trong CSDL của hệ thống không đủ để kết luận pháp lý rằng sản phẩm chắc chắn là hàng giả**. Ở tầng ứng dụng nên hiển thị “Không xác minh được/Không có trong nguồn đăng ký”. Muốn kết luận “chính hãng”, bản ghi phải đến từ nguồn đáng tin cậy và được admin xác nhận.

## 6. Phân quyền xác nhận sản phẩm

Seller có thể đăng ký thông tin sản phẩm, nhưng bản ghi mới ở trạng thái `pending`.

Admin có thể:

```text
PATCH /api/admin/products/{product_id}/verification
```

Body:

```json
{
  "verification_status": "verified",
  "verification_note": "Đã đối chiếu với dữ liệu nhà cung cấp."
}
```

Các trạng thái:

```text
pending  = chờ xác minh
verified = đã xác minh nguồn
revoked  = đã thu hồi xác minh
```

## 7. Phát hiện review giả

Luồng nghiên cứu:

```text
Review
  ↓
Tiền xử lý / Vector hóa TF-IDF
  ↓
Logistic Regression
  ↓
P(Fake) + P(Real)
  ↓
Fake / Real
  ↓
Lưu Prediction
```

Không dùng `random confidence` cho kết quả nghiên cứu. Khi chưa có model `.joblib`, backend chỉ có fallback phục vụ kiểm thử API.

Train model thật:

```cmd
python -m ml.train --data data\reviews.csv --output ml\models\fake_review_model.joblib
```

CSV tối thiểu:

```text
text,label
"Nội dung đánh giá...",real
"Nội dung đánh giá...",fake
```

## 8. Endpoint chính

### Xác thực

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Sản phẩm

```text
POST   /api/products
GET    /api/products
GET    /api/products/{id}
PUT    /api/products/{id}
DELETE /api/products/{id}
GET    /api/products/{id}/qr
GET    /api/products/{id}/qr/image
```

### Xác thực sản phẩm

```text
POST /api/product-verification/verify
GET  /api/product-verification/verify
```

### Đánh giá

```text
POST   /api/reviews
GET    /api/reviews
GET    /api/reviews/{id}
PUT    /api/reviews/{id}
DELETE /api/reviews/{id}
GET    /api/reviews/product/{product_id}
```

### AI

```text
POST /api/predictions/analyze
POST /api/predictions
GET  /api/predictions/{id}
GET  /api/predictions/history/me
GET  /api/predictions/model-info
POST /api/predictions/model/reload
```

### Thống kê / Quản trị

```text
GET    /api/statistics/overview
GET    /api/statistics/products/{product_id}
GET    /api/admin/reviews
DELETE /api/admin/reviews/{review_id}
PATCH  /api/admin/users/{user_id}/role
PATCH  /api/admin/products/{product_id}/verification
```

## 9. Database cũ

Nếu bạn đang có database của phiên bản trước, chạy:

```cmd
python migrate_legacy.py
```

Script sẽ thêm cột xác thực sản phẩm, tạo bảng mới nếu thiếu và chuyển prediction cũ sang bảng `predictions`.

## 10. Test

```cmd
pytest -q
```

## 11. Gợi ý kiến trúc frontend

Màn hình “Xác thực sản phẩm” nên có hai lựa chọn:

```text
[ Quét mã QR ]       [ Nhập mã sản phẩm ]
        ↓                    ↓
             Gửi identifier
                    ↓
          /api/product-verification/verify
                    ↓
     ┌──────────────┼────────────────┐
     ↓              ↓                ↓
  Đã xác minh   Chưa xác minh    Không tìm thấy
     ↓              ↓                ↓
 Hiện nguồn     Cảnh báo        Không xác minh
 sản phẩm       cần kiểm tra    được sản phẩm
```


### Database cũ

Nếu database cũ thiếu cột `users.is_active`, chạy `python migrate_legacy.py` trước khi đăng ký tài khoản mới.
