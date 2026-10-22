import os
import numpy as np
import pandas as pd
import joblib

from lime.lime_text import LimeTextExplainer


# =========================================================
# 1. Đường dẫn
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "outputs",
    "models",
    "tfidf_svm_model.joblib"
)

TEST_PATH = os.path.join(
    BASE_DIR,
    "outputs",
    "test_data.csv"
)

LIME_DIR = os.path.join(
    BASE_DIR,
    "outputs",
    "lime"
)

os.makedirs(LIME_DIR, exist_ok=True)


# =========================================================
# 2. Load model và test data
# =========================================================

print("=" * 60)
print("LIME EXPLANATION DEMO")
print("=" * 60)

model = joblib.load(MODEL_PATH)

test_df = pd.read_csv(TEST_PATH)

print("\nĐã load model thành công.")
print("Test data:", test_df.shape)


# =========================================================
# 3. Class names
# =========================================================

# 0 = Original Review
# 1 = Computer Generated

class_names = [
    "Original (OR)",
    "Computer Generated (CG)"
]


# =========================================================
# 4. Hàm probability cho LIME
# =========================================================
# LinearSVC không có predict_proba(),
# nên chuyển decision score sang khoảng 0-1 bằng sigmoid.
#
# Đây là probability-like score dùng để giải thích,
# KHÔNG phải calibrated probability.
# =========================================================

def predict_proba_for_lime(texts):

    scores = model.decision_function(texts)

    prob_cg = 1 / (1 + np.exp(-scores))

    prob_or = 1 - prob_cg

    probabilities = np.column_stack(
        (
            prob_or,
            prob_cg
        )
    )

    return probabilities


# =========================================================
# 5. Dự đoán tập test
# =========================================================

test_df["prediction"] = model.predict(
    test_df["text"]
)

test_df["correct"] = (
    test_df["prediction"]
    ==
    test_df["target"]
)


# =========================================================
# 6. Chọn 1 OR và 1 CG dự đoán đúng
# =========================================================

sample_or = test_df[
    (test_df["target"] == 0)
    &
    (test_df["correct"] == True)
].iloc[0]

sample_cg = test_df[
    (test_df["target"] == 1)
    &
    (test_df["correct"] == True)
].iloc[0]


# =========================================================
# 7. Khởi tạo LIME
# =========================================================

explainer = LimeTextExplainer(
    class_names=class_names,
    random_state=42
)


# =========================================================
# 8. Hàm giải thích một review
# =========================================================

def explain_review(
    sample,
    sample_name
):

    text = sample["text"]

    true_label = int(
        sample["target"]
    )

    predicted_label = int(
        sample["prediction"]
    )

    print("\n" + "=" * 60)
    print(sample_name)
    print("=" * 60)

    print("\nReview:")
    print(text)

    print(
        "\nNhãn thật:",
        class_names[true_label]
    )

    print(
        "SVM dự đoán:",
        class_names[predicted_label]
    )

    # -----------------------------------------
    # Tạo LIME explanation
    # -----------------------------------------

    explanation = explainer.explain_instance(
        text,
        classifier_fn=predict_proba_for_lime,
        labels=[predicted_label],
        num_features=10,
        num_samples=1000
    )

    print(
        "\nTop 10 từ/cụm từ ảnh hưởng:"
    )

    explanation_list = explanation.as_list(
        label=predicted_label
    )

    for word, weight in explanation_list:

        print(
            f"{word:25s} {weight:+.4f}"
        )

    # -----------------------------------------
    # Lưu HTML
    # -----------------------------------------

    html_path = os.path.join(
        LIME_DIR,
        f"{sample_name}.html"
    )

    explanation.save_to_file(
        html_path
    )

    print(
        "\nĐã lưu LIME HTML:"
    )

    print(html_path)

    # -----------------------------------------
    # Lưu feature weights CSV
    # -----------------------------------------

    result_df = pd.DataFrame(
        explanation_list,
        columns=[
            "feature",
            "weight"
        ]
    )

    result_df["true_label"] = (
        class_names[true_label]
    )

    result_df["predicted_label"] = (
        class_names[predicted_label]
    )

    csv_path = os.path.join(
        LIME_DIR,
        f"{sample_name}_weights.csv"
    )

    result_df.to_csv(
        csv_path,
        index=False,
        encoding="utf-8"
    )

    print(
        "Đã lưu feature weights:"
    )

    print(csv_path)


# =========================================================
# 9. Giải thích OR
# =========================================================

explain_review(
    sample_or,
    "lime_original_review"
)


# =========================================================
# 10. Giải thích CG
# =========================================================

explain_review(
    sample_cg,
    "lime_computer_generated_review"
)


print("\n" + "=" * 60)
print("HOÀN THÀNH LIME DEMO")
print("=" * 60)