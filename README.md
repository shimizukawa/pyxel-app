# Pyxel 実装練習

事前にuvをインストールしておく。Python等は不要。
https://docs.astral.sh/uv/getting-started/installation/


## アプリ起動

プログラムをコマンドラインから実行します。

```shell
uv run hello.py
```
これで操作できます。

- 移動: 上下左右キー
- 加速: スペース（移動と組み合わせ可能）
- 終了: ESC, Q

## アプリのHTML化とブラウザでの実行

ブラウザで実行できるようにします。

```shell
uvx pyxel package  . hello.py
uvx pyxel app2html  . sample1.pyxapp
uv run python http.server
```

これで表示されるURLをブラウザで開いて、sample1.html を開いてください。

## マルチプレイサーバーの実行

サーバーを起動しておくと、複数のアプリから接続して同時プレイができます。

```shell
uv run server.py
```
