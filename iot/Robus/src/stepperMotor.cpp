#include "stepperMotor.h"

const uint8_t StepperMotor::seq[8][4] = {
    {1,0,0,0},
    {1,1,0,0},
    {0,1,0,0},
    {0,1,1,0},
    {0,0,1,0},
    {0,0,1,1},
    {0,0,0,1},
    {1,0,0,1}
};

StepperMotor::StepperMotor(ShiftRegister595& reg, uint8_t offset)
    : _reg(reg), _offset(offset), _stepIndex(0), _stepDelayMs(2) {}

void StepperMotor::setStepDelay(uint16_t delayMs) {
    _stepDelayMs = delayMs;
}

void StepperMotor::step(bool direction) {
    _stepIndex = direction ? (_stepIndex + 1) % seqSteps
                           : (_stepIndex - 1 + seqSteps) % seqSteps;
    stepMotor(_stepIndex);
    delay(_stepDelayMs);
}

void StepperMotor::rotateSteps(long steps, bool direction) {
    for (long s = 0; s < steps; s++) {
        step(direction);
    }
    // _reg.write(0); ------------ do poprawy
}

void StepperMotor::stepMotor(int idx) {
     uint8_t mask = 0;
    for (int i = 0; i < 4; i++) {
        mask |= (1 << (_offset + i));
    }

    uint8_t val = 0;
    for (int i = 0; i < 4; i++) {
        if (seq[idx][i]) {
            val |= (1 << (_offset + i));
        }
    }

    uint8_t current = _reg.getState();      // ← aktualny stan 595
    current &= ~mask;                        // wyczyść tylko TEN silnik
    current |= val;                          // ustaw nowe fazy
    _reg.write(current);
}
