# title: Pyxel app 05-typing-filled-algo1
# author: Takayuki Shimizukawa
# desc: Pyxel app 05-typing-filled-algo1
# site: https://github.com/shimizukawa/pyxel-app
# license: MIT
# version: 1.0
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyxel",
# ]
# ///

import json
import random
import dataclasses

import pyxel

TITLE = "Pyxel app 05-typing-filled-algo1"
WIDTH = 320
HEIGHT = 180
CHAR_WIDTH = 6
MAX_LINES = 8

font = pyxel.Font("assets/umplus_j12r.bdf")


def load_words():
    with open("assets/words.json", encoding="utf-8") as f:
        words = json.load(f)
    words = [s for s in words if s.isalpha()]
    random.shuffle(words)
    return words


@dataclasses.dataclass
class Line:
    chars_per_line: int
    words: list[str] = dataclasses.field(default_factory=list)

    def __getitem__(self, i):
        return self.words[i]

    def __len__(self):
        return len(self.words)

    def __iter__(self):
        yield from self.words

    def append(self, word):
        self.words.append(word)

    @property
    def text(self):
        t = " ".join(self.words)
        return t + " " if t else t

    def can_add(self, word):
        return len(self.text) + len(word) <= self.chars_per_line

    def is_full(self):
        return len(self.text) >= self.chars_per_line


class Lines:
    def __init__(self, char_per_line):
        self.lines = [Line(char_per_line) for _ in range(MAX_LINES)]

    def __getitem__(self, i):
        return self.lines[i]

    def __len__(self):
        """単語数"""
        return sum(len(line) for line in self.lines)

    def __iter__(self):
        yield from self.lines

    def is_full(self):
        return all(line.is_full() for line in self.lines)

    def append(self, word: str):
        if self.is_full():
            return
        for line in self.lines:
            if line.can_add(word):
                line.append(word)
                break

    def remove(self, word):
        for line in self.lines:
            if word in line:
                line.words.remove(word)
                break


@dataclasses.dataclass(frozen=True)
class State:
    line: int
    result: bool | None  # None: trying, False: failed, True: success


class App:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.img = pyxel.Image(WIDTH, HEIGHT)
        pyxel.load("assets/res.pyxres")
        self.words = load_words()
        self.current_pos = 0
        self.left_margin = self.width // 10
        self.char_per_line = (self.width - self.left_margin * 2) // CHAR_WIDTH
        self.lines = Lines(self.char_per_line)
        self.state = State(-1, True)
        self.trying = None

    def update(self):
        if self.lines.is_full():
            return

        if pyxel.btnp(pyxel.KEY_SPACE, 10, 2) or pyxel.btnp(pyxel.KEY_RIGHT, 10, 2):
            # 右かスペースで次の状態を開始
            if self.state.result:
                word = self.words[self.current_pos]
                self.trying = self.try_push_word(word)
            try:
                self.state = next(self.trying)
            except StopIteration:
                self.current_pos += 1
                self.state = State(-1, True)
        elif pyxel.btnp(pyxel.KEY_LEFT, 10, 2) and self.current_pos >= 0:
            # 左で前の状態に戻る
            self.state = State(-1, True)
            self.current_pos = max(self.current_pos - 1, 0)
            self.lines.remove(self.words[self.current_pos])

    def try_push_word(self, word):
        for i, line in enumerate(self.lines):
            if line.can_add(word):
                yield State(i, None)
                line.append(word)
                self.current_pos += 1
                yield State(i, True)
                break
            else:
                yield State(i, False)

    def render(self):
        g = self.img
        g.cls(1)
        next_words = self.words[self.current_pos : self.current_pos + 10]
        word = next_words[0]
        info1 = f"WORD: {self.current_pos} / {len(self.words)} : "
        g.text(8, 8, info1, 7, font)
        g.text(8 + font.text_width(info1), 8, word, 10, font)
        w = font.text_width(word)
        g.line(8 + font.text_width(info1), 20, 8 + font.text_width(info1) + w, 20, 10)
        g.text(
            8 + font.text_width(info1) + w, 8, f" {' '.join(next_words[1:])}", 7, font
        )
        left_margin = self.left_margin

        for i, line in enumerate(self.lines):
            text = line.text
            y = 50 + i * 14
            color = 5 if line.is_full() else 3
            g.text(left_margin, y, text, color, font)
            g.rectb(left_margin - 2, y - 1, self.char_per_line * CHAR_WIDTH + 2, 15, 5)
            if self.state.line == i:
                w0 = font.text_width(text)
                if self.state.result is None:  # trying
                    g.text(left_margin + w0, y, word, 10, font)
                elif not self.state.result:  # failed
                    g.text(left_margin + w0, y, word, 8, font)
                if not self.state.result:  # trying or failed
                    g.line(
                        8 + font.text_width(info1) + w // 2,
                        22,
                        left_margin + w0 + w // 2,
                        y - 1,
                        10,
                    )

        if self.state.line >= 0:
            y = 50 + self.state.line * 14 - 1
            g.rectb(left_margin - 2, y, self.char_per_line * CHAR_WIDTH + 2, 15, 13)

        return g

    def draw(self):
        g = self.render()
        pyxel.blt(0, 0, g, 0, 0, g.width, g.height)


class ParentApp:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, TITLE)
        self.child = App(width=WIDTH, height=HEIGHT)
        pyxel.run(self.update, self.draw)

    def update(self):
        self.child.update()

    def draw(self):
        g = self.child.render()
        pyxel.blt(
            (pyxel.width - g.width) // 2,
            (pyxel.height - g.height) // 2,
            g,
            0,
            0,
            g.width,
            g.height,
        )


if __name__ == "__main__":
    ParentApp()
