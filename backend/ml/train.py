"""Train the phishing text classifier.

Usage (from backend/):  python ml/train.py

Reads every CSV in ml/data/ (and CSVs inside any .zip there), normalises labels
to 1=phishing / 0=legitimate, deduplicates, does a stratified 80/20 split and
saves models/text_clf.joblib, models/metrics.json and two PNG charts.
"""
import csv
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score, roc_curve, ConfusionMatrixDisplay)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
MODEL_DIR = BASE.parent / "models"
MAX_CHARS = 4000  # truncate very long emails to keep training fast
# Combined file in the Kaggle zip duplicates the others without a subject column.
SKIP_FILES = {"phishing_email.csv"}

TEXT_COLS = ["body", "text", "email_text", "email text", "text_combined"]
LABEL_COLS = ["label", "email type", "class"]
PHISH_LABELS = {"1", "phishing", "phishing email", "spam", "malicious", "fraud"}
SAFE_LABELS = {"0", "legitimate", "safe email", "safe", "ham", "benign"}


def _norm_label(v):
    s = str(v).strip().lower()
    if s.endswith(".0"):
        s = s[:-2]
    if s in PHISH_LABELS:
        return 1
    if s in SAFE_LABELS:
        return 0
    return None


def _frame_to_xy(df: pd.DataFrame, name: str):
    cols = {c.lower().strip(): c for c in df.columns}
    text_col = next((cols[c] for c in TEXT_COLS if c in cols), None)
    label_col = next((cols[c] for c in LABEL_COLS if c in cols), None)
    if text_col is None or label_col is None:
        print(f"  skip {name}: no text/label column ({list(df.columns)})")
        return None
    text = df[text_col].fillna("").astype(str)
    if "subject" in cols:
        text = df[cols["subject"]].fillna("").astype(str) + "\n" + text
    out = pd.DataFrame({"text": text.str.slice(0, MAX_CHARS),
                        "label": df[label_col].map(_norm_label), "source": name})
    out = out.dropna(subset=["label"])
    out["label"] = out["label"].astype(int)
    print(f"  {name}: {len(out)} rows, phishing={int(out.label.sum())}")
    return out


def load_dataset():
    frames = []
    for path in sorted(DATA_DIR.iterdir()):
        if path.suffix.lower() == ".csv" and path.name not in SKIP_FILES:
            f = _frame_to_xy(pd.read_csv(path, engine="python", on_bad_lines="skip"), path.name)
            if f is not None:
                frames.append(f)
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as z:
                for n in z.namelist():
                    if n.lower().endswith(".csv") and Path(n).name not in SKIP_FILES:
                        with z.open(n) as fh:
                            df = pd.read_csv(fh, engine="python", on_bad_lines="skip")
                        f = _frame_to_xy(df, f"{path.name}:{n}")
                        if f is not None:
                            frames.append(f)
    if not frames:
        sys.exit(f"No dataset found. Put a CSV (text + label columns) or the Kaggle "
                 f"'phishing-email-dataset' zip into {DATA_DIR}")
    return pd.concat(frames, ignore_index=True)


def normalise(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower()).strip()


def build_pipeline():
    features = FeatureUnion([
        ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2,
                                 max_features=50000, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                 max_features=50000, sublinear_tf=True)),
    ])
    clf = LogisticRegression(C=4, class_weight="balanced", max_iter=2000)
    return Pipeline([("features", features), ("clf", clf)])


def main():
    print("Loading dataset ...")
    df = load_dataset()
    df["norm"] = df["text"].map(normalise)
    before = len(df)
    df = df[df["norm"].str.len() > 0].drop_duplicates(subset="norm")
    print(f"Deduplicated: {before} -> {len(df)} rows")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, stratify=df["label"], random_state=42)

    t0 = time.time()
    pipe = build_pipeline().fit(X_train, y_train)
    base_secs = time.time() - t0
    print(f"Base pipeline trained in {base_secs:.1f}s")

    # Calibration needs 3 more fits; only do it when that keeps total < 2 min.
    calibrated = base_secs * 3 < 120
    if calibrated:
        t0 = time.time()
        model = CalibratedClassifierCV(build_pipeline(), cv=3, method="sigmoid",
                                       ensemble=False).fit(X_train, y_train)
        print(f"Calibrated model trained in {time.time() - t0:.1f}s")
    else:
        model = pipe

    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    cm = confusion_matrix(y_test, pred)
    metrics = {
        "dataset": "Kaggle 'Phishing Email Dataset' (Naser Abdullah Alam): "
                   + ", ".join(sorted({s.split(':')[-1] for s in df['source']})),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "phishing_ratio": round(float(df["label"].mean()), 4),
        "calibrated": calibrated,
        "accuracy": round(accuracy_score(y_test, pred), 4),
        "precision": round(precision_score(y_test, pred), 4),
        "recall": round(recall_score(y_test, pred), 4),
        "f1": round(f1_score(y_test, pred), 4),
        "roc_auc": round(roc_auc_score(y_test, proba), 4),
        "confusion_matrix": {"labels": ["legitimate", "phishing"], "matrix": cm.tolist()},
        "per_source_rows": df["source"].value_counts().to_dict(),
    }

    MODEL_DIR.mkdir(exist_ok=True)
    # "explainer" is a plain pipeline used for top_terms (LR coefficients).
    joblib.dump({"model": model, "explainer": pipe, "version": metrics["timestamp"]},
                MODEL_DIR / "text_clf.joblib", compress=3)
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    ConfusionMatrixDisplay(cm, display_labels=["Legitimate", "Phishing"]).plot(cmap="Blues")
    plt.title("Confusion matrix (test set)")
    plt.savefig(MODEL_DIR / "confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()

    fpr, tpr, _ = roc_curve(y_test, proba)
    plt.plot(fpr, tpr, label=f"ROC-AUC = {metrics['roc_auc']}")
    plt.plot([0, 1], [0, 1], "k--", linewidth=0.8)
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curve (test set)")
    plt.legend(loc="lower right")
    plt.savefig(MODEL_DIR / "roc_curve.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(json.dumps({k: v for k, v in metrics.items() if k != "per_source_rows"}, indent=2))


if __name__ == "__main__":
    main()
