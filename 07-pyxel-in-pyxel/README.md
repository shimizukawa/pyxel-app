# ナナメスクロール

背景がナナメにスクロールする子アプリ（06-diagonal相当）を、親アプリ内にApp in App的に描画。
このために、子アプリは新規作成したpyxel.Imageに対してレンダリングし、親アプリがその結果を任意の場所にbltしている。

## アプリ起動

```shell
uv run main.py
```

## 操作

- 終了: ESC
