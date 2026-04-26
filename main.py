import json
import shutil
import config

from datetime import datetime

from http_client import HttpClient
from auth import KSeFAuthClient
from validator.validate_fa import validate_pending_directory, validate_xml_basic
from validator.business_rules import check_business_rules

from sender.send_manifest import upsert_invoice
from sender.send_invoice import prepare_invoice_payload
from sender.ksef_sender import send_approved_dry_run
from sender.ksef_sender import send_approved_dry_run, send_approved_real
from sender.pdf_preview import generate_pdf_preview
from sender.archive import archive_invoice
from sender.ksef_online_session import get_access_token

def print_menu():
    print("\nKSeF Send")
    print("1 - sprawdź konfigurację")
    print("2 - waliduj XML w outbound/pending")
    print("3 - przygotuj faktury do wysyłki")
    print("4 - symuluj wysyłkę approved → sent")
    print("5 - przygotuj payload faktury")
    print("6 - test http client")
    print("7 - test autoryzacji KSeF")
    print("8 - REALNA wysyłka do KSeF")
    print("9 - archiwizuj pierwszą fakturę z sent")
    print("10 - wyjście")
    print("11 - pobierz accessToken KSeF")
    print("12 - test zapisu numeru KSeF do manifestu")

def check_config():
    config.ensure_dirs()
    config.validate_config()

    print("Konfiguracja OK")
    print("Środowisko:", config.KSEF_ENV)
    print("API:", config.KSEF_BASE_URL)
    print("Pending:", config.PENDING_DIR)


def validate_pending():
    config.ensure_dirs()

    report = validate_pending_directory(config.PENDING_DIR)

    print("\nRaport walidacji XML")
    print("Katalog:", report["pending_dir"])
    print("Plików XML:", report["count"])
    print("Poprawnych:", report["valid_count"])
    print("Błędnych:", report["invalid_count"])

    for item in report["results"]:
        status = "OK" if item["ok"] else "BŁĄD"
        print(f"- {status}: {item['file']}")

        for warning in item["warnings"]:
            print(f"  OSTRZEŻENIE: {warning}")

        for error in item["errors"]:
            print(f"  BŁĄD: {error}")

    out_file = config.LOGS_DIR / "validate_pending_report.json"
    out_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("Raport zapisany:", out_file)


def approve_valid_xml():
    config.ensure_dirs()

    pending = config.PENDING_DIR
    approved = config.APPROVED_DIR

    files = list(pending.glob("*.xml"))

    if not files:
        print("Brak XML w pending.")
        return

    moved = 0

    for f in files:
        xml_report = validate_xml_basic(f)

        if not xml_report["ok"]:
            print("BŁĄD XML:", f.name)
            continue

        business = check_business_rules(f)

        if not business["ok"]:
            print("BŁĄD BIZNESOWY:", f.name)
            for err in business["errors"]:
                print("   ", err)
            continue

        target = approved / f.name
        shutil.move(str(f), str(target))

        pdf_path = generate_pdf_preview(target)
        payload = prepare_invoice_payload(target)

        upsert_invoice(
            filename=target.name,
            status="approved",
            xml_path=str(target),
            pdf_path=str(pdf_path),
            sha256=payload["sha256"],
            size_bytes=payload["size_bytes"],
            note="XML validated, business rules passed, PDF preview generated"
        )

        print("OK:", f.name, "→ approved")
        print("PDF preview:", pdf_path)

        moved += 1

    print("Przeniesiono:", moved)


def prepare_payload_for_first_approved():
    config.ensure_dirs()

    files = list(config.APPROVED_DIR.glob("*.xml"))

    if not files:
        print("Brak XML w approved")
        return

    xml_file = files[0]
    payload = prepare_invoice_payload(xml_file)

    print("\nPayload faktury:")
    print("plik:", payload["filename"])
    print("rozmiar:", payload["size_bytes"], "bajtów")
    print("sha256:", payload["sha256"])

    log_file = config.LOGS_DIR / f"payload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    safe_payload = {
        "filename": payload["filename"],
        "size_bytes": payload["size_bytes"],
        "sha256": payload["sha256"],
    }

    log_file.write_text(
        json.dumps(safe_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("Log payload:", log_file)


def test_http_client():
    client = HttpClient(config.KSEF_BASE_URL)
    print("HTTP client OK")
    print("Base URL:", client.base_url)


def test_ksef_auth():
    config.ensure_dirs()

    print("BASE URL:", config.KSEF_BASE_URL)
    print("NIP:", config.NIP)
    print("TOKEN length:", len(config.KSEF_TOKEN or ""))
    print("PUBLIC KEY:", config.PUBLIC_KEY_PATH)
    print("PUBLIC KEY exists:", config.PUBLIC_KEY_PATH.exists())

    http = HttpClient(config.KSEF_BASE_URL)
    auth_client = KSeFAuthClient(http, config.AUTH_DIR)

    result = auth_client.authenticate()

    print("\nAutoryzacja OK")
    print("Access token:", result["accessToken"]["token"][:30] + "...")


def main():
    while True:
        print_menu()
        choice = input("Twój wybór: ").strip()

        try:
            if choice == "1":
                check_config()

            elif choice == "2":
                validate_pending()

            elif choice == "3":
                approve_valid_xml()

            elif choice == "4":
                result = send_approved_dry_run()

                print("\nSymulacja wysyłki")
                print("Środowisko:", result["env"])
                print("Tryb:", result["mode"])
                print("Wysłano testowo:", result["sent_count"])

                for item in result["files"]:
                    print("-", item["filename"], "→ sent")

                print("Log:", result.get("log_file"))

            elif choice == "5":
                prepare_payload_for_first_approved()

            elif choice == "6":
                test_http_client()

            elif choice == "7":
                test_ksef_auth()
                

            elif choice == "8":
                # REAL SEND !!!

                if config.KSEF_ENV == "prod" and not config.ALLOW_PROD_SEND:
                    raise RuntimeError(
                        "Realna wysyłka do produkcji KSeF jest zablokowana. "
                        "Ustaw ALLOW_PROD_SEND=true w .env aby odblokować."
                    )

                result = send_approved_real()

                print("\nRealna wysyłka KSeF")
                print("Środowisko:", result["env"])
                print("Tryb:", result["mode"])
                print("Wysłano:", result["sent_count"])
                print("Zablokowano:", result["blocked_count"])

                for item in result["files"]:
                    print("-", item["filename"], "|", item["status"], "|", item.get("reason", ""))

            elif choice == "9":

                from sender.archive import archive_invoice

                files = list(config.SENT_DIR.glob("*.xml"))

                if not files:
                    print("Brak XML w sent.")
                    continue

                xml_file = files[0]

                pdf_file = config.PREVIEW_DIR / f"{xml_file.stem}.pdf"

                archive_dir = archive_invoice(
                    xml_path=xml_file,
                    pdf_path=pdf_file,
                    response={
                        "status": "manual_archive_test",
                        "note": "Archiwizacja testowa bez realnej wysyłki do KSeF"
                    },
                    metadata={
                        "source_status": "sent",
                        "ksef_number": None
                    }
                )

                print("Zarchiwizowano:", archive_dir)
                    
                    
                    
            elif choice == "11":
                token = get_access_token()
                print("Access token OK:", token[:30] + "...")

                xml_file = files[0]
                pdf_file = config.PREVIEW_DIR / f"{xml_file.stem}.pdf"
         

            elif choice == "12":
                from sender.send_manifest import mark_invoice_accepted

                files = list(config.SENT_DIR.glob("*.xml")) or list(config.APPROVED_DIR.glob("*.xml"))

                if not files:
                    print("Brak XML w sent albo approved.")
                    continue

                xml_file = files[0]

                fake_response = {
                    "status": {
                        "code": 200,
                        "description": "TEST: Faktura przyjęta przez KSeF"
                    },
                    "ksefReferenceNumber": "TEST-KSEF-20260426-ABCDEF123456"
                }

                item = mark_invoice_accepted(
                    filename=xml_file.name,
                    ksef_number=fake_response["ksefReferenceNumber"],
                    invoice_reference="TEST-INVOICE-REF-001",
                    session_reference="TEST-SESSION-REF-001",
                    response=fake_response,
                )

                print("Zapisano testowy numer KSeF w manifeście:")
                print(item["filename"])
                print(item["ksef_number"])



                # archive_dir = archive_invoice(
                    # xml_path=xml_file,
                    # pdf_path=pdf_file,
                    # response={
                        # "status": "manual_archive_test",
                        # "note": "Archiwizacja testowa bez realnej wysyłki do KSeF"
                    # },
                    # metadata={
                        # "source_status": "sent",
                        # "ksef_number": None
                    # }
                # )

                # print("Zarchiwizowano:", archive_dir)
            
            elif choice == "10":
                print("Koniec.")
                break    

            else:
                print("Nieznana opcja.")

        except Exception as e:
            print("\nWystąpił błąd:")
            print(e)


if __name__ == "__main__":
    main()