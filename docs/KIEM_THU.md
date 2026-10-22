# Vòng kiểm tra 22/10/2026

32 kiểm thử backend liên quan và 24 kiểm thử Flutter đạt; analyze và build thành công. Xem CAO_DU_LIEU_VA_DATABASE.md để phân biệt kiểm thử fixture, phản hồi thật và bản lưu. Các mục bên dưới là các vòng trước.

# Cập nhật 19/10/2026

Backend 41 kiểm thử đạt; Flutter 24 kiểm thử đạt; Flutter analyze và hai bản build web thành công. Kiểm thử Selenium thực tế chưa thành công do trình duyệt không khởi chạy/timeout. Xem PHUONG_AN_THU_THAP.md; các kết quả dưới đây mô tả các vòng trước.

# Kiểm thử luồng kiểm tra sản phẩm mới

- Backend: `pytest tests/test_upgrade.py tests/test_product_links.py -q` — **36 passed**, 27,14 giây; một cảnh báo TestClient/httpx.
- Flutter: **24 passed**; có kiểm thử gửi link, polling kết quả thiếu review, lịch sử không có nút mua hàng và các ca hồi quy.
- Web React: build thành công; bundle khoảng 829KB, gzip 233KB, còn cảnh báo kích thước chunk.
- Flutter web: build thành công; không xác nhận APK/IPA native.
- Ba link thật: kết quả lưu `KET_QUA_3_LINK.json`; TikTok/Shopee chưa lấy được review do giới hạn truy cập; Lazada lấy tên/mô tả nhưng không có review đọc được.
- Ảnh thật được tạo cho kiểm thử và video MP4 tổng hợp đã giải mã thành công; không dùng chúng làm bằng chứng chất lượng nhận diện gian lận thực tế.
- Kiểm thử mới bao gồm URL giả mạo/localhost, chuyển hướng không an toàn, nhận diện ID của ba sàn, bỏ trang CAPTCHA, không suy ra hàng thật khi có 0 review, bỏ bản ghi trùng ID, không chấm NLP tiếng Việt, phân quyền lịch sử và thống kê admin, ảnh/tệp giả định dạng, tệp trùng và khung hình video.

Không có mô hình ảnh/video giả hoặc dữ liệu nhãn gian lận thực địa mới được huấn luyện trong lần cập nhật này. Tỷ lệ mới là **tỷ lệ review/tệp có dấu hiệu trong mẫu**, không phải accuracy, xác suất hàng giả hay xác suất người viết là bot.

---

## Hồ sơ phiên bản trước (giữ làm lịch sử)

# Hồ sơ kiểm thử và phạm vi xác nhận

Kiểm tra trên Windows, Python 3.12, Flutter 3.47.7/Dart 3.13.5. Phiên bản Python packages nằm trong `constraints-tested.txt`; AI packages trong `constraints-ai-tested.txt`; web dùng package-lock.json, Flutter dùng pubspec.lock. Đây là kết quả quan sát thực tế trong phiên nâng cấp, không phải báo cáo tải production.

## Kết quả

| Kiểm tra | Kết quả |
|---|---|
| Backend `pytest tests/test_upgrade.py -q` | 18 passed, 22,25 giây |
| Flutter `flutter test --no-pub --concurrency=1` | 22 passed |
| Dart `dart analyze lib test` | No issues found |
| React `vite build` | Thành công; cảnh báo bundle khoảng 884KB, gzip 242KB |
| Flutter `flutter build web --no-pub --release --no-web-resources-cdn` | Thành công, khoảng 52 giây |
| API `/health` | 200, status ok, version 3.0.0 |
| Model-info | ready true, tfidf_svm_calibrated, version 20261018103459 |
| Web cổng 5173 / Flutter cổng 8080 | HTTP 200; giao diện đã mở kiểm tra |
| CORS Flutter origin http://127.0.0.1:8080 | OPTIONS 200, đúng Access-Control-Allow-Origin |
| Elasticsearch 8.17.0 localhost:9200 | Health available; reindex 12 tài liệu; tìm cable trả sản phẩm USB-C Cable |
| Huấn luyện SVM và DistilBERT | Hai artifact thật; số liệu trong BAO_CAO_THUC_NGHIEM.md |
| DistilBERT suy luận từ checkpoint lưu | Đã gọi predict_proba thành công với văn bản thử |

Backend có cảnh báo Starlette về tích hợp TestClient/httpx; hiện kiểm thử chạy đạt. Build web cảnh báo dung lượng bundle lớn; chưa tối ưu tách bundle và chưa đo tải nhiều người dùng.

## Các trường hợp backend chính

- Ranh giới điểm tài khoản 0, 50, 50,01, 69,99, 70, 100.
- Dự đoán model thật, LIME, giữ lịch sử và thống kê không đếm trùng nhiều phiên bản.
- Quyền xử lý báo cáo/kiểm duyệt và lưu audit.
- Hành vi review ngắn/lặp, cộng đồng phối hợp và bằng chứng.
- Đổi mật khẩu thu hồi phiên, reset dùng một lần và hết hiệu lực phiên cũ.
- Review chỉ sau mua hoàn tất; rollback giao dịch khi bước phân tích lỗi.
- Hoàn tất đơn không trừ tồn kho hai lần; đơn thiếu hàng giữ pending; không xóa sản phẩm có đơn.
- Xuất PDF/XLSX năm nhóm báo cáo, quyền role và chống công thức Excel từ nội dung người dùng.
- Thiếu model trả 503; A/B ổn định theo người dùng và chỉ tính đồng thuận khi có nhãn kiểm duyệt.
- Nhãn kiểm duyệt ảnh hưởng bộ lọc và nhãn hiệu lực, giữ dự đoán AI riêng.

Kiểm thử dùng database SQLite trong bộ nhớ và các tài khoản/đơn hàng tổng hợp. Luồng A/B sử dụng hai model được kiểm soát trong test để xác minh phân nhánh; không coi dữ liệu test đó là kết quả A/B thực địa.

## Các trường hợp Flutter chính

Parse schema người dùng, trạng thái đăng nhập/phiên hết hạn, báo cáo và yêu cầu đăng nhập, điều hướng trang chủ→sản phẩm→review→lọc→chi tiết, tìm kiếm debounce, nạp hơn 100 review qua phân trang và phân biệt P(fake) với confidence nhãn. HTTP được mock trong widget/unit test để kiểm soát kết quả. Ngoài test tự động, bản Flutter web đã hiển thị ba sản phẩm từ API và database demo đang chạy thật; ảnh tại `screenshots/flutter-web.png`.

Ảnh web hành vi/đồ thị: `screenshots/account-risk.png`. Bằng chứng giao diện xác nhận dữ liệu tổng hợp đã được nối, không xác nhận tài khoản demo gian lận thực tế.

## Chưa được xác nhận

- Google/Facebook/Phone login thật, SMTP/Twilio/FCM gửi ra ngoài; chủ dự án tự điền cấu hình. Không có thông báo nào được gửi đến người thật trong phiên này.
- APK/IPA trên thiết bị, cấu hình chữ ký Android/iOS và push nền; bản đã build là Flutter web.
- Redis/PostgreSQL thực tế, chuyển dữ liệu cũ bằng migration, backup/restore production, tải đồng thời và triển khai public.
- Độ chính xác tiếng Việt/ngoài miền, đánh giá cộng đồng đồ thị bằng ground truth thực tế và A/B đủ mẫu.
- Định dạng luận văn Word, khảo sát hoặc slide do chưa có các file đó.

## Chạy lại

Trong backend: `python -m pytest tests/test_upgrade.py -q`.
Trong web: `npm ci`, `npm run build`.
Trong Flutter: `flutter pub get`, `flutter analyze`, `flutter test`, `flutter build web --release --no-web-resources-cdn`.
Không cần huấn luyện lại model chỉ để mở demo; huấn luyện lại sẽ thay artifact nếu dùng đường dẫn mặc định.
