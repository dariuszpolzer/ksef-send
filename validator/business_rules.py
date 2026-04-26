import xml.etree.ElementTree as ET
from pathlib import Path
import config


def check_business_rules(xml_path: Path):

    result = {
        "file": str(xml_path),
        "ok": True,
        "errors": [],
        "warnings": []
    }

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

    except Exception as e:
        result["ok"] = False
        result["errors"].append(f"Błąd parsowania XML: {e}")
        return result

    nip_sprzedawcy = None

    for el in root.iter():
        tag = el.tag.lower()

        if "nipsprzedawcy" in tag:
            nip_sprzedawcy = el.text

    if not nip_sprzedawcy:
        result["warnings"].append("Brak NIP sprzedawcy w XML")

    else:
        if nip_sprzedawcy != config.NIP:
            result["errors"].append(
                f"NIP sprzedawcy ({nip_sprzedawcy}) ≠ konfiguracja ({config.NIP})"
            )

    numer = None

    for el in root.iter():
        if "numerfaktury" in el.tag.lower():
            numer = el.text

    if not numer:
        result["warnings"].append("Brak numeru faktury")

    return result