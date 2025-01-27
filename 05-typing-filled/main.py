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
LINE_HEIGHT = 14
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
class Word:
    text: str
    x: int = 0
    y: int = 0
    typed_pos: int = 0

    def __post_init__(self):
        self.text = self.text.lower()

    def __len__(self) -> int:
        return len(self.text) + 1  # 単語の文字数と区切りのスペース

    def test_input(self) -> tuple[bool | None, bool]:
        """入力文字が正しいか判定

        戻り値:
        - (入力が正しいか, 入力が最後まで完了したか)
        - 入力が正しいか: None: 未入力, False: タイプミス, True: 正解
        - 入力が最後まで完了したか: True: 入力完了, False: 未入力あり

        正しい場合:
        - 位置を更新
        - まだ未入力があるなら (True, False) を返す
        - 最後まで一致していたら (True, True) を返す

        間違っている場合
        - (False, False) を返す
        """
        ch = self.text[self.typed_pos]
        correct: bool | None = None  # None: 未入力, False: タイプミス, True: 正解
        for c in range(ord("a"), ord("z") + 1):
            if ch == chr(c) and pyxel.btnp(c):
                # 正解
                correct = True
                self.typed_pos += 1
                break
            elif pyxel.btnp(c):
                # タイプミス
                correct = False
                break

        return (correct, self.typed_pos == len(self.text))

    def draw(self, offset_x, offset_y):
        """文字列を入力済みと未入力分とで表現を変えてx,y座標に描画する"""
        before = self.text[: self.typed_pos]
        after = self.text[self.typed_pos :]
        x = self.x + offset_x
        y = self.y + offset_y
        if before:
            draw_text_with_border(x, y, before, 3, 0, font)
        if after:
            pyxel.text(x + font.text_width(before), y, after, 3, font)


class WordSet:
    word_pos: int
    words: list[Word]
    lines: list[list[Word]]

    def __init__(self, words: list[str]):
        self.word_pos = 0
        self.lines = [[] for _ in range(MAX_LINES)]

        # 単語リストから、文字数がいっぱいになるところまで選択する
        _total = 0
        for i, text in enumerate(words):
            _total += len(text) + 1
            if _total > CHAR_PER_LINE * MAX_LINES:
                break

        # 使用する単語を文字数の多い順に詰め込んでいく
        stock_words = sorted(words[:i], key=len, reverse=True)
        for text in stock_words:
            if not self._append(text):
                break

        self._update_word_loc()
        self.words = [word for line in self.lines for word in line]
        print(f"Words: {len(self.words)}/{len(words)}")

    def _append(self, text: str) -> bool:
        word = Word(text)
        size = len(word)  # 単語の文字数と区切りのスペース

        # 文字列が少ない順に並べて、先頭行に詰め込む
        self.lines.sort(key=lambda line: sum(len(w) for w in line))

        # 先頭行に追加できるかチェック
        col = sum(len(w) for w in self.lines[0])
        if col + size > CHAR_PER_LINE:
            return False

        self.lines[0].append(word)
        return True

    def _update_word_loc(self):
        """単語の位置を更新する"""
        random.shuffle(self.lines)
        for row, line in enumerate(self.lines):
            random.shuffle(line)
            col = 0
            for word in line:
                word.x = col * CHAR_WIDTH
                word.y = row * LINE_HEIGHT
                col += len(word)

    @property
    def is_finished(self) -> bool:
        return self.word_pos >= len(self.words)

    def test_input(self) -> tuple[bool | None, bool]:
        if self.is_finished:
            return None, False

        corr, comp = self.words[self.word_pos].test_input()
        if comp:
            self.word_pos += 1
        return corr, comp

    def draw(self, x, y):
        for line in self.lines:
            for word in line:
                word.draw(x, y)


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
        self.wordset = WordSet(words)
        self.score = 0
        self.error = 0
        self.start_time = time.time()
        self.time = 0
        self.started = False

    def start(self):
        self.started = True

    def finish(self):
        self.started = False

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
        elif self.time >= 60 or self.wordset.is_finished:
            # スタート後60秒以上経過しているか、全ての単語を入力した
            self.finish()
            return

        self.time = time.time() - self.start_time

        correct, complete = self.wordset.test_input()
        match correct:
            case True:
                # 正解
                pyxel.play(0, 0)
                self.score += 1
            case False:
                # タイプミス
                pyxel.play(0, 1)
                self.error += 1
            case None:
                # 未入力
                pass

        if complete:
            # 入力完了
            pass

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
        pyxel.text(8, 20, f"WORDS: {self.wordset.word_pos: >2}", 7, font)
        pyxel.text(120, 8, f"TYPE: {self.score: >5}", 7, font)
        pyxel.text(120, 20, f"TPM: {self.tpm: >8.1f}", 7, font)
        pyxel.text(220, 8, f"ERROR: {self.error: >4}", 14, font)
        pyxel.text(220, 20, f"EPM: {self.epm: >8.1f}", 14, font)

        self.wordset.draw(LEFT_MARGIN, 50)

        if not self.started:
            if self.wordset.is_finished:
                # ゲームクリア
                text = "FINISHED!\nPRESS SPACE TO START"
            elif self.time > 0:
                # ゲーム終了
                text = "TIMES UP!\nPRESS SPACE TO START"
            else:
                # ゲーム開始前
                text = "PRESS SPACE TO START"

            # 色を3フレーム毎に変える
            color = (pyxel.frame_count // 3) % 12 + 4
            for i, line in enumerate(text.splitlines()):
                # 行ごとにセンタリング
                x = (pyxel.width - font.text_width(line)) // 2
                draw_text_with_border(
                    x, pyxel.height // 2 + i * 14, line, color, 0, font
                )


App()
