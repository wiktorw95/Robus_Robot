import asyncio
import websockets
import keyboard
import json
import cv2
import numpy as np
import threading
import time
import datetime

# ================= CONFIG =================

ROBOT_IP = "192.168.4.1"

CONTROL_URI = f"ws://{ROBOT_IP}/ws/cmd"
VIDEO_URI   = f"ws://{ROBOT_IP}/ws/cam"

SEND_HZ = 5              # safer for embedded controllers
DURATION = 0.2
FRAME_SIZE = (320, 240)

# ================= GLOBAL STATE =================

current_dir = None
running = True

# ================= LOGGING =================

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

# ================= KEYBOARD THREAD =================

def keyboard_loop():
    global current_dir
    log("Keyboard thread started")

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

    log("Keyboard thread stopped")

# ================= CONTROL SOCKET =================

async def control_loop():
    interval = 1.0 / SEND_HZ

    try:
        async with websockets.connect(CONTROL_URI) as ws:
            log("CONTROL connected")

            while running:
                if current_dir:
                    msg = {
                        "dir": current_dir,
                        "duration": DURATION
                    }
                    await ws.send(json.dumps(msg))
                await asyncio.sleep(interval)

    except Exception as e:
        log(f"CONTROL error / disconnected: {e}")

    finally:
        log("CONTROL socket closed")

# ================= VIDEO SOCKET =================

async def video_loop():
    global running
    latest_frame = None

    try:
        async with websockets.connect(VIDEO_URI, max_size=None) as ws:
            log("VIDEO connected")

            async for msg in ws:
                if not running:
                    break

                if isinstance(msg, bytes):
                    # Keep ONLY the newest frame (drop old ones)
                    latest_frame = msg

                if latest_frame is None:
                    continue

                img = np.frombuffer(latest_frame, dtype=np.uint8)
                latest_frame = None

                frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                frame = cv2.resize(frame, FRAME_SIZE)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 80, 160)

                combined = np.hstack((
                    frame,
                    cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                ))

                cv2.imshow("Robot | Camera + Lines", combined)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    log("Quit requested by user")
                    running = False
                    break

    except Exception as e:
        log(f"VIDEO error / disconnected: {e}")

    finally:
        log("VIDEO socket closed")
        cv2.destroyAllWindows()

# ================= MAIN =================

async def main():
    log("Client starting")

    threading.Thread(
        target=keyboard_loop,
        daemon=True
    ).start()

    await asyncio.gather(
        control_loop(),
        video_loop()
    )

    log("Client stopped")

# ================= ENTRY =================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        running = False
        log("KeyboardInterrupt – exiting")
