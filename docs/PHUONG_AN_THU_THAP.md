# Thu thập dữ liệu: phương án chính và dự phòng

## Phương án đã thống nhất

1. Chính: dán link Shopee, TikTok Shop hoặc Lazada; backend thử Selenium với Chrome để đọc review được hiển thị. Nếu chưa có review, thử nguồn HTTP công khai hiện có. Chỉ phân tích dữ liệu thực sự đọc được.
2. Kiểm thử và dự phòng: người dùng nhập review trực tiếp hoặc nhập file review JSON. Hệ thống lưu và phân tích qua cùng backend, nhưng gắn nhãn nguồn dự phòng rõ ràng. Đây không phải review đã xác minh từ sàn.

Web và Flutter đều có nhập review dự phòng. Web cho tải bộ dữ liệu gốc; cả hai có thể phân tích lại bản lưu có review. Mỗi bộ dữ liệu có thời điểm thu thập và SHA-256; phát lại sử dụng bản lưu, không ngụ ý dữ liệu hiện tại của sàn. Chỉ chủ dữ liệu được đọc/phát lại. Admin xem thống kê riêng theo nguồn và chế độ.

## Cài trên máy mới

Cài Google Chrome, rồi tại backend-api/backend chạy:

```powershell
python -m pip install -r requirements-browser.txt -c constraints-tested.txt -c constraints-browser-tested.txt
```

Chức năng ảnh/video còn cần requirements-media.txt và constraints-media-tested.txt. Selenium Manager tải driver phù hợp Chrome khi cần; lần đầu cần mạng. Có thể cấu hình BROWSER_BINARY và BROWSER_DRIVER_PATH bằng đường dẫn tuyệt đối tới Chrome/driver. BROWSER_TEMP_DIR và SE_CACHE_PATH phải là thư mục server ghi được. BROWSER_SCRAPING_ENABLED=false tắt trình duyệt; khi đó chế độ tự động vẫn thử HTTP.

Khởi động lại backend sau khi cập nhật. RUN_LOCAL_API.cmd trong outputs đã trỏ đến các dependency và cache trên máy phát triển hiện tại; máy khác dùng hướng dẫn cài chuẩn trong README_UPGRADE.md.

## Phạm vi và kết quả kiểm tra ngày 19/10/2026

- Backend: 41 kiểm thử đạt, gồm chiến lược thu thập, chặn đích mạng nội bộ, nguồn review tự nhập, phân quyền bản lưu, phát hiện sửa dữ liệu, và phát lại không thu thập lần hai.
- Flutter: 24 kiểm thử đạt; phân tích tĩnh không phát hiện lỗi; build web release thành công. Frontend React build thành công.
- Selenium và ChromeDriver 155.0.8059.84 khớp Chrome trên máy này. Tuy nhiên lần chạy thực tế với ba link được cung cấp gặp lỗi Chrome khởi động; lần thử tiếp theo hết thời gian chờ. Do đó CHƯA xác nhận cào review thật thành công bằng Selenium từ ba sàn. File KET_QUA_SELENIUM_3_LINK.json lưu các lần thử ban đầu; không được diễn giải lỗi trình duyệt thành bằng chứng sàn chặn.
- Kiểm thử đơn vị không thay thế kiểm thử thu thập thật. Cần chạy lại trên môi trường Chrome hoạt động và cập nhật selector theo giao diện sàn nếu cần.

Trình duyệt dùng hồ sơ tạm riêng, không dùng phiên đăng nhập của khách hàng, không giải CAPTCHA hay vượt xác minh. Giới hạn tối đa 3 trang review và 200 review mỗi yêu cầu; mặc định 50. Có giới hạn thời gian và mạng. Không đảm bảo đọc hết mọi link hoặc mọi review; nếu không đọc được phải hiển thị thiếu dữ liệu và đề nghị nhập dữ liệu dự phòng.

## Diễn giải khoa học

Dữ liệu cào không tự có nhãn thật/giả. Review tự nhập dùng kiểm thử luồng, không tự chứng minh độ chính xác mô hình. Tỷ lệ báo cáo là tỷ lệ dấu hiệu đáng nghi trên mẫu phân tích; không phải xác suất sản phẩm giả hay tài khoản là bot. Tiếng Việt hiện chủ yếu sàng lọc quy tắc; mô hình tiếng Anh và bộ dữ liệu huấn luyện có giới hạn miền áp dụng. Ảnh/video chỉ kiểm tra dấu hiệu kỹ thuật hiện có, chưa xác minh hàng chính hãng hoặc deepfake.
