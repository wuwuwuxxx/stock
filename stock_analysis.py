import os
import pickle
import warnings

from utils import send_serverchan_notification

GOOD = "data/good.txt"
DONE = "data/done.txt"
ALL = "data/all_result.pkl"

def get_prev_good():
    codes = set()
    if os.path.exists(GOOD):
        with open(GOOD) as f:
            for line in f:
                data = line.split(',')
                codes.add(data[0])
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

new_good = open(GOOD, 'w')
msg = "new:\n{}\nremoved:\n{}"
with open(ALL, 'rb') as f:
    analysis_data: dict = pickle.load(f)
    new = ""
    for code, line in analysis_data.items():
        data = line.split(',')
        code = data[0]
        score = float(data[3])
        avg_profit = float(data[13])
        operate_income_yoy = float(data[15])
        if score > 50 and avg_profit > 0.20 and operate_income_yoy > 30:
            new_good.write(line)
            if code not in old_good:
                new += f"{data[0]},{data[1]}  "
            else:
                old_good.remove(code)

removed = ''
for v in old_good:
    # TODO, send msg
    removed += f"{v}, "
    warnings.warn(f"{v} is removed in the newest season")

send_serverchan_notification("cg", msg.format(new, removed))

new_good.close()