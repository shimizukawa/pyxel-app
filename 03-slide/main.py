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
import dataclasses
import re
import time
from pathlib import Path

import pyxel


TITLE = "Pyxel app 03-slide"
MD_FILENAME = "slide.md"
# DEBUG = True
DEBUG = False

LINE_NUMS = 12  # lines per page
LINE_MARGIN_RATIO = 0.5  # フォント高さの50%
DEFAULT_LINE_HEIGHT = int(12 * (1 + LINE_MARGIN_RATIO))  # default font height 12
WINDOW_PADDING = DEFAULT_LINE_HEIGHT // 2
HEIGHT = DEFAULT_LINE_HEIGHT * LINE_NUMS
WIDTH = HEIGHT * 16 // 9
KEY_REPEAT = 1  # for 30fps
KEY_HOLD = 15  # for 30fps

# The Font class only supports BDF format fonts
font_title = pyxel.Font("assets/b24.bdf")
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

DIRECTION_MAP = {
    ("f", "h2"): "right",
    ("f", "h3"): "down",
    ("b", "h3"): "up",
    ("b", "h2"): "left",
}

directive_pattern = re.compile(r"^{(.+?)}\s*(.*)$")
directive_option_pattern = re.compile(r":(\w+): (.+)", re.MULTILINE)


@dataclasses.dataclass
class Slide:
    sec: int
    page: int
    tokens: list
    level: str


class FPS:
    def __init__(self):
        self.value = 0
        self.frame_times = [time.time()] * 30

    def calc(self):
        self.frame_times.append(time.time())
        self.frame_times.pop(0)
        # 10フレームごとにFPSを計算
        if pyxel.frame_count % 10:
            return
        self.value = int(
            len(self.frame_times) / (self.frame_times[-1] - self.frame_times[0])
        )

    def __rmul__(self, other):
        return self.value * other

    def __rtruediv__(self, other):
        return other / self.value

    def __floordiv__(self, other):
        return self.value // other

    def __str__(self):
        return str(self.value)


class App:
    def __init__(self):
        self.first_pages_in_section = []  # セクションの開始ページ
        self.slides = self.load_slides(MD_FILENAME)
        self._page = 0
        self.fps = FPS()
        self.in_transition = [0, 0, "down"]  # (rate(1..0), old_page, direction)
        self.child_apps = {}  # page: app
        self.child_is_updated = False
        pyxel.init(
            WIDTH + WINDOW_PADDING * 2,
            HEIGHT + WINDOW_PADDING,
            title=TITLE,
            quit_key=pyxel.KEY_NONE,
        )
        self.renderd_page_bank = [
            (None, pyxel.Image(WIDTH, HEIGHT)),
            (None, pyxel.Image(WIDTH, HEIGHT)),
        ]
        pyxel.mouse(True)
        self.colors = pyxel.colors.to_list()  # 親アプリ用のcolorsをバックアップ
        self.render_page(0)

        # run forever
        pyxel.run(self.update, self.draw)

    def load_slides(self, filepath) -> list[Slide]:
        import markdown_it

        md = markdown_it.MarkdownIt()
        content = Path(filepath).read_text(encoding="utf-8")
        tokens = md.parse(content)
        slides: list[Slide] = []
        slide_tokens: list[markdown_it.token.Token] = []
        sec = 0
        page = 0
        for token in tokens:
            if token.type == "heading_open" and token.tag in ["h1", "h2", "h3"]:
                if slide_tokens:
                    slides.append(Slide(sec, page, slide_tokens, slide_tokens[0].tag))
                    page += 1
                    sec = sec + 1 if token.tag in ("h1", "h2") else sec
                    slide_tokens = []
            slide_tokens.append(token)
        if slide_tokens:
            slides.append(Slide(sec, page, slide_tokens, slide_tokens[0].tag))

        for i, slide in enumerate(slides):
            if slide.level in ("h1", "h2"):
                self.first_pages_in_section.append(i)
        return slides

    def load_child(
        self,
        page: int,
        x: int,
        y: int,
        width: int,
        height: int,
        filename: str,
        scale: float | None,
    ):
        # ファイル名が .py の前提で読み込む
        child = __import__(filename[:-3])
        # scale処理
        if scale is not None:
            width = int(width / scale)
            height = int(height / scale)
        a = self.child_apps[page] = child.App(width, height)
        # x 座標は、左パディングのみ考慮
        a.__x = max((pyxel.width - width) // 2, WINDOW_PADDING)
        a.__y = y
        a.__colors = pyxel.colors.to_list()  # colorsバックアップ
        a.__scale = scale

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, new_page):
        old_page, self._page = self._page, new_page
        if old_page != new_page:
            self.render_page(new_page)

        if old_page < new_page:  # forward
            self.in_transition = [
                1.0,
                old_page,
                DIRECTION_MAP["f", self.slides[new_page].level],
            ]
        if old_page > new_page:  # backward
            self.in_transition = [
                1.0,
                old_page,
                DIRECTION_MAP["b", self.slides[old_page].level],
            ]

    def go_forward(self):
        self.page = min((self.page + 1), len(self.slides) - 1)

    def go_backward(self):
        self.page = max((self.page - 1), 0)

    def go_next_page(self):
        if (
            self.page + 1 not in self.first_pages_in_section
            and self.page != len(self.slides) - 1
        ):
            self.page += 1

    def go_prev_page(self):
        if self.page not in self.first_pages_in_section:
            self.page -= 1

    def go_next_section(self):
        sec = min(self.slides[self.page].sec + 1, len(self.first_pages_in_section) - 1)
        self.page = self.first_pages_in_section[sec]

    def go_prev_section(self):
        sec = max(self.slides[self.page].sec - 1, 0)
        self.page = self.first_pages_in_section[sec]

    def update_child(self):
        """子アプリの更新

        更新条件
        - 子アプリのあるページを表示中
        - transition中でない
        - マウスが子アプリ内にある
        """
        if self.page not in self.child_apps:
            return False
        if self.in_transition[0] > 0:
            return False

        a = self.child_apps[self.page]
        if (a.__x <= pyxel.mouse_x < a.width + a.__x) and (
            a.__y <= pyxel.mouse_y < a.height + a.__y
        ):
            a.update()
            return True

        return False

    def update(self):
        self.fps.calc()
        self.child_is_updated = self.update_child()
        if self.child_is_updated:
            return

        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        key_hold = KEY_HOLD * self.fps // 30
        key_repeat = KEY_REPEAT * self.fps // 30

        if self.in_transition[0] > 0:
            self.in_transition[0] = self.in_transition[0] - 3 / self.fps

        if pyxel.btnp(pyxel.KEY_DOWN, key_hold, key_repeat):
            self.go_next_page()
        elif pyxel.btnp(pyxel.KEY_UP, key_hold, key_repeat):
            self.go_prev_page()
        elif pyxel.btnp(pyxel.KEY_RIGHT, key_hold, key_repeat):
            self.go_next_section()
        elif pyxel.btnp(pyxel.KEY_LEFT, key_hold, key_repeat):
            self.go_prev_section()
        elif pyxel.btnp(pyxel.KEY_SPACE, key_hold, key_repeat):
            if pyxel.btn(pyxel.KEY_SHIFT):
                self.go_backward()
            else:
                self.go_forward()

    def draw(self):
        pyxel.cls(7)
        self.blt_slide()
        # 子アプリの描画
        self.blt_child()
        # Navigation
        self.draw_nav()
        # FPSを表示
        pyxel.text(5, pyxel.height - 10, f"FPS: {self.fps}", 13)

    def render_page(self, page: int) -> pyxel.Image:
        """render page to old image bank"""
        for p, img in self.renderd_page_bank:
            if p == page:
                return img

        _, img = self.renderd_page_bank.pop(0)
        img.rect(0, 0, WIDTH, HEIGHT, 7)
        visitor = Visitor(self, page, img)
        visitor.walk(self.slides[page].tokens)
        self.renderd_page_bank.append((page, img))
        return img

    def get_rendered_img(self, page: int):
        for i, (p, img) in enumerate(self.renderd_page_bank):
            if p == page:
                used = self.renderd_page_bank.pop(i)
                self.renderd_page_bank.append(used)
                return img
        else:
            return self.render_page(page)

    def blt_slide(self):
        if self.in_transition[0] > 0:
            rate, old_page, direction = self.in_transition
            if direction == "down":
                old_x = WINDOW_PADDING
                old_y = WINDOW_PADDING - HEIGHT * (1 - rate) ** 2
                new_x = WINDOW_PADDING
                new_y = WINDOW_PADDING + HEIGHT * rate**2
            elif direction == "up":
                old_x = WINDOW_PADDING
                old_y = WINDOW_PADDING + HEIGHT * (1 - rate) ** 2
                new_x = WINDOW_PADDING
                new_y = WINDOW_PADDING - HEIGHT * rate**2
            elif direction == "right":
                old_x = WINDOW_PADDING - WIDTH * (1 - rate) ** 2
                old_y = WINDOW_PADDING
                new_x = WINDOW_PADDING + WIDTH * rate**2
                new_y = WINDOW_PADDING
            elif direction == "left":
                old_x = WINDOW_PADDING + WIDTH * (1 - rate) ** 2
                old_y = WINDOW_PADDING
                new_x = WINDOW_PADDING - WIDTH * rate**2
                new_y = WINDOW_PADDING
            new_img = self.get_rendered_img(self.page)
            old_img = self.get_rendered_img(old_page)
            # old
            pyxel.dither(rate)
            pyxel.blt(old_x, old_y, old_img, 0, 0, WIDTH, HEIGHT, 7)
            # new
            pyxel.dither(1 - rate)
            pyxel.blt(new_x, new_y, new_img, 0, 0, WIDTH, HEIGHT, 7)
            pyxel.dither(1)
        else:
            img = self.get_rendered_img(self.page)
            pyxel.blt(WINDOW_PADDING, WINDOW_PADDING, img, 0, 0, WIDTH, HEIGHT)
            if self.child_is_updated:
                pyxel.dither(0.5)
                pyxel.rect(0, 0, pyxel.width, pyxel.height, 13)
                pyxel.dither(1.0)

    def blt_child(self):
        """子アプリのオーバーレイ"""
        if self.page not in self.child_apps:
            pyxel.colors.from_list(self.colors)  # 親アプリ用のcolorsに切替
            return
        if self.in_transition[0] > 0:
            return

        a = self.child_apps[self.page]
        pyxel.colors.from_list(a.__colors)  # 子アプリ用のcolorsに切替
        g = a.render()
        x = max((pyxel.width - g.width) // 2, WINDOW_PADDING)
        x = WINDOW_PADDING + a.__x
        y = WINDOW_PADDING + a.__y
        s1 = a.__scale or 1
        s2 = (1 - s1) / 2
        w, h = g.width, g.height
        pyxel.blt(x - int(w * s2), y - int(h * s2), g, 0, 0, w, h, scale=a.__scale)
        if self.child_is_updated:
            pyxel.rectb(x, y, int(w * s1), int(h * s1), 8)

    def draw_nav(self):
        if self.child_is_updated:
            return
        w, h = pyxel.width, pyxel.height
        if (
            self.page + 1 not in self.first_pages_in_section
            and self.page != len(self.slides) - 1
        ):
            # セクション内の最後のページではない
            pyxel.line(w - 20, h - 10, w - 15, h - 15, 5)
            pyxel.line(w - 20, h - 10, w - 25, h - 15, 5)
        if self.page < self.first_pages_in_section[-1]:
            # 最後のセクションではない
            pyxel.line(w - 5, h - 25, w - 10, h - 20, 5)
            pyxel.line(w - 5, h - 25, w - 10, h - 30, 5)
        if self.page not in self.first_pages_in_section:
            # セクション内の最初のページではない
            pyxel.line(w - 20, h - 40, w - 15, h - 35, 6)
            pyxel.line(w - 20, h - 40, w - 25, h - 35, 6)
        if self.page != 0:
            # 最初のセクションではない
            pyxel.line(w - 35, h - 25, w - 30, h - 20, 6)
            pyxel.line(w - 35, h - 25, w - 30, h - 30, 6)


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
    list_stack: list[tuple[str, int]]

    def __init__(self, app: App, page: int, img: pyxel.Image):
        self.app = app
        self.img = img
        self.page = page
        self.x = 0
        self.y = 0
        self.indent_stack = [self.x]
        self.font_stack = ["default"]
        self.color_stack = [(0, -1)]
        self.section_level = 0
        self.align = "left"
        self.list_stack = []  # 箇条書きのマーク用

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
        list_type, ordered_num = self.list_stack[-1]
        if list_type == "ordered":
            return f"{ordered_num}. "
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
        self.list_stack.append(("bullet", 1))

    def visit_bullet_list_close(self, token):
        self._dedent()
        self.list_stack.pop()

    def visit_ordered_list_open(self, token):
        self._indent(WINDOW_PADDING)
        self.list_stack.append(("ordered", 1))

    def visit_ordered_list_close(self, token):
        self._dedent()
        self.list_stack.pop()

    def visit_list_item_open(self, token):
        x = self.x
        self._text(self.list_marker)  # 本当はここでマイナスインデントするのが良いかも？
        self.x = x  # 元の位置に戻す
        self._indent(max(self.font_height, self.font.text_width(self.list_marker)))

    def visit_list_item_close(self, token):
        self._dedent()
        list_type, ordered_num = self.list_stack.pop()
        self.list_stack.append((list_type, ordered_num + 1))

    def visit_paragraph_open(self, token):
        pass

    def visit_paragraph_close(self, token):
        self._crlf(margin=True)

    def visit_em_open(self, token):
        self.color_stack.append((9, -1))
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
        if token.info:
            if directive_pattern.match(token.info):
                return self._directive(token)
            print("fence info", token.info)
        if not hls:
            print("fence: No content")
            return
        w = DEFAULT_LINE_HEIGHT + max(hls)
        h = DEFAULT_LINE_HEIGHT + len(hls) * DEFAULT_LINE_HEIGHT
        self.img.rect(self.x, self.y, w, h, 0)

        self._indent(WINDOW_PADDING)
        self.y += WINDOW_PADDING
        for line in token.content.splitlines():
            self._text(line)
            self._crlf()
        self._dedent()

    def _directive(self, token):
        """ディレクティブ処理

        ```{directive} args
        :opt1: value1

        content
        ```

        - `{figure}`: 画像表示
          - args = "filename.*"
            - `.py` ではアプリ読み込み
            - `.png`, `.jpg` では画像読み込み
            - `.*` では上記の順番にトライ
          - options:
            - `scale`: 50 （50% 表記は非対応）
        """
        m = directive_pattern.match(token.info)
        directive, args = m.groups()
        if directive != "figure":
            print("unsupported directive", directive)
            return
        options = dict(directive_option_pattern.findall(token.content))

        if args.endswith(".*"):
            args = args[:-2]
            for ext in [".py", ".png", ".jpg"]:
                path = Path(args + ext)
                if path.exists():
                    args = path.name
                    break

        if args.endswith(".py"):
            s = int(options["scale"]) / 100 if "scale" in options else None
            self.app.load_child(self.page, self.x, self.y, 355, 200, args, s)
            return

        if args.endswith((".png", ".jpg")):
            p = pyxel.Image.from_image(args)
            if "scale" in options:
                s = int(options["scale"]) / 100
            else:
                s = self.img.width / max(p.width, self.img.width)
            x, y, w, h = self.x, self.y, p.width, p.height
            lm = max(int(self.img.width - w * s) // 2, 0)
            self.img.blt(
                lm + x - int(w * (1 - s) / 2),
                y - int(h * (1 - s) / 2),
                p,
                0,
                0,
                w,
                h,
                scale=s,
            )
            return

        print("Not Found.", args)

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
