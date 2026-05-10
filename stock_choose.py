import akshare as ak
import argparse
import enum
import numpy as np
import pandas as pd
import pickle
import sqlite3

from scipy import stats
from tqdm import tqdm

from utils import get_code_sh, get_code_sz, get_done_codes

def update_stock():
    stock_sh = ak.stock_info_sh_name_code(symbol="主板A股")
    stock_sz = ak.stock_info_sz_name_code(symbol="A股列表")

    # 如果你想保存到CSV文件中，可以使用pandas的to_csv方法
    stock_sh.to_csv('stock_sh.csv', index=False, encoding='utf-8')
    stock_sz.to_csv('stock_sz.csv', index=False, encoding='utf-8')

class Stat(enum.Enum):
    Up = 0
    Down = 1
    Wave = 2
    Other = 3

class StockChoose:
    range = 12 # 3 years
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.data_range = StockChoose.range
        self.base_score = 0
    
    def name(self):
        return self.df['SECUCODE'][0], self.df['SECURITY_NAME_ABBR'][0]
    
    def _mom_score(self, data, yoy=False):
        score = self.base_score
        for j in range(1, min(len(data), self.data_range)):
            try:
                prev = data[j-1]
                curr = data[j]
                if pd.isna(prev) or pd.isna(curr):
                    break
                if curr < 0:
                    growth_rate = (prev - curr) / abs(curr)
                else:
                    growth_rate = (prev - curr) / curr
            except ZeroDivisionError:
                growth_rate = 0
            if j == 1:
                if yoy:
                    self.yoy = growth_rate
                else:
                    self.mom = growth_rate
            score += growth_rate
            if growth_rate <= 0:
                break
        return score
        
    def _yoy_score(self, data):
        # 存储每个年度的总和
        annual_sum = []
        # 计算每年的总和
        for i in range(0, self.data_range, 4):
            year_total = sum(data[i:i+4])
            annual_sum.append(year_total)
        return self._mom_score(annual_sum, yoy=True)
    
    def _base_score(self, data):
        if data.isna().all():
            self.base_score = 0
            return
        ret, conf = self._detect_trend(data)
        clean = data.dropna()
        max_value = np.max(clean) if len(clean) > 0 else 0
        min_value = np.min(clean) if len(clean) > 0 else 0
        
        if min_value < 0:
            self.base_score = abs(min_value / (max_value + 0.0001)) * -10
        
        if ret == Stat.Up:
            self.base_score = 10 * conf
        elif ret == Stat.Down:
            self.base_score = -10 * conf
        elif ret == Stat.Wave:
            self.base_score = -100
        elif ret == Stat.Other:
            self.base_score = 0
        else:
            assert 0, f"not support stat"
        for v in data:
            if v < 0:
                self.base_score -= 15
            
    
    def _detect_trend(self, data):
        clean = data.dropna()
        if len(clean) < 3:
            return Stat.Other, 0
        x = np.arange(len(clean))
        slope, _, r_value, _, _ = stats.linregress(x, clean)

        annual_sum = []
        for i in range(0, self.data_range, 4):
            year_total = sum(data[i:i+4])
            annual_sum.append(year_total)

        clean_annual = pd.Series(annual_sum).dropna()
        if len(clean_annual) < 2:
            return Stat.Other, 0
        x = np.arange(len(clean_annual))
        slope_y, _, r_value_y, _, _ = stats.linregress(x, clean_annual)

        stat_y, conf_y = self._get_stat(clean_annual, r_value_y, slope_y)
        stat_q, conf_q = self._get_stat(clean[:3], r_value, slope)

        if stat_y == Stat.Wave:
            return stat_y, conf_y
        elif stat_y == Stat.Down:
            return stat_y, conf_y
        elif stat_q == Stat.Down:
            return stat_q, conf_q
        elif stat_y == Stat.Up or stat_q == Stat.Up:
            return Stat.Up, max(conf_q, conf_y)
        elif stat_y == Stat.Other and (stat_q == Stat.Other or stat_q == Stat.Wave):
            return stat_y, 0
        else:
            return Stat.Other, 0
        
    def _get_stat(self, data, r_value, slope):
        # 相邻差值统计
        diffs = np.diff(data)
        pos_ratio = np.sum(diffs > 0) / len(diffs)
        neg_ratio = np.sum(diffs < 0) / len(diffs)
        
        # 波动性（标准差）
        volatility = np.std(data)
        
        # 判断逻辑
        conf = r_value**2
        if abs(slope) > 0.1 and conf> 0.5:
            return ((Stat.Up, conf) if slope < 0 else (Stat.Down, conf))
        elif abs(pos_ratio - neg_ratio) < 0.3 and volatility > np.mean(data)*0.1:
            return Stat.Wave, 0
        else:
            return Stat.Other, 0

    def _y2q(self, data_type: str):
        type = self.df['REPORT_TYPE']
        data = self.df[data_type].astype(float)
        assert len(data) >= self.data_range, f"data is not enouge"
        for i in range(self.data_range):
            if type[i] == '年报':
                if not (pd.isna(data.iloc[i]) or pd.isna(data.iloc[i+1])):
                    self.df.loc[(i, data_type)] = data.iloc[i] - data.iloc[i+1]
            elif type[i] == '三季报':
                if not (pd.isna(data.iloc[i]) or pd.isna(data.iloc[i+1])):
                    self.df.loc[(i, data_type)] = data.iloc[i] - data.iloc[i+1]
            elif type[i] == '中报':
                if not (pd.isna(data.iloc[i]) or pd.isna(data.iloc[i+1])):
                    self.df.loc[(i, data_type)] = data.iloc[i] - data.iloc[i+1]
            elif type[i] == '一季报':
                pass
            else:
                assert 0, f"not supported report type {type[i]}"
        data = data[:self.data_range]
        self._base_score(data)
        return data

    def _get_score(self, data_type):
        # data_type = 
        data = self._y2q(data_type)
        return self._calculate(data)
    
    def _calculate(self, data):
        score = 0
        self.yoy = 0
        self.mom = 0
        score += self._yoy_score(data)
        if score > 0:
            score += self._mom_score(data)
        return score

    def _get_profit_score(self):
        denominator = self.df['OPERATE_INCOME'].replace(0, np.nan).astype(float)
        profit = self.df['DEDUCT_PARENT_NETPROFIT'].astype(float) / denominator
        profit = profit[:self.data_range]
        clean = profit.dropna()
        avg_profit = np.mean(clean[:4]) if len(clean[:4]) > 0 else 0
        latest = clean.iloc[0] if len(clean) > 0 else 0
        return self._calculate(profit), avg_profit, latest


    def judge(self):
        total_score = 0
        desc = ''
        for type in ['OPERATE_INCOME', 'DEDUCT_PARENT_NETPROFIT']:
        # for type in ['DEDUCT_PARENT_NETPROFIT']:
            if type == 'DEDUCT_PARENT_NETPROFIT':
                mask = self.df[type].isna()
                if mask.sum() > 0:
                    self.df.loc[mask, type] = self.df.loc[mask, 'NETPROFIT']
            score = self._get_score(type)
            desc += f",{type},{score},{type}_YOY,{self.yoy},{type}_MOM,{self.mom}"
            total_score += score
        score, avg_profit, latest_profit = self._get_profit_score()
        desc += f",PROFIT_MARGIN,{score},LATEST_PROFIT,{latest_profit},AVG_PROFIT,{avg_profit}"
        total_score += score
        return total_score, desc
       

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument('--code', default='sz300308', type=str)
    # parser.add_argument('--prev', default=0, type=int)

    parser.add_argument('--prev', default=0, type=int)
    parser.add_argument('--code', default='sh603259', type=str)
    parser.add_argument('--dur', default=12, type=int)

    args = parser.parse_args()

    db_name = 'data/financial_data.db'
    conn = sqlite3.connect(db_name)  # 数据库文件名为financial_data.db

    for i in range(args.dur):
        result_dict = {}
        args.prev = i
        print(f"{i+1}/{args.dur}")
        if args.code is not None:
            i = 'tmp'
        with open(f"data/result_{i}.pkl", 'wb') as f_all:
            for i, code in tqdm(enumerate(get_done_codes('2025三季'))):
                if args.code is not None:
                    code = args.code
                query = f"SELECT * FROM {code} LIMIT {StockChoose.range + 1 + args.prev}"
                df = pd.read_sql(query, conn)
                if len(df) != StockChoose.range + 1 + args.prev:
                    print(f"data is not enough for {code}")
                    continue
                name: str = df['SECURITY_NAME_ABBR'][0]
                # st
                if name.startswith('S'):
                    continue
                if args.prev == 0:
                    sc = StockChoose(df)
                else:
                    sc = StockChoose(df[args.prev:].copy().reset_index(drop=True))
                score, desc = sc.judge()
                org_type = df['ORG_TYPE'][0]
                result = f"{code},{name},{org_type},{score}{desc}\n"

                if args.code is not None:
                    print(result)
                    exit(0)
                result_dict[code] = result
            pickle.dump(result_dict, f_all)
        
    conn.close()
