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

import pyxel
import random
import time

TITLE = "Pyxel app 04-typing"
WIDTH = 320
HEIGHT = 180

WORDS = [
    "apple", "bag", "cat", "dog", "egg", "fan", "gift", "hat", "ice", "job",
    "key", "lion", "map", "note", "owl", "pen", "queen", "rain", "sun", "toy",
    "umbrella", "van", "wall", "yard", "zoo", "boy", "girl", "man",
    "woman", "water", "fire", "wood", "metal", "stone", "fish", "bird", "paper",
    "book", "foot", "hand", "head", "eye", "ear", "mouth", "nose", "tooth",
    "tongue", "hair", "arm", "leg", "knee", "toe", "finger", "thumb", "desk",
    "chair", "table", "door", "window", "floor", "ceiling", "light", "sound",
    "music", "art", "dance", "sing", "run", "walk", "jump", "sit", "stand",
    "laugh", "cry", "smile", "frown", "think", "write", "read", "count", "play",
    "work", "rest", "sleep", "dream", "eat", "drink", "cook", "bake", "drive",
    "ride", "clean", "wash", "open", "close", "push", "pull", "give", "take"
]

font = pyxel.Font("assets/umplus_j12r.bdf")


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
        self.cur_pos = 0
        self.cur_text = random.choice(WORDS)
        self.score = 0
        self.error = 0
        self.words = 0
        self.start = time.time()
        self.time = 0

        # run forever
        pyxel.run(self.update, self.draw)

    def update(self):
        if self.time >= 60:
            # なにも更新しない（ESCで終了）
            return
    
        self.time = time.time() - self.start
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
            self.cur_text = random.choice(WORDS)
            self.cur_pos = 0

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
        pyxel.text(120, 20, f"TPM: {self.score / self.time * 60: >8.1f}", 7, font)
        pyxel.text(220, 8, f"ERROR: {self.error: >4}", 14, font)
        pyxel.text(220, 20, f"EPM: {self.error / self.time * 60: >8.1f}", 14, font)

App()
