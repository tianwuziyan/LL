"""
cron "39 12 * * *" script-path=xxx.py,tag=恩山论坛签到
new Env('恩山论坛签到')
"""

import os
import re
import time
import random
import requests
from datetime import datetime

# ================= 通知模块 =================

hadsend = False
send = None

try:
    from notify import send
    hadsend = True
    print("✅ notify加载成功")
except:
    print("⚠️ notify未加载")


# ================= 配置 =================

BASE_URL = "https://www.right.com.cn/forum"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",   # ❗禁止 br（服务器关键）
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

SIGN_URL = f"{BASE_URL}/plugin.php?id=erling_qd:action&action=sign"
INFO_URL = f"{BASE_URL}/home.php?mod=spacecp&ac=credit"

enshan_cookie = os.getenv("enshan_cookie")

# ================= 工具 =================

def notify_user(title, content):
    if hadsend:
        try:
            send(title, content)
        except Exception as e:
            print(e)
    else:
        print(title, content)


def extract_first(text, patterns, default=None, flags=0):
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            return m.group(1).strip()
    return default


def extract_number(text):
    if not text:
        return 0
    num = re.sub(r"[^\d]", "", str(text))
    return int(num) if num else 0


def parse_cookies(cookie_str):
    if not cookie_str:
        return []
    out = []
    for line in cookie_str.split("\n"):
        line = line.strip()
        if not line:
            continue
        out.extend([x.strip() for x in line.split("&&") if x.strip()])
    return out


# ================= 核心类 =================

class EnshanSigner:

    def __init__(self, cookie, index=1):
        self.cookie = cookie
        self.index = index

        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.headers["Cookie"] = cookie

        self.formhash = None

        self.user = "未知"
        self.coin_before = 0
        self.coin_after = 0
        self.point_before = 0
        self.point_after = 0

    # ---------- 获取formhash（最稳定方式） ----------
    def get_formhash(self):

        urls = [
            f"{BASE_URL}/forum.php",
            BASE_URL
        ]

        for url in urls:
            try:
                r = self.session.get(url, timeout=20)

                print(f"🔍 访问: {url} -> {r.status_code}")

                if r.status_code != 200:
                    continue

                html = r.text

                self.formhash = extract_first(
                    html,
                    [
                        r'name="formhash"\s+value="([a-zA-Z0-9]+)"',
                        r'formhash=([a-zA-Z0-9]+)'
                    ],
                    flags=re.I
                )

                if self.formhash:
                    print(f"✅ formhash: {self.formhash}")
                    return True

            except Exception as e:
                print("❌", e)

        return False

    # ---------- 用户信息 ----------
    def get_user_info(self, after=False):

        try:
            r = self.session.get(INFO_URL, timeout=20)

            print(f"👤 用户信息: {r.status_code}")

            if r.status_code != 200:
                return False

            html = r.text

            coin = extract_first(html, [r"恩山币[:：]\s*</em>\s*([^<&\s]+)"], "0", re.S)
            point = extract_first(html, [r"积分[:：]\s*</em>\s*([^<&\s]+)"], "0", re.S)

            if after:
                self.coin_after = extract_number(coin)
                self.point_after = extract_number(point)
            else:
                self.coin_before = extract_number(coin)
                self.point_before = extract_number(point)

                self.user = extract_first(
                    html,
                    [
                        r'访问我的空间">([^<]+)</a>',
                        r'class="vwmy"[^>]*>([^<]+)</a>'
                    ],
                    "未知用户",
                    re.S
                )

            return True

        except Exception as e:
            print(e)
            return False

    # ---------- 签到 ----------
    def sign(self):

        print("📝 开始签到...")

        # ⭐关键：先预热（模拟浏览器）
        self.session.get(f"{BASE_URL}/forum.php", timeout=20)

        time.sleep(random.uniform(1, 3))

        headers = {
            **HEADERS,
            "Referer": f"{BASE_URL}/forum.php",
            "Origin": "https://www.right.com.cn",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        data = {
            "formhash": self.formhash
        }

        try:
            r = self.session.post(
                SIGN_URL,
                headers=headers,
                data=data,
                timeout=20
            )

            print(f"📡 签到状态码: {r.status_code}")

            text = r.text

            # ⭐关键：识别“200但实际是提示页”
            if "<html" in text and "提示信息" in text:
                return False, "被风控拦截（提示页）"

            if "已签到" in text:
                return True, "今日已签到"

            if "成功" in text:
                return True, "签到成功"

            return False, text[:150]

        except Exception as e:
            return False, str(e)

    # ---------- 主流程 ----------
    def run(self):

        print(f"\n==== 账号{self.index} 开始 ====")

        if not self.get_formhash():
            return False, "获取formhash失败（Cookie/IP问题）"

        self.get_user_info(False)

        time.sleep(random.uniform(2, 4))

        ok, msg = self.sign()

        time.sleep(random.uniform(2, 4))

        self.get_user_info(True)

        coin_gain = self.coin_after - self.coin_before
        point_gain = self.point_after - self.point_before

        result = f"""
🌟 恩山签到结果

👤 用户: {self.user}

💰 恩山币: {self.coin_before} → {self.coin_after}
📊 积分: {self.point_before} → {self.point_after}

🎁 收益:
+{coin_gain} 币
+{point_gain} 积分

📝 签到结果:
{msg}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return ok, result


# ================= 主程序 =================

def main():

    print("==== 恩山论坛签到开始 ====")

    if not enshan_cookie:
        notify_user("恩山签到失败", "未配置cookie")
        return

    cookies = parse_cookies(enshan_cookie)

    print(f"📦 账号数: {len(cookies)}")

    success = 0

    for i, cookie in enumerate(cookies):

        try:
            signer = EnshanSigner(cookie, i + 1)

            ok, msg = signer.run()

            if ok:
                success += 1

            notify_user(
                f"账号{i+1}{'成功' if ok else '失败'}",
                msg
            )

            time.sleep(random.uniform(8, 15))

        except Exception as e:
            notify_user(f"账号{i+1}异常", str(e))

    notify_user(
        "签到汇总",
        f"成功 {success}/{len(cookies)}"
    )


def handler(event, context):
    main()


if __name__ == "__main__":
    main()
