import json
import threading
import time
import typing

import pyxel

WS_ADDR = "wss://ws.freia.jp/"


class _PyWS:
    def __init__(
        self,
        addr: str,
        on_message: typing.Callable | None = None,
        on_error: typing.Callable | None = None,
    ):
        self.on_message = on_message
        self.on_error = on_error
        self.addr = addr

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.addr,
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
        except (
            websocket.WebSocketConnectionClosedException,
            ssl.SSLError,
            OSError,
        ) as e:
            print(f"Failed to send message: {e}")
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
        self.connect()


class _JSWS:
    def __init__(
        self,
        addr: str,
        on_message: typing.Callable | None = None,
        on_error: typing.Callable | None = None,
    ):
        self.on_message = on_message
        self.on_error = on_error
        self.addr = addr

    def connect(self):
        self.ws = websocket.new(self.addr)
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
        pass
        # eventデータの中身がわからないので、一旦コメントアウト
        # if self.on_error:
        #     self.on_error(event)

    def _on_close(self, event):
        # close_status_code = event.code
        # close_msg = event.reason
        print("WebSocket closed, attempting to reconnect...")
        self.connect()


try:
    import websocket
    import ssl

    WS = _PyWS
except ImportError:
    from js import WebSocket as websocket

    WS = _JSWS


class Comm:
    others: dict[str, typing.Any]
    last_send: tuple[float, dict[str, typing.Any]]
    last_recvd: dict[str, float]

    def __init__(self, addr: str):
        self.others = {}
        self.last_send = (time.time(), {})
        self.last_recvd = {}

        # Websocket
        self.ws = WS(addr, self.on_message, self.on_error)
        try:
            self.ws.connect()
        except Exception:
            print("Failed to connect to server. Skipped.")

    def on_message(self, data):
        if data["type"] == "connected":
            print("Connected to server, Clients:", data["clients"])
        elif data["type"] == "disconnect":
            self.on_error(data["id"])
        elif data["type"] == "update":
            new_at = data.get("time", time.time())
            if self.last_recvd.get(data["id"], 0) < new_at:
                self.others[data["id"]] = data
                self.last_recvd[data["id"]] = new_at

    def on_error(self, error):
        try:
            del self.others[error]
            del self.last_recvd[error]
        except Exception:
            print(f"WebSocket error: {error!r}")

    def send(self, **kwargs):
        at, data = self.last_send
        now = time.time()
        if kwargs == data and now - at < 1:
            return
        self.last_send = (now, kwargs)
        kwargs = kwargs | {"time": now}
        self.ws.send(**kwargs)


class SampleApp:
    def __init__(self):
        # pyxel.init(...)
        self.comm = Comm(WS_ADDR)
        self.x = 0
        self.y = 0
        # pyxel.run(self.update, self.draw)

    def update(self):
        self.comm.send(id=id(self), x=self.x, y=self.y)

    def draw(self):
        for other in self.comm.others.values():
            pyxel.circb(other["x"], other["y"], 5, 8)
        # myself
        pyxel.circb(self.x, self.y, 5, 7)
