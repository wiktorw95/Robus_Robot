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

CMD_URI = f"ws://{ROBOT_IP}/ws/cmd"
CAM_URI = f"ws://{ROBOT_IP}/ws/cam"

FRAME_SIZE = (320, 240)

COMMAND_DURATION = 1     # SECONDS (IMPORTANT)
SEND_INTERVAL = 0.3      # seconds

running = True
current_dir = None
last_sent_dir = None

# ================= LOG =================

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

# ================= KEYBOARD =================

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

# ================= CONTROL =================

async def control_loop():
    global last_sent_dir

    try:
        async with websockets.connect(CMD_URI) as ws:
            log("CONTROL connected")

            while running:
                if current_dir != last_sent_dir:
                    if current_dir is None:
                        msg = {"dir": "stop", "duration": 0}
                    else:
                        msg = {
                            "dir": current_dir,
                            "duration": COMMAND_DURATION
                        }

                    await ws.send(json.dumps(msg))
                    last_sent_dir = current_dir

                await asyncio.sleep(SEND_INTERVAL)

    except Exception as e:
        log(f"CONTROL error: {e}")

    finally:
        log("CONTROL disconnected")

# ================= CAMERA =================

async def camera_loop():
    global running

    try:
        async with websockets.connect(CAM_URI, max_size=None) as ws:
            log("CAMERA connected")

            async for msg in ws:
                if not running:
                    break

                if not isinstance(msg, bytes):
                    continue

                img = np.frombuffer(msg, dtype=np.uint8)
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
                    running = False
                    break

    except Exception as e:
        log(f"CAMERA error: {e}")

    finally:
        log("CAMERA disconnected")
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
        camera_loop()
    )

    log("Client stopped")

# ================= ENTRY =================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        running = False
        log("Interrupted")
