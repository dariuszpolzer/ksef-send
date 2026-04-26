import json
from datetime import datetime, timezone

import config


LEDGER_PATH = config.OUTBOUND_DIR / "session_ledger.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_ledger() -> dict:
    if not LEDGER_PATH.exists():
        return {
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "env": config.KSEF_ENV,
            "events": []
        }

    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def save_ledger(ledger: dict) -> None:
    ledger["updated_at"] = utc_now()
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def log_event(
    event_type: str,
    status: str,
    filename: str | None = None,
    session_reference: str | None = None,
    invoice_reference: str | None = None,
    ksef_number: str | None = None,
    response: dict | None = None,
    error: str | None = None,
) -> dict:
    ledger = load_ledger()

    event = {
        "at": utc_now(),
        "env": config.KSEF_ENV,
        "event_type": event_type,
        "status": status,
        "filename": filename,
        "session_reference": session_reference,
        "invoice_reference": invoice_reference,
        "ksef_number": ksef_number,
        "response": response,
        "error": error,
    }

    ledger["events"].append(event)
    save_ledger(ledger)

    return event