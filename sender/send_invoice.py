from pathlib import Path
import base64
import hashlib


def prepare_invoice_payload(xml_path: Path):
    xml_path = Path(xml_path)

    if not xml_path.exists():
        raise FileNotFoundError(xml_path)

    xml_bytes = xml_path.read_bytes()
    xml_text = xml_bytes.decode("utf-8")

    payload = {
        "filename": xml_path.name,
        "size_bytes": len(xml_bytes),
        "sha256": hashlib.sha256(xml_bytes).hexdigest(),
        "invoice_text": xml_text,
        "invoice_base64": base64.b64encode(xml_bytes).decode("ascii"),
    }

    return payload