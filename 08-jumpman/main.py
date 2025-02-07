# title: Pyxel app 08-jumpman
# author: Takayuki Shimizukawa
# desc: Pyxel app 08-jumpman midified from Pyxel Platformer example by Takashi Kitao
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

TRANSPARENT_COLOR = 2
SCROLL_BORDER_X = 80
TILE_FLOOR = (1, 0)
WALL_TILE_X = 4

scroll_x = 0
_height = 0
player = None
is_loose = False
show_bb = False


def get_tile(tile_x, tile_y):
    return pyxel.tilemaps[0].pget(tile_x, tile_y)


def is_colliding(x, y, is_falling, use_loose=False):
    x1 = pyxel.floor(x) // 8
    y1 = pyxel.floor(y) // 8
    x2 = (pyxel.ceil(x) + 7) // 8
    y2 = (pyxel.ceil(y) + 7) // 8
    if use_loose:
        x1 = (pyxel.floor(x)+ 4) // 8
        x2 = (pyxel.ceil(x) + 3) // 8

    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            if get_tile(xi, yi)[0] >= WALL_TILE_X:
                return True
    if use_loose:
        return False

    if is_falling and y % 8 == 1:
        for xi in range(x1, x2 + 1):
            if get_tile(xi, y1 + 1) == TILE_FLOOR:
                return True
    return False


def push_back(x, y, dx, dy):
    for _ in range(pyxel.ceil(abs(dy))):
        step = max(-1, min(1, dy))
        if dy > 0 and is_colliding(x, y + step, dy > 0):
            break
        elif dy < 0 and is_colliding(x, y + step, dy > 0, use_loose=is_loose):
            break
        y += step
        dy -= step
    for _ in range(pyxel.ceil(abs(dx))):
        step = max(-1, min(1, dx))
        if is_colliding(x + step, y, dy > 0):
            break
        x += step
        dx -= step
    return x, y


class Player:
    def __init__(self, x, y, img):
        self.img = img
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = 1
        self.is_falling = False
        self.frame_count = 0

    def update(self):
        self.frame_count = pyxel.frame_count
        global scroll_x
        last_y = self.y
        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -1 * (2 if pyxel.btn(pyxel.KEY_SHIFT) else 1)
            self.direction = -1
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = 1 * (2 if pyxel.btn(pyxel.KEY_SHIFT) else 1)
            self.direction = 1
        self.dy = min(self.dy + 1, 3)
        if pyxel.btnp(pyxel.KEY_SPACE):
            if self.dy == 3 and not self.is_falling:  # 落下3で落ちていない状態
                self.dy = -6
        self.x, self.y = push_back(self.x, self.y, self.dx, self.dy)

        # looseモードでの、ブロックハマりからの押し戻し処理
        if is_loose and is_colliding(self.x, self.y, False):
            shift_x = round(self.x / 8) * 8  - self.x  # 近い方のタイルにずらす
            shift_x = max(-1, min(1, shift_x))  # ずらす量を-1, 0, 1に制限
            # 全てのdxについて、スクロール内で、かつ、ぶつかっていないdxがあるか
            for dx in (-4, 4):
                if self.x + dx > scroll_x and not is_colliding(self.x + dx, self.y, False):
                    self.x += shift_x
                    break
            else:
                # ハマっているので右方向にずらす
                self.x += 1

        if self.x < scroll_x:
            self.x = scroll_x
        if self.y < 0:
            self.y = 0
        self.dx = int(self.dx * 0.8)
        self.is_falling = self.y > last_y

        if self.x > scroll_x + SCROLL_BORDER_X:
            scroll_x = min(self.x - SCROLL_BORDER_X, 240 * 8)
        if self.y >= _height:
            game_over()

    def draw(self):
        u = (2 if self.is_falling else self.frame_count // 3 % 2) * 8
        w = 8 if self.direction > 0 else -8
        self.img.blt(self.x, self.y, 0, u, 24, w, 8, TRANSPARENT_COLOR)
        if show_bb:
            self.img.rectb(self.x, self.y, 8, 8, 10)


class App:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        global _height
        _height = height
        self.img = pyxel.Image(width, height)
        pyxel.load("assets/08-jumpman.pyxres")

        # Change enemy spawn tiles invisible
        pyxel.images[0].rect(0, 8, 24, 8, TRANSPARENT_COLOR)

        global player
        player = Player(0, 30, self.img)

    def update(self):
        global is_loose, show_bb
        if pyxel.btnp(pyxel.KEY_1):
            is_loose = not is_loose
        elif pyxel.btnp(pyxel.KEY_2):
            show_bb = not show_bb
        player.update()

    def render(self):
        g = self.img
        g.cls(0)

        # Draw level
        g.camera()
        g.bltm(0, 0, 0, scroll_x, 0, 128, 128, TRANSPARENT_COLOR)
        g.text(1, 1, "1:Loose ON" if is_loose else "1:Loose OFF", 7 if is_loose else 5)
        g.text(60, 1, "2:BBox ON" if show_bb else "2:BBox OFF", 7 if show_bb else 5)

        # Draw characters
        g.camera(scroll_x, 0)
        player.draw()
        return g


def game_over():
    global scroll_x
    scroll_x = 0
    player.x = 0
    player.y = 30
    player.dx = 0
    player.dy = 0


class ParentApp:
    def __init__(self):
        pyxel.init(128, 96, title="Pyxel Platformer")
        self.child = App(width=128, height=96)
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
