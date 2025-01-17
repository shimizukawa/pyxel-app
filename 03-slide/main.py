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
#     "pyxel-universal-font",
# ]
# ///

from pathlib import Path

import PyxelUniversalFont as puf  # noqa
from markdown_it import MarkdownIt
import pyxel

TITLE = "Pyxel app 03-slide"
WIDTH = 800
HEIGHT = 450
LINES_PER_PAGE = 15
SPEED = 1

# Font alias
WRITERS = puf.get_writers()
WRITERS["mincho"] = WRITERS["IPA_Mincho.ttf"]
WRITERS["pmincho"] = WRITERS["IPA_PMincho.ttf"]
WRITERS["gothic"] = WRITERS["IPA_Gothic.ttf"]
WRITERS["pgothic"] = WRITERS["IPA_PGothic.ttf"]
WRITERS["em"] = WRITERS["IPA_PGothic.ttf"]
WRITERS["strong"] = WRITERS["IPA_Gothic.ttf"]
WRITERS["literal"] = WRITERS["misaki_gothic.ttf"]


class App:
    def __init__(self):
        self.slides = self.load_slides("slide.md")
        self.page = 0
        pyxel.init(WIDTH, HEIGHT, title=TITLE)

        # run forever
        pyxel.run(self.update, self.draw)

    def load_slides(self, filepath):
        content = Path(filepath).read_text(encoding="utf-8")
        md = MarkdownIt()
        tokens = md.parse(content)
        slides = []
        current_slide = []
        for token in tokens:
            if token.type == "heading_open" and token.tag in ["h1", "h2"]:
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


def get_hl(text: str):
    """half length: 半角文字数を返す"""
    import unicodedata

    w = 0
    for c in text:
        x = unicodedata.east_asian_width(c)
        if x in "WFA":
            w += 2
        else:
            w += 1
    return w


class Visitor:
    def __init__(self, app):
        self.app = app
        self.line_height = HEIGHT // LINES_PER_PAGE
        self.y = self.line_height // 2
        self.indent_stack = [self.line_height]
        self.line_pos = 0
        self.size_stack = [int(self.line_height * 0.8)]
        self.font_stack = ["pgothic"]
        self.color_stack = [(0, -1)]

    @property
    def x(self):
        indent = self.indent_stack[-1]
        return indent + self.size // 2 * self.line_pos

    @property
    def size(self):
        return self.size_stack[-1]

    @property
    def color(self):
        return self.color_stack[-1][0]

    @property
    def bgcolor(self):
        return self.color_stack[-1][1]

    @property
    def draw(self):
        return WRITERS[self.font_stack[-1]].draw

    def _text(self, text):
        hl = get_hl(text)
        if self.bgcolor >= 0:
            pyxel.rect(self.x, self.y, hl * self.size // 2, self.size, self.bgcolor)
        self.draw(self.x, self.y, text, self.size, self.color)
        self.line_pos += hl

    def _crlf(self):
        # carriage return
        self.line_pos = 0
        # line feed
        self.y += self.size

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
            self.size_stack.append(int(self.line_height * 2.0))
            self._text("#")
        elif token.tag == "h2":
            self.size_stack.append(int(self.line_height * 1.3))
            self._text("##")

    def visit_heading_close(self, token):
        self._crlf()
        self._crlf()
        self.size_stack.pop()

    def visit_text(self, token):
        self._text(token.content)

    def visit_bullet_list_open(self, token):
        self.indent_stack.append(self.indent_stack[-1] + self.size // 2)
        self.y += self.line_height // 10

    def visit_bullet_list_close(self, token):
        self.y += self.line_height // 10
        self.indent_stack.pop()

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
        hls = [get_hl(line) for line in token.content.splitlines()]
        half = self.size // 2  # half size
        w = self.size + max(hls) * half
        h = self.size + len(hls) * self.size
        pyxel.rect(self.x, self.y, w, h, 0)

        self.indent_stack.append(self.indent_stack[-1] + half)
        self.y += half
        for line in token.content.splitlines():
            self._text(line)
            self._crlf()

        self.indent_stack.pop()


App()
