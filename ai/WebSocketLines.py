import asyncio
import websockets
import cv2
import numpy as np

ROBOT_IP = "192.168.4.1"
VIDEO_URI = f"ws://192.168.4.1/ws/cam"

FRAME_SIZE = (320, 240)

async def video_loop():
    async with websockets.connect(VIDEO_URI, max_size=None) as ws:
        async for msg in ws:
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
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(video_loop())
