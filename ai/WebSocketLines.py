import asyncio
import websockets
import json
import cv2
import numpy as np
import random
import datetime

# ================= CONFIG =================

ROBOT_IP = "192.168.4.1"

CMD_URI = f"ws://{ROBOT_IP}/ws/cmd"
CAM_URI = f"ws://{ROBOT_IP}/ws/cam"

FRAME_SIZE = (320, 240)

EDGE_ZONE_RATIO = 0.20     # bottom 20% of frame
EDGE_THRESHOLD = 2500      # tune if needed

running = True
edge_detected = False

# ================= LOG =================

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

# ================= COMMAND SEND =================

async def send_cmd(ws, direction, duration):
    log(f"CMD: {direction} for {duration}s")
    await ws.send(json.dumps({
        "dir": direction,
        "duration": int(duration)
    }))
    await asyncio.sleep(duration)

# ================= CAMERA LOOP =================

async def camera_loop():
    global edge_detected, running

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

            # Fix upside-down camera
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 80, 160)

            h, w = edges.shape
            zone_h = int(h * EDGE_ZONE_RATIO)
            bottom_zone = edges[h - zone_h : h, :]

            edge_count = cv2.countNonZero(bottom_zone)
            edge_detected = edge_count > EDGE_THRESHOLD

            # Visual debug
            vis = frame.copy()
            cv2.rectangle(
                vis,
                (0, h - zone_h),
                (w, h),
                (0, 0, 255) if edge_detected else (0, 255, 0),
                2
            )

            combined = np.hstack((
                vis,
                cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            ))

            cv2.imshow("AUTO | Camera + Edge Detection", combined)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False
                break

    cv2.destroyAllWindows()
    log("CAMERA disconnected")

# ================= AUTONOMY LOOP =================

async def autonomy_loop():
    global edge_detected, running

    async with websockets.connect(CMD_URI) as ws:
        log("CONTROL connected")

        while running:
            # ---- DRIVE FORWARD ----
            drive_time = random.randint(1, 3)
            start = asyncio.get_event_loop().time()

            log(f"Driving forward ({drive_time}s)")
            await ws.send(json.dumps({
                "dir": "front",
                "duration": drive_time
            }))

            while asyncio.get_event_loop().time() - start < drive_time:
                if edge_detected:
                    log("EDGE DETECTED — emergency turn")
                    await ws.send(json.dumps({"dir": "stop", "duration": 0}))
                    await asyncio.sleep(0.1)

                    turn = random.choice(["left", "right"])
                    await send_cmd(ws, turn, 1)   # ~90°
                    break

                await asyncio.sleep(0.05)

            # ---- NORMAL TURN ----
            if not edge_detected:
                turn = random.choice(["left", "right"])
                turn_time = random.uniform(0.5, 1.0)  # ~30–90°
                await send_cmd(ws, turn, round(turn_time))

            edge_detected = False

    log("CONTROL disconnected")

# ================= MAIN =================

async def main():
    log("Autonomous client starting")

    await asyncio.gather(
        camera_loop(),
        autonomy_loop()
    )

    log("Stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        running = False
        log("Interrupted")
