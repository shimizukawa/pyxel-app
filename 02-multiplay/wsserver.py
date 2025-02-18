# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "websockets",
# ]
# ///
import asyncio
import json

import websockets

clients = set()


async def echo(websocket):
    _id = id(websocket)
    await websocket.send(
        json.dumps({"id": _id, "type": "connected", "clients": len(clients) + 1})
    )
    clients.add(websocket)
    print(f"Client {_id} connected, count: {len(clients)}")
    try:
        async for message in websocket:
            data = json.loads(message)
            for client in clients:
                if client != websocket:
                    data |= {"id": _id, "type": "update"}
                    try:
                        await client.send(json.dumps(data))
                    except:
                        pass
    except websockets.exceptions.ConnectionClosedError:
        pass

    if websocket in clients:
        clients.remove(websocket)
        print(f"Client {_id} disconnected, count: {len(clients)}")

    for client in clients:
        try:
            await client.send(json.dumps({"id": _id, "type": "disconnect"}))
        except websockets.exceptions.ConnectionClosedError:
            pass

    print("exit echo")


async def main():
    async with websockets.serve(echo, "127.0.0.1", 9999):
        print("Server started, count: 0")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
