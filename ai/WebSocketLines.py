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
DURATION = 1
FRAME_SIZE = (320, 240)

# ================= GLOBAL STATE =================

running = True
control_queue = asyncio.Queue(maxsize=1)

# ================= KEYBOARD THREAD =================

def keyboard_loop(loop):
    global running
    last_dir = None

    while running:
        if keyboard.is_pressed("w"):
            cur = "front"
        elif keyboard.is_pressed("s"):
            cur = "back"
        elif keyboard.is_pressed("a"):
            cur = "left"
        elif keyboard.is_pressed("d"):
            cur = "right"
        else:
            cur = None

        if cur != last_dir:
            def push():
                if not control_queue.full():
                    control_queue.put_nowait(cur)

            loop.call_soon_threadsafe(push)
            last_dir = cur

        time.sleep(0.03)

# ================= ASYNC TASKS =================

async def send_controls(ws):
    while running:
        direction = await control_queue.get()

        if direction is None:
            continue

        msg = {
            "dir": direction,
            "duration": DURATION
        }

        await ws.send(json.dumps(msg))


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
        loop = asyncio.get_running_loop()

        threading.Thread(
            target=keyboard_loop,
            args=(loop,),
            daemon=True
        ).start()

        await asyncio.gather(
            receive_frames(ws),   # receiver must stay responsive
            send_controls(ws)
        )

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        asyncio.run(ws_loop())
    except KeyboardInterrupt:
        running = False
        print("Stopped")
