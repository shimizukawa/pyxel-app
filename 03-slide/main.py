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
import time
from pathlib import Path

import pyxel


TITLE = "Pyxel app 03-slide"
MD_FILENAME = "slide.md"
# DEBUG = True
DEBUG = False

LINE_NUMS = 12  # lines per page
LINE_MARGIN_RATIO = 0.3  # フォント高さの50%
DEFAULT_LINE_HEIGHT = int(12 * (1 + LINE_MARGIN_RATIO))  # default font height 12
WINDOW_PADDING = DEFAULT_LINE_HEIGHT // 2
HEIGHT = DEFAULT_LINE_HEIGHT * LINE_NUMS
WIDTH = HEIGHT * 4 // 3
KEY_REPEAT = 1  # for 30fps
KEY_HOLD = 15  # for 30fps

# The Font class only supports BDF format fonts
font_title = pyxel.Font("assets/b16.bdf")
font_pagetitle = pyxel.Font("assets/b16_b.bdf")
font_default = pyxel.Font("assets/b12.bdf")
font_bold = pyxel.Font("assets/b12_b.bdf")
font_italic = pyxel.Font("assets/b12_i.bdf")
font_bolditalic = pyxel.Font("assets/b12_bi.bdf")
font_literal = pyxel.Font("assets/b12.bdf")
FONTS = {
    "title": font_title,
    "pagetitle": font_pagetitle,
    "default": font_default,
    "strong": font_bold,
    "em": font_italic,
    "literal": font_literal,
}
LIST_MARKERS = ["使用しない", "●", "○", "■", "▲", "▼", "★"]


class App:
    def __init__(self):
        self.slides = self.load_slides(MD_FILENAME)
        self._page = 0
        self.frame_times = [time.time()] * 30
        self.fps = 0
        self.renderd_page_nums = [None, None, None]
        self.in_transition = [0, 0, 0]  # (rate(1..0), old_page, direction)
        pyxel.init(WIDTH + WINDOW_PADDING*2, HEIGHT + WINDOW_PADDING, title=TITLE)
        pyxel.mouse(True)
        self.render_page(1)

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

    @property
    def page(self):
        return self._page
    @page.setter
    def page(self, new_page):
        old_page, self._page = self._page, new_page
        if old_page < new_page:
            self.render_page(new_page)
            self.in_transition = [1.0, old_page, 0]
        if old_page > new_page:
            self.render_page(new_page)
            self.in_transition = [1.0, old_page, 1]

    def forward(self):
        self.page = min((self.page + 1), len(self.slides) - 1)

    def backward(self):
        self.page = max((self.page - 1), 0)

    def render_page(self, page_num: int):
        """render page (page_num) to image bank
        
        0: images[0]
        1: images[1]
        2: images[2]
        3: images[0]
        ...
        p: images[p % 3]
        """
        for i in [-1, 0, 1]:
            p = page_num + i
            if p < 0 or p >= len(self.slides):
                continue
            if self.renderd_page_nums[p % 3] == p:
                continue
            tokens = self.slides[p]
            img = pyxel.images[p % 3]
            img.rect(0, 0, WIDTH, HEIGHT, 7)
            visitor = Visitor(self, img)
            visitor.walk(tokens)
            self.renderd_page_nums[p % 3] = p

    def update(self):
        self.calc_fps()

        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        key_hold = KEY_HOLD * self.fps // 30
        key_repeat = KEY_REPEAT * self.fps // 30

        if self.in_transition[0] > 0:
            self.in_transition[0] = self.in_transition[0] - 3 / self.fps

        if pyxel.btnp(pyxel.KEY_RIGHT, key_hold, key_repeat):
            self.forward()
        elif pyxel.btnp(pyxel.KEY_LEFT, key_hold, key_repeat):
            self.backward()
        elif pyxel.btnp(pyxel.KEY_SPACE, key_hold, key_repeat):
            if pyxel.btn(pyxel.KEY_SHIFT):
                self.backward()
            else:
                self.forward()

    def calc_fps(self):
        self.frame_times.append(time.time())
        self.frame_times.pop(0)
        # 10フレームごとにFPSを計算
        if pyxel.frame_count % 10:
            return
        self.fps = int(
            len(self.frame_times) / (self.frame_times[-1] - self.frame_times[0])
        )

    def draw(self):
        pyxel.cls(7)
        self.blt_slide()
        # FPSを表示
        pyxel.text(5, pyxel.height - 10, f"FPS: {self.fps}", 13)

    def blt_slide(self):
        img = pyxel.images[self.page % 3]
        if self.in_transition[0] > 0:
            rate, old_page, direction = self.in_transition
            old_img = pyxel.images[old_page % 3]
            if direction == 0:
                old_x = WINDOW_PADDING
                old_y = WINDOW_PADDING - HEIGHT * (1 - rate)
                new_x = WINDOW_PADDING
                new_y = WINDOW_PADDING + HEIGHT * rate
            elif direction == 1:
                old_x = WINDOW_PADDING
                old_y = WINDOW_PADDING + HEIGHT * (1 - rate)
                new_x = WINDOW_PADDING
                new_y = WINDOW_PADDING - HEIGHT * rate
            pyxel.blt(old_x, old_y, old_img, 0, 0, WIDTH, HEIGHT)
            pyxel.blt(new_x, new_y, img, 0, 0, WIDTH, HEIGHT)
        else:
            pyxel.blt(WINDOW_PADDING, WINDOW_PADDING, img, 0, 0, WIDTH, HEIGHT)


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
    def __init__(self, app, img):
        self.app = app
        self.img = img
        self.x = 0
        self.y = 0
        self.indent_stack = [self.x]
        self.font_stack = ["default"]
        self.color_stack = [(0, -1)]
        self.section_level = 0
        self.align = "left"
        self.list_stack = []  # 箇条書きのマーク用
        self.list_ordered_num = None  # 番号付き箇条書きの場合は1以上の数値

    @property
    def color(self):
        return self.color_stack[-1][0]

    @property
    def bgcolor(self):
        return self.color_stack[-1][1]

    @property
    def font(self):
        return FONTS[self.font_stack[-1]]

    @property
    def font_height(self):
        return self.font.text_width("あ")  # あの幅を文字の高さとする

    @property
    def list_marker(self):
        list_level = len(self.list_stack)
        list_type = self.list_stack[-1]
        if list_type == "ordered":
            return f"{self.list_ordered_num}. "
        elif list_type == "bullet":
            return LIST_MARKERS[list_level]  # 深いとエラーになるけど実質問題ない

    def _text(self, text):
        w = self.font.text_width(text)
        # アラインメント
        if self.align == "center":
            self.x = (WIDTH - w) // 2
        elif self.align == "right":
            self.x = WIDTH - w

        # 背景色
        if self.bgcolor >= 0:
            self.img.rect(self.x, self.y, w, self.font_height, self.bgcolor)

        if DEBUG:
            self.img.rectb(self.x, self.y, w, self.font_height, 0)

        self.img.text(self.x, self.y, text, self.color, self.font)

        # バグ: centerやrightの場合は連続で _text が呼ばれると位置がずれる
        self.x += w

    def _crlf(self, margin: bool = False):
        # carriage return
        self.x = self.indent_stack[-1]
        # line feed
        self.y += self.font_height
        if margin:
            # 文字高さの50%分のマージンを追加
            self.y += int(self.font_height * LINE_MARGIN_RATIO)

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
            self.font_stack.append("title")
            self.align = "center"
            self._crlf()
        elif token.tag == "h2":
            self.section_level = 2
            self.font_stack.append("title")
            self.align = "center"
            self._crlf()
            self._crlf()
        elif token.tag == "h3":
            self.section_level = 3
            self.font_stack.append("pagetitle")
            self.align = "left"
            self._text("# ")

    def visit_heading_close(self, token):
        self._crlf()
        self._crlf()
        self.font_stack.pop()

    def visit_text(self, token):
        content = token.content
        max_width = WIDTH - self.x
        if DEBUG:
            self.img.rectb(self.x, self.y, max_width, self.font_height, 2)
        while content:
            i = len(content)
            w = self.font.text_width(content)
            while w > max_width:
                i -= 1
                w = self.font.text_width(content[:i])
            self._text(content[:i])
            content = content[i:]
            if content:
                self._crlf()

    def visit_bullet_list_open(self, token):
        self._indent(WINDOW_PADDING)
        self.list_stack.append("bullet")

    def visit_bullet_list_close(self, token):
        self._dedent()
        self.list_stack.pop()

    def visit_ordered_list_open(self, token):
        self._indent(WINDOW_PADDING)
        self.list_stack.append("ordered")
        self.list_ordered_num = 1

    def visit_ordered_list_close(self, token):
        self._dedent()
        self.list_stack.pop()
        self.list_ordered_num = None

    def visit_list_item_open(self, token):
        x = self.x
        self._text(self.list_marker)  # 本当はここでマイナスインデントするのが良いかも？
        self.x = x  # 元の位置に戻す
        self._indent(max(self.font_height, self.font.text_width(self.list_marker)))

    def visit_list_item_close(self, token):
        self._dedent()
        if self.list_ordered_num:
            self.list_ordered_num += 1

    def visit_paragraph_open(self, token):
        pass

    def visit_paragraph_close(self, token):
        self._crlf(margin=True)

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
        w = DEFAULT_LINE_HEIGHT + max(hls)
        h = DEFAULT_LINE_HEIGHT + len(hls) * DEFAULT_LINE_HEIGHT
        self.img.rect(self.x, self.y, w, h, 0)

        self._indent(WINDOW_PADDING)
        self.y += WINDOW_PADDING
        for line in token.content.splitlines():
            self._text(line)
            self._crlf()
        self._dedent()

    def visit_hardbreak(self, token):
        self._crlf()

    def visit_softbreak(self, token):
        self._crlf()

    def visit_html_block(self, token):
        pass


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
