# 空気品質センサー

空気品質センサーと温湿度、気圧センサーで、温度、湿度、気圧、CO2、TVOC(総揮発性有機化合物)などを測定し、[Ambient](https://ambidata.io)に送信するサンプルプログラムです。

* CCS811_test: 空気品質センサーCCS811の動作確認プログラム

* Ambient_CCS811_BME280: 空気品質センサーCCS811と温湿度、気圧センサーBME280で温度、湿度、気圧、CO2、TVOCを測定し、Ambientに送信するプログラム。

* Ambient_GPS_BME280_CCS811: GPSモジュールと空気品質センサーCCS811と温湿度、気圧センサーBME280で、いろいろな場所の温度、湿度、気圧、CO2を測定し、位置情報をつけてAmbientに送信するプログラム。

* Micro_Serial_CCS811_BME280: Arduino Micro (ATmega32U4) 向けサンプル。WiFiを使わず、温度/湿度/気圧/CO2/TVOCをUSBシリアル(CSV形式)で出力する。ラズパイ等のホストに接続してロギングする想定。

## python/

* air_quality_logger.py: `Micro_Serial_CCS811_BME280` の出力を受信し、タイムスタンプ付きでCSVファイルに追記するロガースクリプト。`pip install pyserial` が必要。
