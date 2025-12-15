#ifndef SHIFTREGISTER_H
#define SHIFTREGISTER_H

#include <Arduino.h>
#include <SPI.h>

class ShiftRegister595 {
public:
    ShiftRegister595(uint8_t latchPin);
    void begin(uint8_t sckPin, uint8_t mosiPin);
    void write(uint8_t data);

private:
    uint8_t _latchPin;
};

#endif
