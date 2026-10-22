# Cấu hình dịch vụ trên máy của chủ dự án

Bạn đã xác nhận có tài khoản dịch vụ và sẽ tự cấu hình. Không gửi mật khẩu, private key hoặc service-account JSON vào chat hay commit lên Git. Mẫu chỉ chứa tên biến, không chứa bí mật.

## Backend

Tại `backend-api/backend`, cài `requirements-integrations.txt`. Tạo `.env`, chép các mục cần dùng từ `.env.integrations.example`. Giữ `DATABASE_URL=sqlite:///./fake_review.db` nếu chạy demo SQLite. Cấu hình `SECRET_KEY` ngẫu nhiên đủ dài; production buộc ít nhất 32 ký tự. Restart API và worker sau khi sửa env.

- `FIREBASE_PROJECT_ID`: cùng project Firebase với web/mobile.
- `GOOGLE_APPLICATION_CREDENTIALS`: đường dẫn tuyệt đối tới service-account JSON lưu riêng trên máy; không đặt file đó trong thư mục đóng gói project.
- `FRONTEND_URL`: web nhận link khôi phục mật khẩu.
- SMTP: `SMTP_HOST`, `SMTP_PORT=587`, `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`. Adapter hiện dùng STARTTLS, không dùng SMTP implicit SSL cổng 465.
- Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`; điện thoại theo E.164. Hạn chế tài khoản trial do nhà cung cấp quyết định.
- Elasticsearch: `ELASTICSEARCH_URL`, tùy chọn `ELASTICSEARCH_USER`/`ELASTICSEARCH_PASSWORD`.
- Redis: `REDIS_URL`; thiếu Redis dùng cache bộ nhớ có giới hạn và TTL.

## Đăng nhập web

Trong Firebase Console, bật các provider Google/Facebook/Phone cần demo. Thêm domain ứng dụng vào Authorized domains. Với Facebook, cấu hình App ID/secret và redirect URL tại nhà cung cấp theo cấu hình Firebase.

Trong `frontend-web/.env.local`, điền các biến `VITE_FIREBASE_*` từ `.env.example`, restart Vite. Các cấu hình web app công khai khác với private key service account. Backend xác minh Firebase ID token, email đã xác thực hoặc danh tính điện thoại, rồi phát phiên JWT của hệ thống; giao diện không tự gán quyền admin/seller.

Kiểm tra từng provider bằng tài khoản thử của bạn. Cấu hình test phone number của Firebase cho buổi demo để tránh phát sinh OTP ngoài ý muốn.

## Flutter

Sao chép `firebase-config.example.json` sang file cấu hình riêng, điền cấu hình app Firebase đúng nền tảng rồi chạy:

```powershell
flutter run -d chrome --web-port=8080 --dart-define-from-file=firebase-config.local.json
```

Thêm `API_BASE_URL` vào file JSON để trỏ API. Android cần applicationId đúng Firebase, SHA-1/SHA-256 cho Google/Phone, file cấu hình nền tảng phù hợp; Google native cần `GOOGLE_WEB_CLIENT_ID`. Facebook native cần cấu hình App ID/client token/scheme theo app tại nhà cung cấp. iOS cần bundle ID, cấu hình URL scheme, quyền push và APNs. Các mục này phụ thuộc tài khoản và chữ ký app của bạn, chưa được thiết lập thay bạn.

Thông báo đẩy Flutter web cần VAPID key và service worker. Có mẫu `web/firebase-messaging-sw.js.example`: chép thành `firebase-messaging-sw.js`, thay giá trị bằng cấu hình web app của bạn, build lại. Service worker phải được phục vụ trên cùng origin HTTPS (localhost dùng phát triển), scope và đăng ký phù hợp Firebase Messaging. `FIREBASE_VAPID_KEY` được đọc từ dart-define. Trình duyệt phải cấp quyền thông báo. Web React hiện có lựa chọn kênh; đăng ký token push được triển khai trong Flutter.

## Worker và gửi thông báo

Chạy tại backend, cùng môi trường Python và env với API:

```powershell
python worker.py --once
python worker.py
```

Worker đồng bộ các thay đổi sang Elasticsearch và tạo bản tổng hợp lũy kế vào đầu mỗi tuần khi worker hoạt động. Không gửi email/SMS/push nếu thiếu cờ sau:

```powershell
python worker.py --once --deliver
```

Chỉ dùng cờ này sau khi cấu hình và chọn người nhận thử của bạn. Hàng đợi lỗi được đánh dấu failed; cần kiểm tra cấu hình trước khi chủ động đưa lại queued qua công cụ quản trị DB. Không có cơ chế tự gửi lại vô hạn. Khôi phục mật khẩu gửi link dùng một lần, hết hạn 15 phút qua email; nếu worker không chạy thì email còn trong hàng đợi.

## Dịch vụ dữ liệu

`docker-compose.yml` có PostgreSQL, Elasticsearch và Redis tùy chọn; cấu hình DATABASE_URL phù hợp trước khi dùng. Tạo bảng được hỗ trợ; chưa có bộ migration đầy đủ để chuyển schema database cũ sang mọi phiên bản production. Sao lưu DB trước thay đổi.

Trên máy hiện tại Elasticsearch 8.17.0 đã chạy và lập chỉ mục thật ở cổng 9200; launcher chỉ bind localhost. Ngưỡng disk headroom 4/2/1GB được đặt cho demo tại ổ C. Elasticsearch phải khởi động xong trước reindex; xem `/api/workspace/search/health`. Thiếu dịch vụ trả lỗi rõ ràng, không giả kết quả Elasticsearch bằng SQL.

Đã kiểm tra các luồng local và hàng đợi. Chưa xác thực đăng nhập nhà cung cấp, gửi SMTP/Twilio/FCM, PostgreSQL/Redis thực tế hoặc build native khi chưa có cấu hình chủ dự án.
