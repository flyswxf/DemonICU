from pathlib import Path
from typing import ByteString
from .. import constants as C


def ensure_dirs() -> None:
    C.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def ensure_feedback_dirs() -> None:
    C.FEEDBACK_RESULT_DIR.mkdir(parents=True, exist_ok=True)


def save_feedback_text(text: str) -> Path:
    """Save user augmentation text into feedback response.txt."""
    ensure_feedback_dirs()
    with open(C.FEEDBACK_RESPONSE_TXT, "w", encoding="utf-8") as f:
        f.write(text or "")
    return C.FEEDBACK_RESPONSE_TXT


def save_patient(session_id: str, raw_json: ByteString) -> Path:
    ensure_dirs()
    path = C.UPLOAD_DIR / f"{session_id}.json"
    with open(path, "wb") as f:
        f.write(raw_json)
    return path