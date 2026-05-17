# -*- coding: utf-8 -*-

"""
//name: 宅恋API签到
//cron: 0 0,9 * * *
"""

import os
import requests
import time
import random

def bark_push(title, body):

    bark_key = os.getenv("BARK_KEY")

    if not bark_key:
        print("⚠️ 未配置 BARK_KEY，跳过推送")
        return

    url = f"https://api.day.app/{bark_key}"

    try:
        data = {
            "title": title,
            "body": body
        }

        requests.post(url, json=data, timeout=10)
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

        print("状态码:", res.status_code)

        if res.status_code != 200:
            print("❌ 请求失败")
            print(res.text)
            return

        result = res.json()

        message = result.get("message", "未知结果")

        # 昨日数据
        yesterday = result.get("yesterdayStats", {})
        calls = yesterday.get("calls", 0)
        consumption = round(float(yesterday.get("consumption", 0)), 2)

        # ===== 动态奖励解析（核心）=====
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

        # 去重（防止重复档位）
        reward_list = list(dict.fromkeys(reward_list))

        reward_text = " | ".join(reward_list) if reward_list else "无"

        # ===== 输出日志 =====
        print(
            f"✅ {message}\n"
            f"昨日调用: {calls} 次\n"
            f"昨日消费: ¥{consumption:.2f}\n"
            f"预计奖励: {reward_text}"
        )
    bark_push(
        "宅恋API签到",
        f"{message}\n"
        f"调用: {calls}\n"
        f"消费: {consumption:.2f}\n"
        f"奖励: {reward_text}"
    )
    except Exception as e:
        print("❌ 请求异常:", str(e))


if __name__ == "__main__":

    max_random_delay = os.getenv("MAX_RANDOM_DELAY")

    if max_random_delay == "0":
        print("🚀 已关闭随机延迟，立即执行")
    else:
        delay = random.randint(0, 1800)
        print(f"⏰ 随机延迟 {delay} 秒")
        time.sleep(delay)

    zlapi_checkin()
