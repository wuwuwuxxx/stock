import datetime
import os
import pickle
import random
import sqlite3
import time
import traceback

import akshare as ak
import pandas as pd

from datetime import datetime as dt

from stock_choose import StockChoose
from utils import code_complete, get_done_codes, update_all

years = ["2026"]
targets = ["半年报"]

# df = ak.stock_zh_a_spot()
# print(df[["代码", "名称"]].head())
#          代码    名称
# 0  bj430017  星昊医药
# 1  bj430047  诺思兰德
# 2  bj430090  同辉信息
# 3  bj430139  华岭股份
# 4  bj430198  微创光电

period_map = {}
for year in years:
    period_map[f"{year}一季"] = f"{year}-03-31 00:00:00"
    period_map[f"{year}半年报"] = f"{year}-06-30 00:00:00"
    period_map[f"{year}三季"] = f"{year}-09-30 00:00:00"
    period_map[f"{year}年报"] = f"{year}-12-31 00:00:00"

periods = [year + target for year, target in zip(years, targets)]

DB_NAME = "data/financial_data.db"
SAVE_EVERY = 100


def load_analysis_data():
    path = "data/result_update.pkl"
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return pickle.load(f)


def save_analysis_data(analysis_data):
    with open("data/result_update.pkl", "wb") as f:
        pickle.dump(analysis_data, f)


def get_skipped_codes(period):
    tmp = set()
    path = f"data/{period}_not_enough.txt"
    if not os.path.exists(path):
        return tmp
    with open(path, "r") as f:
        for line in f:
            tmp.add(line.strip())
    return tmp


def record_failed(period, code, reason):
    with open(f"data/{period}_failed.txt", "a") as f:
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {code}\t{reason}\n")


def record_not_enough(period, code):
    with open(f"data/{period}_not_enough.txt", "a") as f:
        f.write(f"{code}\n")


def record_done(period, code):
    with open(f"data/{period}_done.txt", "a") as f:
        f.write(f"{code}\n")


for period in periods:
    time.sleep(10)
    target = period_map[period]
    done_codes = get_done_codes(period)
    skipped_codes = get_skipped_codes(period)
    try:
        # 获取A股财报预约披露日期
        df = ak.stock_report_disclosure(period=period)
    except ValueError:  # error if no data
        continue

    conn = sqlite3.connect(DB_NAME)

    analysis_data = load_analysis_data()

    count = 0
    dates = df["实际披露"]
    codes = df["股票代码"]
    try:
        for date_time, code in zip(dates, codes):
            if pd.isna(date_time):
                continue
            try:
                code = code_complete(code)
            except Exception as e:
                record_failed(period, code, f"bad code: {e}")
                continue
            if code in done_codes or code in skipped_codes:
                continue
            try:
                df = ak.stock_profit_sheet_by_report_em(symbol=code)
            except Exception as e:
                print(f"{code} not found: {e}")
                record_failed(period, code, f"no profit sheet data: {e}")
                continue

            try:
                format = r"%Y-%m-%d %H:%M:%S"
                if dt.strptime(target, format) > dt.strptime(df["REPORT_DATE"][0], format):
                    continue

                date_columns = ["REPORT_DATE", "NOTICE_DATE", "UPDATE_DATE"]
                for col in date_columns:
                    df[col] = pd.to_datetime(df[col])
                df.to_sql(
                    name=code,
                    con=conn,
                    if_exists="replace",
                    index=False,
                    dtype={
                        "REPORT_DATE": "DATETIME",
                        "NOTICE_DATE": "DATETIME",
                        "UPDATE_DATE": "DATETIME",
                    },
                )
                conn.commit()

                query = f"SELECT * FROM {code} LIMIT {StockChoose.range + 1}"
                df = pd.read_sql(query, conn)

                if len(df) != StockChoose.range + 1:
                    print(f"data is not enough for {code}")
                    record_not_enough(period, code)
                    continue

                print(f"{date_time}")

                sc = StockChoose(df)
                score, desc = sc.judge()
                org_type = df["ORG_TYPE"][0]
                name: str = df["SECURITY_NAME_ABBR"][0]
                result = f"{code},{name},{org_type},{score}{desc}\n"
                analysis_data[code] = result

                count += 1
                record_done(period, code)
                if count % SAVE_EVERY == 0:
                    save_analysis_data(analysis_data)
                time.sleep(random.uniform(5, 8))
            except Exception as e:
                print(f"[ERROR] {code} failed: {e}")
                traceback.print_exc()
                record_failed(period, code, str(e))
                continue
    finally:
        save_analysis_data(analysis_data)
        conn.close()

    print(f"{period}, update {count} company in {datetime.datetime.now()}")
    if count > 0:
        update_all()
