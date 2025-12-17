import asyncio
import websockets
import keyboard
import json

URI = "ws://192.168.4.1/ws"
DURATION = 2  # sekundy

async def send_cmd(dir, duration):
    async with websockets.connect(URI) as ws:
        msg = json.dumps({"dir": dir, "duration": duration})
        await ws.send(msg)


async def loop():
    while True:
        if keyboard.is_pressed("w"):
            await send_cmd("front", DURATION)
        elif keyboard.is_pressed("s"):
            await send_cmd("back", DURATION)
        elif keyboard.is_pressed("a"):
            await send_cmd("left", DURATION)
        elif keyboard.is_pressed("d"):
            await send_cmd("right", DURATION)
        await asyncio.sleep(0.1)


asyncio.run(loop())