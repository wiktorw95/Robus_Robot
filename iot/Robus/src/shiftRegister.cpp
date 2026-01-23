#include "shiftregister.h"

ShiftRegister595::ShiftRegister595(uint8_t latchPin) : _latchPin(latchPin), _state(0) {}

void ShiftRegister595::begin(uint8_t sckPin, uint8_t mosiPin) {
    pinMode(_latchPin, OUTPUT);
    digitalWrite(_latchPin, HIGH);
    SPI.begin(sckPin, -1, mosiPin, -1);
}

void ShiftRegister595::write(uint8_t data) {
    _state = data;
    digitalWrite(_latchPin, LOW);
    SPI.transfer(data);
    digitalWrite(_latchPin, HIGH);
}