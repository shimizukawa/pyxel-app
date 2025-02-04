# title: Pyxel app 07-pyxel-in-pyxel
# author: Takayuki Shimizukawa
# desc: Pyxel app 07-pyxel-in-pyxel
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

TITLE = "Pyxel app 07-pyxel-in-pyxel"

font = pyxel.Font("assets/umplus_j12r.bdf")


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


class ChildApp:
    def __init__(self, width=320, height=180, word="Hello, Pyxel!"):
        self.width = width
        self.height = height
        self.img = pyxel.Image(width, height)
        self.word = word + " "
        self.ww = ww = font.text_width(self.word)  # word width
        self.lh = 15  # line height
        self.wpl = self.width // ww + 2  # word per line
        self.lc = self.height // self.lh + 1  # line count
        self.fps = FPS()
        self.positions = []
        for i in range(self.wpl * self.lc):
            col = i % self.wpl
            row = i // self.wpl
            x = col * ww - row * ww // 7
            y = row * self.lh
            self.positions.append((x, y))
        self.frame_times = [time.time()] * 30

    def update(self):
        self.fps.calc()
        for i, (x, y) in enumerate(self.positions):
            x, y = (x - 1, y + 1)
            if x < -font.text_width(self.word):
                x += self.wpl * self.ww
            if y > self.height:
                y = -self.lh
            self.positions[i] = (x, y)

    def render(self):
        img = self.img
        img.cls(1)
        for i, (x, y) in enumerate(self.positions):
            draw_text_with_border(img, x, y, self.word, i, (8 + i) % 16, font)
        img.rect(20, 20, self.width - 40, self.height - 40, 0)
        img.rectb(20, 20, self.width - 40, self.height - 40, 2)
        img.text(30, 30, "Diagonal Scroll", 7)
        img.text(5, self.height - 10, f"FPS: {self.fps}", 13)
        return img

    def draw(self):
        img = self.render()
        pyxel.blt(0, 0, img, 0, 0, img.width, img.height)


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


class ParentApp:
    def __init__(self):
        self.child = ChildApp(width=320, height=240, word="Hello, Pyxel!")
        self.move_parent = True
        self.move_child = True
        self.parent_count = 0
        self.child_camera = (0, 0)
        self.fps = FPS()
        pyxel.init(480, 320, "Pyxel in Pyxel")
        # run forever
        pyxel.run(self.update, self.draw)

    def update(self):
        self.fps.calc()
        if pyxel.btnp(pyxel.KEY_F1):
            self.move_parent = not self.move_parent
        if pyxel.btnp(pyxel.KEY_F2):
            self.move_child = not self.move_child

        if self.move_child:
            self.child.update()

        if self.move_parent:
            self.parent_count += 1
            x = int(
                (pyxel.width - self.child.width)
                // 2
                * (1 + pyxel.sin(self.parent_count))
            )
            y = int(
                (pyxel.height - self.child.height)
                // 2
                * (1 + pyxel.cos(self.parent_count))
            )
            self.child_camera = (-x, -y)

    def draw(self):
        pyxel.camera(0, 0)
        pyxel.cls(0)

        pyxel.camera(*self.child_camera)
        pyxel.text(0, 0 - 10, "Child App", (pyxel.frame_count // 10) % 8 + 8)
        if self.move_child:
            self.child.render()
        img = self.child.img
        pyxel.blt(0, 0, img, 0, 0, img.width, img.height)

        pyxel.camera(0, 0)
        pyxel.text(5, 5, "Parent App", (pyxel.frame_count // 10) % 8)
        pyxel.rect(4, 14, 65, 7, 11 if self.move_parent else 8)
        pyxel.text(5, 15, f"F1: {'Pause' if self.move_parent else 'Move'} Parent", 7)
        pyxel.rect(4, 24, 65, 7, 11 if self.move_child else 8)
        pyxel.text(5, 25, f"F2: {'Pause' if self.move_child else 'Move'} Child", 7)
        pyxel.text(5, pyxel.height - 10, f"FPS: {self.fps}", 13)


if __name__ == "__main__":
    ParentApp()
