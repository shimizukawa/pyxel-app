# Pyxel 実装練習

各ディレクトリのREADMEにプログラム固有の説明があります。

## デモ

- https://shimizukawa.github.io/pyxel-app/

## 実行

以下は、共通の起動方法など。

### 環境準備と実行

事前にuvをインストールしておきます。Python等は不要。
https://docs.astral.sh/uv/getting-started/installation/


### アプリ起動

各ディレクトリに移動して、main.pyを実行します。

```shell
cd 01-circle
uv run main.py
```

### アプリのHTML化とブラウザでの実行

ブラウザで実行できるようにします。

```shell
uv run make.py
uv run python -m http.server
```

これで表示されるURLをブラウザで開いて、拡張子が `.html` ファイルを開いてください。
