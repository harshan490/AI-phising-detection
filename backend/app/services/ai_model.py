"""Loads the trained phishing text classifier (see ml/train.py). No training at runtime."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
MODEL_PATH = MODEL_DIR / "text_clf.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
MAX_CHARS = 4000  # same truncation as training


class PhishingTextModel:
    def __init__(self, path: Path = MODEL_PATH):
        if not path.exists():
            raise RuntimeError(f"Model file {path} not found. Run `python ml/train.py` first.")
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.explainer = bundle["explainer"]
        self.version = bundle.get("version", "unknown")
        features = self.explainer.named_steps["features"]
        self._features = features
        self._names = np.array([n.split("__", 1)[-1] for n in features.get_feature_names_out()])
        self._coef = self.explainer.named_steps["clf"].coef_[0]
        logger.info("Loaded text model version %s", self.version)

    def predict_proba(self, text: str) -> float:
        """Probability (0-1) that the text is phishing."""
        if not text or not text.strip():
            return 0.0
        return float(self.model.predict_proba([text[:MAX_CHARS]])[0, 1])

    def top_terms(self, text: str, k: int = 8) -> List[Dict[str, Any]]:
        """Top n-grams by |TF-IDF weight x LR coefficient|. Positive = pushes towards phishing."""
        if not text or not text.strip():
            return []
        row = self._features.transform([text[:MAX_CHARS]]).tocoo()
        contrib = row.data * self._coef[row.col]
        order = np.argsort(-np.abs(contrib))
        out, seen = [], set()
        for i in order:
            term = self._names[row.col[i]].strip()
            if not term or term in seen:
                continue
            seen.add(term)
            out.append({"feature": term, "weight": round(float(contrib[i]), 4)})
            if len(out) == k:
                break
        return out


def load_metrics() -> Dict[str, Any]:
    if not METRICS_PATH.exists():
        return {}
    return json.loads(METRICS_PATH.read_text())


ai_model = PhishingTextModel()
