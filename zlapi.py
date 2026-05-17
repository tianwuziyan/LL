# -*- coding: utf-8 -*-

"""
name: 宅恋API签到
cron: 0 0,9 * * *
"""

import os
import requests
import time
import random


# ==================== Bark 配置（青龙标准版）====================
BARK_PUSH = os.getenv("BARK_PUSH")
BARK_ICON = os.getenv("BARK_ICON", "")
BARK_SOUND = os.getenv("BARK_SOUND", "")
BARK_GROUP = os.getenv("BARK_GROUP", "QingLong")
BARK_LEVEL = os.getenv("BARK_LEVEL", "active")
BARK_ARCHIVE = os.getenv("BARK_ARCHIVE", "1")
BARK_URL = os.getenv("BARK_URL", "")
PUSH_SWITCH = os.getenv("PUSH_SWITCH", "1")
# ===============================================================


def bark_push(title: str, body: str):
    """青龙标准 Bark 推送（完全兼容顺丰脚本写法）"""

    if PUSH_SWITCH != "1":
        print("📴 推送已关闭")
        return

    if not BARK_PUSH:
        print("📴 未配置 BARK_PUSH，跳过推送")
        return

    # 自动补全 URL
    bark_url = BARK_PUSH
    if not bark_url.startswith("http"):
        bark_url = f"https://api.day.app/{bark_url}"

    data = {
        "title": title,
        "body": body,
        "icon": BARK_ICON,
        "sound": BARK_SOUND,
        "group": BARK_GROUP,
        "level": BARK_LEVEL,
        "archive": BARK_ARCHIVE,
        "url": BARK_URL
    }

    try:
        res = requests.post(bark_url, json=data, timeout=10)
        if res.status_code == 200:
            print("✅ Bark推送成功")
        else:
            print(f"⚠️ Bark推送失败: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ Bark推送异常: {e}")


def zlapi_checkin():

    username = os.getenv("ZLAPI_USERNAME")

    # ⚠️ 如果你写死账号，就会覆盖环境变量
    username = "tianwuziyan"

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

    try:
        res = requests.post(url, headers=headers, json={"username": username}, timeout=15)

        print("状态码:", res.status_code)

        if res.status_code != 200:
            msg = f"❌ 请求失败: {res.text}"
            print(msg)
            bark_push("宅恋API签到失败", msg)
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
            f"{message}\n"
            f"昨日调用: {calls} 次\n"
            f"昨日消费: ¥{consumption:.2f}\n"
            f"预计奖励: {reward_text}\n\n"
            "签到：https://qd.zlapi.pro/"
        )

        print(final_msg)

        bark_push("宅恋API签到成功", final_msg)

    except Exception as e:
        err = f"❌ 请求异常: {str(e)}"
        print(err)
        bark_push("宅恋API签到异常", err)


if __name__ == "__main__":

    max_random_delay = os.getenv("MAX_RANDOM_DELAY", "0")

    if max_random_delay == "0":
        print("🚀 已关闭随机延迟，立即执行")
    else:
        delay = random.randint(0, 1800)
        print(f"⏰ 随机延迟 {delay} 秒")
        time.sleep(delay)

    zlapi_checkin()
