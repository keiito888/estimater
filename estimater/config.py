"""環境変数・設定の読み込み"""

import os
import random
import time
from pathlib import Path
from dotenv import load_dotenv

# パッケージルート (estimater/) の2階層上 = プロジェクトルートの .env を確実に読み込む
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def get_spreadsheet_id() -> str:
    sid = os.getenv("SPREADSHEET_ID", "")
    if not sid:
        raise ValueError(
            "SPREADSHEET_ID が設定されていません。.env ファイルを確認してください。"
        )
    return sid


def get_credentials_path() -> Path:
    path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/service_account.json"))
    if not path.exists():
        raise FileNotFoundError(
            f"サービスアカウントキーが見つかりません: {path}\n"
            "GCP コンソールでサービスアカウントを作成し、JSONキーを配置してください。"
        )
    return path


def is_headless() -> bool:
    return os.getenv("HEADLESS", "true").lower() == "true"


def scrape_delay() -> None:
    """スクレイピング間の待機 (ランダム)"""
    min_ms = int(os.getenv("SCRAPE_DELAY_MIN_MS", "1000"))
    max_ms = int(os.getenv("SCRAPE_DELAY_MAX_MS", "3000"))
    time.sleep(random.randint(min_ms, max_ms) / 1000)
