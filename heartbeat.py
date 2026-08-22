import datetime as dt
import json
import os

STATE_FILE = "data/heartbeat_state.json"
HEARTBEAT_INTERVAL_SECONDS = 24 * 3600

REPORT_PERIOD_BY_MONTH = {
    1: "年报",
    4: "一季",
    7: "半年报",
    8: "半年报",
    10: "三季",
}


def _load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def _save_state(state):
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False)


def touch_last_message():
    state = _load_state()
    state["last_message"] = dt.datetime.now().isoformat()
    _save_state(state)


def heartbeat_due(now):
    last = _load_state().get("last_message")
    if not last:
        return True
    try:
        return (now - dt.datetime.fromisoformat(last)).total_seconds() >= HEARTBEAT_INTERVAL_SECONDS
    except ValueError:
        return True


def _count_lines(path):
    try:
        with open(path) as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def _report_period(now):
    month = REPORT_PERIOD_BY_MONTH.get(now.month)
    if not month:
        return None
    if now.month == 1:
        return f"{now.year - 1}年报"
    return f"{now.year}{month}"

def send_heartbeat():
    now = dt.datetime.now()
    state = _load_state()
    period = _report_period(now)

    done = _count_lines(f"data/{period}_done.txt") if period else 0
    failed = _count_lines(f"data/{period}_failed.txt") if period else 0
    good = _count_lines("data/good.txt")

    prev_done = state.get("done", done)
    prev_good = state.get("good", good)
    delta_done = max(0, done - prev_done)
    delta_good = max(0, good - prev_good)

    parts = [
        "## 💓 心跳：24小时无新消息",
        f"> {now:%Y-%m-%d %H:%M:%S}",
        "",
        "**本轮任务:** 抓取财报数据 → 写入数据库 → 选股分析 → 推送通知",
        "",
    ]
    if period:
        parts.append(f"### 当前财报季: {period}")
        parts.append(f"- 累计已更新 **{done}** 家")
        parts.append(f"- 更新失败 **{failed}** 家")
        parts.append(f"- 近24小时新增 **{delta_done}** 家")
    else:
        parts.append("### 当前非财报季，无调度任务")
    parts.append(f"- 入选股票池共 **{good}** 只（近24小时 +{delta_good}）")

    if os.path.exists("update.log"):
        mtime = dt.datetime.fromtimestamp(os.path.getmtime("update.log"))
        parts.append(f"- 最近一次更新管线运行: {mtime:%Y-%m-%d %H:%M:%S}")

    from utils import send_serverchan_notification

    send_serverchan_notification("heartbeat", "\n".join(parts))

    state["last_message"] = now.isoformat()
    state["done"] = done
    state["good"] = good
    _save_state(state)
