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


def zlapi_checkin():

    username = os.getenv("ZLAPI_USERNAME")

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
            f"昨日调用: {calls} 次\n"
            "————————-\n"
            f"昨日消费: ¥{consumption:.2f}\n"
            f"预计奖励: {reward_text}\n"
            "————————-\n"
            "签到：https://qd.zlapi.pro/"
        )

        print(final_msg)

        # ⭐ 统一通知出口
        send("宅恋API签到成功", final_msg)

    except Exception as e:
        err = f"❌ 请求异常: {str(e)}"
        print(err)
        send("宅恋API签到异常", err)


if __name__ == "__main__":

    delay = os.getenv("MAX_RANDOM_DELAY", "0")

    if delay == "0":
        print("🚀 立即执行")
    else:
        t = random.randint(0, 1800)
        print(f"⏰ 延迟 {t} 秒")
        time.sleep(t)

    zlapi_checkin()
