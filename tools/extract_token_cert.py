import base64
import json
from pathlib import Path


INPUT = Path("public_keys.json")
OUTPUT = Path("keys/ksef_public_key.pem")


def wrap_pem(b64: str, title: str = "CERTIFICATE") -> str:
    lines = [b64[i:i + 64] for i in range(0, len(b64), 64)]
    return f"-----BEGIN {title}-----\n" + "\n".join(lines) + f"\n-----END {title}-----\n"


data = json.loads(INPUT.read_text(encoding="utf-8"))

selected = None

for item in data:
    usage = item.get("usage", [])
    if "KsefTokenEncryption" in usage:
        selected = item
        break

if not selected:
    raise RuntimeError("Nie znaleziono certyfikatu KsefTokenEncryption")

cert_b64 = selected["certificate"]

# sprawdzenie, czy Base64 jest poprawne
base64.b64decode(cert_b64)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(wrap_pem(cert_b64), encoding="utf-8")

print("Zapisano:", OUTPUT)
print("validFrom:", selected.get("validFrom"))
print("validTo:", selected.get("validTo"))
print("usage:", selected.get("usage"))