"""Reproducible English OR/CG baseline, train-only CV calibration, untouched test."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import joblib
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score, brier_score_loss
from ml.text import clean_batch, clean_text

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]


def dataset(path):
    df = pd.read_csv(path)
    text_col = 'text' if 'text' in df else 'text_'
    labels = {'OR': 0, 'CG': 1, 'real': 0, 'fake': 1, '0': 0, '1': 1}
    df = df.dropna(subset=[text_col, 'label']).copy()
    df['text'] = df[text_col].astype(str)
    df['target'] = df['label'].astype(str).map(labels)
    if df.target.isna().any():
        raise ValueError('Unsupported labels')
    df['normalized'] = df.text.map(clean_text)
    conflicts = df.groupby('normalized').target.nunique()
    df = df[~df.normalized.isin(conflicts[conflicts > 1].index)]
    return df[df.normalized.str.len() > 0].drop_duplicates('normalized').reset_index(drop=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', default=str(PROJECT / 'data/fake_reviews_product.csv'))
    p.add_argument('--output', default=str(ROOT / 'ml/models/fake_review_model.joblib'))
    p.add_argument('--feedback', default='', help='Optional human-moderated data; never added to the held-out test')
    args = p.parse_args()
    df = dataset(args.data)
    train_idx, test_idx = train_test_split(df.index, test_size=.2, stratify=df.target, random_state=42)
    pipeline = Pipeline([('clean', FunctionTransformer(clean_batch)),
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=30000, min_df=2, max_df=.95, sublinear_tf=True)),
        ('svm', LinearSVC(C=1., random_state=42))])
    model = CalibratedClassifierCV(pipeline, cv=3, method='sigmoid', ensemble=False)
    training_text=df.loc[train_idx,'text'].copy()
    training_labels=df.loc[train_idx,'target'].copy()
    feedback_size=0
    if args.feedback:
        feedback=dataset(args.feedback)
        feedback=feedback[~feedback.normalized.isin(df.normalized)]
        training_text=pd.concat([training_text,feedback.text],ignore_index=True)
        training_labels=pd.concat([training_labels,feedback.target],ignore_index=True)
        feedback_size=len(feedback)
    model.fit(training_text,training_labels)
    actual = df.loc[test_idx, 'target']
    probs = model.predict_proba(df.loc[test_idx, 'text'])[:, list(model.classes_).index(1)]
    pred = (probs >= .5).astype(int)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    meta = dict(model_name='tfidf_svm_calibrated', version=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S'),
        language='en', task='original vs computer generated reviews', sklearn_version=sklearn.__version__,
        data_sha256=hashlib.sha256(Path(args.data).read_bytes()).hexdigest(), random_state=42,
        train_size=len(training_text), feedback_size=feedback_size, test_size=len(test_idx), calibration='sigmoid, 3-fold on training only',
        accuracy=float(accuracy_score(actual, pred)), roc_auc=float(roc_auc_score(actual, probs)),
        brier_score=float(brier_score_loss(actual, probs)),
        classification_report=classification_report(actual, pred, output_dict=True),
        confusion_matrix=confusion_matrix(actual, pred).tolist())
    output.with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    train_set = set(train_idx)
    df.assign(split=['train' if i in train_set else 'test' for i in df.index]).to_csv(output.parent / 'dataset_split.csv', index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    truth, forecast = calibration_curve(actual, probs, n_bins=10)
    plt.plot(forecast, truth, 'o-', label='SVM calibrated'); plt.plot([0,1], [0,1], '--')
    plt.xlabel('Predicted probability'); plt.ylabel('Observed frequency'); plt.legend()
    plt.savefig(output.parent / 'calibration.png', dpi=150); plt.close()
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
