#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

#include "shiftregister.h"
#include "steppermotor.h"

/* ====== WIFI (AP MODE) ====== */
const char* ssid = "RobotAP";
const char* pass = "12345678";

/* ====== MOTORY ====== */
const int LATCH_PIN = D2;
const long STEPS_PER_REV = 4096;

ShiftRegister595 reg(LATCH_PIN);
StepperMotor motor1(reg, 0);
StepperMotor motor2(reg, 4);

/* ====== COMMAND ====== */
enum Direction { STOP, FRONT, BACK, LEFT, RIGHT };

struct Command {
    Direction dir;
    uint16_t duration_s;
};

QueueHandle_t commandQueue;

/* ====== WEBSOCKET ====== */
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

/* ====== MOTOR CONTROL ====== */
void stopMotors() {
    reg.write(0);
}

void move(Direction dir) {
    switch (dir) {
        case FRONT:
            motor1.step(true);
            motor2.step(false);
            break;
        case BACK:
            motor1.step(false);
            motor2.step(true);
            break;
        case LEFT:
            motor1.step(false);
            motor2.step(false);
            break;
        case RIGHT:
            motor1.step(true);
            motor2.step(true);
            break;
        default:
            stopMotors();
    }
}

/* ====== TASK: MOTORS ====== */
void taskMotors(void* pv) {
    Command cmd;

    for (;;) {
        if (xQueueReceive(commandQueue, &cmd, portMAX_DELAY)) {
            if (cmd.dir == STOP) {
                stopMotors();
                continue;
            }

            uint32_t endTime = millis() + cmd.duration_s * 1000UL;

            while (millis() < endTime) {
                move(cmd.dir);
                vTaskDelay(1 / portTICK_PERIOD_MS);
            }

            stopMotors();
        }
    }
}

/* ====== TASK: WEBSOCKET ====== */
void taskWebSocket(void* pv) {
    ws.onEvent([](AsyncWebSocket* server,
                  AsyncWebSocketClient* client,
                  AwsEventType type,
                  void* arg,
                  uint8_t* data,
                  size_t len) {

        if (type != WS_EVT_DATA) return;

        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, data, len);
        if (error) {
            Serial.println("JSON parse failed");
            return;
        }

        Command cmd{};
        String dir = doc["dir"] | "stop";
        cmd.duration_s = doc["duration"] | 0;

        if (dir == "front") cmd.dir = FRONT;
        else if (dir == "back") cmd.dir = BACK;
        else if (dir == "left") cmd.dir = LEFT;
        else if (dir == "right") cmd.dir = RIGHT;
        else cmd.dir = STOP;

        xQueueOverwrite(commandQueue, &cmd);

        // Dodajemy drukowanie do Serial Monitora
        Serial.print("Received command: ");
        Serial.print("dir=");
        Serial.print(dir);
        Serial.print(", duration=");
        Serial.println(cmd.duration_s);
    });

    server.addHandler(&ws);
    server.begin();

    for (;;) {
        ws.cleanupClients();
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}


/* ====== SETUP ====== */
void setup() {
    Serial.begin(115200);

    reg.begin(17, 15);

    // tryb Access Point
    WiFi.softAP(ssid, pass);
    IPAddress IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(IP);

    commandQueue = xQueueCreate(1, sizeof(Command));

    // Task do sterowania silnikami
    xTaskCreatePinnedToCore(
        taskMotors,
        "Motors",
        4096,
        nullptr,
        2,
        nullptr,
        1
    );

    // Task do WebSocket
    xTaskCreatePinnedToCore(
        taskWebSocket,
        "WebSocket",
        4096,
        nullptr,
        1,
        nullptr,
        1
    );

    Serial.println("Robot AP ready");
}

void loop() {
    // puste, wszystko obsługują taski
}
