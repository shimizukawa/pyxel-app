# title: Pyxel app 05-typing-filled
# author: Takayuki Shimizukawa
# desc: Pyxel app 05-typing-filled
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
import time
import dataclasses

import pyxel

TITLE = "Pyxel app 05-typing-filled"
WIDTH = 320
HEIGHT = 180
CHAR_WIDTH = 6
LEFT_MARGIN = WIDTH // 10
CHAR_PER_LINE = (WIDTH - LEFT_MARGIN * 2) // CHAR_WIDTH
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
    words: list[str] = dataclasses.field(default_factory=list)
    chars_per_line: int = CHAR_PER_LINE

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
        return " ".join(self.words)

    def can_add(self, word):
        return len(self.text) + len(word) <= self.chars_per_line

    def is_full(self):
        return len(self.text) >= self.chars_per_line


class Lines:
    def __init__(self):
        self.lines = [Line() for _ in range(MAX_LINES)]
        self.line_counts = [0] * 10

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
        self.line_counts = [len(line) for line in self.lines]

    def get_word(self, pos: int):
        for count, line in zip(self.line_counts, self.lines):
            if pos < count:
                return line[pos]
            pos -= count

    def get_state(self, pos: int):
        """i番目の単語について、単語、i行目、n文字目を返す"""
        for i, (count, line) in enumerate(zip(self.line_counts, self.lines)):
            if pos < count:
                return line[pos], i, len(" ".join(line[:pos]))
            pos -= count


def create_lines(words, chars_per_line=CHAR_PER_LINE):
    """1行の文字数にできるだけ詰めて複数行の文字列のリストを作る"""
    lines = Lines()
    _total = len(words)
    for _i, word in enumerate(words):
        lines.append(word)
        if lines.is_full():
            break
    print(f"Words: {_i}/{_total}")
    return lines


def draw_text_with_border(x, y, s, col, bcol, font):
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx != 0 or dy != 0:
                pyxel.text(
                    x + dx,
                    y + dy,
                    s,
                    bcol,
                    font,
                )
    pyxel.text(x, y, s, col, font)


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title=TITLE)
        pyxel.load("assets/res.pyxres")
        self.reset()

        # run forever
        pyxel.run(self.update, self.draw)

    def reset(self):
        words = load_words()
        lines = create_lines(words)
        self.lines = lines
        self.cur_word_pos = 0
        self.cur_pos = 0
        self.score = 0
        self.error = 0
        self.start_time = time.time()
        self.time = 0
        self.started = False

    def start(self):
        self.started = True

    def finish(self):
        self.started = False

    @property
    def cur_text(self):
        return self.lines.get_word(self.cur_word_pos).lower()

    def update(self):
        if not self.started:
            # スタートしていない
            if pyxel.btnp(pyxel.KEY_SPACE):
                # スペースで開始
                self.reset()
                self.start()
            else:
                # なにもしない
                return
        elif self.time >= 60:
            # スタート後60秒以上経過している
            self.finish()
            return

        self.time = time.time() - self.start_time
        ch = self.cur_text[self.cur_pos]
        for c in range(ord("a"), ord("z") + 1):
            if ch == chr(c) and pyxel.btnp(c):
                # 正解
                pyxel.play(0, 0)
                self.cur_pos += 1
                self.score += 1
                break
            elif pyxel.btnp(c):
                # タイプミス
                pyxel.play(0, 1)
                self.error += 1
                break

        if self.cur_pos == len(self.cur_text):
            # 入力完了
            self.cur_word_pos += 1
            self.cur_pos = 0

    @property
    def tpm(self):
        if self.time > 0:
            return self.score / self.time * 60
        return 0

    @property
    def epm(self):
        if self.time > 0:
            return self.error / self.time * 60
        return 0

    def draw(self):
        pyxel.cls(1)
        pyxel.text(8, 8, f"TIME: {self.time: >4.1f} / 60", 7, font)
        pyxel.text(8, 20, f"WORDS: {self.cur_word_pos: >2}", 7, font)
        pyxel.text(120, 8, f"TYPE: {self.score: >5}", 7, font)
        pyxel.text(120, 20, f"TPM: {self.tpm: >8.1f}", 7, font)
        pyxel.text(220, 8, f"ERROR: {self.error: >4}", 14, font)
        pyxel.text(220, 20, f"EPM: {self.epm: >8.1f}", 14, font)

        word, line_num, pos = self.lines.get_state(self.cur_word_pos)

        cur_pos = self.cur_pos + pos
        for i, line in enumerate(self.lines):
            text = " ".join(line)
            y = 50 + i * 14
            if i < line_num:
                draw_text_with_border(LEFT_MARGIN, y, text, 3, 0, font)
            if i == line_num:
                before, after = text[:cur_pos], text[cur_pos:]
                w = font.text_width(before)
                if before:
                    draw_text_with_border(LEFT_MARGIN, y, before, 3, 0, font)
                if after:
                    pyxel.text(LEFT_MARGIN + w, y, after, 3, font)
            if i > line_num:
                pyxel.text(LEFT_MARGIN, y, text, 3, font)

        if not self.started:
            if self.time >= 60:
                # ゲーム終了
                text = "TIME UP!\nPRESS SPACE TO START"
            else:
                # ゲーム開始前
                text = "PRESS SPACE TO START"

            # 色を3フレーム毎に変える
            color = (pyxel.frame_count // 3) % 12 + 4
            for i, line in enumerate(text.splitlines()):
                # 行ごとにセンタリング
                x = (pyxel.width - font.text_width(line)) // 2
                draw_text_with_border(
                    x, pyxel.height // 2 + i * 10, line, color, 0, font
                )


App()
