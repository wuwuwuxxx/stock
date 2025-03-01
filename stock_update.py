import akshare as ak
import datetime
import pandas as pd
import pickle
import random
import sqlite3
import time

from utils import code_complete, get_done_codes
from stock_choose import StockChoose

period = '2024年报'
done_codes = get_done_codes(period)
# 获取A股财报预约披露日期
df = ak.stock_report_disclosure(period=period)

db_name = 'data/financial_data.db'

conn = sqlite3.connect(db_name)  # 数据库文件名为financial_data.db

with open("data/all_result.pkl", 'rb') as f:
    analysis_data = pickle.load(f)

        
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
        
        with open(f"data/{period}_done.txt", 'a') as f:
            f.write(f"{code}\n")

        count += 1
        time.sleep(random.uniform(3, 8))


conn.close()

with open("data/all_result.pkl", 'wb') as f_all:
    pickle.dump(analysis_data, f_all)
print(f"update {count} company in {datetime.datetime.now()}")