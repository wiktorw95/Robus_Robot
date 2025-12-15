#include <Arduino.h>
#include "shiftregister.h"
#include "steppermotor.h"

const int LATCH_PIN = D2;
const int BUTTON_PIN = D14;
const long STEPS_PER_REV = 4096;

ShiftRegister595 reg(LATCH_PIN);
StepperMotor motor1(reg, 0); // Q0-Q3
StepperMotor motor2(reg, 4); // Q4-Q7

bool motorsOn = false;
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

void setup() {
    Serial.begin(115200);
    reg.begin(17, 15); // SCK=17, MOSI=15
    pinMode(BUTTON_PIN, INPUT);
    Serial.println("shiftregister + 2x28BYJ-48 ready");
}

void loop() {
    int reading = digitalRead(BUTTON_PIN);

    if (reading != lastButtonState) lastDebounceTime = millis();

    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading == LOW) {
            motorsOn = !motorsOn;
            Serial.println(motorsOn ? "Motors ON" : "Motors OFF");
            if (!motorsOn) reg.write(0);
            delay(200);
        }
    }

    lastButtonState = reading;

    if (motorsOn) {
        motor1.rotateSteps(STEPS_PER_REV, true);   // CW
        motor2.rotateSteps(STEPS_PER_REV, false);  // CCW
    } else {
        delay(100);
    }
}
