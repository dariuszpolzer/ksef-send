from pathlib import Path
import xml.etree.ElementTree as ET


def validate_xml_basic(xml_path: Path) -> dict:
    xml_path = Path(xml_path)

    result = {
        "file": str(xml_path),
        "ok": True,
        "errors": [],
        "warnings": [],
        "root_tag": None,
    }

    if not xml_path.exists():
        result["ok"] = False
        result["errors"].append("Plik XML nie istnieje.")
        return result

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        result["root_tag"] = root.tag

        if "Faktura" not in root.tag:
            result["warnings"].append(
                f"Nietypowy root tag XML: {root.tag}"
            )

    except ET.ParseError as e:
        result["ok"] = False
        result["errors"].append(f"Błąd parsowania XML: {e}")

    return result


def validate_pending_directory(pending_dir: Path) -> dict:
    pending_dir = Path(pending_dir)

    files = sorted(pending_dir.glob("*.xml"))
    results = []

    for xml_file in files:
        results.append(validate_xml_basic(xml_file))

    return {
        "pending_dir": str(pending_dir),
        "count": len(files),
        "valid_count": sum(1 for r in results if r["ok"]),
        "invalid_count": sum(1 for r in results if not r["ok"]),
        "results": results,
    }