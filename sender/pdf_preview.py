import subprocess
from pathlib import Path

import config


def generate_pdf_preview(xml_path: Path) -> Path:
    xml_path = Path(xml_path).resolve()

    config.ensure_dirs()

    pdf_path = (config.PREVIEW_DIR / f"{xml_path.stem}.pdf").resolve()

    if pdf_path.exists():
        return pdf_path

    cmd = [
        "node",
        str(config.PDF_RENDER_SCRIPT),
        str(xml_path),
        str(pdf_path),
    ]

    subprocess.run(
        cmd,
        check=True,
        cwd=str(config.BASE_DIR),
    )

    if not pdf_path.exists():
        raise RuntimeError(f"PDF nie został utworzony: {pdf_path}")

    return pdf_path