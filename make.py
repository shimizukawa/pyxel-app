# 数字で始まる各ディレクトリについて以下を実行する
# uvx pyxel package <ディレクトリ名> <ディレクトリ名>/main.py
# uvx pyxel app2html <ディレクトリ名>

import subprocess
from pathlib import Path


# 任意のディレクトリに対して以下を実行する
def process_directory(directory):
    subprocess.run(["uvx", "pyxel", "package", directory, f"{directory}/main.py"])
    subprocess.run(["uvx", "pyxel", "app2html", directory])
    # <directory>.html と <directory>.pyxapp を dist に移動
    Path(f"{directory}.html").replace(f"dist/{directory}.html")
    Path(f"{directory}.pyxapp").replace(f"dist/{directory}.pyxapp")


def main():
    Path("./dist").mkdir(exist_ok=True, parents=True)
    # 数字で始まるサブディレクトリを処理
    for directory in Path(".").glob("[0-9][0-9]-*"):
        if directory.is_dir():
            process_directory(str(directory))


if __name__ == "__main__":
    main()
