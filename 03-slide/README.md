# MDスライド表示

Markdownで書いたスライドをPyxelで表示します。

- 日本語表示対応
- 対応している記法
  - ヘディング1 = スライドタイトル
  - ヘディング2 = 各ページタイトル
  - 番号なし箇条書き
  - 番号付き箇条書き
  - **強調**
  - *斜体*
  - `literal`
  - URL link
  - コードフェンス（+ハイライト）
  - 画像読み込み ( `{figure} file.png` )
  - Pyxel App 読み込み ( `{figure} file.py` )

## アプリ起動

```shell
uv run main.py
```

## 操作

- 移動:
  - スペース: 次のスライド
  - シフト+スペース: 前のスライド
  - 下: セクション内の次スライド
  - 上: セクション内の前スライド
  - 右: 次のセクション
  - 左: 前のセクション
- リロード: Ctrl+R
- 終了: Ctrl+Q
