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

REPO = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCAM_EML = next(REPO.glob("*30,000,000 USD*.eml"))
DISCORD_EML = REPO / "Discord Password Changed.eml"
LOOKALIKE_EML = FIXTURES / "lookalike_paypal.eml"
