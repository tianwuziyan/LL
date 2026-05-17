# -*- coding: utf-8 -*-
//name: 宅恋API签到
//cron: 15 12 * * *
"""
项目：zlapi 签到
青龙变量：
export ZLAPI_USERNAME="你的用户名"
"""

import os
import requests
import time
import random

def zlapi_checkin():
    username = os.getenv("ZLAPI_USERNAME")

    if not username:
        print("❌ 未配置环境变量 ZLAPI_USERNAME")
        return

    url = "https://qd.zlapi.pro/api/checkin"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://qd.zlapi.pro",
        "Referer": "https://qd.zlapi.pro/"
    }

    data = {
        "username": username
    }

    try:
        response = requests.post(
            url=url,
            headers=headers,
            json=data,
            timeout=15
        )

        print("状态码:", response.status_code)

        if response.status_code != 200:
            print("❌ 请求失败")
            print(response.text)
            return

        result = response.json()

        message = result.get("message", "未知结果")

        # 昨日数据
        yesterday = result.get("yesterdayStats", {})

        calls = yesterday.get("calls", 0)
        consumption = yesterday.get("consumption", 0)

        # 保留两位小数（四舍五入）
        consumption = round(float(consumption), 2)

        reward_list = []

        # calls奖励
        if calls >= 10:
            reward_list.append("¥0.01-¥0.10")

        # consumption奖励
        if consumption >= 20:
            reward_list.append("¥2.00")
        elif consumption >= 10:
            reward_list.append("¥1.00")
        elif consumption >= 5:
            reward_list.append("¥0.50")
        elif consumption >= 1:
            reward_list.append("¥0.10")

        reward_text = ""

        if reward_list:
            reward_text =  " | ".join(reward_list)

        print(
            f"{message} "
            f"昨日调用: {calls} 次\n"
            f"昨日消费: ¥{consumption:.2f} 元\n"
            f"预计奖励: {reward_text} 元"
        )

    except Exception as e:
        print("❌ 请求异常:", str(e))


if __name__ == "__main__":

    # 读取环境变量
    max_random_delay = os.getenv("MAX_RANDOM_DELAY")

    # 只有值为 0 时立即执行
    if max_random_delay == "0":
        print("🚀 已关闭随机延迟，立即执行")
    else:
        # 默认随机延迟 0~30 分钟
        delay = random.randint(0, 1800)

        print(f"⏰ 随机延迟 {delay} 秒后执行")

        time.sleep(delay)

    zlapi_checkin()
