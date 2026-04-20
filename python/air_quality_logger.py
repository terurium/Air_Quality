"""
Air Quality Logger

Arduino Micro (examples/Micro_Serial_CCS811_BME280) からUSBシリアル経由で
受信したCSVデータを、タイムスタンプ付きでファイルに追記する。

使い方:
    python3 air_quality_logger.py

依存:
    pyserial (pip install pyserial)
"""

import csv
import datetime
import sys

import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 115200
OUTPUT_FILE = "air_quality.csv"
TIMEOUT_SEC = 120  # Arduino側が60秒周期のため余裕を持たせる


def main() -> None:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT_SEC)
    except serial.SerialException as e:
        print(f"シリアルポート {SERIAL_PORT} を開けませんでした: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"ログ開始: {SERIAL_PORT} -> {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        try:
            while True:
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line or line.startswith("#"):
                    # ヘッダ・コメント行は無視
                    continue

                fields = line.split(",")
                if len(fields) != 5:
                    # 想定外の行はスキップ
                    continue

                timestamp = datetime.datetime.now().isoformat(timespec="seconds")
                writer.writerow([timestamp] + fields)
                f.flush()
                print(f"{timestamp},{','.join(fields)}")
        except KeyboardInterrupt:
            print("\n終了します")
        finally:
            ser.close()


if __name__ == "__main__":
    main()
