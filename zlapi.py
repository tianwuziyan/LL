# -*- coding: utf-8 -*-

"""
name: 宅恋API签到
cron: 0 0,9 * * *
"""

import os
import requests
import time
import random

# 统一通知入口
try:
    from notify import send
except ImportError:
    def send(title, content):
        print(f"[通知]\n{title}\n{content}")


# =========================
# 时间工具
# =========================
def format_time(seconds):
    """格式化：X分X秒 / X秒"""
    m, s = divmod(seconds, 60)
    if m > 0:
        return f"{m}分{s}秒"
    return f"{s}秒"


def countdown(delay_seconds):
    """带倒计时 + 最后5秒提示"""
    if delay_seconds <= 0:
        print("🚀 立即执行")
        return

    print(f"⏰ 随机延迟：{format_time(delay_seconds)} 后执行")

    while delay_seconds > 0:
        # 最后5秒强提示
        if delay_seconds <= 5:
            print(f"⚡ 即将执行：{delay_seconds}秒")

        time.sleep(1)
        delay_seconds -= 1

    print("🚀 开始执行任务")


# =========================
# 主逻辑
# =========================
def zlapi_checkin():
    username = os.getenv("ZLAPI_USERNAME")

    if not username:
        msg = "❌ 未配置 ZLAPI_USERNAME"
        print(msg)
        send("宅恋API签到失败", msg)
        return

    url = "https://qd.zlapi.pro/api/checkin"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://qd.zlapi.pro",
        "Referer": "https://qd.zlapi.pro/"
    }

    try:
        res = requests.post(url, headers=headers, json={"username": username}, timeout=15)

        print("状态码:", res.status_code)

        if res.status_code != 200:
            msg = f"❌ 请求失败：{res.text}"
            print(msg)
            send("宅恋API签到失败", msg)
            return

        result = res.json()

        message = result.get("message", "未知结果")

        yesterday = result.get("yesterdayStats", {})
        calls = yesterday.get("calls", 0)
        consumption = round(float(yesterday.get("consumption", 0)), 2)

        reward_levels = result.get("rewardLevels", {})
        reward_list = []

        for _, level in reward_levels.items():
            r_type = level.get("type")
            reward = level.get("minRewardYuan", 0)

            if r_type == "calls":
                if calls >= level.get("minCalls", 0):
                    reward_list.append(f"¥{reward:.2f}")

            elif r_type == "consumption":
                if consumption >= level.get("minConsumption", 0):
                    reward_list.append(f"¥{reward:.2f}")

        reward_list = list(dict.fromkeys(reward_list))
        reward_text = " | ".join(reward_list) if reward_list else "无"

        final_msg = (
            f"\n{message}\n"
            "————————-\n"
            f"昨日调用: {calls} 次\n"
            f"昨日消费: ¥{consumption:.2f}\n"
            f"预计奖励: {reward_text}\n"
            "————————-\n\n"
            "签到：https://qd.zlapi.pro"
        )

        print(final_msg)
        send("宅恋API签到成功", final_msg)

    except Exception as e:
        err = f"❌ 请求异常: {str(e)}"
        print(err)
        send("宅恋API签到异常", err)


# =========================
# 启动入口
# =========================
if __name__ == "__main__":
    max_random_delay = os.getenv("MAX_RANDOM_DELAY")

    try:
        max_random_delay = int(max_random_delay)
    except:
        max_random_delay = 0

    if max_random_delay <= 0:
        print("🚀 立即执行")
        delay = 0
    else:
        # 随机延迟（秒）
        delay = random.randint(0, max_random_delay)
        # 倒计时执行
        countdown(delay)
        
    # 执行签到
    zlapi_checkin()
