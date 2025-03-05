import os
import pandas as pd
import pickle
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

if __name__ == "__main__":
    # update_all()
    show('sz300502')