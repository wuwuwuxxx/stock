import hashlib
import os
import pandas as pd
import pickle
import requests
from fnmatch import fnmatch

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

patterns = [
    '中国*公司',
    '*国有资*',
    '*人民政府',
    '*财政局',
    '中华人民共和国*',
    '*委员会',
    '*广播电*',
    '*财政厅',
    '*供销合作*',
    '中国科学院*',
    '*省*公司',
    '*财政部',
    '*国有企业*',
    '国家*局',
    '*水务局',
    '*国资局',
    '*国资委',
    '*交通运输厅',
    '*省委宣传部',
    '*大学',
    '*经济合作社',
    '人民日报社',
    '*资产经营中心',
    '空天信息创新研究院',
    '江苏国泰国际贸易有限公司',
    '黑龙江出版集团有限公司',
    '*文化交流促进会',
    '大连市星海湾开发建设管理中心',
    '西安高科集团有限公司',
    '招商局集团有限公司',
    '中央汇金投资有限责任公司',
    '上海国际集团有限公司',
    '深圳市投资控股有限公司',
    '中国*研究院',
    '*高新技术产业开发区管委会',
    '新华通讯社',
    '武汉邮电科学研究院',
    '浙江日报报业集团',
    '河南省农业科学院',
    '国家开发投资集团有限公司',
    '四川省地质矿产勘查开发局',
    '北京电子控股有限责任公司',
    '长江产业投资集团有限公司',
    '衢州工业控股集团有限公司',
    '*国有*资产*',
    '鞍钢集团*',
    '首都文化科技集团有限公司',
    '中央*',
    '陕西投资集团有限公司',
    '潍坊市政府投融资管理中心',
    '深圳市资本运营集团有限公司',
    '中粮*',
    '中国共产党*',
    '浙江出版联合集团有限公司',
    '交通运输部公路科学研究所',
    '*横店社团经济企业联合*',
    '湖北省汉川市钢丝绳厂',
    '*市公有资产经营有限公司',
    '新疆生产建设兵团农业建设第*师',
    '海南省慈航公益基金会',
    '杭州日报*',
    '广州市国有经营性文化资产监督管理办公室',
    '上海大众企业管理有限公司职工持股会',
    '佛山市南海区公有资产管理办公室',
    '内蒙古鄂尔多斯投资控股集团有限公司',
    '湖北省国有文化资产监督管理与产业发展领导小组办公室',
    '山东出版集团有限公司',
    '中国*研究院',
    '郴州市发展投资集团产业投资经营有限公司',
    '广州电气装备集团有限公司',
    '深圳市特发集团有限公司',
]


def is_gq(name):
    global patterns
    found = any(fnmatch(name, p) for p in patterns)
    # if found:
    return found

if __name__ == "__main__":
    # update_all()
    # show('sz300502')
    # print(get_file_hash("data/good.txt"))
    print(is_gq('sh600350'))