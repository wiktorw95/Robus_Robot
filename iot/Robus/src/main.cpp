#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "DFRobot_AXP313A.h"
#include "esp_task_wdt.h"

#include <U8g2lib.h>
#include <Wire.h>

#include "shiftregister.h"
#include "steppermotor.h"

/* ================= OLED ================= */
#define SDA_OLED D7
#define SCL_OLED D9

U8G2_SSD1306_64X48_ER_F_SW_I2C u8g2(
    U8G2_R0,
    SCL_OLED,
    SDA_OLED,
    U8X8_PIN_NONE
);

int eyeXOffset = 2;
int eyeDir = 1;
int blinkCounter = 0;
bool eyesOpen = true;

/* ================= WIFI ================= */
const char* ssid = "Kerfus";
const char* pass = "12345678";

/* ================= MOTORS ================= */
const int LATCH_PIN = D2;
ShiftRegister595 reg(LATCH_PIN);
StepperMotor motor1(reg, 0);
StepperMotor motor2(reg, 4);

/* ================= COMMAND ================= */
enum Direction { STOP, FRONT, BACK, LEFT, RIGHT };

struct Command {
    Direction dir;
    uint16_t duration_s;
};

QueueHandle_t commandQueue;

/* ================= WEBSOCKET ================= */
AsyncWebServer server(80);
AsyncWebSocket wsCam("/ws/cam");
AsyncWebSocket wsCmd("/ws/cmd");

AsyncWebSocketClient* cameraClient = nullptr;

/* ================= CAMERA ================= */
DFRobot_AXP313A axp;
QueueHandle_t camQueue;

/* CAMERA PINS */
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    45
#define SIOD_GPIO_NUM    1
#define SIOC_GPIO_NUM    2
#define Y2_GPIO_NUM      39
#define Y3_GPIO_NUM      40
#define Y4_GPIO_NUM      41
#define Y5_GPIO_NUM      4
#define Y6_GPIO_NUM      7
#define Y7_GPIO_NUM      8
#define Y8_GPIO_NUM      46
#define Y9_GPIO_NUM      48
#define VSYNC_GPIO_NUM   6
#define HREF_GPIO_NUM    42
#define PCLK_GPIO_NUM    5

/* ================= OLED ================= */
void drawKerfusFace(int eyeOffset, bool eyesOpen) {
    u8g2.clearBuffer();
    u8g2.drawFrame(5, 5, 54, 38);

    u8g2.drawHLine(13 + eyeOffset, 13, 8);
    u8g2.drawHLine(33 + eyeOffset, 13, 8);

    if (eyesOpen) {
        u8g2.drawBox(14 + eyeOffset, 15, 6, 6);
        u8g2.drawBox(34 + eyeOffset, 15, 6, 6);
        u8g2.setDrawColor(0);
        u8g2.drawPixel(16 + eyeOffset, 17);
        u8g2.drawPixel(36 + eyeOffset, 17);
        u8g2.setDrawColor(1);
    } else {
        u8g2.drawHLine(14 + eyeOffset, 18, 6);
        u8g2.drawHLine(34 + eyeOffset, 18, 6);
    }

    u8g2.sendBuffer();
}

/* ================= MOTORS ================= */
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

/* ================= TASK: OLED ================= */
void taskDisplay(void* pv) {
    esp_task_wdt_add(NULL);

    u8g2.begin();
    for (;;) {
        eyeXOffset += eyeDir;
        if (eyeXOffset <= 0 || eyeXOffset >= 4)
            eyeDir = -eyeDir;

        blinkCounter++;
        if (blinkCounter >= 20) {
            eyesOpen = !eyesOpen;
            blinkCounter = 0;
        }

        drawKerfusFace(eyeXOffset, eyesOpen);
        vTaskDelay(pdMS_TO_TICKS(150));
    }
}

/* ================= TASK: MOTORS ================= */
void taskMotors(void* pv) {
    esp_task_wdt_add(NULL);

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
                vTaskDelay(pdMS_TO_TICKS(2));
            }
            stopMotors();
        }
    }
}

/* ================= WS CAMERA ================= */
void onWsCamEvent(AsyncWebSocket*,
                  AsyncWebSocketClient* client,
                  AwsEventType type,
                  void*, uint8_t*, size_t) {

    if (type == WS_EVT_CONNECT) {
        cameraClient = client;
        Serial.println("Camera WS connected");
    }

    if (type == WS_EVT_DISCONNECT) {
        if (cameraClient == client)
            cameraClient = nullptr;
        Serial.println("Camera WS disconnected");
    }
}

/* ================= WS COMMAND ================= */
void onWsCmdEvent(AsyncWebSocket*,
                  AsyncWebSocketClient*,
                  AwsEventType type,
                  void* arg,
                  uint8_t* data,
                  size_t len) {

    if (type != WS_EVT_DATA)
        return;

    AwsFrameInfo* info = (AwsFrameInfo*)arg;
    if (info->opcode != WS_TEXT)
        return;

    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, data, len))
        return;

    Command cmd{};
    String dir = doc["dir"] | "stop";
    cmd.duration_s = doc["duration"] | 0;

    if      (dir == "front") cmd.dir = FRONT;
    else if (dir == "back")  cmd.dir = BACK;
    else if (dir == "left")  cmd.dir = LEFT;
    else if (dir == "right") cmd.dir = RIGHT;
    else                     cmd.dir = STOP;

    xQueueOverwrite(commandQueue, &cmd);
}

/* ================= TASK: WS ================= */
void taskWebSocket(void* pv) {
    esp_task_wdt_add(NULL);
    
    wsCam.onEvent(onWsCamEvent);
    wsCmd.onEvent(onWsCmdEvent);

    server.addHandler(&wsCam);
    server.addHandler(&wsCmd);
    server.begin();

    for (;;) {
        wsCam.cleanupClients();
        wsCmd.cleanupClients();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

/* ================= CAMERA INIT ================= */
void taskCameraInit(void* pv) {
    esp_task_wdt_add(NULL);

    camera_config_t config{};
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.frame_size = FRAMESIZE_VGA;
    config.pixel_format = PIXFORMAT_JPEG;
    config.jpeg_quality = 30;
    config.fb_count = 4;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;

    if (esp_camera_init(&config) != ESP_OK) {
        Serial.println("Camera init failed");
        vTaskDelete(NULL);
    }

    Serial.println("Camera initialized");
    vTaskDelete(NULL);
}

/* ================= CAMERA CAPTURE ================= */
void taskCameraCapture(void* pv) {
    esp_task_wdt_add(NULL);

    camera_fb_t* fb;
    for (;;) {
        fb = esp_camera_fb_get();
        if (fb) {
            xQueueOverwrite(camQueue, &fb);
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

/* ================= CAMERA TX ================= */
void taskCameraTx(void* pv) {
    esp_task_wdt_add(NULL);
    
    camera_fb_t* fb;
    for (;;) {
        if (!cameraClient || !cameraClient->canSend()) {
            vTaskDelay(pdMS_TO_TICKS(20));
            continue;
        }

        if (xQueueReceive(camQueue, &fb, pdMS_TO_TICKS(50))) {
            cameraClient->binary(fb->buf, fb->len);
            esp_camera_fb_return(fb);
        }
    }
}

/* ================= SETUP ================= */
void setup() {
    Serial.begin(115200);
    reg.begin(17, 15);

    while (axp.begin() != 0) {
        delay(500);
    }
    axp.enableCameraPower(axp.eOV2640);

    WiFi.mode(WIFI_AP);
    WiFi.softAP(ssid, pass);
    Serial.println(WiFi.softAPIP());

    commandQueue = xQueueCreate(1, sizeof(Command));
    camQueue = xQueueCreate(1, sizeof(camera_fb_t*));

    xTaskCreatePinnedToCore(taskMotors, "Motors", 8096, NULL, 3, NULL, 0);
    xTaskCreatePinnedToCore(taskDisplay, "Display", 8096, NULL, 1, NULL, 0);
    xTaskCreatePinnedToCore(taskWebSocket, "WebSocket", 16096, NULL, 2, NULL, 1);

    delay(1000);
    xTaskCreatePinnedToCore(taskCameraInit, "CameraInit", 8096, NULL, 4, NULL, 0);
    delay(1000);
    xTaskCreatePinnedToCore(taskCameraCapture, "CameraCap", 32096, NULL, 1, NULL, 1);
    xTaskCreatePinnedToCore(taskCameraTx, "CameraTx", 32096, NULL, 1, NULL, 1);

    Serial.println("Robot ready");
    Serial.printf("Free heap: %u bytes\n", ESP.getFreeHeap());
    Serial.printf("Free PSRAM: %u bytes\n", ESP.getFreePsram());

    // === TASK WATCHDOG INIT ===
    esp_task_wdt_init(5, true); // timeout 5s, auto-reset ESP przy zacięciu
}

void loop() {}
