import heapq
import os
import pickle
import warnings

from utils import send_serverchan_notification, get_file_hash

GOOD = "data/good.txt"
DONE = "data/done.txt"
ALL = "data/result_{}.pkl"


def get_prev_good():
    codes = {}
    if os.path.exists(GOOD):
        with open(GOOD) as f:
            for line in f:
                data = line.split(",")
                codes[data[2]] = data[3]
    return codes


def get_done():
    codes = set()
    if os.path.exists(DONE):
        with open(DONE) as f:
            for line in f:
                data = line.split(",")
                codes.add(data[2])
    return codes


old_hash = get_file_hash(GOOD)
old_good = get_prev_good()
old_order = list(old_good.keys())
done = get_done()
old_good = {k: v for k, v in old_good.items() if k not in done}

new_good = []
count = {}

new = []
for i in range(12):
    with open(ALL.format(i), "rb") as f:
        analysis_data: dict = pickle.load(f)
        for code, line in analysis_data.items():
            data = line.split(",")
            code = data[0]
            score = float(data[3])

            latest_profit = float(data[19])
            avg_profit = float(data[21].strip())
            operate_income_yoy = float(data[7])
            operate_income_mom = float(data[9])
            deduct_netprofit_yoy = float(data[13])
            deduct_netprofit_mom = float(data[15])
            # if score > 50 and avg_profit > 0.20 and operate_income_yoy > 30:
            if (
                score > 50
                and deduct_netprofit_yoy > 0.20
                and (avg_profit > 0.2 or latest_profit > 0.2)
                and operate_income_yoy > 0.05
            ):
                if i == 0:
                    sort_score = deduct_netprofit_yoy + operate_income_yoy
                    heapq.heappush(new_good, (-sort_score, code, line))
                    count[code] = 1
                    if code not in old_good:
                        new.append((code, data[1], score))
                    else:
                        del old_good[code]
                else:
                    if code in count:
                        count[code] += 1

removed = []
for v, name in old_good.items():
    removed.append((v, name))
    warnings.warn(f"{v} is removed in the newest season")


ranking = []
with open(GOOD, "w") as f:
    while new_good:
        priority, code, line = heapq.heappop(new_good)
        num = count[code]
        f.write(f"count,{num}," + line)
        data = line.split(",")
        ranking.append((data[0], data[1], float(data[3]), num))

new_hash = get_file_hash(GOOD)

new_order = [code for code, *_ in ranking]
names = {code: name for code, name, *_ in ranking}
moved = []
for i, code in enumerate(new_order):
    old_pos = old_order.index(code) if code in old_order else -1
    if old_pos != -1 and old_pos != i:
        moved.append((code, names[code], old_pos + 1, i + 1))

SEND = True
if new or removed:
    parts = ["## 📊 财报季选股更新"]
    if new:
        parts.append(f"### 🆕 新增 {len(new)} 只")
        parts += [
            f"{i}. **{code} {name}** ({score:.0f}分)"
            for i, (code, name, score) in enumerate(new, 1)
        ]
    if removed:
        parts.append(f"### ❌ 剔除 {len(removed)} 只")
        parts += [
            f"{i}. **{code} {name}**" for i, (code, name) in enumerate(removed, 1)
        ]
    msg = "\n".join(parts)
    if new_hash != old_hash:
        msg += "\n> hash 已变化"
elif moved:
    parts = ["## 📊 选股排名变化", "> 仅排名变化，非完整名单", ""]
    parts += [
        f"{i}. **{name}** ({code}) 第{old_pos}位 → 第{new_pos}位"
        for i, (code, name, old_pos, new_pos) in enumerate(moved, 1)
    ]
    msg = "\n".join(parts)
else:
    msg = ""

if not msg:
    print("no change, skip notification")
elif SEND:
    send_serverchan_notification("cg", msg)
else:
    print(msg)
