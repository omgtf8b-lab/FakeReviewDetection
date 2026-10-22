import os
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# 1. Đường dẫn
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "fake_reviews_product.csv"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================================================
# 2. Đọc dataset
# =========================================================

df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("THÔNG TIN DATASET")
print("=" * 60)

print("\nKích thước dataset:")
print(df.shape)

print("\nCác cột:")
print(df.columns.tolist())

print("\n5 dòng đầu:")
print(df.head())


# =========================================================
# 3. Kiểm tra dữ liệu
# =========================================================

print("\n" + "=" * 60)
print("KIỂM TRA DỮ LIỆU")
print("=" * 60)

print("\nMissing values:")
print(df.isnull().sum())

print("\nSố dòng trùng hoàn toàn:")
print(df.duplicated().sum())

print("\nSố nội dung review bị trùng:")
print(df["text_"].duplicated().sum())


# =========================================================
# 4. Phân bố label
# =========================================================

print("\n" + "=" * 60)
print("PHÂN BỐ LABEL")
print("=" * 60)

print(df["label"].value_counts())

print("\nTỷ lệ (%):")
print(df["label"].value_counts(normalize=True) * 100)


# =========================================================
# 5. Phân bố rating
# =========================================================

print("\n" + "=" * 60)
print("PHÂN BỐ RATING")
print("=" * 60)

print(df["rating"].value_counts().sort_index())


# =========================================================
# 6. Phân bố category
# =========================================================

print("\n" + "=" * 60)
print("PHÂN BỐ CATEGORY")
print("=" * 60)

print(df["category"].value_counts())


# =========================================================
# 7. Biểu đồ label
# =========================================================

label_counts = df["label"].value_counts()

plt.figure(figsize=(6, 4))

plt.bar(label_counts.index, label_counts.values)

plt.title("Distribution of Fake and Original Reviews")
plt.xlabel("Label")
plt.ylabel("Number of Reviews")

plt.tight_layout()

label_path = os.path.join(
    OUTPUT_DIR,
    "label_distribution.png"
)

plt.savefig(label_path, dpi=300)
plt.show()

print("\nĐã lưu:", label_path)


# =========================================================
# 8. Biểu đồ rating
# =========================================================

rating_counts = df["rating"].value_counts().sort_index()

plt.figure(figsize=(7, 4))

plt.bar(
    rating_counts.index.astype(str),
    rating_counts.values
)

plt.title("Distribution of Review Ratings")
plt.xlabel("Rating")
plt.ylabel("Number of Reviews")

plt.tight_layout()

rating_path = os.path.join(
    OUTPUT_DIR,
    "rating_distribution.png"
)

plt.savefig(rating_path, dpi=300)
plt.show()

print("Đã lưu:", rating_path)


# =========================================================
# 9. Biểu đồ category
# =========================================================

category_counts = df["category"].value_counts()

plt.figure(figsize=(10, 6))

plt.barh(
    category_counts.index,
    category_counts.values
)

plt.title("Number of Reviews by Product Category")
plt.xlabel("Number of Reviews")
plt.ylabel("Category")

plt.tight_layout()

category_path = os.path.join(
    OUTPUT_DIR,
    "category_distribution.png"
)

plt.savefig(category_path, dpi=300)
plt.show()

print("Đã lưu:", category_path)


print("\n" + "=" * 60)
print("HOÀN THÀNH PHÂN TÍCH DATASET")
print("=" * 60)