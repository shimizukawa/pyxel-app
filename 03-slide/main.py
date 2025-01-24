# title: Pyxel app 03-slide
# author: Takayuki Shimizukawa
# desc: Pyxel app 03-slide
# site: https://github.com/shimizukawa/pyxel-app
# license: MIT
# version: 1.0
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markdown-it-py",
#     "pyxel",
# ]
# ///

import asyncio
from pathlib import Path

import pyxel


TITLE = "Pyxel app 03-slide"
WIDTH = 600
HEIGHT = 360
LINE_HEIGHT = 24  # lines per page = 360/24 = 15
SPEED = 1

# The Font class only supports BDF format fonts
font_default = pyxel.Font("assets/b24.bdf")
font_bold = pyxel.Font("assets/b24_b.bdf")
font_italic = pyxel.Font("assets/b24_i.bdf")
font_bolditalic = pyxel.Font("assets/b24_bi.bdf")
font_literal = pyxel.Font("assets/b24.bdf")
FONTS = {
    "default": font_default,
    "strong": font_bold,
    "em": font_italic,
    "literal": font_literal,
}


class App:
    def __init__(self):
        self.slides = self.load_slides("slide.md")
        self.page = 0
        pyxel.init(WIDTH, HEIGHT, title=TITLE)

        # run forever
        pyxel.run(self.update, self.draw)

    def load_slides(self, filepath):
        from markdown_it import MarkdownIt

        md = MarkdownIt()
        content = Path(filepath).read_text(encoding="utf-8")
        tokens = md.parse(content)
        slides = []
        current_slide = []
        for token in tokens:
            if token.type == "heading_open" and token.tag in ["h1", "h2", "h3"]:
                current_slide = []
                slides.append(current_slide)
            current_slide.append(token)
        if current_slide:
            slides.append(current_slide)
        return slides

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.page = min((self.page + 1), len(self.slides) - 1)
        elif pyxel.btnp(pyxel.KEY_LEFT):
            self.page = max((self.page - 1), 0)

    def draw(self):
        pyxel.cls(7)
        self.draw_slide(self.slides[self.page])

    def draw_slide(self, tokens):
        visitor = Visitor(self)
        visitor.walk(tokens)


def use_font(font: str):
    def decorator(func):
        def wrapper(self, token):
            self.font_stack.append(font)
            func(self, token)
            self.font_stack.pop()

        return wrapper

    return decorator


def use_color(fg: int, bg: int):
    def decorator(func):
        def wrapper(self, token):
            self.color_stack.append((fg, bg))
            func(self, token)
            self.color_stack.pop()

        return wrapper

    return decorator


class Visitor:
    def __init__(self, app):
        self.app = app
        self.line_height = LINE_HEIGHT
        self.x = LINE_HEIGHT // 2  # 初期padding
        self.y = LINE_HEIGHT // 2  # 初期padding
        self.indent_stack = [self.x]
        self.font_stack = ["default"]
        self.color_stack = [(0, -1)]
        self.section_level = 0

    @property
    def color(self):
        return self.color_stack[-1][0]

    @property
    def bgcolor(self):
        return self.color_stack[-1][1]

    @property
    def font(self):
        return FONTS[self.font_stack[-1]]

    def _text(self, text):
        w = self.font.text_width(text)
        if self.bgcolor >= 0:
            pyxel.rect(self.x, self.y, w, self.line_height, self.bgcolor)
        pyxel.text(self.x, self.y, text, self.color, self.font)
        self.x += w

    def _crlf(self):
        # carriage return
        self.x = self.indent_stack[-1]
        # line feed
        self.y += self.line_height

    def _indent(self, indent):
        self.x += indent
        self.indent_stack.append(self.x)

    def _dedent(self):
        dedent = self.indent_stack.pop() - self.indent_stack[-1]
        self.x -= dedent

    def walk(self, tokens):
        for token in tokens:
            self.visit(token)
            if token.children:
                self.walk(token.children)
            self.depart(token)

    def visit(self, token):
        method_name = f"visit_{token.type}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(token)
        else:
            print("visit", token.type)

    def depart(self, token):
        method_name = f"depart_{token.type}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(token)

    def visit_heading_open(self, token):
        if token.tag == "h1":
            self.section_level = 1
            # TODO: タイトルは大きくセンタリング、本文はセンタリング
            self._text("# ")
        elif token.tag == "h2":
            self.section_level = 2
            # TODO: タイトルは中くらいでセンタリング、本文はセンタリング
            self._text("## ")
        elif token.tag == "h3":
            # TODO: タイトルは上部左寄せ、本文は左寄せ
            self.section_level = 3
            self._text("### ")

    def visit_heading_close(self, token):
        self._crlf()
        self._crlf()

    def visit_text(self, token):
        self._text(token.content)

    def visit_bullet_list_open(self, token):
        self._indent(LINE_HEIGHT // 2)
        self.y += self.line_height // 10

    def visit_bullet_list_close(self, token):
        self.y += self.line_height // 10
        self._dedent()

    def visit_list_item_open(self, token):
        self._text("・")

    def visit_list_item_close(self, token):
        pass

    def visit_paragraph_open(self, token):
        pass

    def visit_paragraph_close(self, token):
        self.y += self.line_height // 10 * 2
        self._crlf()

    def visit_em_open(self, token):
        self.color_stack.append((3, -1))
        self.font_stack.append("em")

    def visit_em_close(self, token):
        self.font_stack.pop()
        self.color_stack.pop()

    def visit_strong_open(self, token):
        self.color_stack.append((4, -1))
        self.font_stack.append("strong")

    def visit_strong_close(self, token):
        self.font_stack.pop()
        self.color_stack.pop()

    def visit_inline(self, token):
        pass

    @use_font("literal")
    @use_color(1, 6)
    def visit_code_inline(self, token):
        self._text(token.content)

    @use_font("literal")
    @use_color(7, -1)
    def visit_fence(self, token):
        hls = [self.font.text_width(line) for line in token.content.splitlines()]
        w = LINE_HEIGHT + max(hls)
        h = LINE_HEIGHT + len(hls) * LINE_HEIGHT
        pyxel.rect(self.x, self.y, w, h, 0)

        self._indent(LINE_HEIGHT // 2)
        self.y += LINE_HEIGHT // 2
        for line in token.content.splitlines():
            self._text(line)
            self._crlf()
        self._dedent()

    def visit_hardbreak(self, token):
        self._crlf()


# micropipがasync/awaitを要求するため
async def main():
    try:
        import micropip
    except ImportError:
        micropip = None

    if micropip:
        print("Installing ...")
        await micropip.install("markdown-it-py")
        print("installed successfully")

    App()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Pyodide上では用意されているイベントループを使って実行
        asyncio.ensure_future(main())
    else:
        # ローカルの場合はあらたにイベントループで実行
        asyncio.run(main())
