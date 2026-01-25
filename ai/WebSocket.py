import asyncio
import websockets
import keyboard
import json
import threading
import time

ROBOT_IP = "192.168.4.1"
CONTROL_URI = f"ws://192.168.4.1/cmd"

SEND_HZ = 10
DURATION = 0.2

current_dir = None
running = True

def keyboard_loop():
    global current_dir
    while running:
        if keyboard.is_pressed("w"):
            current_dir = "front"
        elif keyboard.is_pressed("s"):
            current_dir = "back"
        elif keyboard.is_pressed("a"):
            current_dir = "left"
        elif keyboard.is_pressed("d"):
            current_dir = "right"
        else:
            current_dir = None
        time.sleep(0.01)

async def control_loop():
    async with websockets.connect(CONTROL_URI) as ws:
        interval = 1 / SEND_HZ
        while running:
            if current_dir:
                await ws.send(json.dumps({
                    "dir": current_dir,
                    "duration": DURATION
                }))
            await asyncio.sleep(interval)

async def main():
    threading.Thread(target=keyboard_loop, daemon=True).start()
    await control_loop()

if __name__ == "__main__":
    asyncio.run(main())
