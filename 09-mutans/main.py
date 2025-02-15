# title: Pyxel app 08-jumpman
# author: Takayuki Shimizukawa
# desc: Pyxel app 08-jumpman midified from Pyxel Platformer example by Takashi Kitao
# site: https://github.com/shimizukawa/pyxel-app
# license: MIT
# version: 1.0

import pyxel

TRANSPARENT_COLOR = 2
TOOTH_LIST = [
    (2, 3),
    (16, 3),
    (2, 5),
    (16, 5),
    (2, 7),
    (16, 7),
    (2, 9),
    (16, 9),
    (4, 11),
    (14, 11),
    (6, 13),
    (8, 13),
    (10, 13),
    (12, 13),
]


class Tooth:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.damage_count = 0

    def get_location(self):
        return self.x, self.y

    def damage(self):
        self.damage_count += 1

    @property
    def stage(self):
        stage = min(self.damage_count // 300, 4)
        return stage

    def is_broken(self):
        return self.damage_count >= 300 * 5

    def update(self):
        self.damage_count = max(self.damage_count - 1, 0)

    def draw(self):
        pyxel.blt(self.x*8, self.y*8, 0, 8*self.stage, 8, 8, 8, TRANSPARENT_COLOR)


class Mutan:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # direction: 1: right, -1: left, 0: stop, 2: down, -2: up
        self.direction = pyxel.rndi(-2, 2)
        self.energy = 100
        self.damaged_at = 0

    def get_location(self):
        return (self.x + 4) // 8, (self.y + 4) // 8

    def eat(self, tooth: Tooth):
        self.direction = 0
        self.energy += 1
        tooth.damage()

    def can_zousyoku(self):
        return self.energy >= 200

    def zousyoku(self):
        self.energy = 100
        return Mutan(
            pyxel.rndi(self.x - 5, self.x + 5),
            pyxel.rndi(self.y - 5, self.y + 5),
        )

    def damage(self):
        self.energy = max(self.energy - 10, 0)
        self.damaged_at = pyxel.frame_count

    def is_broken(self):
        return self.energy <= 0

    def update(self):
        if self.direction in (1, -1):
            self.x = min(max(self.x + self.direction, 0), 152)
        elif self.direction in (2, -2):
            self.y = min(max(self.y + self.direction // 2, 0), 112)

        if self.x < 0 or self.x > 152:
            self.direction *= -1
        elif self.y < 0 or self.y > 112:
            self.direction *= -1

        if pyxel.frame_count % pyxel.rndi(1, 60) == 0:
            self.direction = pyxel.rndi(0, 5) - 2

        if self.damaged_at and pyxel.frame_count - self.damaged_at > 15:
            self.damaged_at = 0

    def draw(self):
        if self.direction == 0:
            u = 16
            w = 8 if (self.x + 4) // 8 != self.x // 8 else -8
        else:
            u = (pyxel.frame_count // 3 % 2) * 8
            w = 8 if self.direction > 0 else -8
        
        if self.damaged_at and pyxel.frame_count % 2 == 0:
            pyxel.rect(self.x, self.y, 8, 8, 10)
        else:
            pyxel.blt(self.x, self.y, 0, u, 16, w, 8, TRANSPARENT_COLOR)


class Brush:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_brushing = False

    def get_location(self):
        return (self.x + 4) // 8, (self.y + 4) // 8

    def attach(self, mutan: Mutan):
        if not self.is_brushing:
            return
        if mutan.get_location() == self.get_location():
            mutan.damage()

    def update(self):
        self.is_brushing = pyxel.btn(pyxel.KEY_SPACE)
        speed = 1 if self.is_brushing else 2

        if pyxel.btn(pyxel.KEY_LEFT):
            self.x = max(self.x - speed, 0)
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.x = min(self.x + speed, 152)
        if pyxel.btn(pyxel.KEY_UP):
            self.y = max(self.y - speed, 0)
        if pyxel.btn(pyxel.KEY_DOWN):
            self.y = min(self.y + speed, 112)

    def draw(self):
        u = 0
        if self.is_brushing:
            u = (pyxel.frame_count // 3 % 2) * 8
        pyxel.blt(self.x, self.y, 0, u, 24, 8, 16, TRANSPARENT_COLOR)


class App:
    def __init__(self):
        pyxel.init(160, 120, "Pyxel app 09-mutans")
        pyxel.load("assets/09-mutans.pyxres")
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.brushed_count = 0
        self.tooths = {(x, y): Tooth(x, y) for x, y in TOOTH_LIST}
        self.mutans = [
            Mutan(pyxel.rndi(0, 100), pyxel.rndi(0, 100))
            for _ in range(5)
        ]
        self.brush = Brush(72, 50)

    def update(self):
        # move
        for mutan in self.mutans:
            mutan.update()
        if not self.tooths:
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.reset()
            return
        self.brush.update()

        # brushing, mutans eating and zousyoku
        for mutan in self.mutans:
            self.brush.attach(mutan)
            if mutan.is_broken():
                self.mutans.remove(mutan)
                self.brushed_count += 1
                continue
            if tooth := self.tooths.get(mutan.get_location()):
                mutan.eat(tooth)
                if tooth.is_broken():
                    del self.tooths[tooth.get_location()]
                if mutan.can_zousyoku():
                    self.mutans.append(mutan.zousyoku())

        # recover tooth
        for tooth in self.tooths.values():
            tooth.update()

        # new mutans
        if pyxel.rndf(0, 1) < 0.01 / 10:
            self.mutans.append(Mutan(pyxel.rndi(0, 160), pyxel.rndi(0, 120)))

    def draw(self):
        pyxel.cls(14)
        for tooth in self.tooths.values():
            tooth.draw()
        for mutan in self.mutans:
            mutan.draw()
        self.brush.draw()

        pyxel.text(2, 2, f"MUTANS: {len(self.mutans)}", 5)
        pyxel.text(50, 2, f"BRUSHED: {self.brushed_count}", 5)

        if not self.tooths:
            text = "GAME OVER!\nPRESS SPACE TO START"

            # 色を3フレーム毎に変える
            color = (pyxel.frame_count // 3) % 12 + 4
            for i, line in enumerate(text.splitlines()):
                # 行ごとにセンタリング
                x = (pyxel.width - 4 * len(line)) // 2
                pyxel.text(x, pyxel.height // 2 + i * 10, line, color)

App()
