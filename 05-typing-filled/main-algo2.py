# title: Pyxel app 05-typing-filled-algo2
# author: Takayuki Shimizukawa
# desc: Pyxel app 05-typing-filled-algo2
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

import enum
import json
import random
import dataclasses

import pyxel

TITLE = "Pyxel app 05-typing-filled-algo2"
WIDTH = 320
HEIGHT = 180
CHAR_WIDTH = 6
LINE_HEIGHT = 14
MAX_LINES = 8

font = pyxel.Font("assets/umplus_j12r.bdf")


def load_words():
    with open("assets/words.json", encoding="utf-8") as f:
        words = json.load(f)
    words = [s for s in words if s.isalpha()]
    random.shuffle(words)
    return words


@dataclasses.dataclass
class Word:
    text: str
    x: int = 0
    y: int = 0
    typed_pos: int = 0

    def __post_init__(self):
        self.text = self.text.lower()

    def __len__(self) -> int:
        return len(self.text) + 1  # 単語の文字数と区切りのスペース


class Line(list):
    def __init__(self, *args, id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id


class WordSet:
    word_pos: int
    words: list[str]
    lines: list[Line[Word]]

    def __init__(self, words: list[str], max_lines, char_per_line):
        self.word_pos = 0
        self.char_per_line = char_per_line
        self.lines = [Line(id=i+1) for i in range(max_lines)]
        self.words = words

        # 単語リストから、文字数がいっぱいになるところまで選択する
        _total = 0
        for i, text in enumerate(words):
            _total += len(text)  # 区切りスペースを考慮しないことで多めに単語を積んでおく
            if _total > char_per_line * max_lines:
                break
        self.words = sorted(words[:i], key=len, reverse=True)

    def sort_lines(self):
        # 文字列が少ない順に並べて、先頭行に詰め込む
        self.lines.sort(key=lambda line: sum(len(w) for w in line))

    def append(self, text: str) -> bool:
        word = Word(text)
        size = len(word)  # 単語の文字数と区切りのスペース

        # 先頭行に追加できるかチェック
        col = sum(len(w) for w in self.lines[0])
        if col + size - 1 > self.char_per_line:
            return False

        self.lines[0].append(word)
        self.word_pos += 1
        return True

    def remove(self, word: str):
        for line in self.lines:
            for w in line:
                if w.text == word:
                    line.remove(w)
                    self.word_pos += 1
                    return

    @property
    def is_finished(self) -> bool:
        if self.word_pos >= len(self.words):
            return True
        return all(sum(len(w) for w in line) >= self.char_per_line for line in self.lines)


def draw_text_with_border(img, x, y, s, col, bcol, font):
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx != 0 or dy != 0:
                img.text(
                    x + dx,
                    y + dy,
                    s,
                    bcol,
                    font,
                )
    img.text(x, y, s, col, font)


Status = enum.Enum("Status", "start sorting trying failed success")


@dataclasses.dataclass(frozen=True)
class State:
    line: int
    status: Status


class App:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.img = pyxel.Image(WIDTH, HEIGHT)
        pyxel.load("assets/res.pyxres")
        self.current_pos = 0
        self.state = State(-1, Status.start)
        self.trying = None

        words = load_words()
        self.left_margin = self.width // 10
        self.char_per_line = (self.width - self.left_margin * 2) // CHAR_WIDTH
        self.wordset = WordSet(words, MAX_LINES, self.char_per_line)
        self.words = self.wordset.words

    def update(self):
        if self.wordset.is_finished:
            return

        if pyxel.btnp(pyxel.KEY_SPACE, 10, 1) or pyxel.btnp(pyxel.KEY_RIGHT, 10, 2):
            # 右かスペースで次の状態を開始
            if self.wordset.is_finished:
                # もう終了している場合は何もしない
                self.state = State(-1, Status.start)
            else:
                # 次の単語を試行する
                word = self.words[self.current_pos]
                self.state = self.try_push_word(word)
                if self.state.status == Status.start:
                    self.current_pos += 1
        elif pyxel.btnp(pyxel.KEY_LEFT, 10, 2) and self.current_pos >= 0:
            # 左で前の状態に戻る
            self.state = State(-1, Status.start)
            self.current_pos = max(self.current_pos - 1, 0)
            self.wordset.remove(self.words[self.current_pos])

    def try_push_word(self, word):
        # 使用する単語を文字数の多い順に詰め込んでいく
        match self.state.status:
            case Status.start:
                self.wordset.sort_lines()
                return State(0, Status.sorting)
            case Status.sorting:
                return State(0, Status.trying)
            case Status.trying:
                if self.wordset.append(word):
                    return State(0, Status.success)
                else:
                    return State(0, Status.failed)
            case Status.success | Status.failed:
                return State(0, Status.start)
            case _:
                print("match default")
                return self.state

        print("end of try_push_word")


    def render(self):
        g = self.img
        next_words = self.words[self.current_pos : self.current_pos + 10]
        if not next_words:
            return g
        g.cls(1)
        info1 = f"WORD: {self.current_pos} / {len(self.words)} : "
        g.text(8, 8, info1, 7, font)
        word = next_words[0]
        g.text(8 + font.text_width(info1), 8, word, 10, font)
        w = font.text_width(word)
        g.line(
            8 + font.text_width(info1), 20, 8 + font.text_width(info1) + w, 20, 10
        )
        g.text(
            8 + font.text_width(info1) + w, 8, f" {' '.join(next_words[1:])}", 7, font
        )
        g.text(8, 20, f"Status: {self.state.status.name}", 7, font)

        for i, line in enumerate(self.wordset.lines):
            text = (" ".join(w.text for w in line) + " ").lstrip()
            y = 50 + i * 14
            color = 5 if len(text) >= self.char_per_line - 1 else 3
            prefix = f"{line.id: 2}-"
            left_margin = self.left_margin
            g.text(left_margin, y, prefix, 7, font)
            left_margin += font.text_width(prefix)
            g.text(left_margin, y, text, color, font)
            g.rectb(
                left_margin - 2, y - 1, self.char_per_line * CHAR_WIDTH + 2, 15, 5
            )
            if self.state.line == i:
                w0 = font.text_width(text)
                if self.state.status == Status.trying:
                    g.text(left_margin + w0, y, word, 10, font)
                elif self.state.status == Status.failed:
                    g.text(left_margin + w0, y, word, 8, font)
                if self.state.status in (Status.trying, Status.failed):
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
