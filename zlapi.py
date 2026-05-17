# -*- coding: utf-8 -*-

"""
//name: 宅恋API签到
//cron: 0 12 * * *
"""

import os
import requests
import time
import random


# ===== Bark 推送 =====
def bark_push(title, content):

    bark_key = os.getenv("BARK_KEY")

    if not bark_key:
        print("⚠️ 未配置 BARK_KEY，跳过推送")
        return

    url = f"https://api.day.app/{bark_key}/{title}/{content}"

    try:
        requests.get(url, timeout=10)
        print("📲 Bark推送成功")
    except Exception as e:
        print("❌ Bark推送失败:", str(e))


def zlapi_checkin():

    username = os.getenv("ZLAPI_USERNAME")

    if not username:
        print("❌ 未配置 ZLAPI_USERNAME")
        return

    url = "https://qd.zlapi.pro/api/checkin"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://qd.zlapi.pro",
        "Referer": "https://qd.zlapi.pro/"
    }

    data = {"username": username}

    try:
        res = requests.post(url, headers=headers, json=data, timeout=15)

        if res.status_code != 200:
            msg = "请求失败"
            print(msg)
            bark_push("签到失败", res.text[:200])
            return

        result = res.json()

        message = result.get("message", "未知结果")

        yesterday = result.get("yesterdayStats", {})
        calls = yesterday.get("calls", 0)
        consumption = round(float(yesterday.get("consumption", 0)), 2)

        # ===== 动态奖励 =====
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

        # ===== 控制台输出 =====
        log_text = (
            f"{message}\n"
            f"昨日调用: {calls} 次\n"
            f"昨日消费: ¥{consumption:.2f}\n"
            f"预计奖励: {reward_text}"
        )

        print(log_text)

        # ===== Bark推送 =====
        bark_title = "宅恋API签到"
        bark_content = (
            f"{message}\\n"
            f"调用:{calls} 消费:{consumption:.2f}\\n"
            f"奖励:{reward_text}"
        )

        bark_push(bark_title, bark_content)

    except Exception as e:
        err = f"异常: {str(e)}"
        print(err)
        bark_push("签到异常", err[:200])


if __name__ == "__main__":

    max_random_delay = os.getenv("MAX_RANDOM_DELAY")

    if max_random_delay == "0":
        print("🚀 已关闭随机延迟，立即执行")
    else:
        delay = random.randint(0, 1800)
        print(f"⏰ 随机延迟 {delay} 秒")
        time.sleep(delay)

    zlapi_checkin()
