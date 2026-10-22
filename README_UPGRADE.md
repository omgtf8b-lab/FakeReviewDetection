# Fake Review Detection — bản nâng cấp khóa luận

Mã nguồn được sửa trên bản sao trong thư mục này; ZIP người dùng gửi được giữ nguyên. Đọc `docs/KIEM_THU.md` để phân biệt chức năng đã kiểm thử với tích hợp cần chủ dự án cấu hình.

## Cập nhật 22/10: cào → lưu database → phân tích

Đã thêm bảng collected_reviews và thư viện services/crawl_pipeline.py. Dữ liệu được lưu trước khi phân tích; có API đọc review theo trang và phát lại từ database. Đã lấy được một mẫu 10 review thật của link Lazada và kiểm chứng phân tích bản lưu trong DB (job 18, buyer@example.com). Thu thập trực tiếp vẫn chập chờn do trang xác minh; chưa cào ổn định ba sàn hoặc toàn bộ hàng nghìn review. Xem [module và kiểm chứng](docs/CAO_DU_LIEU_VA_DATABASE.md).

## Cập nhật 19/10: scraping chính, nhập review dự phòng

Đã nối Selenium làm nguồn chính, HTTP công khai làm bước tiếp theo, nhập review/file làm kiểm thử và dự phòng. Có lưu bộ dữ liệu với thời điểm, SHA-256 và phân tích lại bản lưu. **Chrome chưa khởi chạy thành công trong kiểm thử thực tế tại môi trường này; chưa xác nhận đọc review thật bằng Selenium từ ba sàn.** Xem [cách cài và phạm vi kiểm thử](docs/PHUONG_AN_THU_THAP.md).

## Luồng người dùng mới: kiểm tra sản phẩm từ link / ảnh / video

Mở http://127.0.0.1:5173/review-check sau đăng nhập. Người dùng thường chỉ thấy kiểm tra sản phẩm, lịch sử riêng, thông báo, tài khoản và trợ giúp. Thống kê mới dành riêng admin/kỹ sư; các chức năng đơn hàng/tồn kho trước đây được giữ trong mã nguồn cũ để tham khảo, không nằm trong luồng người dùng mới.

App Flutter mở mặc định tab **Kiểm tra**, có **Lịch sử** và **Tài khoản**; chỉ admin/kỹ sư có tab quản trị. Bản build web nằm trong frontend_mobile/build/web.

Có nhận diện link Shopee Việt Nam, TikTok Shop, Lazada Việt Nam; thu thập dữ liệu công khai đọc được, giải thích dấu hiệu, tỷ lệ trên mẫu, lưu lịch sử và tải kết quả JSON. Nếu sàn chặn hoặc không trả review, kết quả là **chưa đủ cơ sở**, không tạo review hay tỷ lệ giả lập. Ba link người dùng gửi đã được kiểm tra: TikTok xác minh bảo mật; Shopee từ chối truy cập; Lazada đọc được tên/mô tả sản phẩm nhưng chưa đọc được review. Xem docs/KET_QUA_3_LINK.json và docs/LUONG_KIEM_TRA_SAN_PHAM.md.

Tải ảnh/video: kiểm tra định dạng/kích thước, ảnh/tệp trùng; video lấy tối đa 6 khung hình. Đây chưa phải mô hình phát hiện ảnh/video AI hoặc xác minh hàng chính hãng. Không tính xác suất hàng giả từ các dấu hiệu này.

Để đọc video trên máy mới, tại backend-api/backend cài:

```powershell
python -m pip install -r requirements-media.txt -c constraints-tested.txt -c constraints-media-tested.txt
```

Môi trường local hiện tại đã cài bộ đọc video. Đọc tài liệu luồng mới trước các mục nghiệp vụ cũ bên dưới. ZIP bàn giao sử dụng database demo tổng hợp mới, không chép tài khoản cá nhân đã đăng ký trong database đang làm việc.

## Chạy nhanh trên máy hiện tại

1. Mở `RUN_LOCAL_API.cmd` ở thư mục outputs, đợi API khởi động.
2. Mở `RUN_LOCAL_WEB.cmd`, truy cập http://127.0.0.1:5173 và chọn **Kiểm tra sản phẩm** sau đăng nhập.
3. Muốn xem Flutter, mở `RUN_LOCAL_MOBILE.cmd`, truy cập http://127.0.0.1:8080. Bản Flutter web dùng chung backend.
4. Tìm kiếm Elasticsearch cần `RUN_LOCAL_SEARCH.cmd`, đợi http://127.0.0.1:9200 trả JSON, rồi dùng nút **Đồng bộ chỉ mục** trong tab Tìm kiếm nâng cao.

Nếu terminal báo cổng đã dùng thì server đang chạy; không mở thêm bản thứ hai trên cùng cổng. Dừng bằng Ctrl+C trong terminal tương ứng.

Tài khoản dữ liệu demo:

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản trị | admin@example.com | <DEMO_PASSWORD_FROM_ENV> |
| Bán hàng | seller@example.com | <DEMO_PASSWORD_FROM_ENV> |
| Người mua | buyer@example.com | <DEMO_PASSWORD_FROM_ENV> |
| Kỹ sư | engineer@example.com | <DEMO_PASSWORD_FROM_ENV> |

Dữ liệu demo là dữ liệu tổng hợp. Hai tài khoản demo_account_a/b mô phỏng lặp nội dung qua nhiều sản phẩm; không phải tài khoản gian lận ngoài đời. `seed_demo.py` tạo dữ liệu khi database mới; không cần chạy lại mỗi lần mở ứng dụng.

## Cài đặt chuẩn khi chuyển máy

Dùng Python 3.12 và Node có npm. Các launcher ở thư mục outputs chỉ dành cho đường dẫn máy hiện tại.

Từ `backend-api/backend`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c constraints-tested.txt
$env:DATABASE_URL='sqlite:///./fake_review.db'
.\.venv\Scripts\python.exe seed_demo.py
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Để dùng DistilBERT, cài thêm `requirements-ai.txt` với `-c constraints-tested.txt -c constraints-ai-tested.txt`. Artifact SVM được lưu bằng scikit-learn 1.9.1; dùng đúng phiên bản hoặc train lại trong môi trường mới. Chỉ nạp artifact joblib từ nguồn tin cậy của dự án.

Từ `frontend-web`:

```powershell
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Từ `frontend_mobile` với Flutter 3.47.7 / Dart 3.13.5 đã kiểm thử:

```powershell
flutter pub get
flutter run -d chrome --web-port=8080 --dart-define=API_BASE_URL=http://127.0.0.1:8001
```

Android emulator dùng `API_BASE_URL=http://10.0.2.2:8001`; thiết bị thật dùng IP LAN máy chạy API và backend bind `0.0.0.0`. Bản phát hành cần endpoint HTTPS; cấu hình Android/iOS/Firebase theo `docs/CAU_HINH_DICH_VU.md`. Chưa tạo và thử APK trên thiết bị thật trong phiên này.

Khi chạy Vite local, web gọi `/api` trên chính cổng đang mở và Vite chuyển tiếp tới `127.0.0.1:8001`, tránh lỗi CORS nếu web chuyển sang cổng 5174. Để `VITE_API_BASE_URL` trống cho cấu hình này; nếu tự đặt URL API, cần cấu hình CORS phù hợp.

API docs: http://127.0.0.1:8001/docs. Model thực nạp: `/api/predictions/model-info`. Thiếu artifact sẽ trả 503 khi phân tích, không tạo dự đoán giả lập.

## Các phần đã bổ sung

- SVM có hiệu chỉnh xác suất; DistilBERT đã huấn luyện thật, cùng tập test; LIME và lưu phiên bản dự đoán.
- Phân tích tài khoản bằng hành vi, ngưỡng 50%/70%; đồ thị người dùng–sản phẩm và cộng đồng Louvain có bằng chứng.
- Độ uy tín shop, chuỗi thời gian, sao sau lọc, so sánh shop cùng nhóm sản phẩm và gợi ý cải thiện.
- Mua hàng/hoàn tất/trừ tồn kho; review sau mua; ảnh/trạng thái hàng; danh mục; hồ sơ; đổi/khôi phục mật khẩu; báo cáo, kiểm duyệt có lịch sử; phản hồi và bình chọn hữu ích trên web.
- Trang nghiệp vụ web và tab Hoạt động Flutter nối API; phân quyền buyer/seller/admin/engineer.
- Quản lý model, tác vụ train, kích hoạt phiên bản, A/B theo người dùng và feedback từ nhãn kiểm duyệt.
- Elasticsearch thật, hàng đợi đồng bộ, cache bộ nhớ hoặc Redis; Excel/PDF cho review/shop/danh mục/cụm/model.
- Bộ nối Firebase Google/Facebook/Phone, SMTP/Twilio/FCM; hàng đợi thông báo chỉ gửi khi chạy worker với `--deliver` và đủ cấu hình.

Web có phần quản trị/kỹ sư đầy đủ hơn Flutter. Flutter tập trung tra cứu, review, mua hàng, hồ sơ, thông báo, báo cáo và quản lý hàng của shop. Không cam kết mọi màn hình quản trị web đều có bản Flutter tương ứng.

## Tài liệu bàn giao

- `docs/THIET_KE_HE_THONG.md`: use case, đặc tả, class/ERD/activity/sequence bằng Mermaid.
- `docs/BAO_CAO_THUC_NGHIEM.md`: số liệu và cấu hình huấn luyện thật.
- `docs/CAU_HINH_DICH_VU.md`: điền cấu hình dịch vụ trên máy.
- `docs/KICH_BAN_DEMO.md`: trình tự demo theo vai trò.
- `docs/KIEM_THU.md`: bằng chứng kiểm tra và giới hạn.
- `docs/TIEN_DO_CAP_NHAT.md`: đối chiếu những phần đã làm và việc học thuật còn cần người dùng.

Bản thảo luận văn Word, khảo sát thực tế và slide bảo vệ chưa được cung cấp. Các tài liệu này là nguồn để bạn tích hợp và xác minh vào báo cáo, chưa thay thế một luận văn đã được giảng viên duyệt.
