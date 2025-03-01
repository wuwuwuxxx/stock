import schedule
import time
import subprocess

def run_script():
    # 这里替换为你要执行的脚本
    subprocess.run(["bash", "update.sh"])

# 每隔3小时执行一次
schedule.every(5).hours.do(run_script)

while True:
    schedule.run_pending()
    time.sleep(1)