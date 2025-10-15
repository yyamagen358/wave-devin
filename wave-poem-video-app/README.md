# 無条件の波動 - 詩の自動動画生成システム

詩のテキストファイルから自動的に動画を生成するWebアプリケーションです。

## 機能

- 詩のテキストファイルから自動動画生成
- トップページ：「無条件の波動」タイトル + 詩のタイトル表示
- 各段落を個別のスライドとして表示（1行14文字、中央配置）
- 最終ページ：全文をロールアップ表示
- 背景画像：9:16縦型のランダム選択
- BGM：フェードイン/アウト付き
- 単一生成モード
- バッチ生成モード（複数動画を一度に生成）
- 動画ダウンロード機能

## 技術スタック

### バックエンド
- FastAPI
- Python 3.12
- MoviePy (動画生成)
- Pillow (画像処理)

### フロントエンド
- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Lucide Icons

## セットアップ

### バックエンド

```bash
cd backend

# 依存関係のインストール
poetry install

# データディレクトリの準備
mkdir -p data/poem data/poem_used data/images data/bgm data/videos

# 詩ファイルを data/poem/ に配置
# 画像ファイル（9:16縦型）を data/images/ に配置
# BGMファイルを data/bgm/bgm_poem.mp3 として配置

# サーバー起動
poetry run fastapi dev app/main.py --port 8000
```

### フロントエンド

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数の設定
echo "VITE_API_URL=http://localhost:8000" > .env

# サーバー起動
npm run dev
```

ブラウザで http://localhost:5173 にアクセス

## ディレクトリ構造

```
backend/
  app/
    main.py                 # FastAPI アプリケーション
    poem_manager.py        # 詩ファイル管理
    video_generator.py     # 動画生成エンジン
  data/
    poem/                  # 未使用の詩ファイル
    poem_used/             # 使用済みの詩ファイル
    images/                # 背景画像（9:16）
    bgm/                   # BGMファイル
    videos/                # 生成された動画

frontend/
  src/
    App.tsx               # メインアプリケーション
    components/           # UIコンポーネント
```

## API エンドポイント

- `GET /api/poems/available` - 利用可能な詩の数を取得
- `POST /api/generate/single` - 単一動画生成
- `POST /api/generate/batch` - バッチ動画生成
- `GET /api/status/{task_id}` - 生成状況確認
- `GET /api/videos` - 生成済み動画一覧
- `GET /api/videos/{filename}` - 動画ダウンロード

## 使用方法

1. 詩ファイル（.txt）を `backend/data/poem/` に配置
2. 画像ファイル（9:16縦型）を `backend/data/images/` に配置
3. BGMファイルを `backend/data/bgm/bgm_poem.mp3` として配置
4. Webインターフェースで「生成開始」をクリック
5. 生成が完了したら動画をダウンロード

## 詩ファイルフォーマット

```
《タイトル1》

「タイトル2」

段落1の内容
複数行可能

段落2の内容
複数行可能
```

## 注意事項

- 動画生成には時間がかかります（1動画あたり約30-60秒）
- 使用済みの詩ファイルは自動的に `poem_used/` に移動されます
- 動画は `data/videos/` に保存されます
