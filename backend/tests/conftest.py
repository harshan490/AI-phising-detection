import os
import sys
import tempfile
from pathlib import Path

# Must be set before the app is imported.
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db").replace("\\", "/")
os.environ["VT_API_KEY"] = ""
os.environ["URLHAUS_AUTH_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures"
# Real received emails with the recipient's identifiers and tracking tokens removed
# (see fixtures/redact_samples.py).
SCAM_EML = FIXTURES / "real_scam_lottery_redacted.eml"
DISCORD_EML = FIXTURES / "real_discord_password_changed_redacted.eml"
LOOKALIKE_EML = FIXTURES / "lookalike_paypal.eml"
