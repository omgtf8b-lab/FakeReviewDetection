# Báo cáo thực nghiệm từ artifact đã huấn luyện

## Dữ liệu và quy trình

Nguồn đầu vào là `data/fake_reviews_product.csv` có sẵn trong ZIP. Nhãn OR được ánh xạ thành 0/real, CG thành 1/fake. Bài toán là phân biệt văn bản đánh giá gốc với văn bản được sinh bằng máy tính trong bộ dữ liệu tiếng Anh. Tên nhãn fake trong giao diện không chứng minh gian lận thương mại ngoài thực tế.

Quy trình chuẩn hóa xóa HTML/URL, viết thường và lọc ký tự theo pipeline tiếng Anh. Loại văn bản rỗng, nhóm chuẩn hóa có nhãn xung đột và bản trùng trước chia tập. Còn 40.387 mẫu; chia stratified 80/20, seed 42: 32.309 train và 8.078 test. Tập test có 4.043 OR và 4.035 CG. `dataset_split.csv` lưu phân chia dùng chung. SHA256 dữ liệu đầu vào: `ea03422988824bc917b5f7217e3867e27b597c647d5261adfae73cd7a85e1e1a`.

Chưa có hồ sơ nguồn gốc/giấy phép của bộ dữ liệu ngoài các file người dùng gửi; cần xác minh tác giả, URL nguồn và điều kiện sử dụng để trích dẫn chính xác trong luận văn. Không tự tạo thông tin nguồn hoặc kết quả khảo sát.

## Cấu hình

| Thành phần | SVM | DistilBERT |
|---|---|---|
| Biểu diễn | TF-IDF unigram + bigram | distilbert/distilbert-base-uncased |
| Giới hạn | 30.000 features; min_df=2; max_df=0,95; sublinear_tf | max_length=128 |
| Bộ phân loại | LinearSVC C=1 | đầu phân loại hai lớp |
| Huấn luyện | seed 42 | seed 42, batch 8, 3 epoch |
| Tối ưu | SVM + sigmoid calibration CV 3-fold chỉ trên train | AdamW, lr 2e-5, weight_decay 0,01 |
| Hàm mất mát | hinge của LinearSVC | CrossEntropyLoss |
| Chọn model | calibration không dùng test | validation loss nhỏ nhất (epoch 2) |

DistilBERT tách 3.231 validation từ phần train ban đầu; train thực tế 29.078 mẫu. GPU RTX 3050 4GB, gradient checkpointing; thời gian được ghi trong metadata 2.108,265 giây. Revision checkpoint gốc: `12040accade4e8a0f71eabdb258fecc2e7e948be`. Chọn checkpoint bằng validation, sau đó đánh giá một lần trên test giữ lại.

## Kết quả cùng tập test

| Chỉ số | SVM calibrated | DistilBERT fine-tuned |
|---|---:|---:|
| Accuracy | 94,8502% | 97,9946% |
| Macro F1 | 0,948501 | 0,979944 |
| ROC AUC | 0,988600 | 0,997396 |
| Precision CG | 0,952488 | 0,970367 |
| Recall CG | 0,943990 | 0,990087 |
| Brier score | 0,038666 | Chưa đo |
| Version | 20261018103459 | 1792322524 |

Chênh lệch accuracy là khoảng 3,1443 điểm phần trăm. Một lần chia tập không đủ để kết luận độ ổn định giữa nhiều lần chạy hay khả năng tổng quát hóa sang dữ liệu khác.

Confusion matrix: hàng là nhãn thật, cột là dự đoán; thứ tự OR, CG.

| Model | OR → OR | OR → CG | CG → OR | CG → CG |
|---|---:|---:|---:|---:|
| SVM | 3853 | 190 | 226 | 3809 |
| DistilBERT | 3921 | 122 | 40 | 3995 |

| Epoch | Train loss | Train accuracy | Validation loss | Validation accuracy |
|---|---:|---:|---:|---:|
| 1 | 0,156249 | 95,3951% | 0,179927 | 95,3884% |
| 2 | 0,061972 | 98,5247% | 0,105137 | 97,7097% |
| 3 | 0,035121 | 99,2537% | 0,132973 | 97,8025% |

Epoch 3 tăng validation accuracy nhẹ nhưng validation loss cao hơn epoch 2; checkpoint được chọn theo quy tắc validation loss đã định.

![Loss và Accuracy](../backend-api/backend/ml/models/distilbert_curves.png)

![Hiệu chỉnh xác suất SVM](../backend-api/backend/ml/models/calibration.png)

## Tái lập

Trong `backend-api/backend`, dùng môi trường đã cài dependency phù hợp:

```powershell
python -m ml.train
python -m ml.train_bert --epochs 3 --batch-size 8 --learning-rate 2e-5
```

Lệnh train sẽ ghi đè artifact mặc định; muốn giữ bản đã kiểm thử hãy chỉ định `--output ml/models/ten_phien_ban.joblib`. Chạy `--help` để xem tham số. Không dùng `--limit` cho số liệu báo cáo đầy đủ. Dùng giao diện Model để train candidate và chỉ kích hoạt sau đánh giá; A/B chỉ tính đồng thuận kiểm duyệt khi đã có nhãn con người, không coi dự đoán của model là ground truth.

## Diễn giải và giới hạn

LIME lấy nhiễu văn bản và gọi model thực để ước lượng đóng góp từ; dấu dương tăng P(fake), dấu âm giảm P(fake). Đây là giải thích cục bộ, phụ thuộc văn bản và model. LIME không thay thế bằng chứng hành vi. SHAP chưa được triển khai riêng.

P(fake), độ tin cậy nhãn, tỷ lệ review hành vi bất thường của tài khoản và độ uy tín shop là các đại lượng khác nhau. Ngưỡng tài khoản đã được người dùng chấp thuận: ≤50% bình thường; >50% và <70% nghi vấn; ≥70% đáng ngờ. Không tự khóa tài khoản từ AI hoặc cộng đồng đồ thị.

Chưa đánh giá tiếng Việt, đánh giá ngoài miền, biến thể mô hình sinh mới, near-duplicate theo ngữ nghĩa hay tách tập theo người viết/sản phẩm. Chuẩn hóa hiện tại dành cho tiếng Anh nên không dùng điểm số này để tuyên bố độ chính xác tiếng Việt. Chưa đo calibration DistilBERT, độ trễ tải đồng thời hoặc so sánh công bằng tài nguyên. Khi viết kết luận cần nêu rõ các giới hạn này.
