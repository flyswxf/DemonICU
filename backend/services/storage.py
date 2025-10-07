from pathlib import Path
from typing import ByteString
from .. import constants as C


def ensure_dirs() -> None:
    C.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_patient(session_id: str, raw_json: ByteString) -> Path:
    ensure_dirs()
    path = C.UPLOAD_DIR / f"{session_id}.json"
    with open(path, "wb") as f:
        f.write(raw_json)
    return path