# title: Pyxel app 02-mutiplay
# author: Takayuki Shimizukawa
# desc: Pyxel app 02-multiplay
# site: https://github.com/shimizukawa/pyxel-app
# license: MIT
# version: 1.0
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyxel",
#     "websocket-client",
# ]
# ///

import threading
import json
import os
import time
import typing

import pyxel

# WS_ADDR = os.getenv("WS_ADDR", "ws://127.0.0.1:9999")
WS_ADDR = os.getenv("WS_ADDR", "wss://skylark-quiet-neatly.ngrok-free.app")
WIDTH = 160
HEIGHT = 120
SPEED = 1


class PyWS:
    def __init__(
        self,
        on_message: typing.Callable | None = None,
        on_error: typing.Callable | None = None,
    ):
        self.on_message = on_message
        self.on_error = on_error

    def connect(self):
        print("Connect to", WS_ADDR)
        self.ws = websocket.WebSocketApp(
            WS_ADDR,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def send(self, **kwargs):
        try:
            self.ws.send(json.dumps(kwargs))
        except websocket.WebSocketConnectionClosedException:
            # print(f"Failed to send message: {e}")
            pass

    def _on_message(self, ws, message):
        data = json.loads(message)
        if self.on_message:
            self.on_message(data)

    def _on_error(self, ws, error):
        if self.on_error:
            self.on_error(error)

    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed, attempting to reconnect...")
        time.sleep(1)
        self.connect()


class JSWS:
    def __init__(
        self,
        on_message: typing.Callable | None = None,
        on_error: typing.Callable | None = None,
    ):
        self.on_message = on_message
        self.on_error = on_error

    def connect(self):
        self.ws = websocket.new(WS_ADDR)
        self.ws.onmessage = self._on_message
        self.ws.onerror = self._on_error
        self.ws.onclose = self._on_close

    def send(self, **kwargs):
        try:
            self.ws.send(json.dumps(kwargs))
        except Exception:
            # print(f"Failed to send message: {e}")
            pass

    def _on_message(self, event):
        message = event.data
        data = json.loads(message)
        if self.on_message:
            self.on_message(data)

    def _on_error(self, event):
        error = event.message
        if self.on_error:
            self.on_error(error)

    def _on_close(self, event):
        # close_status_code = event.code
        # close_msg = event.reason
        print("WebSocket closed, attempting to reconnect...")
        time.sleep(1)
        self.connect()


try:
    import websocket

    WS = PyWS
except ImportError:
    from js import WebSocket as websocket

    WS = JSWS


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Hello Pyxel")
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.radius = 4
        self.players = {}

        # Websocket
        self.ws = WS(self.on_message, self.on_error)
        try:
            self.ws.connect()
        except Exception:
            print("Failed to connect to server. Skipped.")

        # run forever
        pyxel.run(self.update, self.draw)

    def on_message(self, data):
        if data["type"] == "connected":
            print("Connected to server, Clients:", data["clients"])
        elif data["type"] == "disconnect":
            self.on_error(data["id"])
        elif data["type"] == "update":
            self.players[data["id"]] = data

    def on_error(self, error):
        try:
            del self.players[error]
        except Exception:
            print(f"WebSocket error: {error!r}")

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

        self.ws.send(id=id(self), x=self.x, y=self.y)

    def draw(self):
        pyxel.cls(1)
        for player in self.players.values():
            pyxel.circb(player["x"], player["y"], self.radius, 8)
        pyxel.circb(self.x, self.y, self.radius, 7)


App()
