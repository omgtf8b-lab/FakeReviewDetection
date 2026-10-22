from __future__ import annotations
from pathlib import Path
from typing import Any
import joblib
from config import settings


class ReviewPredictor:
    def __init__(self):
        self.model = None
        self._load_model()

    @property
    def ready(self) -> bool:
        return self.model is not None

    def _load_model(self) -> None:
        path = Path(settings.model_path)
        if path.exists():
            try:
                self.model = joblib.load(path)
            except Exception:
                self.model = None

    def reload(self) -> bool:
        self.model = None
        self._load_model()
        return self.ready

    def _fallback(self, content: str) -> dict[str, Any]:
        # Deterministic fallback for local development only.
        # The thesis result should come from a trained model.
        text = content.lower().strip()
        promotional = [
            "quá tuyệt vời", "tuyệt vời", "đỉnh của chóp", "xuất sắc",
            "không thể tin nổi", "rất hài lòng", "siêu tốt", "ủng hộ shop",
            "100 điểm", "mua ngay"
        ]
        signals = sum(1 for p in promotional if p in text)
        repetition = 1 if len(set(text.split())) / max(len(text.split()), 1) < 0.35 else 0
        fake_prob = min(0.45 + 0.12 * signals + 0.12 * repetition, 0.85)
        real_prob = 1 - fake_prob
        label = "fake" if fake_prob >= 0.5 else "real"
        confidence = max(fake_prob, real_prob)
        explanation = "Fallback heuristic: kết quả tạm thời, chưa dùng model đã train."
        if signals:
            explanation += " Phát hiện ngôn ngữ quảng cáo/rập khuôn."
        if repetition:
            explanation += " Mật độ từ lặp cao."
        return {
            "predicted_label": label,
            "fake_probability": round(fake_prob, 4),
            "real_probability": round(real_prob, 4),
            "confidence_score": round(confidence, 4),
            "explanation": explanation,
            "model_name": "fallback-heuristic",
            "model_version": "dev-only",
        }

    def predict(self, content: str) -> dict[str, Any]:
        if not self.ready:
            return self._fallback(content)

        model = self.model
        prediction = model.predict([content])[0]
        label = str(prediction).lower()
        if label in {"1", "fake", "giả", "spam"}:
            label = "fake"
        else:
            label = "real"

        fake_prob = real_prob = None
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba([content])[0]
            classifier = model.named_steps.get("clf") or model.named_steps.get("classifier") if hasattr(model, "named_steps") else model
            classes = [str(c).lower() for c in getattr(classifier, "classes_", range(len(probs)))]
            for cls, prob in zip(classes, probs):
                if cls in {"1", "fake", "giả", "spam"}:
                    fake_prob = float(prob)
                else:
                    real_prob = float(prob)
            fake_prob = 0.5 if fake_prob is None else fake_prob
            real_prob = 1 - fake_prob if real_prob is None else real_prob
        else:
            fake_prob = 1.0 if label == "fake" else 0.0
            real_prob = 1.0 - fake_prob

        explanation = self._explain(model, content, label)
        return {
            "predicted_label": label,
            "fake_probability": round(fake_prob, 4),
            "real_probability": round(real_prob, 4),
            "confidence_score": round(max(fake_prob, real_prob), 4),
            "explanation": explanation,
            "model_name": settings.model_name,
            "model_version": settings.model_version,
        }

    def _explain(self, model: Any, content: str, label: str) -> str:
        # Lightweight XAI for TF-IDF + linear models.
        try:
            if hasattr(model, "named_steps"):
                vectorizer = model.named_steps.get("tfidf") or model.named_steps.get("vectorizer")
                classifier = model.named_steps.get("clf") or model.named_steps.get("classifier")
                if vectorizer is not None and classifier is not None and hasattr(vectorizer, "transform") and hasattr(classifier, "coef_"):
                    x = vectorizer.transform([content])
                    feature_names = vectorizer.get_feature_names_out()
                    coef = classifier.coef_[0]
                    indices = x.nonzero()[1]
                    contributions = []
                    for idx in indices:
                        score = float(x[0, idx]) * float(coef[idx])
                        contributions.append((feature_names[idx], score))
                    contributions.sort(key=lambda item: abs(item[1]), reverse=True)
                    top = [word for word, score in contributions[:5]]
                    if top:
                        return f"Model explanation ({label}): các đặc trưng văn bản nổi bật gồm {', '.join(top)}."
        except Exception:
            pass
        return f"Model prediction: {label}."


predictor = ReviewPredictor()
