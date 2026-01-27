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

FRAME_SIZE = (640, 480)

EDGE_ZONE_RATIO = 0.20
EDGE_THRESHOLD = 2500

FORWARD_MIN = 10
FORWARD_MAX = 30
TURN_TIME = 5

RECONNECT_DELAY = 2

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

# ================= CAMERA TASK =================

async def camera_task():
    global edge_detected, running

    FRAME_TIMEOUT = 0.5

    while running:
        last_frame_time = asyncio.get_event_loop().time()

        try:
            log("CAMERA connecting...")
            async with websockets.connect(CAM_URI, max_size=None) as ws:
                log("CAMERA connected")

                while running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=FRAME_TIMEOUT)
                        last_frame_time = asyncio.get_event_loop().time()
                    except asyncio.TimeoutError:
                        log("CAMERA frame timeout — reconnecting")
                        break

                    if not isinstance(msg, bytes):
                        continue

                    img = np.frombuffer(msg, dtype=np.uint8)
                    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    frame = cv2.resize(frame, FRAME_SIZE)
                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (5, 5), 0)

                    edges = cv2.Canny(gray, 50, 150)

                    # --- focus on bottom region ---
                    h, w = edges.shape
                    zone_h = int(h * EDGE_ZONE_RATIO)
                    roi = edges[h - zone_h: h, :]

                    # --- thicken edges ---
                    kernel = np.ones((5, 5), np.uint8)
                    roi_thick = cv2.dilate(roi, kernel, iterations=1)

                    # --- detect lines ---
                    lines = cv2.HoughLinesP(
                        roi_thick,
                        rho=1,
                        theta=np.pi / 180,
                        threshold=50,
                        minLineLength=w // 4,
                        maxLineGap=40
                    )

                    edge_detected = False

                    if lines is not None:
                        for line in lines:
                            x1, y1, x2, y2 = line[0]
                            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                            if angle < 20:  # near-horizontal
                                edge_detected = True
                                break

                    # --- visual debug ---
                    vis = frame.copy()
                    cv2.rectangle(
                        vis,
                        (0, h - zone_h),
                        (w, h),
                        (0, 0, 255) if edge_detected else (0, 255, 0),
                        2
                    )

                    if lines is not None:
                        for line in lines:
                            x1, y1, x2, y2 = line[0]
                            cv2.line(
                                vis,
                                (x1, y1 + h - zone_h),
                                (x2, y2 + h - zone_h),
                                (255, 0, 0),
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

        except Exception as e:
            log(f"CAMERA socket error: {e}")

        finally:
            edge_detected = False
            cv2.destroyAllWindows()

            if running:
                log("CAMERA reconnecting immediately...")
                await asyncio.sleep(0)  # yield only

# ================= AUTONOMY TASK =================

async def autonomy_task():
    global edge_detected, running

    while running:
        try:
            log("CONTROL connecting...")
            async with websockets.connect(CMD_URI) as ws:
                log("CONTROL connected")

                while running:
                    # ---- DRIVE FORWARD ----
                    drive_time = random.randint(FORWARD_MIN, FORWARD_MAX)
                    log(f"Driving forward ({drive_time}s)")

                    await ws.send(json.dumps({
                        "dir": "front",
                        "duration": drive_time
                    }))

                    start = asyncio.get_event_loop().time()
                    interrupted = False

                    while asyncio.get_event_loop().time() - start < drive_time:
                        if edge_detected:
                            log("EDGE DETECTED — emergency stop & turn")
                            await ws.send(json.dumps({"dir": "stop", "duration": 0}))
                            await asyncio.sleep(0.1)

                            turn = random.choice(["left", "right"])
                            await send_cmd(ws, turn, TURN_TIME)

                            interrupted = True
                            break

                        await asyncio.sleep(0.05)

                    if interrupted:
                        edge_detected = False
                        continue

                    # ---- NORMAL TURN ----
                    turn = random.choice(["left", "right"])
                    await send_cmd(ws, turn, TURN_TIME)

        except Exception as e:
            log(f"CONTROL disconnected: {e}")
            if running:
                log(f"Reconnecting control in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)

# ================= MAIN =================

async def main():
    log("Autonomous system starting")

    await asyncio.gather(
        camera_task(),
        autonomy_task()
    )

    log("System stopped")

# ================= ENTRY =================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        running = False
        log("Interrupted by user")
