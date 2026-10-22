import os
import re
import pandas as pd


# =========================================================
# 1. Đường dẫn
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "fake_reviews_product.csv"
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

os.makedirs(PROCESSED_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(
    PROCESSED_DIR,
    "fake_reviews_clean.csv"
)


# =========================================================
# 2. Đọc dataset
# =========================================================

df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("TEXT PREPROCESSING")
print("=" * 60)

print("\nKích thước ban đầu:")
print(df.shape)


# =========================================================
# 3. Kiểm tra và loại dữ liệu không hợp lệ
# =========================================================

# Xóa dòng có text bị thiếu
df = df.dropna(subset=["text_"]).copy()

# Xóa khoảng trắng đầu/cuối
df["text_"] = df["text_"].astype(str).str.strip()

# Loại text rỗng
df = df[df["text_"] != ""].copy()

print("\nSau khi loại text thiếu/rỗng:")
print(df.shape)


# =========================================================
# 4. Xóa review trùng
# =========================================================

duplicate_text = df["text_"].duplicated().sum()

print("\nSố review text bị trùng:")
print(duplicate_text)

df = df.drop_duplicates(
    subset=["text_"],
    keep="first"
).copy()

df = df.reset_index(drop=True)

print("\nSau khi xóa review trùng:")
print(df.shape)


# =========================================================
# 5. Chuẩn hóa label
# =========================================================

# CG = Computer Generated = Fake
# OR = Original Review = Real

label_mapping = {
    "OR": 0,
    "CG": 1
}

df["target"] = df["label"].map(label_mapping)

print("\nPhân bố target:")
print(df["target"].value_counts())

print("\nQuy ước:")
print("OR (Original Review)     = 0")
print("CG (Computer Generated) = 1")


# =========================================================
# 6. Hàm tiền xử lý văn bản
# =========================================================

def clean_text(text):
    # Chuyển sang chữ thường
    text = text.lower()

    # Xóa URL
    text = re.sub(
        r"http\S+|www\S+",
        " ",
        text
    )

    # Xóa HTML tag
    text = re.sub(
        r"<.*?>",
        " ",
        text
    )

    # Giữ chữ cái và dấu nháy đơn
    # Ví dụ: don't, wasn't, didn't
    text = re.sub(
        r"[^a-zA-Z'\s]",
        " ",
        text
    )

    # Xóa khoảng trắng dư thừa
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =========================================================
# 7. Tạo clean_text
# =========================================================

df["clean_text"] = df["text_"].apply(clean_text)


# Loại trường hợp clean_text trở thành rỗng
df = df[df["clean_text"].str.len() > 0].copy()

df = df.reset_index(drop=True)


# =========================================================
# 8. Xem ví dụ trước và sau
# =========================================================

print("\n" + "=" * 60)
print("VÍ DỤ TRƯỚC VÀ SAU TIỀN XỬ LÝ")
print("=" * 60)

for i in range(3):
    print(f"\nReview {i + 1}")

    print("\nOriginal:")
    print(df.loc[i, "text_"])

    print("\nClean:")
    print(df.loc[i, "clean_text"])

    print("-" * 60)


# =========================================================
# 9. Kiểm tra kết quả
# =========================================================

print("\nKích thước cuối cùng:")
print(df.shape)

print("\nCác cột:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())

print("\nPhân bố label:")
print(df["label"].value_counts())

print("\nPhân bố target:")
print(df["target"].value_counts())


# =========================================================
# 10. Lưu dataset đã xử lý
# =========================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8"
)

print("\n" + "=" * 60)
print("HOÀN THÀNH TIỀN XỬ LÝ")
print("=" * 60)

print("\nĐã lưu dataset sạch tại:")
print(OUTPUT_PATH)