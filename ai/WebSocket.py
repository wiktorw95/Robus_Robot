# import asyncio
# import websockets
# import keyboard
# import json
# import cv2
# import numpy as np
#
# URI = "ws://192.168.1.50/ws"
# DURATION = 1
# SEND_RATE = 0.1  # seconds
#
# async def ws_loop():
#     async with websockets.connect(URI, max_size=None) as ws:
#         print("Connected")
#
#         async def send_controls():
#             while True:
#                 if keyboard.is_pressed("w"):
#                     await ws.send(json.dumps({"dir": "front", "duration": DURATION}))
#                 elif keyboard.is_pressed("s"):
#                     await ws.send(json.dumps({"dir": "back", "duration": DURATION}))
#                 elif keyboard.is_pressed("a"):
#                     await ws.send(json.dumps({"dir": "left", "duration": DURATION}))
#                 elif keyboard.is_pressed("d"):
#                     await ws.send(json.dumps({"dir": "right", "duration": DURATION}))
#
#                 await asyncio.sleep(SEND_RATE)
#
#         async def receive_frames():
#             async for msg in ws:
#                 if not isinstance(msg, bytes):
#                     continue
#
#                 img = np.frombuffer(msg, dtype=np.uint8)
#                 frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
#                 if frame is None:
#                     continue
#
#                 cv2.imshow("ESP32 Camera", frame)
#                 if cv2.waitKey(1) & 0xFF == ord("q"):
#                     break
#
#         await asyncio.gather(send_controls(), receive_frames())
#
#     cv2.destroyAllWindows()
#
# asyncio.run(ws_loop())
