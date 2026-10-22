"""Lazy scikit-learn-like adapter for locally fine-tuned Transformers checkpoints."""
class BertAdapter:
    classes_ = [0, 1]

    def __init__(self, checkpoint):
        self.checkpoint = str(checkpoint)
        self._model = None
        self._tokenizer = None

    def predict_proba(self, texts):
        import torch
        import numpy as np
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from pathlib import Path
        path = Path(self.checkpoint)
        if not path.exists():
            path = Path(__file__).resolve().parent / 'models' / path.name
        if self._model is None:
            self._tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
            self._model = AutoModelForSequenceClassification.from_pretrained(path, local_files_only=True).eval()
        results = []
        with torch.inference_mode():
            for i in range(0,len(texts),16):
                batch=self._tokenizer(list(texts[i:i+16]),padding=True,truncation=True,max_length=128,return_tensors='pt')
                results.extend(torch.softmax(self._model(**batch).logits,dim=-1).cpu().numpy())
        return np.array(results)

    def predict(self, texts):
        return self.predict_proba(texts).argmax(axis=1)
