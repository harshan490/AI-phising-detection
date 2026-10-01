# Intelligent Phishing Email Detection and Threat Intelligence Platform Using AI

AI in Cybersecurity (AICS) course project. Upload a raw `.eml` email and the platform parses it, runs 16 phishing
heuristics, checks URLs against threat intelligence, scores the text with a trained machine-learning model and
combines everything into an explainable risk score (Safe / Suspicious / Phishing).

**Demo video:** [`demo/AICS_phishing_platform_demo.mp4`](demo/AICS_phishing_platform_demo.mp4) (2 min 35 s, real recording of the running app)

## Features

- **AI text classifier** – TF-IDF (word 1–2-grams + character 3–5-grams) → Logistic Regression, trained on 81,863
  real emails. Explanations show the top contributing n-grams (TF-IDF weight × model coefficient).
- **16 phishing heuristics** – link text vs. real link target, look-alike / punycode domains (Levenshtein ≤ 2 from
  brand domains), brand display-name impersonation, Reply-To / Return-Path mismatch, IP-address URLs, URL shorteners,
  `@` in URLs, excessive subdomains, suspicious TLDs, risky / double-extension attachments, SPF / DKIM / DMARC
  results, urgency keywords.
- **Combined risk score**
  `risk = 0.45·text + 0.25·url + 0.15·auth + 0.10·attachment + 0.05·sender` (each component = max severity of its
  triggered checks); a local-blocklist hit raises risk to ≥ 0.90. Safe < 40 ≤ Suspicious < 70 ≤ Phishing.
- **Threat intelligence** – offline local blocklist (`backend/data/blocklist.txt`); optional VirusTotal / URLhaus
  lookups only when API keys are configured (3 s timeout, 24 h database cache). Nothing is fabricated.
- **IOC database** – every domain, URL, IP and attachment SHA-256 is upserted with first/last seen, hit count and the
  worst verdict of the emails it appeared in.
- **Dashboard & analytics** – real statistics from stored scans, Chart.js charts, model metrics, IOC table.
- **Security** – JWT auth on all scanner/model endpoints, per-user scan isolation, bcrypt passwords, 10 MB `.eml`
  upload limit, required `JWT_SECRET`, CORS restricted to the frontend origin, generic client error messages.

## Model results (held-out test set)

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| 99.36 % | 99.27 % | 99.51 % | 99.39 % | 0.9997 |

Dataset: Kaggle *Phishing Email Dataset* (Naser Abdullah Alam) – CEAS-08, Enron, Ling, Nazario, Nigerian Fraud,
SpamAssassin; 82,486 emails → 81,863 after de-duplication; stratified 80/20 split (65,490 train / 16,373 test).
Confusion matrix: legitimate 7,787 correct / 62 false positives; phishing 8,482 caught / 42 missed.
Charts: [`backend/models/confusion_matrix.png`](backend/models/confusion_matrix.png),
[`backend/models/roc_curve.png`](backend/models/roc_curve.png).

> Note: scores this high are typical for this benchmark and partly reflect differences between the source corpora;
> real-world performance will be lower. Some sources label spam vs. ham rather than strictly phishing.

## Running locally

Requirements: Python 3.11, Node 20.19+.

```bash
# backend
cd backend
pip install -r requirements.txt
cp .env.example .env            # then set JWT_SECRET to a long random string
python ml/train.py              # optional: retrain (needs the Kaggle zip in backend/ml/data/); a trained model is included
python -m uvicorn app.main:app --port 8000
```

```bash
# frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

```bash
# tests
cd backend
python -m pytest -q
```

API docs: http://localhost:8000/docs. Docker: `JWT_SECRET=... docker compose up --build` (compose file provided,
not tested in this submission).

## Project structure

```
backend/
  app/api/endpoints/   auth, scanner (upload, status, dashboard-stats, iocs, scan-url), model (metrics)
  app/services/        email_parser, heuristics, risk, threat_intel, ai_model, scan_pipeline
  app/models/          User, Scan, IOC, TICache (SQLAlchemy)
  ml/train.py          training script → models/text_clf.joblib, metrics.json, charts
  tests/               pytest suite + .eml fixtures
frontend/src/          React pages (Dashboard, Scanner, Analytics, Settings) and components
demo/                  demo video + Playwright script that recorded it
```

The two real sample emails in `backend/tests/fixtures/real_*_redacted.eml` were received by the author; the
recipient's address, usernames and per-recipient tracking tokens were removed with
`tests/fixtures/redact_samples.py`. `lookalike_paypal.eml` is a synthetic test email.

## Limitations and future work

- Transformer model (e.g. DistilBERT) compared against this baseline; LIME / SHAP explanations.
- Live threat-intel feeds (URLhaus, PhishTank, OpenPhish) and resolving click-tracking redirects to their real target.
- Independent SPF / DKIM / DMARC verification (currently read from the `Authentication-Results` header).
- Attachment sandboxing, QR-code phishing detection, WHOIS domain age.
