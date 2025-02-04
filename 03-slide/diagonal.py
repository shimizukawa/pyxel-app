# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyxel",
# ]
# ///
import time
import pyxel

font = pyxel.Font("assets/b12.bdf")


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


class App:
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
        img.text(5, self.height - 10, f"FPS: {self.fps.value}", 13)
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
        self.child = App(width=320, height=240, word="Hello, Pyxel!")
        pyxel.init(480, 320, "Pyxel in Pyxel")
        pyxel.run(self.update, self.draw)

    def update(self):
        self.child.update()
        
    def draw(self):
        g = self.child.img
        self.child.render()
        pyxel.blt((pyxel.width-g.width)//2, (pyxel.height-g.height)//2, g, 0, 0, g.width, g.height)


if __name__ == "__main__":
    ParentApp()
