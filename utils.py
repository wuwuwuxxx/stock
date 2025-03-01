import os
import pandas as pd
import requests


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
    tmp = int(code)
    if tmp < 600000:
        return 'sz' + code
    elif 600000 < tmp < 699999:
        return 'sh' + code
    else:
        assert 0, f"not supported {code}"
        
def send_serverchan_notification(title, message):
    if len(message) == 15:
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
