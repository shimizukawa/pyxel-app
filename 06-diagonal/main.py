# title: Pyxel app 06-diagonal
# author: Takayuki Shimizukawa
# desc: Pyxel app 06-diagonal
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

import time
import pyxel

TITLE = "Pyxel app 06-diagonal"

font = pyxel.Font("assets/umplus_j12r.bdf")


class App:
    width = 320
    height = 180

    def __init__(self):
        self.word = "Hello, Pyxel! "
        self.ww = ww = font.text_width(self.word)  # word width
        self.lh = 15  # line height
        self.wpl = self.width // ww + 2  # word per line
        self.lc = self.height // self.lh + 1  # line count
        self.positions = []
        for i in range(self.wpl * self.lc):
            col = i % self.wpl
            row = i // self.wpl
            x = col * ww - row * ww // 7
            y = row * self.lh
            self.positions.append((x, y))
        self.frame_times = [time.time()] * 30

    def calc_fps(self):
        self.frame_times.append(time.time())
        self.frame_times.pop(0)
        # 10フレームごとにFPSを計算
        if pyxel.frame_count % 10:
            return
        self.fps = int(
            len(self.frame_times) / (self.frame_times[-1] - self.frame_times[0])
        )

    def update(self):
        self.calc_fps()
        for i, (x, y) in enumerate(self.positions):
            x, y = (x - 1, y + 1)
            if x < -font.text_width(self.word):
                x += self.wpl * self.ww
            if y > self.height:
                y = -self.lh
            self.positions[i] = (x, y)

    def cls(self, col):
        pyxel.cls(col)

    def draw(self):
        self.cls(1)
        for i, (x, y) in enumerate(self.positions):
            draw_text_with_border(x, y, self.word, i, (8 + i) % 16, font)
        pyxel.rect(20, 20, self.width - 40, self.height - 40, 0)
        pyxel.rectb(20, 20, self.width - 40, self.height - 40, 2)
        pyxel.text(30, 30, "Diagonal Scroll", 7)
        pyxel.text(5, self.height - 10, f"FPS: {self.fps}", 13)


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


if __name__ == "__main__":
    pyxel.init(App.width, App.height, TITLE, fps=60)
    app = App()
    # run forever
    pyxel.run(app.update, app.draw)
