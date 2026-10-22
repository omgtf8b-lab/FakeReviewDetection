# Chuyển database sang PostgreSQL trên máy hiện tại

Thông tin từ pgAdmin: localhost, port 5432, username postgres. Database đích: fake_review_db.

Chưa chuyển dữ liệu cho đến khi bạn nhập mật khẩu trực tiếp trên máy. Không gửi mật khẩu vào chat.

1. Dừng backend đang chạy bằng Ctrl+C trong terminal backend. Dừng các tiến trình khác đang ghi vào cùng SQLite nếu có.
2. Trong CMD chạy:

```cmd
cd /d <LOCAL_WORKSPACE>\outputs
SETUP_POSTGRES.cmd
```

3. Nhập mật khẩu PostgreSQL khi được hỏi. Khi nhập sẽ không thấy ký tự. Công cụ chỉ kết nối máy local; không đọc mật khẩu lưu trong pgAdmin.
4. Chỉ khi xuất hiện `DA CHUYEN ...` mới coi chuyển và cấu hình đã xong. Công cụ sao lưu SQLite bằng SQLite Backup API, tạo schema mới `fake_review_app`, chép bảng theo thứ tự khóa ngoại, kiểm tra số dòng, đặt lại sequence ID và sau cùng cập nhật backend `.env`. Schema cũ/public và SQLite gốc được giữ nguyên. Nếu schema fake_review_app đã tồn tại thì dừng, không xóa hoặc ghi đè.
5. Chạy RUN_LOCAL_API.cmd để mở backend mới. Web/Flutter dùng cùng API nên không phải đổi URL của giao diện.
6. Trong pgAdmin chuột phải fake_review_db > Refresh, mở Schemas > fake_review_app > Tables. Chuột phải collected_reviews > View/Edit Data > All Rows để xem review.

SQL xem dữ liệu trong Query Tool:

```sql
SELECT id, snapshot_id, source_review_id, content, rating
FROM fake_review_app.collected_reviews
ORDER BY id;
```

Bản sao SQLite và báo cáo số dòng nằm trong outputs/db_backups, không chứa trong ZIP bàn giao. Bản .env trước chuyển được giữ ở backend/.env.before-postgres.*, không đưa lên Git hoặc chia sẻ; file đó có thể chứa khóa/mật khẩu.

Nếu cần chuyển lại mà schema đã tồn tại, dùng tên schema mới, ví dụ SETUP_POSTGRES.cmd --schema fake_review_app_v2. Công cụ không gộp vào bảng PostgreSQL hiện có để tránh đụng ID và mất dữ liệu. Nếu bước ghi .env thất bại sau khi database đã commit, schema mới vẫn còn; đọc báo cáo và xử lý cấu hình, không coi đó là đã chuyển backend thành công.

Đổi lại SQLite nếu cần: dừng backend, đặt DATABASE_URL=sqlite:///./fake_review.db trong backend/.env rồi mở lại backend. Dữ liệu mới đã ghi vào PostgreSQL sau chuyển sẽ không tự xuất hiện trong SQLite.

Mật khẩu có ký tự đặc biệt được mã hóa trong URL cấu hình. Không log DATABASE_URL hoặc nội dung .env. Các launcher trên máy này trỏ đến runtime ở work; khi chuyển máy cài requirements.txt và chạy python setup_postgres.py từ backend-api/backend.

Kiểm tra tự động bao gồm xử lý mật khẩu đặc biệt, bảo toàn cấu hình, bản sao SQLite và biên dịch schema SQLAlchemy cho PostgreSQL. Chưa xác minh kết nối/migration PostgreSQL thực tế khi chưa nhập mật khẩu.
