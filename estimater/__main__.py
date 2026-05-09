import sys
import io

# Windows CP932 環境でも日本語・特殊文字が正しく表示されるよう UTF-8 に設定
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from estimater.cli import app

app()
