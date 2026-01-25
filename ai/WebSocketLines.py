import asyncio
import websockets
import keyboard
import json
import cv2
import numpy as np

URI = "ws://192.168.1.50/ws"
DURATION = 1


async def ws_loop():
    print(f"Łączenie z {URI}...")
    async with websockets.connect(URI, max_size=None) as ws:
        print("Połączono z robotem")

        async def send_controls():
            while True:
                # Sterowanie (bez zmian)
                if keyboard.is_pressed("w"):
                    await ws.send(json.dumps({"dir": "front", "duration": DURATION}))
                elif keyboard.is_pressed("s"):
                    await ws.send(json.dumps({"dir": "back", "duration": DURATION}))
                elif keyboard.is_pressed("a"):
                    await ws.send(json.dumps({"dir": "left", "duration": DURATION}))
                elif keyboard.is_pressed("d"):
                    await ws.send(json.dumps({"dir": "right", "duration": DURATION}))
                await asyncio.sleep(0.1)

        async def receive_frames():
            async for msg in ws:
                if isinstance(msg, bytes):
                    img = np.frombuffer(msg, dtype=np.uint8)
                    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

                    if frame is not None:
                        # 1. Konwersja do skali szarości (wymagane dla algorytmu Canny)
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # 2. Wykrywanie krawędzi (Algorytm Canny)
                        # Parametry 100 i 200 to progi histerezy (min i max).
                        # Możesz je zmieniać, aby wykrywać mniej lub więcej szczegółów.
                        edges = cv2.Canny(gray, 100, 200)

                        # Opcjonalnie: Wyświetlanie obu obrazów obok siebie
                        # Musimy przekonwertować edges z powrotem na BGR, żeby połączyć je z frame
                        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                        combined = np.hstack((frame, edges_bgr))

                        # Wyświetlanie
                        cv2.imshow("Widok Robota + Krawedzie", combined)

                        # Jeśli chcesz widzieć TYLKO krawędzie, odkomentuj linię poniżej
                        # cv2.imshow("Tylko Krawedzie", edges)

                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

        await asyncio.gather(send_controls(), receive_frames())

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        asyncio.run(ws_loop())
    except KeyboardInterrupt:
        print("Zatrzymano program")
