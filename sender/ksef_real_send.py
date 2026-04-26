import config
from auth import KSeFAuthClient
from http_client import HttpClient

from sender.send_invoice import prepare_invoice_payload
from sender.session_ledger import log_event
from sender.send_manifest import mark_invoice_accepted
from sender.ksef_sender import require_pdf_preview, require_prod_confirmation


def send_invoice_real():
    config.ensure_dirs()

    files = sorted(config.APPROVED_DIR.glob("*.xml"))

    result = {
        "mode": "real_send",
        "env": config.KSEF_ENV,
        "sent_count": 0,
        "blocked_count": 0,
        "files": []
    }

    if not files:
        return result

    xml_file = files[0]

    try:
        require_pdf_preview(xml_file)
        require_prod_confirmation(xml_file.name)

        http = HttpClient(config.KSEF_BASE_URL)
        auth = KSeFAuthClient(http, config.AUTH_DIR)

        auth_result = auth.authenticate()
        access_token = auth_result["accessToken"]["token"]

        log_event(
            event_type="auth",
            status="ok",
            filename=xml_file.name,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        session_response = http.request(
            "POST",
            f"{config.KSEF_BASE_URL}/sessions/online",
            headers=headers,
            json_body={}
        )
        session = session_response.json()

        session_ref = session["referenceNumber"]

        log_event(
            event_type="open_session",
            status="ok",
            filename=xml_file.name,
            session_reference=session_ref,
            response=session
        )

        payload = prepare_invoice_payload(xml_file)

        invoice_response = http.request(
            "POST",
            f"{config.KSEF_BASE_URL}/sessions/online/{session_ref}/invoices",
            headers=headers,
            json_body=payload
        )
        invoice = invoice_response.json()

        invoice_ref = invoice["referenceNumber"]

        log_event(
            event_type="send_invoice",
            status="ok",
            filename=xml_file.name,
            session_reference=session_ref,
            invoice_reference=invoice_ref,
            response=invoice
        )

        status_response = http.request(
            "GET",
            f"{config.KSEF_BASE_URL}/sessions/online/{session_ref}/invoices/{invoice_ref}",
            headers=headers
        )
        status = status_response.json()

        ksef_number = status.get("ksefReferenceNumber")

        log_event(
            event_type="invoice_status",
            status="ok",
            filename=xml_file.name,
            session_reference=session_ref,
            invoice_reference=invoice_ref,
            ksef_number=ksef_number,
            response=status
        )

        if not ksef_number:
            result["blocked_count"] += 1
            result["files"].append({
                "filename": xml_file.name,
                "status": "status_without_ksef_number",
                "response": status,
            })
            return result

        mark_invoice_accepted(
            filename=xml_file.name,
            ksef_number=ksef_number,
            invoice_reference=invoice_ref,
            session_reference=session_ref,
            response=status,
        )

        result["files"].append({
            "filename": xml_file.name,
            "status": "accepted",
            "ksef_number": ksef_number
        })

        result["sent_count"] = 1
        return result

    except Exception as e:
        log_event(
            event_type="error",
            status="failed",
            filename=xml_file.name,
            error=str(e)
        )
        raise