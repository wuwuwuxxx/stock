import akshare as ak
import datetime
import pandas as pd
import pickle
import random
import sqlite3
import time

from utils import code_complete, get_done_codes, update_all
from stock_choose import StockChoose

years = ['2024', '2025']
targets = ['年报', '一季']

period_map = {}
for year in years:
    period_map[f"{year}一季"] = f"{year}-03-31 00:00:00"
    period_map[f"{year}半年报"] = f"{year}-06-30 00:00:00"
    period_map[f"{year}三季"] = f"{year}-09-30 00:00:00"
    period_map[f"{year}年报"] = f"{year}-12-31 00:00:00"

periods = [year + target for year, target in zip(years, targets)]

for period in periods:
    time.sleep(10)
    target = period_map[period]
    done_codes = get_done_codes(period)
    try:
        # 获取A股财报预约披露日期
        df = ak.stock_report_disclosure(period=period)
    except ValueError: # error if no data
        continue

    db_name = 'data/financial_data.db'

    conn = sqlite3.connect(db_name)  # 数据库文件名为financial_data.db

    # with open("data/result_update.pkl", 'rb') as f:
    #     analysis_data = pickle.load(f)

    analysis_data = {}
            
    count = 0
    dates = df['实际披露']
    codes = df['股票代码']
    for date_time, code in zip(dates, codes):
        if not pd.isna(date_time):
            if int(code) > 699999:
                continue
            code = code_complete(code)
            if code in done_codes:
                continue
            df = ak.stock_profit_sheet_by_report_em(symbol=code)

            if target != df['REPORT_DATE'][0]:
                continue
            
            date_columns = ['REPORT_DATE', 'NOTICE_DATE', 'UPDATE_DATE']
            for col in date_columns:
                df[col] = pd.to_datetime(df[col])
            df.to_sql(name=code,
                    con=conn,
                    if_exists='replace',  # 如果表已存在则替换
                    index=False,          # 不保存索引
                    dtype={'REPORT_DATE': 'DATETIME',  # 手动指定日期类型
                            'NOTICE_DATE': 'DATETIME',
                            'UPDATE_DATE': 'DATETIME'})
            query = f"SELECT * FROM {code} LIMIT {StockChoose.range + 1}"
            df = pd.read_sql(query, conn)

            with open(f"data/{period}_done.txt", 'a') as f:
                f.write(f"{code}\n")

            if len(df) != StockChoose.range + 1:
                print(f"data is not enough for {code}")
                continue

            print(f"{date_time}")

            sc = StockChoose(df)
            score, desc = sc.judge()
            org_type = df['ORG_TYPE'][0]
            name: str = df['SECURITY_NAME_ABBR'][0]
            result = f"{code},{name},{org_type},{score}{desc}\n"
            analysis_data[code] = result

            count += 1
            time.sleep(random.uniform(3, 8))


    conn.close()

    print(f"{period}, update {count} company in {datetime.datetime.now()}")
    if count > 0:
        with open("data/result_update.pkl", 'wb') as f_all:
            pickle.dump(analysis_data, f_all)
        update_all()
       