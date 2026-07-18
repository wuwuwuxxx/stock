import datetime as dt
import subprocess
import time

import schedule

TRADING_MORNING = (dt.time(9, 30), dt.time(11, 30))
TRADING_AFTERNOON = (dt.time(13, 0), dt.time(15, 0))

# 财报披露密集月份：1月(年报预告)、4月(一季报+年报)、7月(中报预告)、
# 8月(中报)、10月(三季报)
REPORT_SEASON_MONTHS = {1, 4, 7, 8, 10}

# 不同场景下的调度间隔（分钟）
INTERVAL_TRADING_HOURS = 0      # 交易时段不跑
INTERVAL_REPORT_SEASON = 30     # 财报季、非交易时段
INTERVAL_OFF_SEASON = 120       # 非财报季、工作日
INTERVAL_WEEKEND_HOLIDAY = 240  # 周末/节假日


def is_trading_time(now: dt.datetime) -> bool:
    t = now.time()
    return (TRADING_MORNING[0] <= t <= TRADING_MORNING[1]
            or TRADING_AFTERNOON[0] <= t <= TRADING_AFTERNOON[1])


def is_weekend(now: dt.datetime) -> bool:
    return now.weekday() >= 5


def is_report_season(now: dt.datetime) -> bool:
    return now.month in REPORT_SEASON_MONTHS


def next_interval_minutes(now: dt.datetime) -> int:
    if is_trading_time(now):
        # 距离最近的非交易时段还有多久，避免空转
        if now.time() < TRADING_MORNING[0]:
            wait = (dt.datetime.combine(now.date(), TRADING_MORNING[0]) - now).total_seconds() / 60
        elif TRADING_MORNING[1] < now.time() < TRADING_AFTERNOON[0]:
            wait = (dt.datetime.combine(now.date(), TRADING_AFTERNOON[0]) - now).total_seconds() / 60
        else:  # 收盘后
            wait = (dt.datetime.combine(now.date() + dt.timedelta(days=1), TRADING_MORNING[0]) - now).total_seconds() / 60
        return int(wait) + 1
    if is_weekend(now):
        return INTERVAL_WEEKEND_HOLIDAY
    if is_report_season(now):
        return INTERVAL_REPORT_SEASON
    return INTERVAL_OFF_SEASON


def run_script():
    subprocess.run(["bash", "update.sh"])
    # 根据当前时机动态决定下次间隔，并重新排程
    schedule.clear()
    schedule.every(next_interval_minutes(dt.datetime.now())).minutes.do(run_script)


if __name__ == "__main__":
    run_script()  # 首次立即执行，并排好下一次

    while True:
        schedule.run_pending()
        time.sleep(30)