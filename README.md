# estimater — 制御盤向け電気部品 自動見積もりツール

Googleスプレッドシートに型番・数量を記入するだけで、Misumi/MonotaROから価格を自動取得し、見積書シートに書き込みます。

## 必要なもの

- Python 3.11 以上 (`py` コマンド)
- Google アカウント
- GCP サービスアカウント (無料)

---

## セットアップ手順

### 1. パッケージのインストール

```powershell
cd c:\Users\keiit\src\estimater
py -m pip install -e .
playwright install chromium
```

### 2. GCP サービスアカウントの作成

1. [GCP コンソール](https://console.cloud.google.com/) を開く
2. プロジェクトを作成 (または既存のものを選択)
3. **APIとサービス** → **有効なAPI** → 以下を有効化
   - Google Sheets API
   - Google Drive API
4. **IAM と管理** → **サービスアカウント** → **作成**
5. キーを作成 (JSON) → ダウンロード
6. ダウンロードしたファイルを `credentials/service_account.json` に配置

### 3. Googleスプレッドシートの準備

1. [Googleスプレッドシート](https://sheets.google.com) で新規スプレッドシートを作成
2. URLから `SPREADSHEET_ID` をコピー  
   例: `https://docs.google.com/spreadsheets/d/`**`1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms`**`/edit`
3. スプレッドシートを **サービスアカウントのメールアドレスと共有** (編集権限)  
   サービスアカウントのメールは `credentials/service_account.json` 内の `client_email` フィールドで確認できます

### 4. 環境変数の設定

```powershell
copy .env.example .env
```

`.env` を編集:

```
SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_CREDENTIALS_PATH=credentials/service_account.json
HEADLESS=true
```

### 5. 初期セットアップ実行

```powershell
py -m estimater setup
```

スプレッドシートに「入力」「見積書」「キャッシュ」「設定」の4シートが作成されます。

---

## 使い方

### 見積もりを実行する

1. スプレッドシートの「入力」シートに部品を入力:

| 部品種別 | メーカー | 型番 | 数量 | 仕入先希望 | 備考 |
|---|---|---|---|---|---|
| 遮断器 | 三菱電機 | NF30-CS 3P 5A | 2 | misumi | 主幹 |
| 電磁接触器 | 富士電機 | SC-N1 | 4 | monotaro | |

2. コマンドを実行:

```powershell
py -m estimater run
```

3. 「見積書」シートに結果が書き込まれます。

### オプション

```powershell
# ブラウザを表示しながら実行 (デバッグ用)
py -m estimater run --no-headless

# キャッシュを無視して全件再取得
py -m estimater run --no-cache

# キャッシュをクリア
py -m estimater cache-clear

# 別のスプレッドシートを指定
py -m estimater run --sheet <SPREADSHEET_ID>
```

---

## 注意事項

- Misumi・MonotaROの**利用規約では自動アクセスは禁止**されています。本ツールの使用はご自身の判断と責任で行ってください。
- サイトの構成変更により価格取得が失敗した場合、セルに「要確認」と表示されます。その場合は手動で単価を入力してください。
- `credentials/service_account.json` は **絶対にGitにコミットしないでください**。`.gitignore` で除外済みです。

---

## ディレクトリ構成

```
estimater/
├── estimater/
│   ├── cli.py              # CLIエントリーポイント
│   ├── config.py           # 設定管理
│   ├── models.py           # データモデル
│   ├── scrapers/
│   │   ├── engine.py       # 価格取得エンジン統合
│   │   ├── misumi.py       # Misumiスクレイパー
│   │   └── monotaro.py     # MonotaROスクレイパー
│   └── sheets/
│       ├── client.py       # Sheets APIクライアント
│       ├── reader.py       # 入力シート読み込み
│       ├── writer.py       # 見積書シート書き込み
│       ├── cache.py        # キャッシュシート管理
│       └── setup.py        # 初期セットアップ
├── credentials/            # サービスアカウントキー (gitignore)
├── .env                    # 環境変数 (gitignore)
├── .env.example            # 環境変数テンプレート
├── pyproject.toml
└── README.md
```
