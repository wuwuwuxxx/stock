import akshare as ak
from utils import is_gq


def gq():
    gq_f = open("data/gq.txt", 'w')

    df = ak.stock_hold_control_cninfo()

    for code, name in zip(df.证券代码, df.实际控制人名称):
        if is_gq(name):
            gq_f.write(f'{code}\n')
        else:
            # print(name)
            pass
    gq_f.close()

if __name__ == '__main__':
    gq()