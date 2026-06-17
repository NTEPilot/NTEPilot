# NTEPilot

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a> · <a href="README_JA.md">日本語</a> · <a href="README_TW.md">繁體中文</a>
</p>

<p>
  <img src="https://count.getloli.com/@NTEPilot?name=NTEPilot&theme=moebooru" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vite-7.2-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-green?style=flat-square" alt="License">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/ADB-対応-4CAF50?style=flat-square" alt="ADB">
  <img src="https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/ONNX-推論-005CED?style=flat-square" alt="ONNX">
  <img src="https://img.shields.io/badge/WebSocket-リアルタイム-FF6F00?style=flat-square" alt="WebSocket">
</p>

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEPilot&theme=dark)](https://github.com/NTEPilot/NTEPilot)

---

## 概要

NTEPilot は『異環（Ering）』専用に設計された自動化ツールです。ADB を使って Android エミュレータに接続し、 various なゲーム操作を自動実行します。フロントエンドとバックエンドを分離したアーキテクチャを採用しており、バックエンドは Python + FastAPI でコアロジックを処理し、フロントエンドは React + TypeScript でモダンな制御パネルを構築、WebSocket でリアルタイム双方向通信を実現します。

## 機能モジュール

<table>
  <tr>
    <td width="50%">
      <h3>釣り自動化</h3>
      <ul>
        <li>緑色プログレスバーのリアルタイム追跡</li>
        <li>カーソル位置の自動制御</li>
        <li>エサの自動購入</li>
        <li>魚の自動販売</li>
        <li>安全比率の閾値設定</li>
      </ul>
    </td>
    <td width="50%">
      <h3>チーム管理</h3>
      <ul>
        <li>17キャラクター対応</li>
        <li>E/Q スキルクールダウン自動管理</li>
        <li>スキルローテーション順序の設定</li>
        <li>4人パーティ編成</li>
        <li>キャラクター自動認識マッピング</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>戦闘システム</h3>
      <ul>
        <li>自動戦闘制御</li>
        <li>スキル発動管理</li>
        <li>戦闘状態認識</li>
        <li>自動リトライ機構</li>
      </ul>
    </td>
    <td width="50%">
      <h3>デイリータスク</h3>
      <ul>
        <li>毎日タスク自動化</li>
        <li>カフェインタラクション</li>
        <li>絆システム処理</li>
        <li>ハウス管理</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>画面認識</h3>
      <ul>
        <li>OpenCV テンプレートマッチング</li>
        <li>ゲーム UI 要素の自動検出</li>
        <li>OCR 文字認識（ONNX）</li>
        <li>高精度画像処理</li>
      </ul>
    </td>
    <td width="50%">
      <h3>ページナビゲーション</h3>
      <ul>
        <li>A* 経路探索アルゴリズム</li>
        <li>自動 UI スイッチング</li>
        <li>マップ位置テレポート</li>
        <li>スマート経路計画</li>
      </ul>
    </td>
  </tr>
</table>

## システム要件

<table>
  <tr>
    <td><strong>OS</strong></td>
    <td>Windows 10/11</td>
  </tr>
  <tr>
    <td><strong>Python</strong></td>
    <td>3.14 以上</td>
  </tr>
  <tr>
    <td><strong>Node.js</strong></td>
    <td>18 以上（開発のみ）</td>
  </tr>
  <tr>
    <td><strong>ADB</strong></td>
    <td>Android Debug Bridge</td>
  </tr>
  <tr>
    <td><strong>エミュレータ</strong></td>
    <td>LDPlayer、MuMu、BlueStacks などの Android エミュレータ</td>
  </tr>
</table>

> **なぜエミュレータを使うの？** デスクトップクライアントでスクリプトを実行すると、ゲームウィンドウをフォアグラウンドに維持する必要があります — 実行中はマウスやキーボードを触れない状態になります。エミュレータを使いましょう。

## クイックスタート

ワンクリックランチャーを使うこともできます：

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEP-Launcher)](https://github.com/NTEPilot/NTEP-Launcher)

### 1. リポジトリのクローン

```powershell
git clone https://github.com/NTEPilot/NTEPilot.git
cd NTEPilot
```

### 2. バックエンド依存関係のインストール

```powershell
uv sync
```

### 3. フロントエンド依存関係のインストール

```powershell
cd frontend
npm install
cd ..
```

### 4. フロントエンドのビルド

```powershell
cd frontend
npm run build
cd ..
```

ビルド成果物は `frontend/.static` に出力され、バックエンド起動時に自動的に提供されます。

### 5. サービスの起動

```powershell
uv run main.py
```

http://127.0.0.1:9150/ にアクセスして制御パネルを開きます。

### 6. エミュレータの設定

制御パネルの「一般設定」で ADB デバイスシリアル番号を入力します。例：`127.0.0.1:16448`（エミュレータによってポートが異なります）。

## アーキテクチャ

<table>
  <tr>
    <th width="20%">レイヤー</th>
    <th width="40%">技術スタック</th>
    <th width="40%">説明</th>
  </tr>
  <tr>
    <td><strong>フロントエンド</strong></td>
    <td>React 19 + TypeScript + Vite 7</td>
    <td>Material Design 3、動的設定フォームレンダリング</td>
  </tr>
  <tr>
    <td><strong>バックエンド</strong></td>
    <td>Python 3.14 + FastAPI + Uvicorn</td>
    <td>非同期 WebSocket サービス、プラグイン型ツールシステム</td>
  </tr>
  <tr>
    <td><strong>通信</strong></td>
    <td>WebSocket JSON プロトコル</td>
    <td>リアルタイム双方向通信、ログストリーミング & ステータスプッシュ</td>
  </tr>
  <tr>
    <td><strong>画像処理</strong></td>
    <td>OpenCV 4.13 + ONNX Runtime</td>
    <td>テンプレートマッチング、OCR 推論、画像前処理</td>
  </tr>
  <tr>
    <td><strong>デバイス</strong></td>
    <td>ADB + DroidCast + minitouch</td>
    <td>デバイス接続、スクリーンショットキャプチャ、タッチ入力</td>
  </tr>
</table>

## 開発モード

フロントエンドとバックエンドを同時に実行：

```powershell
# ターミナル 1：バックエンド起動
uv run main.py

# ターミナル 2：フロントエンド開発サーバー起動
cd frontend
npm run dev
```

http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws にアクセス

フロントエンドのみの開発には、内蔵の mock WebSocket サーバーを使用：

```powershell
# ターミナル 1：mock サーバー起動
cd frontend
npm run mock:server

# ターミナル 2：フロントエンド起動
npm run dev
```

## プロジェクト構成

```
NTEPilot/
├── main.py                     # アプリケーションエントリーポイント
├── pyproject.toml              # Python プロジェクト設定
│
├── api/                        # WebSocket API サービス
│   ├── server.py               # FastAPI アプリ & WebSocket エンドポイント
│   ├── scheduler.py            # デイリースケジューラー
│   └── task_runner.py          # スレッド化タスクエグゼキューター
│
├── NTEPilot/                   # コアビジネスロジック
│   ├── config/                 # 設定システム
│   ├── device/                 # Android デバイスインタラクション層
│   ├── tools/                  # ツール実装（fish/combat/bond/cafe/daily/house）
│   ├── team/                   # キャラクター / チーム管理
│   ├── ui/                     # 画面自動化層
│   ├── map/                    # マップナビゲーション
│   ├── ocr.py                  # OCR 文字認識
│   └── instance.py             # インスタンス管理
│
├── template/                   # テンプレート画像アセット
│   ├── fish/                   # 釣りテンプレート
│   ├── control/                # 戦闘制御テンプレート
│   └── ui/                     # 汎用 UI テンプレート
│
├── frontend/                   # React フロントエンド
│   ├── src/
│   │   ├── App.tsx             # メインインターフェース
│   │   ├── components/         # UI コンポーネント
│   │   ├── lib/                # Hooks
│   │   └── types/              # TypeScript 型定義
│   └── vite.config.ts          # Vite 設定
│
├── bin/                        # バイナリ依存関係
│   ├── DroidCast/              # スクリーンショット APK
│   └── Minitouch/              # タッチツール
│
├── instances/                  # ランタイムインスタンス設定
└── logs/                       # ランタイムログ
```

## 設定システム

パス形式のキーとネストされた JSON を使用：

```json
{
  "general": {
    "name": "NTE",
    "serial": "127.0.0.1:16448"
  },
  "tools": {
    "fish": {
      "sell_fish": true,
      "buy_bait": true
    }
  }
}
```

コード内では `config["tools.fish.buy_bait"]` でアクセス。

## 対応キャラクター

| 中国語名 | 英語名 | E クールダウン | Q クールダウン |
|---------|--------|-------------|--------------|
| 零 | Zero | 16s | 15s |
| 早雾 | Sakiri | 16s | 20s |
| 九原 | Jiuyuan | 16s | 15s |
| 哈索尔 | Hathor | 16s | 15s |
| 法帝娅 | Fadia | 16s | 20s |
| 达芙蒂尔 | Daffodill | 16s | 20s |
| 白藏 | Baicang | 14s | 20s |
| 小吱 | Chiz | 3s | 15s |
| 阿德勒 | Adler | 16s | 20s |
| 海月 | Aurelia | 15s | 15s |
| 埃德嘉 | Edgar | 16s | 20s |
| 哈尼娅 | Haniel | 20s | 20s |
| 薄荷 | Mint | 6s | 15s |
| 翳 | Skia | 15s | 15s |
| 娜娜莉 | Nanally | 16s | 15s |
| 浔 | Hotori | 16s | 0s |
| 安魂曲 | Lacrimosa | 16s | 20s |

## 設定パラメータ

### 一般設定

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `general.name` | text | インスタンス名 |
| `general.serial` | text | ADB デバイスシリアル番号 |
| `general.client` | select | クライアントタイプ：異環 / クラウド異環 |

### 釣り設定

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|---------|------|
| `tools.fish.sell_fish` | boolean | true | インベントリ満杯時に魚を自動販売 |
| `tools.fish.buy_bait` | boolean | true | エサ切れ時に自動購入 |
| `tools.fish.buy_bait_stack_count` | number | 5 | 1回の購入エサスタック数（1-20） |
| `tools.fish.green_bar_safe_proportion` | number | 0.4 | 緑バー安全比率（0-1） |

### チーム設定

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `team.chara_1` ~ `team.chara_4` | text | パーティ内のキャラクター名 |
| `team.skill_order` | text | スキルローテーション順序（例：`1E>2E>3E>4E>1A`） |

スキルローテーション形式：`<キャラクター番号><スキルタイプ>`、キャラクター 1-4、スキルタイプ E/Q/A。

## 開発ガイド

### 新しいツールの追加

1. 対応する runner クラスを作成し、タスクロジックを実装
2. `NTEPilot/config/framework.py` でタスク、runner、フィールド、デフォルト値を登録

フロントエンドは新しいツールを自動検出して表示するため、フロントエンドの変更は不要です。

### 新しいキャラクターの追加

`NTEPilot/team/character.py` で：

```python
class NewChara(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)

CHINESE_TO_CHARA['新角色'] = NewChara
```

### テンプレート画像の更新

`template/` ディレクトリに PNG ファイルを追加・削除した後、モジュールインデックスを再生成：

```powershell
python template/update.py
```

## 関連ドキュメント

- [DEV.md](DEV.md) — プロジェクト開発ドキュメント & モジュールインデックス
- [dev_doc/](dev_doc/) — 詳細開発ドキュメント

## ライセンス

このプロジェクトは [GNU Affero General Public License v3.0](LICENSE) でライセンスされています。

## コントリビューター

<a href="https://github.com/NTEPilot/NTEPilot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=NTEPilot/NTEPilot" />
</a>
