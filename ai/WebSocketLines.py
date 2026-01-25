import asyncio
import websockets
import keyboard
import json
import cv2
import numpy as np
import threading
import time

# ================= CONFIG =================

URI = "ws://192.168.4.1/ws"
DURATION = 0.2                 # short duration, sent repeatedly
SEND_HZ = 10                   # commands per second
FRAME_SIZE = (320, 240)

# ================= SHARED STATE =================

current_dir = None
running = True

# ================= KEYBOARD THREAD =================

def keyboard_loop():
    global current_dir, running

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

# ================= ASYNC TASKS =================

async def send_controls(ws):
    interval = 1.0 / SEND_HZ

    while running:
        if current_dir is not None:
            msg = {
                "dir": current_dir,
                "duration": DURATION
            }

            try:
                await ws.send(json.dumps(msg))
            except Exception:
                break

        await asyncio.sleep(interval)


async def receive_frames(ws):
    global running

    async for msg in ws:
        if not isinstance(msg, bytes):
            continue

        img = np.frombuffer(msg, dtype=np.uint8)
        frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
        if frame is None:
            continue

        frame = cv2.resize(frame, FRAME_SIZE)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 80, 160)

        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((frame, edges_bgr))

        cv2.imshow("Robot | Edges", combined)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            running = False
            break

# ================= MAIN =================

async def ws_loop():
    async with websockets.connect(URI, max_size=None) as ws:
        threading.Thread(
            target=keyboard_loop,
            daemon=True
        ).start()

        await asyncio.gather(
            receive_frames(ws),   # never block this
            send_controls(ws)
        )

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        asyncio.run(ws_loop())
    except KeyboardInterrupt:
        running = False
        print("Stopped")
