import json
from pathlib import Path
from datetime import datetime, timezone

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def utc_now():
    return datetime.now(timezone.utc).isoformat()