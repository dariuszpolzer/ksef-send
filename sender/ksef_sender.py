import json
import shutil
from pathlib import Path

import config
from utils import utc_now


def require_pdf_preview(xml_file: Path):
    pdf_file = config.PREVIEW_DIR / f"{xml_file.stem}.pdf"

    if not pdf_file.exists():
        raise RuntimeError(
            f"Brak podglądu PDF dla faktury: {xml_file.name}. "
            f"Najpierw wygeneruj PDF: {pdf_file}"
        )

    print("\nPodgląd PDF istnieje:")
    print(pdf_file)

    confirm = input("Czy sprawdziłeś PDF faktury? Wpisz: SPRAWDZIŁEM PDF: ").strip()

    if confirm != "SPRAWDZIŁEM PDF":
        raise RuntimeError("Przerwano wysyłkę — PDF nie został potwierdzony.")


def require_prod_confirmation(invoice_filename: str):
    if config.KSEF_ENV != "prod":
        return

    if not config.ALLOW_PROD_SEND:
        raise RuntimeError(
            "Wysyłka do PRODUKCJI jest zablokowana. "
            "Ustaw ALLOW_PROD_SEND=true tylko świadomie."
        )

    print("\nUWAGA: ŚRODOWISKO PRODUKCYJNE KSeF")
    print("Faktura:", invoice_filename)
    print("To może mieć skutki podatkowe.")

    confirm = input("Aby wysłać wpisz: WYSYŁAM DO KSEF PROD: ").strip()

    if confirm != "WYSYŁAM DO KSEF PROD":
        raise RuntimeError("Przerwano wysyłkę produkcyjną.")


def send_approved_dry_run() -> dict:
    """
    Tryb testowy bez wysyłki do KSeF.
    Przenosi XML z approved do sent i zapisuje log.
    """

    config.ensure_dirs()

    files = sorted(config.APPROVED_DIR.glob("*.xml"))

    result = {
        "mode": "dry_run",
        "env": config.KSEF_ENV,
        "sent_count": 0,
        "files": [],
        "created_at": utc_now(),
    }

    if not files:
        return result

    for xml_file in files:
        target = config.SENT_DIR / xml_file.name
        shutil.move(str(xml_file), str(target))

        item = {
            "filename": xml_file.name,
            "source": str(xml_file),
            "target": str(target),
            "status": "dry_run_sent",
            "sent_at": utc_now(),
        }

        result["files"].append(item)
        result["sent_count"] += 1

    log_file = config.LOGS_DIR / f"send_dry_run_{utc_now().replace(':', '').replace('-', '')}.json"
    log_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    result["log_file"] = str(log_file)
    return result



# import json
# import hashlib
# from pathlib import Path
# from utils import utc_now
# import config
# from auth import KSeFAuthClient
# from http_client import HttpClient

# from sender.send_invoice import prepare_invoice_payload
# from sender.session_ledger import log_event

# def send_invoice_real():

    # config.ensure_dirs()

    # files = sorted(config.APPROVED_DIR.glob("*.xml"))

    # result = {
        # "mode": "real_send",
        # "env": config.KSEF_ENV,
        # "sent_count": 0,
        # "blocked_count": 0,
        # "files": []
    # }

    # if not files:
        # return result

    # xml_file = files[0]

    # require_pdf_preview(xml_file)
    # require_prod_confirmation(xml_file.name)

    # http = HttpClient(config.KSEF_BASE_URL)
    # auth = KSeFAuthClient(http, config.AUTH_DIR)

    # auth_result = auth.authenticate()
    # access_token = auth_result["accessToken"]["token"]
    # log_event(
    # event_type="auth",
    # status="ok"
# )

    # headers = {
        # "Authorization": f"Bearer {access_token}",
        # "Content-Type": "application/json"
    # }

    # # 1️⃣ otwarcie sesji

    # session = http.request(
        # "POST",
        # "/sessions/online",
        # headers=headers,
        # json={}
    # )

    # session_ref = session["referenceNumber"]
    # log_event(
    # event_type="open_session",
    # status="ok",
    # filename=xml_file.name,
    # session_reference=session_ref,
    # response=session
# )

    # # 2️⃣ przygotowanie payloadu faktury

    # payload = prepare_invoice_payload(xml_file)

    # invoice = http.request(
        # "POST",
        # f"/sessions/online/{session_ref}/invoices",
        # headers=headers,
        # json=payload
    # )

    # invoice_ref = invoice["referenceNumber"]
    # log_event(
    # event_type="send_invoice",
    # status="ok",
    # filename=xml_file.name,
    # session_reference=session_ref,
    # invoice_reference=invoice_ref,
    # response=invoice
# )

    # # 3️⃣ sprawdzenie statusu

    # status = http.request(
        # "GET",
        # f"/sessions/online/{session_ref}/invoices/{invoice_ref}",
        # headers=headers
    # )

    # ksef_number = status.get("ksefReferenceNumber")
    # log_event(
    # event_type="invoice_accepted",
    # status="ok",
    # filename=xml_file.name,
    # session_reference=session_ref,
    # invoice_reference=invoice_ref,
    # ksef_number=ksef_number,
    # response=status
# )

    # update_manifest_after_send(
        # xml_file,
        # ksef_number,
        # invoice_ref,
        # session_ref,
        # status
    # )

    # result["files"].append({
        # "filename": xml_file.name,
        # "status": "accepted",
        # "ksef_number": ksef_number
    # })

    # result["sent_count"] = 1

    # return result

