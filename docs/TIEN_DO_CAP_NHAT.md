> Cập nhật phạm vi: luồng người dùng hiện tại là kiểm tra link/ảnh/video, không đặt mua hay quản lý tồn kho. Xem `LUONG_KIEM_TRA_SAN_PHAM.md`. Các phần mua bán trong tài liệu bên dưới mô tả phiên bản nghiệp vụ trước khi người dùng chốt lại ý tưởng.

# Đối chiếu tiến độ sau nâng cấp

Bản ghi ngày 18/10/2026, mô tả công việc thực tế trong phiên; không thay cho báo cáo tuần đã nộp và không xác nhận có nộp báo cáo các tuần trước.

| Nhóm hướng dẫn | Kết quả trong project | Việc còn cần xác minh |
|---|---|---|
| Web/Mobile/API, bốn vai trò | Web nghiệp vụ, API và Flutter dùng chung dữ liệu, phân quyền | Kiểm tra native Android/iOS trên thiết bị; giao diện quản trị đầy đủ chủ yếu ở web |
| SVM/BERT, tham số/đồ thị/so sánh | Hai artifact thật, cùng test, curves/metrics và báo cáo thực nghiệm | Xác minh nguồn dataset; mở rộng tiếng Việt/ngoài miền nếu đề tài yêu cầu |
| XAI | LIME thật, theo phiên bản model | SHAP là hướng mở rộng nếu giảng viên yêu cầu thêm ngoài LIME |
| Hành vi/ngưỡng tuần 9 | Review ngắn, lặp đa sản phẩm, tần suất, blacklist; ngưỡng người dùng đã duyệt | Điều chỉnh quy tắc bằng dữ liệu đã xác minh thực tế |
| Đồ thị/cộng đồng | Đồ thị hai phía và Louvain có bằng chứng, lưu cluster | Đánh giá chất lượng cluster trên nhãn con người |
| Shop/sản phẩm/đơn hàng | CRUD, ảnh URL/tồn kho/trạng thái, mua rồi review, so sánh, trust/time series | Upload file ảnh trực tiếp chưa có; đang dùng URL ảnh |
| Báo cáo/thông báo | Report workflow, moderation audit, phản hồi/vote web, PDF/XLSX, outbox/worker | Cấu hình Firebase/SMTP/Twilio/FCM rồi test tài khoản thật; chưa gửi ra ngoài |
| Model/feedback/A-B | Candidate train, logs, kích hoạt, feedback SVM, phân nhánh người dùng | Thu thập đủ nhãn thật và đo A/B thực địa |
| Search/cache | Elasticsearch thực đã index/query; Redis adapter và cache bộ nhớ | Redis/PostgreSQL thật và tải đồng thời chưa được kiểm chứng |
| UML và báo cáo | Hồ sơ thiết kế Mermaid, đặc tả 12 UC, thực nghiệm, demo/kiểm thử | Tích hợp vào bản Word đúng mẫu khoa, bổ sung các UC chi tiết nếu khoa yêu cầu toàn bộ |

Chưa nhận bản thảo luận văn Word/slides/phiếu khảo sát nên chưa chỉnh được định dạng luận văn, số trang, tài liệu tham khảo, dữ liệu khảo sát hoặc bản trình chiếu bảo vệ. Chủ dự án cần xác minh nội dung học thuật, nguồn trích dẫn và yêu cầu cuối cùng với giảng viên. Các thiếu sót này không được đánh dấu đã hoàn thành chỉ vì mã nguồn đã bổ sung chức năng.
