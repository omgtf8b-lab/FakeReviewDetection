# Local model artifacts

The upgraded API defaults to `backend-api/backend/ml/models/fake_review_model.joblib` (calibrated TF-IDF + SVM). Provision a trusted artifact and matching `.json` metadata here, or run `python -m ml.train --data PATH_TO_AUTHORIZED_DATA.csv`. Training output uses backend-relative paths.

Model binaries, checkpoints and raw datasets are not synchronized in this branch. ARTIFACTS.json records hashes and sizes of the runtime artifacts without their contents. Missing artifacts produce HTTP 503 for model prediction; this is intentional, not a heuristic replacement. URL collection/storage can still run without an NLP artifact.

Optional DistilBERT: install requirements-ai.txt, provision a local checkpoint and adapter, and configure MODEL_PATH. The adapter resolves a local checkpoint folder beside this file if the training-machine absolute path is unavailable. Do not unpickle artifacts from untrusted sources.

Current English OR/CG models do not validate Vietnamese spam detection or product authenticity. The collector's Vietnamese evidence currently consists of rule-based signals; future Vietnamese/teencode/emoji models require separate validation.
