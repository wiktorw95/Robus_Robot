import asyncio
import websockets
import keyboard
import json
import cv2
import numpy as np

URI = "ws://192.168.1.50/ws"
DURATION = 1


async def ws_loop():
    async with websockets.connect(URI, max_size=None) as ws:
        print("Connected")

        async def send_controls():
            while True:
                if keyboard.is_pressed("w"):
                    await ws.send(json.dumps({"dir": "front", "duration": DURATION}))
                elif keyboard.is_pressed("s"):
                    await ws.send(json.dumps({"dir": "back", "duration": DURATION}))
                elif keyboard.is_pressed("a"):
                    await ws.send(json.dumps({"dir": "left", "duration": DURATION}))
                elif keyboard.is_pressed("d"):
                    await ws.send(json.dumps({"dir": "right", "duration": DURATION}))
                await asyncio.sleep(0.1)

        async def receive_frames():
            async for msg in ws:
                if isinstance(msg, bytes):
                    img = np.frombuffer(msg, dtype=np.uint8)
                    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("ESP32 Camera", frame)
                        cv2.waitKey(1)

        await asyncio.gather(send_controls(), receive_frames())


asyncio.run(ws_loop())
