import json
from pathlib import Path
from datetime import datetime, timezone

import config


MANIFEST_PATH = config.OUTBOUND_DIR / "send_manifest.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "env": config.KSEF_ENV,
            "items": []
        }

    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(manifest: dict) -> None:
    manifest["updated_at"] = utc_now()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def mark_invoice_accepted(
    filename: str,
    ksef_number: str,
    invoice_reference: str | None = None,
    session_reference: str | None = None,
    response: dict | None = None,
) -> dict:
    return upsert_invoice(
        filename=filename,
        status="accepted",
        note="Faktura przyjęta przez KSeF",
        ksef_number=ksef_number,
        invoice_reference=invoice_reference,
        session_reference=session_reference,
        response=response,
    )

def upsert_invoice(
    filename: str,
    status: str,
    xml_path: str | None = None,
    pdf_path: str | None = None,
    sha256: str | None = None,
    size_bytes: int | None = None,
    note: str | None = None,
    ksef_number: str | None = None,
    invoice_reference: str | None = None,
    session_reference: str | None = None,
    response: dict | None = None,
) -> dict:
    manifest = load_manifest()

    item = None
    for existing in manifest["items"]:
        if existing["filename"] == filename:
            item = existing
            break

    if item is None:
        item = {
            "filename": filename,
            "created_at": utc_now(),
            "history": []
        }
        manifest["items"].append(item)

    item["status"] = status
    item["updated_at"] = utc_now()

    if xml_path is not None:
        item["xml_path"] = xml_path

    if pdf_path is not None:
        item["pdf_path"] = pdf_path

    if sha256 is not None:
        item["sha256"] = sha256

    if size_bytes is not None:
        item["size_bytes"] = size_bytes

    if note is not None:
        item["note"] = note

    if ksef_number is not None:
        item["ksef_number"] = ksef_number

    if invoice_reference is not None:
        item["invoice_reference"] = invoice_reference

    if session_reference is not None:
        item["session_reference"] = session_reference

    if response is not None:
        item["last_response"] = response

    item["history"].append({
        "at": utc_now(),
        "status": status,
        "note": note
    })

    save_manifest(manifest)
    return item