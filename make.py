# 数字で始まる各ディレクトリについて以下を実行する
# uvx pyxel package <ディレクトリ名> <ディレクトリ名>/main.py
# uvx pyxel app2html <ディレクトリ名>

import subprocess
from pathlib import Path
import shutil


# 任意のディレクトリに対して以下を実行する
def process_directory(directory: Path):
    shutil.rmtree(directory / "__pycache__", ignore_errors=True)
    shutil.rmtree(directory / "assets" / "__pycache__", ignore_errors=True)
    shutil.rmtree(directory / "_build", ignore_errors=True)
    subprocess.run(["uvx", "pyxel", "package", directory, directory / "main.py"])
    Path(f"{directory}.pyxapp").replace(f"dist/{directory}.pyxapp")
    with Path("template.html").open("r") as f:
        template = f.read()
        Path(f"dist/{directory}.html").write_text(
            template.format(packagename=str(directory))
        )
    # assetsをコピー
    if Path(f"{directory}/assets").exists():
        shutil.copytree(Path(f"{directory}/assets"), "dist/assets", dirs_exist_ok=True)


def main():
    Path("./dist").mkdir(exist_ok=True, parents=True)
    # 数字で始まるサブディレクトリを処理
    for directory in Path(".").glob("[0-9][0-9]-*"):
        if directory.is_dir():
            process_directory(directory)


if __name__ == "__main__":
    main()
