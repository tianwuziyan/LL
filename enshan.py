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
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

SIGN_URL = (
    f"{BASE_URL}/plugin.php?"
    "id=erling_qd:action&action=sign"
)

INFO_URL = (
    f"{BASE_URL}/home.php?"
    "mod=spacecp&ac=credit"
)

# ================= 环境变量 =================

enshan_cookie = os.getenv("enshan_cookie", "")

# ================= 工具函数 =================

def notify_user(title, content):
    if hadsend:
        try:
            send(title, content)
        except Exception as e:
            print(e)

def extract_first(text, patterns, default=None, flags=0):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return default

def extract_number(text):
    if not text:
        return 0

    num = re.sub(r"[^\d]", "", str(text))

    return int(num) if num else 0

def parse_cookies(cookie_str):
    if not cookie_str:
        return []

    cookies = []

    for line in cookie_str.split("\n"):
        line = line.strip()

        if not line:
            continue

        if "&&" in line:
            cookies.extend(line.split("&&"))
        else:
            cookies.append(line)

    return [x.strip() for x in cookies if x.strip()]

# ================= 签到类 =================

class EnshanSigner:

    def __init__(self, cookie, index=1):

        self.index = index
        self.cookie = cookie

        self.session = requests.Session()

        self.session.headers.update(HEADERS)

        self.session.headers.update({
            "Cookie": cookie
        })

        self.formhash = None

        self.username = "未知"

        self.coin_before = 0
        self.coin_after = 0

        self.point_before = 0
        self.point_after = 0

    # ================= 获取formhash =================

    def get_formhash(self):

        print("🔐 获取formhash...")

        urls = [
            f"{BASE_URL}/forum.php",
            BASE_URL,
        ]

        for url in urls:

            try:

                response = self.session.get(
                    url,
                    timeout=20,
                    allow_redirects=True
                )

                print(f"🌐 {url}")
                print(f"📡 状态码: {response.status_code}")

                if response.status_code != 200:
                    continue

                html = response.text

                self.formhash = extract_first(
                    html,
                    [
                        r'formhash=([a-f0-9]+)',
                        r'name="formhash"\s+value="([a-f0-9]+)"'
                    ],
                    flags=re.I
                )

                if self.formhash:

                    print(f"✅ formhash: {self.formhash}")

                    return True

            except Exception as e:

                print(f"❌ {e}")

        return False

    # ================= 获取用户信息 =================

    def get_user_info(self, after=False):

        try:

            response = self.session.get(
                INFO_URL,
                timeout=20
            )

            print(f"👤 用户信息状态码: {response.status_code}")

            if response.status_code != 200:
                return False

            html = response.text

            coin = extract_first(
                html,
                [
                    r"恩山币[:：]\s*</em>\s*([^<&\s]+)",
                    r"恩山币[:：]\s*([^<\s]+)"
                ],
                default="0",
                flags=re.S
            )

            point = extract_first(
                html,
                [
                    r"积分[:：]\s*</em>\s*([^<&\s]+)",
                    r"积分[:：]\s*([^<\s]+)"
                ],
                default="0",
                flags=re.S
            )

            username = extract_first(
                html,
                [
                    r'访问我的空间">([^<]+)</a>',
                    r'class="vwmy"[^>]*>([^<]+)</a>',
                ],
                default="未知用户",
                flags=re.S
            )

            self.username = username

            if after:
                self.coin_after = extract_number(coin)
                self.point_after = extract_number(point)
            else:
                self.coin_before = extract_number(coin)
                self.point_before = extract_number(point)

            return True

        except Exception as e:

            print(e)

            return False

    # ================= 执行签到 =================

    def sign(self):

        print("📝 开始签到...")

        headers = {
            **HEADERS,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.right.com.cn",
            "Referer": f"{BASE_URL}/forum.php",
            "Content-Type": (
                "application/x-www-form-urlencoded;"
                " charset=UTF-8"
            ),
        }

        data = {
            "formhash": self.formhash
        }

        try:

            response = self.session.post(
                SIGN_URL,
                headers=headers,
                data=data,
                timeout=20
            )

            print(f"📡 签到状态码: {response.status_code}")

            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"

            try:

                result = response.json()

                msg = str(
                    result.get("message", "")
                )

            except:

                msg = response.text

            print(msg)

            if (
                "成功" in msg
                or "已签到" in msg
                or "已经签到" in msg
            ):
                return True, msg

            return False, msg

        except Exception as e:

            return False, str(e)

    # ================= 主逻辑 =================

    def run(self):

        print(f"\n========== 账号{self.index} ==========")

        if not self.get_formhash():

            return (
                "❌ 获取formhash失败\n\n"
                "1. Cookie失效\n"
                "2. Cookie不完整\n"
                "3. IP被521风控\n\n"
                "必须重新抓完整Cookie"
            )

        self.get_user_info(after=False)

        time.sleep(random.uniform(2, 5))

        success, msg = self.sign()

        time.sleep(random.uniform(2, 4))

        self.get_user_info(after=True)

        coin_gain = (
            self.coin_after - self.coin_before
        )

        point_gain = (
            self.point_after - self.point_before
        )

        result = f"""
🌟 恩山论坛签到结果

👤 用户: {self.username}

💰 恩山币:
{self.coin_before} → {self.coin_after}

📊 积分:
{self.point_before} → {self.point_after}

🎁 收益:
+{coin_gain} 恩山币
+{point_gain} 积分

📝 结果:
{msg}

⏰ 时间:
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return result

# ================= 主入口 =================

def main():

    print(
        f"==== 恩山签到开始 "
        f"{datetime.now()} ===="
    )

    if not enshan_cookie:

        notify_user(
            "恩山签到失败",
            "未配置 enshan_cookie"
        )

        return

    cookies = parse_cookies(enshan_cookie)

    print(f"📦 共{len(cookies)}个账号")

    for index, cookie in enumerate(cookies):

        try:

            signer = EnshanSigner(
                cookie,
                index + 1
            )

            result = signer.run()

            print(result)

            notify_user(
                f"恩山论坛账号{index+1}",
                result
            )

            time.sleep(
                random.uniform(10, 20)
            )

        except Exception as e:

            error = (
                f"账号{index+1}异常:\n{e}"
            )

            print(error)

            notify_user(
                f"恩山论坛账号{index+1}失败",
                error
            )

    print("==== 全部完成 ====")

# ================= 云函数入口 =================

def handler(event, context):
    main()

if __name__ == "__main__":
    main()
