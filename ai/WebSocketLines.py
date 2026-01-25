import asyncio
import websockets
import keyboard
import json
import cv2
import numpy as np
import threading
import time

# ================= CONFIG =================

ROBOT_IP = "192.168.4.1"

CONTROL_URI = f"ws://{ROBOT_IP}/ws/cmd"
VIDEO_URI   = f"ws://{ROBOT_IP}/ws/cam"

SEND_HZ = 10
DURATION = 0.2
FRAME_SIZE = (320, 240)

# ================= SHARED STATE =================

current_dir = None
running = True

# ================= KEYBOARD THREAD =================

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

# ================= CONTROL SOCKET =================

async def control_loop():
    interval = 1.0 / SEND_HZ

    async with websockets.connect(CONTROL_URI) as ws:
        while running:
            if current_dir:
                await ws.send(json.dumps({
                    "dir": current_dir,
                    "duration": DURATION
                }))
            await asyncio.sleep(interval)

# ================= VIDEO SOCKET =================

async def video_loop():
    global running

    async with websockets.connect(VIDEO_URI, max_size=None) as ws:
        async for msg in ws:
            if not isinstance(msg, bytes):
                continue

            img = np.frombuffer(msg, dtype=np.uint8)
            frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Resize
            frame = cv2.resize(frame, FRAME_SIZE)

            # 🔁 FIX: rotate camera 180° (upside-down fix)
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            # Edge detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 80, 160)

            combined = np.hstack((
                frame,
                cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            ))

            cv2.imshow("Robot | Camera + Lines", combined)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False
                break

    cv2.destroyAllWindows()

# ================= MAIN =================

async def main():
    threading.Thread(target=keyboard_loop, daemon=True).start()

    await asyncio.gather(
        control_loop(),
        video_loop()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        running = False
        print("Stopped")
