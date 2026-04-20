#include <Wire.h>

void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }
    Serial.println(F("=== I2C Scanner ==="));
    Serial.println(F("Arduino Micro: SDA=D2, SCL=D3"));
    Wire.begin();
}

void loop() {
    Serial.println(F("Scanning..."));
    byte count = 0;
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        byte err = Wire.endTransmission();
        if (err == 0) {
            Serial.print(F("  Found device at 0x"));
            if (addr < 16) Serial.print('0');
            Serial.print(addr, HEX);
            if (addr == 0x5A) Serial.print(F("  <- CCS811 (ADDR=LOW)"));
            if (addr == 0x5B) Serial.print(F("  <- CCS811 (ADDR=HIGH)"));
            if (addr == 0x76) Serial.print(F("  <- BME280 (SDO=LOW)"));
            if (addr == 0x77) Serial.print(F("  <- BME280 (SDO=HIGH)"));
            Serial.println();
            count++;
        } else if (err == 4) {
            Serial.print(F("  Unknown error at 0x"));
            if (addr < 16) Serial.print('0');
            Serial.println(addr, HEX);
        }
    }
    Serial.print(count);
    Serial.println(F(" device(s) found."));
    Serial.println();
    delay(5000);
}
