# -*- coding: utf-8 -*-
"""
name: 书香门第签到
cron: 0 0 * * *
环境变量：

sxmd_account=账号1&账号2
sxmd_password=密码1&密码2
"""

import os
import re
import requests

HOST = "www.txtnovel.vip"

accounts = os.getenv("sxmd_account", "").split("&")
passwords = os.getenv("sxmd_password", "").split("&")


headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X)",
}


class SXMD:
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(headers)

    def login(self):
        url = (
            f"http://{HOST}/member.php?mod=logging"
            f"&action=login&loginsubmit=yes&loginhash=LxEUe&mobile=2"
        )

        data = {
            "formhash": "",
            "referer": f"http://{HOST}/plugin.php?id=dsu_paulsign:sign",
            "fastloginfield": "username",
            "cookietime": 2592000,
            "username": self.account,
            "password": self.password,
            "questionid": 0,
            "answer": "",
            "submit": True,
        }

        r = self.session.post(url, data=data, allow_redirects=False)

        if not self.session.cookies:
            raise Exception("登录失败")

def get_formhash(self):
    url = f"http://{HOST}/plugin.php?id=dsu_paulsign:sign&mobile=yes"

    r = self.session.get(url)
    text = r.text

    # print(text)

    if "已经签到过了" in text:
        return None

    patterns = [
        r'name="formhash" value="(.*?)"',
        r'formhash=(.*?)"',
        r'formhash=(.*?)&',
    ]

    for p in patterns:
        formhash = re.search(p, text)

        if formhash:
            return formhash.group(1)

    raise Exception("获取formhash失败")

        return formhash.group(1)

    def sign(self, formhash):
        url = (
            f"http://{HOST}/plugin.php?id=dsu_paulsign:sign"
            f"&operation=qiandao&infloat=0&inajax=0&mobile=yes"
        )

        data = {
            "formhash": formhash,
            "qdxq": "kx",
        }

        r = self.session.post(url, data=data)
        text = r.text

        if "签到成功" in text or "恭喜你" in text:
            return "签到成功"

        if "已经签到过了" in text:
            return "今日已签到"

        return "签到失败"

    def get_gold(self):
        url = f"http://{HOST}/home.php?mod=space"

        r = self.session.get(url)
        text = r.text

        gold = re.search(r"金币</em>(.+?)枚</li>", text)

        if gold:
            return gold.group(1).strip()

        return "未知"

    def run(self):
        print(f"\n========== {self.account} ==========")

        self.login()

        formhash = self.get_formhash()

        if formhash:
            result = self.sign(formhash)
        else:
            result = "今日已签到"

        gold = self.get_gold()

        print(f"签到结果：{result}")
        print(f"当前金币：{gold}")


if __name__ == "__main__":
    if not accounts or not passwords:
        print("请配置环境变量")
        exit()

    for i in range(len(accounts)):
        try:
            sxmd = SXMD(accounts[i], passwords[i])
            sxmd.run()
        except Exception as e:
            print(f"账号{i + 1}执行失败：{str(e)}")
