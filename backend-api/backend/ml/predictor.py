import json
import hashlib
import logging
from pathlib import Path
import joblib
from fastapi import HTTPException
from config import settings

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


def model_path():
    p = Path(settings.model_path)
    return p if p.is_absolute() else ROOT / p


def risk_level(probability):
    return 'high' if probability >= .7 else 'moderate' if probability > .5 else 'low'


class ReviewPredictor:
    def __init__(self, path=None):
        self.path = path
        self.model = None
        self.metadata = {}
        self.error = None
        self.reload()

    @property
    def ready(self):
        return self.model is not None

    def reload(self):
        # Only load artifacts produced locally by the trusted training command.
        path = Path(self.path) if self.path else model_path()
        try:
            candidate = joblib.load(path)
            if not hasattr(candidate, 'predict_proba'):
                raise ValueError('Model must provide calibrated probabilities. Run python -m ml.train.')
            candidate.predict_proba(['test review'])
            metadata_path = path.with_suffix('.json')
            metadata = json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.exists() else {}
            self.model, self.metadata, self.error = candidate, metadata, None
            return True
        except Exception as exc:
            self.error = str(exc)
            log.warning('Model unavailable: %s', exc)
            return False

    def predict(self, content):
        if not self.ready:
            raise HTTPException(503, 'Chưa nạp mô hình đã huấn luyện. Chạy python -m ml.train trước khi phân tích.')
        from services import cache
        key = 'prediction:' + self.metadata.get('version', 'unknown') + ':' + hashlib.sha256(content.encode()).hexdigest()
        cached = cache.get(key)
        if cached:
            return cached
        probs = self.model.predict_proba([content])[0]
        classes = [str(x).lower() for x in self.model.classes_]
        fake_idx = next(i for i, c in enumerate(classes) if c in ('1', 'fake', 'cg'))
        fake = float(probs[fake_idx])
        result = dict(predicted_label='fake' if fake >= .5 else 'real',
                    fake_probability=round(fake, 6), real_probability=round(1-fake, 6),
                    confidence_score=round(max(fake, 1-fake), 6),
                    explanation=f"Mô hình {self.metadata.get('model_name', 'NLP')} phân loại văn bản tiếng Anh OR/CG. Xem LIME để biết đóng góp của từ.",
                    model_name=self.metadata.get('model_name', 'tfidf_svm_calibrated'),
                    model_version=self.metadata.get('version', '2.0.0'))
        cache.put(key, result)
        return result

    def explain(self, content, samples=500):
        if not self.ready:
            raise HTTPException(503, 'Chưa nạp model')
        from lime.lime_text import LimeTextExplainer
        classes = [str(x).lower() for x in self.model.classes_]
        fake_idx = next(i for i, c in enumerate(classes) if c in ('1', 'fake', 'cg'))
        explanation = LimeTextExplainer(class_names=classes, random_state=42).explain_instance(
            content, self.model.predict_proba, labels=(fake_idx,), num_features=10, num_samples=samples)
        return {'method': 'LIME', 'target': 'fake', 'samples': samples,
                'features': [{'token': word, 'weight': float(weight)} for word, weight in explanation.as_list(label=fake_idx)],
                'local_fidelity': float(explanation.score),
                'note': 'Trọng số giải thích cục bộ, không chứng minh review gian lận.',
                'prediction': self.predict(content)}


predictor = ReviewPredictor()

_versions = {}


def version_predictor(filename):
    root = ROOT / 'ml/models'
    path = (root / filename).resolve()
    if path.parent != root.resolve() or path.suffix != '.joblib' or not path.exists():
        raise HTTPException(400, 'Phiên bản mô hình không tồn tại')
    stamp = path.stat().st_mtime_ns
    entry = _versions.get(filename)
    if not entry or entry[0] != stamp:
        candidate = ReviewPredictor(path)
        if not candidate.ready:
            raise HTTPException(503, 'Không nạp được phiên bản mô hình này')
        _versions[filename] = (stamp, candidate)
    return _versions[filename][1]
