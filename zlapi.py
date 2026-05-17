# -*- coding: utf-8 -*-

"""
name: 宅恋API签到
cron: 0 0,9 * * *
"""

import os
import requests
import time
import random
from datetime import datetime, timedelta

try:
    from notify import send
except ImportError:
    def send(title, content):
        print(f"[通知]\n{title}\n{content}")


def format_time(seconds: int):
    """把秒转换为 X分XX秒"""
    m = seconds // 60
    s = seconds % 60
    return m, s


def countdown(seconds: int):
    """最后5秒倒计时"""
    print("\n⏳ 即将执行任务，开始倒计时：")
    for i in range(seconds, 0, -1):
        print(f"⏱ {i}...")
        time.sleep(1)
    print("🚀 开始执行任务\n")


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


if __name__ == "__main__":

    max_random_delay = os.getenv("MAX_RANDOM_DELAY")

    if max_random_delay == "0":
        print("🚀 已关闭延迟，立即执行")
    else:
        # ==============================
        # 🎯 随机生成：1~10分钟（你可以改）
        # ==============================
        delay_seconds = random.randint(60, 600)

        m, s = format_time(delay_seconds)

        now = datetime.now()
        run_time = now + timedelta(seconds=delay_seconds)

        print(f"⏰ 随机延迟：{m}分{s:02d}秒")
        print(f"🕒 预计执行时间：{run_time.strftime('%H:%M:%S')}")

        # 🔥 在最后5秒倒计时
        if delay_seconds > 5:
            time.sleep(delay_seconds - 5)
            countdown(5)
        else:
            countdown(delay_seconds)

    zlapi_checkin()
