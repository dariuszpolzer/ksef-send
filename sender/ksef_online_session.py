import json
import time
from pathlib import Path

import config
from auth import KSeFAuthClient
from http_client import HttpClient
from sender.send_invoice import prepare_invoice_payload
from sender.ksef_sender import require_pdf_preview, require_prod_confirmation
from sender.send_manifest import upsert_invoice
from sender.archive import archive_invoice


def get_access_token() -> str:
    config.ensure_dirs()

    http = HttpClient(config.KSEF_BASE_URL)
    auth_client = KSeFAuthClient(http, config.AUTH_DIR)

    result = auth_client.authenticate()
    return result["accessToken"]["token"]


def open_online_session(access_token: str) -> dict:
    """
    TODO: dopasować body do aktualnego OpenAPI KSeF 2.0.
    Na razie funkcja celowo nie jest używana w produkcyjnej wysyłce.
    """

    http = HttpClient(config.KSEF_BASE_URL)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {
        "formCode": {
            "systemCode": "FA (3)",
            "schemaVersion": "1-0E",
            "value": "FA"
        }
    }

    response = http.request(
        "POST",
        f"{config.KSEF_BASE_URL}/sessions/online",
        headers=headers,
        json_body=body,
    )

    data = response.json()

    if response.status_code >= 400:
        raise RuntimeError(f"Błąd otwarcia sesji online: {data}")

    return data


def send_invoice_in_session(
    access_token: str,
    session_reference: str,
    xml_file: Path,
) -> dict:
    """
    TODO: dopasować finalne body do aktualnego OpenAPI.
    """

    payload = prepare_invoice_payload(xml_file)

    http = HttpClient(config.KSEF_BASE_URL)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    body = {
        "invoiceHash": payload["sha256"],
        "invoiceSize": payload["size_bytes"],
        "invoicePayload": {
            "type": "base64",
            "invoiceBody": payload["invoice_base64"],
        },
    }

    response = http.request(
        "POST",
        f"{config.KSEF_BASE_URL}/sessions/online/{session_reference}/invoices",
        headers=headers,
        json_body=body,
    )

    data = response.json()

    if response.status_code >= 400:
        raise RuntimeError(f"Błąd wysyłki faktury: {data}")

    return data


def wait_for_invoice_status(
    access_token: str,
    session_reference: str,
    invoice_reference: str,
    max_attempts: int = 60,
    sleep_seconds: int = 5,
) -> dict:
    http = HttpClient(config.KSEF_BASE_URL)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    for attempt in range(1, max_attempts + 1):
        response = http.request(
            "GET",
            f"{config.KSEF_BASE_URL}/sessions/{session_reference}/invoices/{invoice_reference}",
            headers=headers,
        )

        data = response.json()

        status = data.get("status", {})
        code = status.get("code")
        desc = status.get("description", "")

        print(f"[INVOICE STATUS] próba={attempt} code={code} desc={desc}")

        if code == 200:
            return data

        if isinstance(code, int) and code >= 400 and code != 429:
            raise RuntimeError(f"Faktura odrzucona: {data}")

        time.sleep(sleep_seconds)

    raise TimeoutError("Przekroczono czas oczekiwania na status faktury.")


def close_online_session(access_token: str, session_reference: str) -> dict:
    http = HttpClient(config.KSEF_BASE_URL)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = http.request(
        "POST",
        f"{config.KSEF_BASE_URL}/sessions/online/{session_reference}/close",
        headers=headers,
    )

    data = response.json()

    if response.status_code >= 400:
        raise RuntimeError(f"Błąd zamykania sesji online: {data}")

    return data


def send_first_approved_invoice_real() -> dict:
    """
    Bezpieczny real-send scaffold:
    - wymaga PDF preview,
    - wymaga blokady/potwierdzenia PROD,
    - na razie NIE wywołuj tej funkcji bez sprawdzenia body z OpenAPI.
    """

    files = sorted(config.APPROVED_DIR.glob("*.xml"))

    if not files:
        return {
            "ok": False,
            "message": "Brak XML w approved.",
        }

    xml_file = files[0]
    pdf_file = config.PREVIEW_DIR / f"{xml_file.stem}.pdf"

    require_pdf_preview(xml_file)
    require_prod_confirmation(xml_file.name)

    raise RuntimeError(
        "Realna wysyłka jest celowo zatrzymana. "
        "Najpierw dopasuj body open_online_session() i send_invoice_in_session() "
        "do aktualnego OpenAPI KSeF 2.0."
    )