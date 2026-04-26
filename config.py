import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def resolve_path(value: str | None, default: str) -> Path:
    raw = value or default
    path = Path(raw)

    if path.is_absolute():
        return path

    return BASE_DIR / path


# ------------------------------------------------------------
# KSeF API
# ------------------------------------------------------------

KSEF_ENV = os.getenv("KSEF_ENV", "test").lower()

if KSEF_ENV == "prod":
    KSEF_BASE_URL = os.getenv(
        "KSEF_BASE_URL",
        "https://api.ksef.mf.gov.pl/v2"
    )
else:
    KSEF_BASE_URL = os.getenv(
        "KSEF_BASE_URL",
        "https://api-test.ksef.mf.gov.pl/v2"
    )


KSEF_NIP = os.getenv("KSEF_NIP", "")
NIP = KSEF_NIP
FA_SCHEMA_VERSION = os.getenv("FA_SCHEMA_VERSION", "FA(3)")
KSEF_TOKEN = os.getenv("KSEF_TOKEN", "")

PUBLIC_KEY_PATH = resolve_path(
    os.getenv("KSEF_PUBLIC_KEY_PATH"),
    "keys/ksef_public_key.pem"
)

AUTH_POLL_INTERVAL = int(os.getenv("AUTH_POLL_INTERVAL", "2"))

ALLOW_PROD_SEND = os.getenv("ALLOW_PROD_SEND", "false").lower() == "true"

# ------------------------------------------------------------
# Katalogi robocze
# ------------------------------------------------------------

OUTBOUND_DIR = resolve_path(
    os.getenv("KSEF_SEND_OUTBOUND_DIR"),
    "outbound"
)

PENDING_DIR = OUTBOUND_DIR / "pending"
APPROVED_DIR = OUTBOUND_DIR / "approved"
SENT_DIR = OUTBOUND_DIR / "sent"
REJECTED_DIR = OUTBOUND_DIR / "rejected"
LOGS_DIR = OUTBOUND_DIR / "logs"
AUTH_DIR = OUTBOUND_DIR / "auth"
PREVIEW_DIR = OUTBOUND_DIR / "preview"
ARCHIVE_DIR = OUTBOUND_DIR / "archive"
# ------------------------------------------------------------
# Walidacja FA
# ------------------------------------------------------------

FA_XSD_PATH = resolve_path(
    os.getenv("FA_XSD_PATH"),
    "xsd/fa.xsd"
)

PREVIEW_DIR = OUTBOUND_DIR / "preview"

PDF_RENDER_SCRIPT = resolve_path(
    os.getenv("PDF_RENDER_SCRIPT"),
    "pdf_generator/render_invoice.mjs"
)

def ensure_dirs():
    for d in (
        OUTBOUND_DIR,
        PENDING_DIR,
        APPROVED_DIR,
        SENT_DIR,
        REJECTED_DIR,
        LOGS_DIR,
        AUTH_DIR,
        PREVIEW_DIR,
        ARCHIVE_DIR,
        
    ):
        d.mkdir(parents=True, exist_ok=True)

def validate_config():
    errors = []

    print("Środowisko KSeF:", KSEF_ENV)
    print("Schemat faktury:", FA_SCHEMA_VERSION)

    if KSEF_ENV == "prod":
        print("UWAGA: skonfigurowano środowisko PRODUKCYJNE.")

    if KSEF_ENV == "prod" and ALLOW_PROD_SEND:
        print("UWAGA: ALLOW_PROD_SEND=true — wysyłka produkcyjna odblokowana.")

    if KSEF_ENV not in ("test", "demo", "prod"):
        errors.append("KSEF_ENV musi być: test, demo albo prod")

    if not KSEF_BASE_URL:
        errors.append("Brak KSEF_BASE_URL")

    if not KSEF_NIP:
        errors.append("Brak KSEF_NIP")

    if not KSEF_TOKEN:
        errors.append("Brak KSEF_TOKEN")

    if not PUBLIC_KEY_PATH.exists():
        errors.append(f"Brak klucza publicznego KSeF: {PUBLIC_KEY_PATH}")

    if errors:
        raise RuntimeError("Błędy konfiguracji: " + "; ".join(errors))
        if KSEF_ENV == "prod" and not ALLOW_PROD_SEND:
        print("\n⚠ PRODUKCJA KSeF jest zablokowana.")
        print("Aby wysyłać faktury ustaw w .env:")
        print("ALLOW_PROD_SEND=true\n")