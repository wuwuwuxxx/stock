import hashlib
import os
import pandas as pd
import pickle
import requests
import akshare as ak


def get_code_sh():
    df = pd.read_csv("data/stock_sh.csv", encoding='utf-8')
    data = df['证券代码'].astype("str").str.zfill(6)
    return 'sh' + data

def get_code_sz():
    df = pd.read_csv("data/stock_sz.csv", encoding='utf-8')
    data = df['A股代码'].astype("str").str.zfill(6)
    return 'sz' + data

def get_done_codes(period):
    tmp = set()
    path = f"data/{period}_done.txt"
    if not os.path.exists(path):
        return tmp
    with open(path, 'r') as f:
        for line in f:
            tmp.add(line.strip())
    return tmp
    

def code_complete(code: str):
    # tmp = int(code)
    if code.startswith(('6', '90')):
        return 'sh' + code
    elif code.startswith(('0', '2', '3')):
        return 'sz' + code
    elif code.startswith(('8', '4', '92')):
        return 'bj' + code
    else:
        assert 0, f"not supported {code}"
        
def send_serverchan_notification(title, message):
    if len(message) == 15:
        print("empty msg")
        return
    sendkey = "SCT271491T9bE1G90ylp6pK4QaQ3U8jQC4"  # 替换为你的 SendKey
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {
        "title": title,  # 消息标题
        "desp": message  # 消息内容（支持 Markdown）
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("ServerChan 推送已发送！")
        print(message)
    else:
        print(f"推送失败: {response.status_code}")


def update_all():
    with open("data/result_update.pkl", 'rb') as f:
        updated: dict = pickle.load(f)
    for i in range(11, 0, -1):
        with open(f"data/result_{i}.pkl", 'rb') as prev_f:
            prev = pickle.load(prev_f)
        with open(f"data/result_{i-1}.pkl", 'rb') as prev_f:
            cur = pickle.load(prev_f)
        for k in updated.keys():
            try:
                prev[k] = cur[k]
            except KeyError:
                pass
        with open(f"data/result_{i}.pkl", 'wb') as prev_f:
            pickle.dump(prev, prev_f)
    with open(f"data/result_0.pkl", 'rb') as prev_f:
        prev = pickle.load(prev_f)
    for k in updated.keys():
        try:
            prev[k] = updated[k]
        except KeyError:
            pass
    with open(f"data/result_0.pkl", 'wb') as prev_f:
        pickle.dump(prev, prev_f)

def show(code):
    for i in range(12):
        with open(f"data/result_{i}.pkl", 'rb') as f:
            data = pickle.load(f)
            print(data[code])

def get_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):  # 分块读取避免大文件内存消耗
            hasher.update(chunk)
    return hasher.hexdigest()


def get_only_hk_stocks():
    """
    获取仅在港股上市、不在A股上市的公司代码列表（格式：XXXX.HK）
    """
    # 获取港股股票列表
    try:
        hk_stock_info = ak.stock_hk_spot_em()
        hk_stocks = hk_stock_info['代码'].apply(lambda x: x + ".HK").tolist()
    except Exception as e:
        print("获取港股数据失败:", e)
        return []

    # 获取A股股票列表
    try:
        a_stock_info = ak.stock_zh_a_spot_em()
        a_stocks = set(a_stock_info['代码'])
        # A股中可能有B股，但我们只关心A股主体代码（6位数字）
        a_stock_codes = set()
        for code in a_stocks:
            if code.startswith(('60', '68', '00', '30')):
                a_stock_codes.add(code)
    except Exception as e:
        print("获取A股数据失败:", e)
        return []

    # 过滤：排除那些也在A股上市的港股（即A+H股）
    only_hk = []
    for hk_code in hk_stocks:
        # 提取港股数字部分（如'00700.HK' -> '00700'）
        base_code = hk_code.split('.')[0].lstrip('0')  # 去除前导0，便于匹配
        if not base_code:
            base_code = '0'  # 防止全0情况
        # 检查是否在A股存在（A股代码通常为6位，带前导0）
        found = False
        for a_code in a_stock_codes:
            # 对比去除前导0后是否相同
            if a_code.lstrip('0') == base_code:
                found = True
                break
        if not found:
            only_hk.append(hk_code)

    return sorted(only_hk)

# 调用示例
if __name__ == "__main__":
    only_hk_list = get_only_hk_stocks()
    print("仅在港股上市的公司代码:")
    print(only_hk_list[:20])
    print(f"总数: {len(only_hk_list)}")
