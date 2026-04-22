"""
Air Quality Dashboard

air_quality_logger.py が書き出した CSV を読み、過去24時間分のデータを
10分平均でターミナルにグラフ表示する。天気予報 CLI (stormshell) と
3分ごとに交互に表示する。

使い方:
    python3 dashboard.py [CSVファイルパス]

依存:
    plotext (pip install plotext)
    stormshell (外部CLI、Raspberry Pi 側にインストール済み前提)
"""

import csv
import datetime
import os
import subprocess
import sys
import time
from collections import defaultdict

import plotext as plt

DEFAULT_CSV = "air_quality.csv"
BUCKET_MINUTES = 10
WINDOW_HOURS = 24
SWITCH_INTERVAL_SEC = 180  # 3分
STORMSHELL_CMD = ["stormshell", "--location", "Nagoya"]


def load_recent_rows(csv_path: str, window: datetime.timedelta) -> list[tuple[datetime.datetime, list[float]]]:
    """CSV を読み、現在から `window` 以内の行だけを返す。"""
    threshold = datetime.datetime.now() - window
    rows: list[tuple[datetime.datetime, list[float]]] = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 6:
                continue
            try:
                ts = datetime.datetime.fromisoformat(row[0])
                values = [float(v) for v in row[1:]]
            except ValueError:
                continue
            if ts < threshold:
                continue
            rows.append((ts, values))
    return rows


def bucket_average(
    rows: list[tuple[datetime.datetime, list[float]]],
    bucket_minutes: int,
) -> tuple[list[datetime.datetime], list[list[float]]]:
    """10分ごとにバケット化して平均値を返す。"""
    buckets: dict[datetime.datetime, list[list[float]]] = defaultdict(list)
    for ts, values in rows:
        bucket_key = ts.replace(
            minute=(ts.minute // bucket_minutes) * bucket_minutes,
            second=0,
            microsecond=0,
        )
        buckets[bucket_key].append(values)

    sorted_keys = sorted(buckets.keys())
    averaged: list[list[float]] = []
    for key in sorted_keys:
        group = buckets[key]
        col_count = len(group[0])
        avg = [sum(row[i] for row in group) / len(group) for i in range(col_count)]
        averaged.append(avg)
    return sorted_keys, averaged


def render_graph(csv_path: str) -> None:
    """CSV から直近24時間を読み出し、subplot でグラフを表示。"""
    try:
        rows = load_recent_rows(csv_path, datetime.timedelta(hours=WINDOW_HOURS))
    except FileNotFoundError:
        print(f"CSVファイルが見つかりません: {csv_path}", file=sys.stderr)
        return

    if not rows:
        print(f"直近{WINDOW_HOURS}時間のデータがありません: {csv_path}")
        return

    times, averaged = bucket_average(rows, BUCKET_MINUTES)
    time_labels = [t.strftime("%H:%M") for t in times]

    temp = [a[0] for a in averaged]
    humid = [a[1] for a in averaged]
    pressure = [a[2] for a in averaged]
    co2 = [a[3] for a in averaged]
    tvoc = [a[4] for a in averaged]

    plt.clf()
    plt.clt()
    plt.subplots(3, 2)
    plt.theme("dark")

    metrics = [
        ("Temperature (C)", temp, "red"),
        ("Humidity (%)", humid, "cyan"),
        ("Pressure (hPa)", pressure, "green"),
        ("CO2 (ppm)", co2, "yellow"),
        ("TVOC (ppb)", tvoc, "magenta"),
    ]

    tick_indices = [i for i, t in enumerate(times) if t.hour % 3 == 0 and t.minute == 0]
    if not tick_indices:
        tick_indices = [0, len(times) // 2, len(times) - 1]
    tick_labels = [time_labels[i] for i in tick_indices]

    for idx, (title, series, color) in enumerate(metrics):
        row = idx // 2 + 1
        col = idx % 2 + 1
        plt.subplot(row, col)
        plt.plot(series, color=color)
        plt.title(title)
        plt.xticks(tick_indices, tick_labels)

    plt.show()
    print(
        f"\n範囲: {times[0].isoformat(timespec='minutes')} 〜 "
        f"{times[-1].isoformat(timespec='minutes')}  "
        f"({len(times)}バケット、{BUCKET_MINUTES}分平均)"
    )


def _terminate(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def render_stormshell(display_sec: int) -> None:
    """stormshell を起動し、display_sec 経過後に終了させる。

    stdin を切り離し、新しいプロセスグループで起動することで、
    端末からの Ctrl+C は Python 側に届くようにする (stormshell が
    raw モードで端末を掴んでも Ctrl+C が効くようにするため)。
    """
    try:
        proc = subprocess.Popen(
            STORMSHELL_CMD,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError:
        print("stormshell が見つかりません。インストールしてください。", file=sys.stderr)
        time.sleep(display_sec)
        return

    try:
        proc.wait(timeout=display_sec)
    except subprocess.TimeoutExpired:
        _terminate(proc)
    except KeyboardInterrupt:
        _terminate(proc)
        raise


def clear_screen() -> None:
    os.system("clear" if os.name != "nt" else "cls")


def render_graph_and_wait(csv_path: str, display_sec: int) -> None:
    render_graph(csv_path)
    time.sleep(display_sec)


def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_CSV

    renderers = [
        ("Stormshell (Nagoya)", lambda: render_stormshell(SWITCH_INTERVAL_SEC)),
        ("Air Quality (24h / 10min avg)", lambda: render_graph_and_wait(csv_path, SWITCH_INTERVAL_SEC)),
    ]
    idx = 0

    try:
        while True:
            clear_screen()
            label, fn = renderers[idx]
            print(f"=== {label} ===  (次の切替まで {SWITCH_INTERVAL_SEC}秒)")
            fn()
            idx = (idx + 1) % len(renderers)
    except KeyboardInterrupt:
        print("\n終了します")


if __name__ == "__main__":
    main()
