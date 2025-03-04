import os
import pickle
import warnings

from utils import send_serverchan_notification

GOOD = "data/good.txt"
DONE = "data/done.txt"
ALL = "data/result_{}.pkl"

def get_prev_good():
    codes = set()
    if os.path.exists(GOOD):
        with open(GOOD) as f:
            for line in f:
                data = line.split(',')
                codes.add(data[2])
    return codes

def get_done():
    codes = set()
    if os.path.exists(DONE):
        with open(DONE) as f:
            for line in f:
                data = line.split(',')
                codes.add(data[0])
    return codes

old_good = get_prev_good()
done = get_done()
old_good = old_good - done

new_good = {}
count = {}
msg = "new:\n{}\nremoved:\n{}"
for i in range(12):
    with open(ALL.format(i), 'rb') as f:
        analysis_data: dict = pickle.load(f)
        new = ""
        for code, line in analysis_data.items():
            data = line.split(',')
            code = data[0]
            score = float(data[3])

            latest_profit = float(data[19])
            avg_profit = float(data[21].strip())
            operate_income_yoy = float(data[7])
            operate_income_mom = float(data[9])
            deduct_netprofit_yoy = float(data[13])
            deduct_netprofit_mom = float(data[15])
            # if score > 50 and avg_profit > 0.20 and operate_income_yoy > 30:
            if score > 50 and deduct_netprofit_yoy > 0.20 and avg_profit > 0.15 and operate_income_yoy > 0.05:
                if i == 0:
                    new_good[code] = line
                    count[code] = 1
                    if code not in old_good:
                        new += f"{data[0]},{data[1]}  "
                    else:
                        old_good.remove(code)
                else:
                    if code in count:
                        count[code] += 1

removed = ''
for v in old_good:
    removed += f"{v}, "
    warnings.warn(f"{v} is removed in the newest season")

SEND = True
msg = msg.format(new, removed)
if SEND:
    send_serverchan_notification("cg", msg)
else:
    print(msg)

with open(GOOD, 'w') as f:
    for k, v in new_good.items():
        num = count[k]
        f.write(f"count,{num},"+v)