# title: Pyxel app 01-circle
# author: Takayuki Shimizukawa
# desc: Pyxel app 01-circle
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

TITLE = "Pyxel app 01-circle"
WIDTH = 160
HEIGHT = 120
SPEED = 1


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title=TITLE)
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 4

        # run forever
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        speed = SPEED
        if pyxel.btn(pyxel.KEY_SPACE):
            speed *= 3
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.x = (self.x + speed) % WIDTH
        elif pyxel.btn(pyxel.KEY_LEFT):
            self.x = (self.x - speed) % WIDTH
        if pyxel.btn(pyxel.KEY_DOWN):
            self.y = (self.y + speed) % HEIGHT
        elif pyxel.btn(pyxel.KEY_UP):
            self.y = (self.y - speed) % HEIGHT
        self.radius = 4 + (pyxel.frame_count // (6 / speed)) % 2

    def draw(self):
        pyxel.cls(1)
        pyxel.circb(self.x, self.y, self.radius, 7)


App()
