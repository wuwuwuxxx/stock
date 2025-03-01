import os

GOOD = "data/good.txt"
ALL = "data/all_result.txt"

def get_prev_good():
    codes = set()
    if os.path.exists(GOOD):
        with open(GOOD) as f:
            for line in f:
                data = line.split(',')
                codes.add(data[0])
    return codes

old_good = get_prev_good()

new_good = open(GOOD, 'w')
with open(ALL) as f:
    for line in f:
        data = line.split(',')
        code = data[0]
        score = float(data[3])
        if score > 50 :
            new_good.write(line)
            if code not in old_good:
                print("--------------------")
                print(f"| {data[0]},{data[1]} |")
                print("--------------------")

new_good.close()