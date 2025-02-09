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
import time
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
    with open("assets/05-typing-words.json", encoding="utf-8") as f:
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

    def __eq__(self, value: str):
        return self.text == value.lower()

    def __len__(self) -> int:
        return len(self.text) + 1  # 単語の文字数と区切りのスペース


Status = enum.Enum("Status", "start sorting trying failed success")


@dataclasses.dataclass(frozen=True)
class State:
    line: int
    word: str
    status: Status


class Transitter:
    def __init__(self, default: int, duration: float = 0.5):
        self.default = default
        self.dur = duration

    def __set_name__(self, owner, name):
        self.name = "__" + name

    def __get__(self, instance, owner):
        obj = getattr(instance, self.name, {"value": self.default})
        value = obj["value"]
        if "start_at" in obj:
            elapsed = time.time() - obj["start_at"]
            if elapsed >= self.dur:
                del obj["start_at"]
            else:
                oval = obj["ovalue"]
                return oval + (value - oval) * (elapsed / self.dur)
        return value

    def __set__(self, instance, value):
        old_obj = getattr(instance, self.name, {})
        oval = old_obj.get("value")
        obj = {
            "ovalue": oval,
            "value": value,
        }
        if oval is not None and oval != value:
            obj["start_at"] = time.time()
        setattr(instance, self.name, obj)


class Line(list):
    x = Transitter(0)
    y = Transitter(0)

    def __init__(self, *args, id, char_per_line, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
        self.char_per_line = char_per_line

    def draw(self, img, x, y, font, state: State | None) -> tuple[int, int]:
        x = self.x + x
        y = self.y + y
        text = (" ".join(w.text for w in self) + " ").lstrip()
        color = 5 if len(text) >= self.char_per_line - 1 else 3
        prefix = f"{self.id: 2}-"
        img.text(x, y, prefix, 7, font)
        x += font.text_width(prefix)
        img.text(x, y, text, color, font)
        img.rectb(
            x - 2, y - 1, self.char_per_line * CHAR_WIDTH + 2, 15, 13 if state else 5
        )
        x += font.text_width(text)
        if not state:
            return x, y

        match state.status:
            case Status.trying:
                img.text(x, y, state.word, 10, font)
            case Status.failed:
                img.text(x, y, state.word, 8, font)

        return x, y


class WordSet:
    word_pos: int
    words: list[str]
    lines: list[Line[Word]]

    def __init__(self, words: list[str], max_lines, char_per_line):
        self.word_pos = 0
        self.char_per_line = char_per_line
        self.words = words
        self.lines = [
            Line(id=i + 1, char_per_line=char_per_line) for i in range(max_lines)
        ]
        self.sort_lines()

        # 単語リストから、文字数がいっぱいになるところまで選択する
        _total = 0
        for i, text in enumerate(words):
            # 区切りスペースを考慮しないことで多めに単語を積んでおく
            _total += len(text)
            if _total > char_per_line * max_lines:
                break
        self.words = sorted(words[:i], key=len, reverse=True)

    def sort_lines(self):
        # 文字列が少ない順に並べて、先頭行に詰め込む
        self.lines.sort(key=lambda line: sum(len(w) for w in line))
        for i, line in enumerate(self.lines):
            line.y = i * LINE_HEIGHT

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
            if word in line:
                line.remove(word)
                self.word_pos -= 1
                return

    @property
    def is_finished(self) -> bool:
        if self.word_pos >= len(self.words):
            return True
        return all(
            sum(len(w) for w in line) >= self.char_per_line for line in self.lines
        )


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


class App:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.img = pyxel.Image(width, height)
        pyxel.load("assets/05-typing.pyxres")
        self.current_pos = 0
        self.state = State(-1, "", Status.start)
        self.trying = None

        words = load_words()
        self.left_margin = self.width // 10
        self.char_per_line = (self.width - self.left_margin * 2) // CHAR_WIDTH
        self.wordset = WordSet(words, MAX_LINES, self.char_per_line)
        self.words = self.wordset.words

    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE, 10, 1) or pyxel.btnp(pyxel.KEY_RIGHT, 10, 2):
            # 右かスペースで次の状態を開始
            if self.wordset.is_finished:
                # もう終了している場合は何もしない
                self.state = State(-1, "", Status.start)
                return
            if self.current_pos < len(self.words):
                # 次の単語を試行する
                word = self.words[self.current_pos]
                self.state = self.try_push_word(word)
                if self.state.status == Status.start:
                    self.current_pos += 1
        elif pyxel.btnp(pyxel.KEY_LEFT, 10, 2) and self.current_pos >= 0:
            # 左で前の状態に戻る
            self.current_pos = max(self.current_pos - 1, 0)
            word = self.words[self.current_pos]
            self.state = State(-1, word, Status.start)
            self.wordset.remove(word)
            self.wordset.sort_lines()

    def try_push_word(self, word):
        # 使用する単語を文字数の多い順に詰め込んでいく
        match self.state.status:
            case Status.start:
                self.wordset.sort_lines()
                return State(0, word, Status.sorting)
            case Status.sorting:
                return State(0, word, Status.trying)
            case Status.trying:
                if self.wordset.append(word):
                    return State(0, word, Status.success)
                else:
                    return State(0, word, Status.failed)
            case Status.success | Status.failed:
                return State(0, "", Status.start)
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
        g.line(8 + font.text_width(info1), 20, 8 + font.text_width(info1) + w, 20, 10)
        g.text(
            8 + font.text_width(info1) + w, 8, f" {' '.join(next_words[1:])}", 7, font
        )
        g.text(8, 20, f"Status: {self.state.status.name}", 7, font)

        for i, line in reversed(list(enumerate(self.wordset.lines))):
            state = self.state if self.state.line == i else None
            last_x, last_y = line.draw(g, self.left_margin, 50, font, state)
            if state and state.status in (Status.trying, Status.failed):
                g.line(
                    8 + font.text_width(info1) + w // 2,
                    22,
                    last_x + w // 2,
                    last_y - 1,
                    10,
                )

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
