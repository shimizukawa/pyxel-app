# title: Pyxel app 04-typing
# author: Takayuki Shimizukawa
# desc: Pyxel app 04-typing
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

import pyxel

TITLE = "Pyxel app 04-typing"
WIDTH = 320
HEIGHT = 180

font = pyxel.Font("assets/umplus_j12r.bdf")


def load_words():
    with open("assets/words.json", encoding="utf-8") as f:
        return json.load(f)


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
        words = list(load_words())
        random.shuffle(words)
        words.append("")  # 開始前は空にする
        self.word_list = words
        self.cur_pos = 0
        self.score = 0
        self.error = 0
        self.words = 0
        self.start_time = time.time()
        self.time = 0
        self.started = False

    def start(self):
        self.word_list.pop()  # 最初の文字列を表示
        self.started = True

    def finish(self):
        self.started = False

    @property
    def cur_text(self):
        return self.word_list[-1].lower()

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
            self.words += 1
            self.word_list.pop()
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
        w = font.text_width(self.cur_text[: self.cur_pos])
        before = self.cur_text[: self.cur_pos]
        after = self.cur_text[self.cur_pos :]
        if before:
            draw_text_with_border(50, 50, before, 3, 0, font)
        if after:
            pyxel.text(50+w, 50, after, 11, font)

        pyxel.text(8, 8, f"TIME: {self.time: >4.1f} / 60", 7, font)
        pyxel.text(8, 20, f"WORDS: {self.words: >2}", 7, font)
        pyxel.text(120, 8, f"TYPE: {self.score: >5}", 7, font)
        pyxel.text(120, 20, f"TPM: {self.tpm: >8.1f}", 7, font)
        pyxel.text(220, 8, f"ERROR: {self.error: >4}", 14, font)
        pyxel.text(220, 20, f"EPM: {self.epm: >8.1f}", 14, font)

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
                draw_text_with_border(x, pyxel.height // 2 + i * 10, line, color, 0, font)

App()
