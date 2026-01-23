#ifndef STEPPERMOTOR_H
#define STEPPERMOTOR_H

#include <Arduino.h>
#include "shiftregister.h"

class StepperMotor {
public:
    StepperMotor(ShiftRegister595& reg, uint8_t offset);
    void step(bool direction);
    void rotateSteps(long steps, bool direction);
    void setStepDelay(uint16_t delayMs);

private:
    ShiftRegister595& _reg;
    uint8_t _offset;
    int _stepIndex;
    uint16_t _stepDelayMs;

    static const uint8_t seqSteps = 8;
    static const uint8_t seq[8][4];
    void stepMotor(int idx);
};

#endif
