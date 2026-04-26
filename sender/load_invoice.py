from pathlib import Path


def load_invoice_xml(xml_path: Path) -> str:
    xml_path = Path(xml_path)

    if not xml_path.exists():
        raise FileNotFoundError(xml_path)

    return xml_path.read_text(encoding="utf-8")