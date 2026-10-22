# Module cào review → database nội bộ → phân tích

Cập nhật 22/10/2026. Mã mới đã nối vào API hiện có; không cần nhập bình luận bằng tay trong luồng thu thập thành công.

## Các hàm dùng lại

- services/marketplaces.py: identify_url, collect, parse_lazada_review_page, lazada_reviews; chuẩn hóa link và review từ nguồn công khai.
- services/browser_collector.py: collect_browser; đọc DOM bằng Selenium, có giới hạn thời gian và số trang.
- services/collection_strategy.py: collect_bounded; giới hạn 105 giây cho toàn bộ thu thập. Lazada thử nguồn PDP công khai trước để giảm số lần mở Chrome.
- services/review_repository.py: save_collection, load_collection; lưu/đọc dữ liệu và xác minh SHA-256.
- services/crawl_pipeline.py: crawl_to_database, analyze_from_database; giao diện thư viện cho nhóm.

Ví dụ Python chạy từ backend-api/backend, với tài khoản nội bộ tồn tại:

```python
from database import SessionLocal
from services.crawl_pipeline import crawl_to_database, analyze_from_database

with SessionLocal() as db:
    snapshot = crawl_to_database(db, user_id=USER_ID_TRONG_DATABASE,
        url=LINK_SAN_PHAM, limit=50, mode='auto')
    snapshot, result = analyze_from_database(db, snapshot.id,
        user_id=USER_ID_TRONG_DATABASE)
```

Hàm thu thập ghi và commit dữ liệu trước. Hàm phân tích đọc lại dữ liệu đã lưu, không cào lần thứ hai. Nếu phân tích lỗi, dữ liệu nguồn vẫn tồn tại.

## Database

Database hiện tại: backend-api/backend/fake_review.db. Có thể đổi DATABASE_URL sang PostgreSQL theo cấu hình chung của project.

- collection_snapshots: chủ dữ liệu, link, nền tảng, nguồn, thời điểm lưu, JSON nguồn chuẩn hóa, SHA-256.
- collected_reviews (bảng bổ sung mới): mỗi review một dòng, snapshot_id, source_review_id, nội dung, số sao, mã tác giả nếu có, JSON review và SHA-256. Unique(snapshot_id, source_review_id) loại cùng bản ghi trong một lần thu thập.
- product_link_analyses: công việc, trạng thái và kết quả phân tích, tham chiếu bản lưu trong result.

Không xóa/rebuild bảng cũ. Khi backend khởi động với AUTO_CREATE_TABLES=true, SQLAlchemy tạo thêm bảng mới. Bản lưu JSON cũ vẫn đọc được. Không gộp kết quả nhiều lần thu thập thành số người duy nhất: một người hoặc review có thể lặp giữa các lần.

## API

POST /api/product-links với JSON url, limit (1..200), collection_mode (auto/browser/http). Yêu cầu đăng nhập. Trả job ID; GET /api/product-links/{id} theo dõi.

GET /api/product-links/snapshots/{id}: tải dữ liệu đã lưu.
GET /api/product-links/snapshots/{id}/reviews?offset=0&limit=50: đọc danh sách review đã lưu theo trang.
POST /api/product-links/snapshots/{id}/analyze: phân tích lại, không cào lần nữa.

Các API chỉ đọc/phân tích dữ liệu của chủ tài khoản. Nếu nội dung bản lưu hoặc bảng review bị sửa/xóa trái với evidence, trả lỗi 409. Nếu bước phân tích thất bại sau lưu, kết quả giữ snapshot_id và UI có nút phân tích lại.

Công cụ CLI cho thành viên có quyền truy cập database trên máy nhóm (không phải API công khai):

```cmd
python crawl_product.py --url "https://www.lazada.vn/products/pdp-i13326005147-s116386241186.html" --owner-email buyer@example.com --limit 10 --mode http
```

Cài requirements-browser.txt cùng constraints-tested.txt, constraints-browser-tested.txt để dùng Selenium; cài requirements-media.txt nếu phân tích ảnh/video. Các launcher RUN_LOCAL_* trong outputs dùng runtime có sẵn trên máy phát triển.

## Kết quả kiểm chứng

- 32 kiểm thử backend liên quan đã đạt: parser Lazada, lỗi trang kế tiếp không mất review trang trước, phân quyền, loại trùng, kiểm tra toàn vẹn, giữ dữ liệu khi phân tích lỗi và phát lại không cào lần hai.
- Flutter: 24 kiểm thử đạt, analyze không có lỗi; React và Flutter web build thành công.
- Thử nguồn thật Lazada có lần nhận 10 review, tổng số nguồn báo cáo 30; có 3 review tham chiếu media. Đây là phản hồi thật, không phải fixture tổng hợp.
- Đã đưa bản thu thập thành công đó vào DB của tài khoản buyer@example.com, snapshot 11; đọc/phân tích từ database thành công, job 18. Mode của job là snapshot: UI ghi rõ đang phân tích bản lưu, không lấy dữ liệu mới từ sàn. KET_QUA_DATABASE_2026-10-22.json ghi kết quả kiểm tra, không chép email/tên/người mua/đơn hàng từ phản hồi sàn.
- Lần gọi trực tiếp kế tiếp lại trả trang xác minh, job 17 lưu lượt thất bại với 0 review. Không thay dữ liệu bị chặn bằng dữ liệu giả hay tự phục vụ bản cũ như dữ liệu mới.
- Shopee/TikTok các lần thử vẫn bị từ chối/xác minh. Chrome chưa khởi động thành công trong môi trường này; lần thử Firefox cũng chưa tạo phiên WebDriver được. Chưa xác minh cào ổn định cả ba sàn.

## Phạm vi thực tế

Lazada hiện tối đa 3 trang, mỗi trang yêu cầu 10 bản ghi (có thể bỏ bản ghi chỉ có số sao). Không phải cào toàn bộ hàng nghìn bình luận. API limit 200 là trần số review, không phải cam kết sàn cung cấp đủ 200. Khi trang sau lỗi, giữ mẫu đã nhận và ghi cảnh báo; không retry liên tục, không vượt đăng nhập/CAPTCHA.

Kết quả tổng hợp áp dụng cho mẫu thu thập. Tỷ lệ dấu hiệu không phải xác suất review giả hay sản phẩm giả. Chưa tích hợp mô hình Việt/teencode/emoji mới; các dấu hiệu tiếng Việt hiện là kiểm tra quy tắc. Nguồn dữ liệu huấn luyện và nguồn dữ liệu cào tách biệt.
