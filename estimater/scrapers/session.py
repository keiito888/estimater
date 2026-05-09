"""ブラウザセッション（ログイン状態）の保存と読み込み"""

import json
from pathlib import Path

SESSION_DIR = Path(__file__).parent.parent.parent / "credentials"
MISUMI_SESSION_FILE = SESSION_DIR / "misumi_session.json"
MONOTARO_SESSION_FILE = SESSION_DIR / "monotaro_session.json"

MISUMI_LOGIN_URL = "https://jp.misumi-ec.com/mypage/login/"
MONOTARO_LOGIN_URL = "https://www.monotaro.com/logout.html"


def save_misumi_session(storage_state: dict) -> None:
    SESSION_DIR.mkdir(exist_ok=True)
    MISUMI_SESSION_FILE.write_text(json.dumps(storage_state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_misumi_session() -> dict | None:
    if MISUMI_SESSION_FILE.exists():
        try:
            return json.loads(MISUMI_SESSION_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def has_misumi_session() -> bool:
    return MISUMI_SESSION_FILE.exists() and MISUMI_SESSION_FILE.stat().st_size > 100
