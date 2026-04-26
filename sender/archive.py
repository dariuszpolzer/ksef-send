import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

import config


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def archive_invoice(
    xml_path: Path,
    pdf_path: Path | None = None,
    response: dict | None = None,
    metadata: dict | None = None,
) -> Path:
    xml_path = Path(xml_path)

    if not xml_path.exists():
        raise FileNotFoundError(f"Brak XML do archiwizacji: {xml_path}")

    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")

    invoice_dir = config.ARCHIVE_DIR / year / month / xml_path.stem
    invoice_dir.mkdir(parents=True, exist_ok=True)

    archived_xml = invoice_dir / "invoice.xml"
    shutil.copy2(xml_path, archived_xml)

    archived_pdf = None
    if pdf_path:
        pdf_path = Path(pdf_path)
        if pdf_path.exists():
            archived_pdf = invoice_dir / "preview.pdf"
            shutil.copy2(pdf_path, archived_pdf)

    if response is None:
        response = {}

    if metadata is None:
        metadata = {}

    metadata_out = {
        "filename": xml_path.name,
        "archived_at": utc_now(),
        "env": config.KSEF_ENV,
        "xml_path": str(archived_xml),
        "pdf_path": str(archived_pdf) if archived_pdf else None,
        **metadata,
    }

    response_file = invoice_dir / "response.json"
    response_file.write_text(
        json.dumps(response, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    metadata_file = invoice_dir / "metadata.json"
    metadata_file.write_text(
        json.dumps(metadata_out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return invoice_dir