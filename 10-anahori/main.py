# title: Pyxel app 10-anahori
# author: Takayuki Shimizukawa
# desc: Anahori runner based upon Pyxel Platformer example by Takashi Kitao
# site: https://github.com/shimizukawa/pyxel-app
# license: MIT
# version: 1.0

import pyxel

TRANSPARENT_COLOR = 2
SCROLL_BORDER_X = 80
TILE_FLOOR = (1, 0)
WALL_TILE_X = 4
TILE_RADDER = (0, 5)
TILE_BRICK = (4, 2)
TILE_SPAWN1 = (0, 1)
TILE_SPAWN2 = (1, 1)
TILE_SPAWN3 = (2, 1)

scroll_x = 0
_height = 0
player = None
is_loose = False
show_bb = False
is_pback = False
score = 0


def dbg(func):
    import sys
    import inspect
    def wrapper(*args, **kwargs):
        r = func(*args, **kwargs)
        argstr = ", ".join(f"{n}={v}" for n, v in zip(func.__code__.co_varnames, args))
        frame_info = inspect.getframeinfo(sys._getframe(1))
        print(f"{frame_info.lineno}: {frame_info.code_context[0].rstrip()}")
        print(f"{func.__code__.co_firstlineno}: {func.__name__}({argstr}, {kwargs}) -> {r}")
        return r
    return wrapper


def get_tile(tile_x, tile_y) -> tuple[int, int]:
    if b := blocks.get((tile_x, tile_y)):
        # blocks初期化後はこちらで判定
        return b.current_type
    return pyxel.tilemaps[0].pget(tile_x, tile_y)


def is_radder(x, y):
    x1 = pyxel.floor(x) // 8
    y1 = pyxel.floor(y) // 8
    x2 = (pyxel.ceil(x) + 7) // 8
    y2 = (pyxel.ceil(y) + 7) // 8

    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            if get_tile(xi, yi) == TILE_RADDER:
                return True

    return False


def is_colliding(x, y, is_falling, use_radder, use_loose=False):
    x1 = pyxel.floor(x) // 8
    y1 = pyxel.floor(y) // 8
    x2 = (pyxel.ceil(x) + 7) // 8
    y2 = (pyxel.ceil(y) + 7) // 8
    if use_loose:
        x1 = (pyxel.floor(x) + 4) // 8
        x2 = (pyxel.ceil(x) + 3) // 8

    for yi in range(y1, y2 + 1):
        for xi in range(x1, x2 + 1):
            if get_tile(xi, yi)[0] >= WALL_TILE_X:
                return True
    if use_loose:
        return False

    if not use_radder and is_falling and y % 8 == 1:
        for xi in range(x1, x2 + 1):
            if get_tile(xi, y1 + 1) in (TILE_FLOOR, TILE_RADDER):
                return True
    return False


def push_back(x, y, dx, dy, use_radder):
    for _ in range(pyxel.ceil(abs(dy))):
        step = max(-1, min(1, dy))
        if dy > 0 and is_colliding(x, y + step, dy > 0, use_radder):
            break
        elif dy < 0 and is_colliding(x, y + step, dy > 1, use_radder, use_loose=is_loose):
            break
        y += step
        dy -= step
    for _ in range(pyxel.ceil(abs(dx))):
        step = max(-1, min(1, dx))
        if is_colliding(x + step, y, dy > 1, use_radder):
            break
        x += step
        dx -= step
    return x, y


# @dbg
def is_wall(x, y, *, include_ladder=False):
    tile = get_tile(x // 8, y // 8)
    if tile == TILE_RADDER and include_ladder:
        return True
    return tile == TILE_FLOOR or tile[0] >= WALL_TILE_X


def is_in_wall(x, y) -> bool:
    if is_wall(x, y) or is_wall(x + 7, y):
        return True
    if is_wall(x, y + 7) or is_wall(x + 7, y + 7):
        return True
    return False


class BaseEnemy:
    x: int
    y: int
    dx: int
    dy: int
    direction: int
    is_alive: bool

    def update(self):
        pass

    def draw(self):
        pass


class Enemy1(BaseEnemy): pass
class Enemy3(BaseEnemy): pass

class Enemy2(BaseEnemy):
    def __init__(self, img, x, y):
        self.img = img
        self.initial_x = self.x = x
        self.initial_y = self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = 1
        self.is_alive = True

    def reset(self):
        self.x = self.initial_x
        self.y = self.initial_y
        self.dx = 0
        self.dy = 0
        self.direction = 1
        self.is_alive = True

    def is_other_enemy(self, x: int, y: int) -> bool:
        for enemy in enemies:
            if enemy is self:
                continue
            if abs(enemy.x - x) < 8 and abs(enemy.y - y) < 8:
                return True
        return False

    def is_in_wall(self) -> bool:
        return is_in_wall(self.x, self.y)

    def update(self):
        if self.is_alive and self.is_in_wall():
            self.is_alive = False
            global score
            score += 100
            return

        self.dx = self.direction
        self.dy = min(self.dy + 1, 3)

        if is_wall(self.x, self.y + 8) or is_wall(self.x + 7, self.y + 8):
            if self.direction < 0 and (
                is_wall(self.x - 1, self.y + 4) or not is_wall(self.x - 1, self.y + 8, include_ladder=True) or self.is_other_enemy(self.x - 1, self.y)
            ):
                self.direction = 1
            elif self.direction > 0 and (
                is_wall(self.x + 8, self.y + 4) or not is_wall(self.x + 7, self.y + 8, include_ladder=True) or self.is_other_enemy(self.x + 8, self.y)
            ):
                self.direction = -1
        self.x, self.y = push_back(self.x, self.y, self.dx, self.dy, False)

    def draw(self):
        if not self.is_alive:
            return

        u = pyxel.frame_count // 4 % 2 * 8 + 16
        w = 8 if self.direction > 0 else -8
        self.img.blt(self.x, self.y, 0, u, 16, w, 8, TRANSPARENT_COLOR)


enemies: list[BaseEnemy] = []


def spawn_enemy(img, left_x, right_x):
    left_x = pyxel.ceil(left_x / 8)
    right_x = pyxel.floor(right_x / 8)
    for x in range(left_x, right_x + 1):
        for y in range(16):
            tile = get_tile(x, y)
            if tile == TILE_SPAWN1:
                enemies.append(Enemy1(img, x * 8, y * 8))
            elif tile == TILE_SPAWN2:
                enemies.append(Enemy2(img, x * 8, y * 8))
            elif tile == TILE_SPAWN3:
                enemies.append(Enemy3(img, x * 8, y * 8))


class Block:
    def __init__(self, img, x, y, type):
        self.img = img
        self.type = type
        self.x = x
        self.y = y
        self.damage = 0

    def __repr__(self):
        return f"Block({self.x=}, {self.y=}, {self.type=}, {self.damage=})"

    def reset(self):
        self.damage = 0

    @property
    def is_diggable(self) -> bool:
        return self.type == TILE_BRICK

    @property
    def current_type(self) -> tuple[int, int]:
        if self.is_diggable:
            return TILE_BRICK if self.damage < 20 else (0, 0)
        return self.type

    def dig(self) -> bool:
        if self.is_diggable:
            if self.damage < 60 and 60 <= self.damage + 3:
                self.damage = 180
            elif 60 < self.damage:
                pass
            else:
                self.damage = min(180, self.damage + 3)
            return True
        return False

    def update(self):
        self.damage = min(180, self.damage)
        self.damage = max(0, self.damage - 1)

    def draw(self):
        u, v = self.type
        if self.damage == 0:
            return
        elif self.damage <= 20:
            u += 1
        elif self.damage <= 40:
            u += 2
        else:
            u += 3
        self.img.blt(self.x, self.y, 0, u * 8, v * 8, 8, 8, TRANSPARENT_COLOR)


def get_diggable_block(x: int, y: int) -> Block | None:
    x1, y1 = (x + 4) // 8, (y + 4) // 8
    b = blocks.get((x1, y1))
    return b if b and b.is_diggable else None


def dig_block(x: int, y: int) -> bool:
    b = get_diggable_block(x, y)
    return b.dig() if b else False


class Player:
    def __init__(self, x, y, img):
        self.img = img
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.direction = 1
        self.is_falling = False
        self.use_radder = False
        self.frame_count = 0
        self.is_die = False

    def reset(self):
        player.x = 0
        player.y = 14
        player.dx = 0
        player.dy = 0
        player.is_die = False
        player.use_radder = False

    def die(self):
        self.is_die = True

    def is_in_wall(self) -> bool:
        return is_in_wall(self.x, self.y)

    def update_for_die(self):
        # サインカーブで飛び上がって落ちる
        df = pyxel.frame_count - self.frame_count 
        if df < 3:
            self.y += -4
        elif df < 15:
            pass
        elif df < 80:
            self.y += 4
            self.use_radder = True
        elif self.y >= _height:
            game_over()

    def update(self):
        if self.is_die:
            return self.update_for_die()
        elif self.is_in_wall():
            self.die()
            return

        self.frame_count = pyxel.frame_count
        global scroll_x
        last_y = self.y

        is_fal = self.is_falling
        is_rdr = is_radder(self.x, self.y)
        diggable_l = not is_fal and get_diggable_block(self.x - 8, self.y + 8)
        diggable_r = not is_fal and get_diggable_block(self.x + 8, self.y + 8)

        if diggable_l and pyxel.btn(pyxel.KEY_Z):
            # 左を優先
            digging = diggable_l.dig()
            self.direction = -1
        elif diggable_r and pyxel.btn(pyxel.KEY_X):
            digging = diggable_r.dig()
            self.direction = 1
        else:
            # 穴掘りしていない場合は移動できる
            if pyxel.btn(pyxel.KEY_LEFT):
                # 左を優先
                self.dx = -1
                self.direction = -1
            elif pyxel.btn(pyxel.KEY_RIGHT):
                self.dx = 1
                self.direction = 1
            if is_rdr and pyxel.btn(pyxel.KEY_UP):
                # 上を優先
                self.dy = -1
                self.use_radder = True
            elif is_rdr and pyxel.btn(pyxel.KEY_DOWN):
                self.dy = 1
                self.use_radder = True
            else:
                # はしごを使っていない場合は落ちる
                self.dy = 2
                self.use_radder = False
            self.x, self.y = push_back(self.x, self.y, self.dx, self.dy, self.use_radder)

        # looseモードでの、ブロックハマりからの押し戻し処理
        if is_pback and is_colliding(self.x, self.y, False, False):
            shift_x = round(self.x / 8) * 8 - self.x  # 近い方のタイルにずらす
            shift_x = max(-1, min(1, shift_x))  # ずらす量を-1, 0, 1に制限
            # 全てのdxについて、スクロール内で、かつ、ぶつかっていないdxがあるか
            for dx in (-4, 4):
                if self.x + dx > scroll_x and not is_colliding(
                    self.x + dx, self.y, False, False
                ):
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
        # self.is_ladder = True

        # if self.x > scroll_x + SCROLL_BORDER_X:
        #     scroll_x = min(self.x - SCROLL_BORDER_X, 240 * 8)
        if self.y >= _height:
            game_over()

    def draw(self):
        if self.use_radder:
            u = (2 + self.frame_count // 3 % 2)
            w = 8
        elif self.is_falling:
            u = 0
            w = 8
        else:
            u = (0 + self.frame_count // 3 % 2)
            w = 8 if self.direction > 0 else -8
        # u = (0 if self.is_falling else self.frame_count // 3 % 2)
        self.img.blt(self.x, self.y, 0, u * 8, 24, w, 8, TRANSPARENT_COLOR)
        if show_bb:
            if is_loose:
                self.img.trib(
                    self.x + 4, self.y, self.x, self.y + 7, self.x + 7, self.y + 7, 14
                )
            else:
                self.img.rectb(self.x, self.y, 8, 8, 10)


blocks: dict[tuple[int, int], Block] = {}


def init_tiles(img):
    for ix in range(0, 16):
        for iy in range(0, 16):
            tile = get_tile(ix, iy)
            print(f"{ix=}, {iy=}, {tile=}")
            x, y = ix * 8, iy * 8
            blocks[(ix, iy)] = Block(img, x, y, tile)


class App:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        global _height
        _height = height
        self.img = pyxel.Image(width, height)
        pyxel.load("assets/10-anahori.pyxres")

        # Change enemy spawn tiles invisible
        pyxel.images[0].rect(0, 8, 24, 8, TRANSPARENT_COLOR)

        global player
        player = Player(0, 14, self.img)

        init_tiles(self.img)
        spawn_enemy(self.img, 0, 127)

    def update(self):
        global is_loose, show_bb, is_pback
        # if pyxel.btnp(pyxel.KEY_1):
        #     show_bb = not show_bb
        # elif pyxel.btnp(pyxel.KEY_2):
        #     is_loose = not is_loose
        # elif pyxel.btnp(pyxel.KEY_3):
        #     is_pback = not is_pback
        if pyxel.btnp(pyxel.KEY_4):
            game_over()
        for b in blocks.values():
            b.update()
        player.update()
        if player.is_die:
            return

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            if abs(player.x - enemy.x) < 6 and abs(player.y - enemy.y) < 6:
                player.die()
                return
            enemy.update()
            if enemy.x < scroll_x - 8 or enemy.x > scroll_x + 160 or enemy.y > 160:
                enemy.is_alive = False

    def render(self):
        g = self.img
        g.cls(0)

        # Draw level
        g.camera()
        g.bltm(0, 0, 0, scroll_x, 0, 128, 128, TRANSPARENT_COLOR)
        for b in blocks.values():
            b.draw()
        g.text(1, 1, "SCORE:", 5)
        g.text(24, 1, f"{score:04d}", 7)
        # g.text(1, 1, "1:BBox", 7 if show_bb else 5)
        # g.text(32, 1, "2:Loose", 7 if is_loose else 5)
        # g.text(68, 1, "3:PBack", 7 if is_pback else 5)
        g.text(98, 1, "4:RST", 5)

        # Draw characters
        g.camera(scroll_x, 0)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        return g


def game_over():
    global scroll_x
    scroll_x = 0
    player.reset()
    for enemy in enemies:
        enemy.reset()
    for b in blocks.values():
        b.reset()


class ParentApp:
    def __init__(self):
        pyxel.init(128, 96, title="anahori", fps=20)
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

