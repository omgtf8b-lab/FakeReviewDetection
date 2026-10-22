# Thu thập review từ trình duyệt của người dùng

Đây là cách thu thập có thao tác người dùng: đọc review đã tải trên trang, không gọi API riêng của sàn và không cần chép cookie/mật khẩu. Không đảm bảo đọc mọi sản phẩm. Chỉ cài trên máy bạn kiểm soát.

1. Giải nén browser-reader.zip tải từ web. Hoặc dùng thư mục browser-reader có sẵn trong project.
2. Mở Chrome, nhập chrome://extensions, bật Developer mode (Chế độ dành cho nhà phát triển), chọn Load unpacked (Tải tiện ích đã giải nén), chọn thư mục browser-reader chứa manifest.json.
3. Mở link sản phẩm Shopee/Lazada/TikTok Shop trong Chrome. Bạn tự đăng nhập hoặc thực hiện xác minh nếu trang yêu cầu. Tiện ích không đăng nhập thay bạn.
4. Mở phần Đánh giá, cuộn để các bình luận tải xong. Bấm tiện ích Fake Review Reader → Đọc bình luận trên tab này.
5. Nếu muốn thêm mẫu, chuyển trang review/cuộn để tải thêm, rồi bấm đọc lần nữa. Tiện ích gộp tối đa 200 review của cùng URL sản phẩm. Các review không có ID nguồn được gộp theo dấu vân tay nội dung/ngày/tác giả; có thể gộp nhầm các review giống hệt nhau, cần lưu ý khi diễn giải.
6. Bấm Tải dữ liệu để phân tích. Về web Fake Review Detection → Thu thập từ Chrome → Nhập bản thu thập từ Chrome → chọn file vừa tải. Link được lấy từ file, không phải dán lại.
7. Xem số review, bằng chứng và tỷ lệ trên mẫu. Server ghi rõ đây là bản thu thập do người dùng cung cấp, chưa xác minh độc lập. Thời gian do tiện ích khai báo khác với thời gian server lưu dữ liệu.

Nếu không tìm thấy review: kiểm tra có đang ở trang chi tiết sản phẩm và review đã tải chưa. Sàn có thể đổi cấu trúc hoặc hiển thị review trong vùng tiện ích chưa hỗ trợ. Khi đó không có kết quả thu thập; dùng nhập nội dung review trực tiếp. Không tạo review mẫu thay cho review thật.

Tiện ích chỉ yêu cầu activeTab, scripting, storage. Nó đọc DOM khi bấm nút, không đọc cookie/password, không chạy nền liên tục, không gửi dữ liệu qua mạng. Một bộ dữ liệu gần nhất được lưu cục bộ trong tiện ích đến khi bạn bấm Xóa bản thu thập hoặc gỡ tiện ích. File xuất chứa review và URL media công khai có thể chứa thông tin người đăng; chỉ sử dụng dữ liệu bạn có quyền sử dụng.

Mẫu DOM của ba sàn và dữ liệu JSON-LD được kiểm thử bằng fixture tổng hợp. Chưa kiểm chứng việc cài và thu thập thật trên Chrome của người dùng trong môi trường này. Selenium phía server vẫn có lỗi khởi động Chrome (Crashpad), nên không hứa dán link là luôn lấy được review.
