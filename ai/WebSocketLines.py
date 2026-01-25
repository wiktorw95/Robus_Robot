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
SEND_INTERVAL = 0.05          # seconds
FRAME_WIDTH = 320             # downscale for speed
FRAME_HEIGHT = 240

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
        time.sleep(0.02)

# ================= ASYNC TASKS =================

async def send_controls(ws):
    last_sent = None

    while running:
        if current_dir and current_dir != last_sent:
            msg = {
                "dir": current_dir,
                "duration": DURATION
            }
            await ws.send(json.dumps(msg))
            last_sent = current_dir

        if current_dir is None:
            last_sent = None

        await asyncio.sleep(SEND_INTERVAL)


async def receive_frames(ws):
    global running

    async for msg in ws:
        if not isinstance(msg, bytes):
            continue

        img = np.frombuffer(msg, dtype=np.uint8)
        frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
        if frame is None:
            continue

        # Resize for speed
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Image processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 100, 200)

        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        combined = np.hstack((frame, edges_bgr))

        cv2.imshow("Robot View | Edges", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break


# ================= MAIN =================

async def ws_loop():
    print(f"Connecting to {URI}...")

    async with websockets.connect(URI, max_size=None) as ws:
        print("Connected to robot")

        await asyncio.gather(
            send_controls(ws),
            receive_frames(ws)
        )

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        threading.Thread(target=keyboard_loop, daemon=True).start()
        asyncio.run(ws_loop())
    except KeyboardInterrupt:
        running = False
        print("Program stopped")

