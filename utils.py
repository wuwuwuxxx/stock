import pandas as pd


def get_code_sh():
    df = pd.read_csv("data/stock_sh.csv", encoding='utf-8')
    data = df['证券代码'].astype("str").str.zfill(6)
    return 'sh' + data

def get_code_sz():
    df = pd.read_csv("data/stock_sz.csv", encoding='utf-8')
    data = df['A股代码'].astype("str").str.zfill(6)
    return 'sz' + data
