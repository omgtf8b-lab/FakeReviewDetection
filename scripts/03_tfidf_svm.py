import os
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)


# =========================================================
# 1. Đường dẫn
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "fake_reviews_clean.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

MODEL_DIR = os.path.join(
    OUTPUT_DIR,
    "models"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# =========================================================
# 2. Đọc dữ liệu đã tiền xử lý
# =========================================================

df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("TF-IDF + SVM BASELINE")
print("=" * 60)

print("\nKích thước dataset:")
print(df.shape)

print("\nPhân bố target:")
print(df["target"].value_counts())


# =========================================================
# 3. Chuẩn bị X và y
# =========================================================

X = df["clean_text"]
y = df["target"]


# =========================================================
# 4. Chia Train / Test
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTrain size:", len(X_train))
print("Test size:", len(X_test))

print("\nTrain label distribution:")
print(y_train.value_counts())

print("\nTest label distribution:")
print(y_test.value_counts())


# =========================================================
# 5. Tạo pipeline TF-IDF + Linear SVM
# =========================================================

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=30000,
            min_df=2,
            max_df=0.95,
            sublinear_tf=True
        )
    ),

    (
        "svm",
        LinearSVC(
            C=1.0
        )
    )
])


# =========================================================
# 6. Huấn luyện
# =========================================================

print("\nĐang huấn luyện TF-IDF + SVM...")

model.fit(X_train, y_train)

print("Train SVM hoàn tất!")


# =========================================================
# 7. Dự đoán
# =========================================================

y_pred = model.predict(X_test)


# =========================================================
# 8. Đánh giá
# =========================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n" + "=" * 60)
print("KẾT QUẢ ĐÁNH GIÁ")
print("=" * 60)

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Accuracy (%): {accuracy * 100:.2f}%")

print("\nClassification Report:")

report = classification_report(
    y_test,
    y_pred,
    target_names=[
        "Original (OR)",
        "Computer Generated (CG)"
    ],
    digits=4
)

print(report)


# =========================================================
# 9. Confusion Matrix
# =========================================================

cm = confusion_matrix(
    y_test,
    y_pred
)

print("\nConfusion Matrix:")
print(cm)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=[
        "Original",
        "Computer Generated"
    ]
)

disp.plot()

plt.title(
    "Confusion Matrix - TF-IDF + Linear SVM"
)

plt.tight_layout()

CONFUSION_PATH = os.path.join(
    OUTPUT_DIR,
    "svm_confusion_matrix.png"
)

plt.savefig(
    CONFUSION_PATH,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("\nĐã lưu Confusion Matrix:")
print(CONFUSION_PATH)


# =========================================================
# 10. Lưu classification report
# =========================================================

REPORT_PATH = os.path.join(
    OUTPUT_DIR,
    "svm_classification_report.txt"
)

with open(
    REPORT_PATH,
    "w",
    encoding="utf-8"
) as f:

    f.write("TF-IDF + Linear SVM\n")
    f.write("=" * 50 + "\n\n")

    f.write(
        f"Accuracy: {accuracy:.4f}\n"
    )

    f.write(
        f"Accuracy (%): {accuracy * 100:.2f}%\n\n"
    )

    f.write("Classification Report:\n")
    f.write(report)

    f.write("\nConfusion Matrix:\n")
    f.write(str(cm))


print("\nĐã lưu Classification Report:")
print(REPORT_PATH)


# =========================================================
# 11. Lưu model
# =========================================================

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "tfidf_svm_model.joblib"
)

joblib.dump(
    model,
    MODEL_PATH
)

print("\nĐã lưu model:")
print(MODEL_PATH)


# =========================================================
# 12. Lưu tập test để dùng cho LIME
# =========================================================

test_data = pd.DataFrame({
    "text": X_test,
    "target": y_test
})

TEST_PATH = os.path.join(
    OUTPUT_DIR,
    "test_data.csv"
)

test_data.to_csv(
    TEST_PATH,
    index=False,
    encoding="utf-8"
)

print("\nĐã lưu tập test:")
print(TEST_PATH)


print("\n" + "=" * 60)
print("HOÀN THÀNH TF-IDF + SVM")
print("=" * 60)