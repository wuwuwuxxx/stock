import pandas as pd
import sqlite3
import akshare as ak
import time
import os
import random

from utils import get_code_sh, get_code_sz


db_name = 'data/financial_data.db'
if os.path.exists(db_name):
    os.remove(db_name)
areas = [get_code_sh(), get_code_sz()]

conn = sqlite3.connect(db_name)  # 数据库文件名为financial_data.db
for area in areas:
    for code in area:
        print(f"start {code}")
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
        query = f"SELECT * FROM {code} LIMIT 5"
        print(pd.read_sql(query, conn))
        print(f"{code} done", flush=True)
        # time.sleep(60)
        time.sleep(random.uniform(3, 8))

conn.close()
