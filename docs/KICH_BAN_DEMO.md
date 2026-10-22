> Cập nhật phạm vi: luồng người dùng hiện tại là kiểm tra link/ảnh/video, không đặt mua hay quản lý tồn kho. Xem `LUONG_KIEM_TRA_SAN_PHAM.md`. Các phần mua bán trong tài liệu bên dưới mô tả phiên bản nghiệp vụ trước khi người dùng chốt lại ý tưởng.

# Kịch bản demo với giảng viên

## Chuẩn bị

Mở API, web và tùy chọn Elasticsearch/Flutter theo README. Dùng database demo. Ghi rõ dữ liệu shop và tài khoản là tổng hợp; không trình bày nó như kết quả khảo sát hoặc hành vi gian lận đã được xác nhận.

## Người mua

1. Đăng nhập buyer@example.com; mở sản phẩm và đánh giá.
2. Trong Hoạt động/Đơn hàng, đặt mua một sản phẩm.
3. Đăng nhập seller ở phiên khác, hoàn tất đơn; trở lại buyer để viết review sau mua.
4. Thử review ngắn một ký tự để thấy hệ thống chấp nhận văn bản và phát hiện hành vi, không chặn chỉ vì dưới 10 ký tự.
5. Phân tích một đoạn tiếng Anh trong tab Phân tích & lịch sử, so sánh P(fake) với độ tin cậy nhãn; mở LIME, đọc từ tăng/giảm điểm.
6. Mở review đã lưu, bình chọn hữu ích và gửi báo cáo; xem trạng thái trong Báo cáo review.

## Người bán

1. Đăng nhập seller@example.com; chỉnh hồ sơ shop, sản phẩm, ảnh URL, giá, tồn kho, trạng thái bán và mã nhóm sản phẩm.
2. Hoàn tất đơn, kiểm tra tồn kho giảm một lần; không xóa sản phẩm đã có đơn, chuyển trạng thái ngừng bán khi cần.
3. Xem Độ uy tín shop, số lượng mẫu, biểu đồ, sao sau lọc và gợi ý.
4. Xem/viết phản hồi review trên web. Xuất PDF/XLSX shop/review/danh mục; chỉ thấy dữ liệu thuộc shop.

## Quản trị và kỹ sư

1. Đăng nhập admin@example.com; mở báo cáo, chuyển investigating rồi resolved/rejected và ghi lý do.
2. Gắn nhãn kiểm duyệt cho review; xem nhãn hiệu lực thay đổi nhưng dự đoán AI vẫn giữ trong lịch sử.
3. Hành vi & mạng lưới: xem demo_account_a/b, tỷ lệ 100%, bằng chứng lặp nhiều sản phẩm. Quét đồ thị để xem cộng đồng phối hợp; kết quả là tín hiệu cần xác minh, không tự khóa tài khoản.
4. Kiểm tra ranh giới ngưỡng 50% và 70% trong cấu hình; P(fake) của một review không được dùng làm tỷ lệ tài khoản.
5. Model: xem metadata SVM/DistilBERT, chỉ số trên cùng 8.078 test và đường loss/accuracy. Kích hoạt model có sẵn nếu đã cài AI dependencies. Huấn luyện là tác vụ thật, có thể tốn thời gian, không cần chạy lại trong buổi bảo vệ.
6. Cấu hình A/B theo người dùng; xem mẫu được phân nhánh và độ trễ. Chỉ có chỉ số đồng thuận khi con người đã gắn nhãn; không gọi đó là accuracy thực địa khi chưa đủ ground truth.
7. Tìm kiếm nâng cao: xem health, đồng bộ chỉ mục rồi tìm `cable`. Dừng Elasticsearch để minh họa thông báo lỗi dịch vụ.
8. Xuất báo cáo cụm và mô hình. Xem thông báo nội bộ. Chỉ demo gửi ngoài khi tài khoản dịch vụ do bạn cấu hình đã được kiểm tra.

## Flutter

Mở http://127.0.0.1:8080 sau launcher; dùng cùng tài khoản và dữ liệu. Kiểm tra tìm kiếm, sản phẩm, phân tích review, báo cáo và tab Hoạt động (shop, đơn hàng, hồ sơ, thông báo). Bản đã build/kiểm thử là Flutter web; trình bày riêng nếu chưa chạy APK trên điện thoại.

## Điểm cần giải thích khi bảo vệ

- NLP nhận diện OR/CG tiếng Anh; hành vi tài khoản là lớp phân tích riêng.
- Manual moderation là nhãn hiệu lực nghiệp vụ, không xóa lịch sử AI.
- Trust shop được tính trên review đã phân loại; thiếu mẫu trả chưa có số liệu.
- Đồ thị và LIME hỗ trợ điều tra, không kết luận tuyệt đối.
- Không đưa số liệu demo tổng hợp vào phần thực nghiệm mô hình hoặc khảo sát thực tế.
