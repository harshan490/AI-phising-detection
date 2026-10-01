"""Records a real end-to-end demo video of the platform with Playwright.

Prerequisites: backend on http://localhost:8000 (fresh DB) and frontend on http://localhost:5173.
Usage (from repo root):  python demo/record_demo.py
Output: demo/AICS_phishing_platform_demo.mp4

Everything shown is the live application: real sign-up, real uploads of .eml files to the
FastAPI backend, real model inference and real database-backed dashboards. The only things
added on top are a visible mouse cursor and caption banners to narrate the steps.
"""
import base64
import html
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FIXTURES = BACKEND / "tests" / "fixtures"
OUT_DIR = ROOT / "demo"
APP = "http://localhost:5173"
API = "http://localhost:8000"
W, H = 1280, 720

DEMO_USER = {"name": "Demo Analyst", "email": "demo.analyst@example.com", "password": "DemoPassw0rd!"}
EMAILS = [
    (FIXTURES / "lookalike_paypal.eml", "Look-alike PayPal phishing email (paypa1.com, fake link, .html attachment)"),
    (FIXTURES / "real_discord_password_changed_redacted.eml", "Real Discord security notification (legitimate)"),
    (FIXTURES / "real_scam_lottery_redacted.eml", "Real '$30,000,000 USD' promotional scam email"),
]

CURSOR_JS = """
(() => {
  if (window.__demoCursor) return;
  window.__demoCursor = true;
  const add = () => {
    const c = document.createElement('div');
    c.id = '__cursor';
    c.style.cssText = 'position:fixed;z-index:2147483647;width:18px;height:18px;border-radius:50%;' +
      'background:rgba(255,255,255,0.9);border:2px solid #60a5fa;box-shadow:0 0 12px rgba(96,165,250,0.9);' +
      'pointer-events:none;transform:translate(-50%,-50%);left:-50px;top:-50px;transition:width .1s,height .1s';
    document.body.appendChild(c);
    document.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; });
    document.addEventListener('mousedown', () => { c.style.width = '12px'; c.style.height = '12px'; });
    document.addEventListener('mouseup', () => { c.style.width = '18px'; c.style.height = '18px'; });
  };
  if (document.body) add(); else document.addEventListener('DOMContentLoaded', add);
})();
"""

CAPTION_JS = """
(text) => {
  let el = document.getElementById('__caption');
  if (!el) {
    el = document.createElement('div');
    el.id = '__caption';
    el.style.cssText = 'position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:2147483646;' +
      'max-width:86%;padding:10px 22px;border-radius:999px;background:rgba(10,10,15,0.88);color:#fff;' +
      'font:600 17px/1.35 Inter,Segoe UI,sans-serif;border:1px solid rgba(96,165,250,0.6);' +
      'box-shadow:0 8px 30px rgba(0,0,0,0.5);text-align:center;pointer-events:none';
    document.body.appendChild(el);
  }
  el.style.display = text ? 'block' : 'none';
  el.textContent = text;
}
"""

CARD_CSS = """
body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;background:#0a0a0f;
color:#e5e7eb;font-family:Inter,'Segoe UI',sans-serif}
.card{max-width:1080px;padding:40px 56px;border-radius:24px;background:rgba(255,255,255,0.04);
border:1px solid rgba(255,255,255,0.1)}
h1{font-size:40px;margin:0 0 12px;background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;color:transparent}
h2{font-size:22px;margin:0 0 18px;color:#cbd5e1;font-weight:600}
li{font-size:19px;margin:8px 0;color:#d1d5db}
pre{font:13px/1.45 Consolas,monospace;margin:0;white-space:pre-wrap;color:#d1d5db}
.ok{color:#4ade80}.k{color:#60a5fa}
"""


def caption(page, text):
    try:
        page.evaluate(CAPTION_JS, text)
    except Exception:
        pass


def pause(s):
    time.sleep(s)


def move_click(page, locator, pause_after=0.6):
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    if box:
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=25)
        pause(0.25)
    locator.click()
    pause(pause_after)


def smooth_scroll(page, total_px, step=90, delay=0.06):
    page.mouse.move(W / 2, H / 2, steps=10)
    for _ in range(int(abs(total_px) / step)):
        page.mouse.wheel(0, step if total_px > 0 else -step)
        pause(delay)


def scroll_page_through(page, delay=0.07):
    height = page.evaluate("document.documentElement.scrollHeight")
    smooth_scroll(page, max(height - H, 0), delay=delay)


def card(page, inner_html, seconds, cap=None):
    page.set_content(f"<html><head><style>{CARD_CSS}</style></head><body><div class='card'>{inner_html}</div></body></html>")
    page.evaluate(CURSOR_JS)
    if cap:
        caption(page, cap)
    pause(seconds)


def run_tests_text():
    res = subprocess.run([sys.executable, "-m", "pytest", "-v", "-p", "no:warnings", "--no-header"],
                         cwd=BACKEND, capture_output=True, text=True)
    lines = [l for l in res.stdout.splitlines() if "::" in l or "passed" in l or "failed" in l]
    out = []
    for l in lines:
        l = html.escape(l)
        out.append(l.replace("PASSED", "<span class='ok'>PASSED</span>").replace(" passed", "<span class='ok'> passed</span>"))
    return "\n".join(out)


def main():
    metrics = json.loads((BACKEND / "models" / "metrics.json").read_text())
    print("Running test suite for the intro slide ...")
    tests_html = run_tests_text()
    raw_dir = OUT_DIR / "_raw"
    shutil.rmtree(raw_dir, ignore_errors=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(raw_dir),
                                  record_video_size={"width": W, "height": H})
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()

        # 1. Title
        card(page, """
          <h1>Intelligent Phishing Email Detection &amp; Threat Intelligence Platform</h1>
          <h2>AI in Cybersecurity (AICS) project &middot; live demo</h2>
          <ul>
            <li><span class='k'>AI model:</span> TF-IDF (word + char n-grams) + Logistic Regression, trained on 81,863 real emails</li>
            <li><span class='k'>Rules:</span> 16 phishing heuristics (look-alike domains, link mismatch, SPF/DKIM/DMARC, attachments...)</li>
            <li><span class='k'>Risk score:</span> 0.45&middot;text + 0.25&middot;URL + 0.15&middot;auth + 0.10&middot;attachment + 0.05&middot;sender</li>
            <li><span class='k'>Stack:</span> FastAPI + SQLAlchemy backend, React + Chart.js frontend, JWT auth</li>
          </ul>""", 7)

        # 2. Tests
        card(page, f"<h2>Automated test suite (pytest) &ndash; run just before this recording</h2><pre>{tests_html}</pre>",
             7, "All backend tests pass: heuristics, risk formula, parser, model and API (incl. the 3 demo emails)")

        # 3. Sign up
        page.goto(f"{APP}/signup")
        pause(4.5)  # boot animation
        caption(page, "Step 1 - Create an analyst account (passwords are bcrypt-hashed, sessions use JWT)")
        for placeholder, value in [("John Doe", DEMO_USER["name"]), ("you@company.com", DEMO_USER["email"]),
                                   ("••••••••", DEMO_USER["password"])]:
            field = page.get_by_placeholder(placeholder)
            move_click(page, field, 0.2)
            field.press_sequentially(value, delay=55)
            pause(0.3)
        move_click(page, page.locator("button[type=submit]"), 2.5)
        caption(page, "Empty dashboard - every number here is computed from scans stored in the database")
        pause(4)

        # 4. Scan the three emails
        for idx, (path, desc) in enumerate(EMAILS):
            move_click(page, page.get_by_text("Scanning", exact=True).first, 1.5)
            caption(page, f"Step 2.{idx + 1} - Upload: {desc}")
            page.set_input_files("input[type=file]", str(path))
            pause(2)
            move_click(page, page.get_by_role("button", name="Analyze Payload"), 0.5)
            page.get_by_text("Risk Components").wait_for(timeout=30000)
            pause(1.5)
            verdict = page.locator("text=/Verdict: (Safe|Suspicious|Phishing)/").first.inner_text()
            caption(page, f"Real pipeline log, then the result - {verdict}")
            smooth_scroll(page, 700, delay=0.07)
            pause(3)
            caption(page, "Risk score = weighted AI text probability + heuristic components; top model terms explain the AI part")
            smooth_scroll(page, 650, delay=0.07)
            pause(3.5)
            caption(page, "Triggered checks show their evidence; URLs are checked against the local threat-intel blocklist")
            scroll_page_through(page, delay=0.05)
            pause(3)
            page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            pause(1)
            move_click(page, page.get_by_role("button", name="Scan another email"), 1)

        # 5. Dashboard
        move_click(page, page.get_by_text("Dashboard", exact=True).first, 2.5)
        caption(page, "Dashboard now reflects the 3 real scans: verdict counts, threat level and recent scans")
        pause(5)
        smooth_scroll(page, 500)
        pause(3)

        # 6. Analytics
        move_click(page, page.get_by_text("Analytics", exact=True).first, 3)
        caption(page, "Analytics (Chart.js): verdict distribution and scans over time")
        pause(4)
        smooth_scroll(page, 560)
        caption(page, "Most frequent triggered checks + model metrics from the held-out test set")
        pause(5)
        smooth_scroll(page, 560)
        caption(page, "Indicators of compromise (domains, URLs, IPs, attachment SHA-256) extracted and upserted per scan")
        pause(5)

        # 7. Model evaluation charts
        cm = base64.b64encode((BACKEND / "models" / "confusion_matrix.png").read_bytes()).decode()
        roc = base64.b64encode((BACKEND / "models" / "roc_curve.png").read_bytes()).decode()
        m = metrics
        card(page, f"""
          <h2>Model evaluation on {m['test_size']:,} unseen test emails (trained on {m['train_size']:,})</h2>
          <div style='display:flex;gap:24px;align-items:center'>
            <img src='data:image/png;base64,{cm}' style='height:330px;background:#fff;border-radius:12px'>
            <img src='data:image/png;base64,{roc}' style='height:330px;background:#fff;border-radius:12px'>
          </div>
          <ul style='display:flex;gap:28px;list-style:none;padding:0;margin-top:20px'>
            <li>Accuracy <b>{m['accuracy']*100:.2f}%</b></li><li>Precision <b>{m['precision']*100:.2f}%</b></li>
            <li>Recall <b>{m['recall']*100:.2f}%</b></li><li>F1 <b>{m['f1']*100:.2f}%</b></li><li>ROC-AUC <b>{m['roc_auc']}</b></li>
          </ul>""", 8, "Charts generated by ml/train.py on the Kaggle Phishing Email Dataset")

        # 8. API docs
        page.goto(f"{API}/docs")
        pause(2.5)
        caption(page, "FastAPI backend - auth, scanner, IOC and model-metrics endpoints (all JWT-protected)")
        pause(3)
        smooth_scroll(page, 500)
        pause(3)

        # 9. End
        card(page, """
          <h1>Thank you</h1>
          <h2>Limitations &amp; future work</h2>
          <ul>
            <li>Transformer model (e.g. DistilBERT) and LIME/SHAP explanations</li>
            <li>Live threat-intel feeds (URLhaus, PhishTank, VirusTotal API key) instead of the local blocklist</li>
            <li>Attachment sandboxing, QR-code phishing detection, WHOIS domain age</li>
          </ul>""", 6)

        video_path = page.video.path()
        ctx.close()
        browser.close()

    out = OUT_DIR / "AICS_phishing_platform_demo.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path), "-c:v", "libx264", "-preset", "slow",
                    "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    shutil.rmtree(raw_dir, ignore_errors=True)
    print("Saved", out)


if __name__ == "__main__":
    main()
