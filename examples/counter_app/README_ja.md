# カウンターアプリ サンプル

Sui + WebAssembly + HTML/JS の統合を示すシンプルなカウンターアプリケーション。

## クイックスタート

**⚠️ 注意: `index.html` を直接開く（`file://`）とCORS制限で動作しない。ローカルサーバーを使う必要がある。**

```bash
# 1. このディレクトリに移動
cd examples/counter_app

# 2. ローカルサーバーを起動
python -m http.server 8080

# 3. ブラウザで開く
open http://localhost:8080
```

`logic.wasm` はコンパイル済みで同梱されている。ビルド不要。

## ファイル

| ファイル | 説明 |
|----------|------|
| `logic.sui` | Suiソースコード |
| `logic.wasm` | コンパイル済みWebAssembly（同梱） |
| `index.html` | UI（vanilla JS） |

## 再ビルド（オプション）

`logic.sui` を変更した場合は再コンパイル：

```bash
sui2wasm logic.sui -o logic.wasm
```

必要なツール: `brew install wabt`

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐
│   index.html    │────▶│   logic.wasm    │
│   (UIレイヤー)   │     │   (Suiロジック)  │
└─────────────────┘     └─────────────────┘
        │                       │
        │   f0() インクリメント   │
        │   f1() デクリメント     │
        │   f2() リセット        │
        │   g0   状態           │
        └───────────────────────┘
```

## Wasmエクスポート

| エクスポート | 型 | 説明 |
|-------------|-----|------|
| `g0` | Global | カウンター状態（`.value`で読み取り） |
| `f0()` | Function | インクリメント |
| `f1()` | Function | デクリメント |
| `f2()` | Function | 0にリセット |
| `main()` | Function | 初期化 |

