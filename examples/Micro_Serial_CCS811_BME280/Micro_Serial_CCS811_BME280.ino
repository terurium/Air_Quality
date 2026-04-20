/*
 * Arduino Micro + CCS811 + BME280
 * SparkFun公式サンプル Example2_BME280Compensation.ino をベースにした、
 * Arduino Micro (ATmega32U4) 向けの移植版。
 * 温度/湿度/気圧/CO2/TVOC を測定し、USBシリアル(CSV形式)で出力する。
 * ラズパイ等のホストから /dev/ttyACM0 で読み取る想定。
 *
 * 出力形式:
 *   起動時 : "# Air Quality Sensor (Arduino Micro)"
 *            "# temp,humid,pressure,co2,tvoc"
 *            "# init done"
 *   測定毎 : "25.12,55.30,1013.25,450,12"
 *   エラー : "# ..." で始まるコメント行
 *
 * 配線 (Arduino Micro):
 *   Micro 3.3V -> CCS811 VCC, BME280 VCC
 *   Micro GND  -> CCS811 GND, BME280 GND, CCS811 nWAKE (常時LOW)
 *   Micro D2   -> SDA (レベルシフタ経由でセンサーSDAへ)
 *   Micro D3   -> SCL (レベルシフタ経由でセンサーSCLへ)
 *   CCS811 nRESET: 未接続でも可 (本コードは制御しない)
 *
 *   ※ Uno系の記事ではSDA=A4, SCL=A5だが、MicroはD2/D3固定。
 *   ※ CCS811のADDRピン: HIGH=0x5B, LOW=0x5A (本コードは0x5B前提)
 */
#include <Wire.h>
#include "BME280.h"
#include "SparkFunCCS811.h"

#define CCS811_ADDR 0x5B

CCS811 ccs811(CCS811_ADDR);
BME280 bme280;

void setup()
{
    Serial.begin(115200);
    // Arduino Microは USB-CDC のため、シリアルモニタが接続されるまで待つ。
    // タイムアウト5秒 (ラズパイ側の接続が遅れても永久ブロックしない)。
    unsigned long t0 = millis();
    while (!Serial && (millis() - t0) < 5000) {
        delay(10);
    }
    delay(200);
    Serial.println(F("# Air Quality Sensor (Arduino Micro)"));
    Serial.println(F("# temp,humid,pressure,co2,tvoc"));

    Wire.begin(); // Microの固定I2Cピン (SDA=D2, SCL=D3)

    // I2Cスキャン(配線確認用)
    Serial.println(F("# I2C scan:"));
    byte found = 0;
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        byte err = Wire.endTransmission();
        if (err == 0) {
            Serial.print(F("#   0x"));
            if (addr < 16) Serial.print('0');
            Serial.print(addr, HEX);
            if (addr == 0x5A || addr == 0x5B) {
                Serial.print(F(" (CCS811 candidate)"));
            } else if (addr == 0x76 || addr == 0x77) {
                Serial.print(F(" (BME280 candidate)"));
            }
            Serial.println();
            found++;
        }
    }
    Serial.print(F("# scan done, "));
    Serial.print(found);
    Serial.println(F(" device(s) found"));

    // CCS811初期化 (内部でsetDriveMode(1) = 1秒毎測定)
    CCS811Core::status returnCode = ccs811.begin();
    if (returnCode != CCS811Core::SENSOR_SUCCESS) {
        Serial.print(F("# CCS811 begin() error: 0x"));
        Serial.println(returnCode, HEX);
        while (1) { delay(1000); }
    }

    delay(10); // BME280の起動待ち (データシートで2ms程度要)
    bme280.begin();

    Serial.println(F("# init done"));
}

void loop()
{
    if (ccs811.dataAvailable()) {
        ccs811.readAlgorithmResults();

        float temp = (float)bme280.readTemperature();
        float humid = (float)bme280.readHumidity();
        float pressure = (float)bme280.readPressure();
        uint16_t CO2 = ccs811.getCO2();
        uint16_t TVOC = ccs811.getTVOC();

        // BME280の値をCCS811へフィードバック(次回の補正に使用)
        ccs811.setEnvironmentalData(humid, temp);

        // CSV出力: temp,humid,pressure,co2,tvoc
        Serial.print(temp, 2);
        Serial.print(',');
        Serial.print(humid, 2);
        Serial.print(',');
        Serial.print(pressure, 2);
        Serial.print(',');
        Serial.print(CO2);
        Serial.print(',');
        Serial.println(TVOC);
    }
    delay(60000); // 60秒周期で出力 (1分に1回ログ記録)
}
