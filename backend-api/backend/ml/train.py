"""Train and evaluate a TF-IDF + Logistic Regression baseline.

Expected CSV columns:
    text,label
Labels accepted: fake/real or 1/0.

Example:
    python -m ml.train --data data/reviews.csv --output ml/models/fake_review_model.joblib
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def normalize_label(value):
    s = str(value).strip().lower()
    if s in {"1", "fake", "giả", "spam"}:
        return "fake"
    if s in {"0", "real", "thật", "genuine"}:
        return "real"
    raise ValueError(f"Nhãn không hợp lệ: {value}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="ml/models/fake_review_model.joblib")
    parser.add_argument("--metrics", default="ml/models/metrics.json")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    missing = {"text", "label"} - set(df.columns)
    if missing:
        raise ValueError(f"Thiếu cột: {sorted(missing)}")
    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df["label"] = df["label"].map(normalize_label)
    if df["label"].nunique() < 2:
        raise ValueError("Dataset phải có cả hai lớp fake và real.")

    x_train, x_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=args.test_size, random_state=args.random_state, stratify=df["label"]
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "classification_report": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "random_state": args.random_state,
    }
    if hasattr(pipeline, "predict_proba"):
        classes = list(pipeline.named_steps["clf"].classes_)
        probs = pipeline.predict_proba(x_test)[:, classes.index("fake")]
        try:
            metrics["roc_auc"] = round(float(roc_auc_score((y_test == "fake").astype(int), probs)), 4)
        except ValueError:
            metrics["roc_auc"] = None

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output)

    metrics_path = Path(args.metrics)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved model to {output}")
    print(f"Saved metrics to {metrics_path}")
    print(json.dumps({k: v for k, v in metrics.items() if isinstance(v, (int, float, str))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
