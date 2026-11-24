
import os
import re
import sys
import ipaddress
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = "https://www.macat.vip/list.txt"
OUTPUT_FILE = Path("rules.list")

# 只处理指定的 Hosts 屏蔽 IP
BLOCK_IP = "0.0.0.0"

DOMAIN_PATTERN = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


def fetch_text():
    request = Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/plain,*/*"
        }
    )

    with urlopen(request, timeout=60) as response:
        data = response.read()

    if not data:
        raise RuntimeError("下载内容为空")

    if b"<html" in data[:2048].lower():
        raise RuntimeError("源地址返回了 HTML，而不是 Hosts 文件")

    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise RuntimeError("无法识别源文件编码")


def is_valid_domain(domain):
    domain = domain.lower().rstrip(".")

    if not domain or len(domain) > 253:
        return False

    try:
        ipaddress.ip_address(domain)
        return False
    except ValueError:
        pass

    if not DOMAIN_PATTERN.fullmatch(domain):
        return False

    return all(
        len(label) <= 63
        for label in domain.split(".")
    )


def extract_domains(text):
    domains = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        # 忽略行内注释
        line = line.split("#", 1)[0].strip()

        parts = line.split()

        if len(parts) < 2:
            continue

        try:
            ip = str(ipaddress.ip_address(parts[0]))
        except ValueError:
            continue

        if ip != BLOCK_IP:
            continue

        for domain in parts[1:]:
            domain = domain.lower().rstrip(".")

            if is_valid_domain(domain):
                domains.add(domain)

    return sorted(domains)


def generate_rules(domains):
    if not domains:
        raise RuntimeError("没有提取到有效域名，禁止覆盖旧文件")

    return "\n".join(
        f"DOMAIN,{domain}" for domain in domains
    ) + "\n"


def save_rules(content):
    temp_file = OUTPUT_FILE.with_suffix(".tmp")

    temp_file.write_text(content, encoding="utf-8")

    # 原子替换，避免写入中断破坏旧文件
    temp_file.replace(OUTPUT_FILE)


def main():
    print("开始下载 Hosts 文件")

    source = fetch_text()

    print("开始提取域名")

    domains = extract_domains(source)

    print(f"有效域名数量：{len(domains)}")

    rules = generate_rules(domains)

    save_rules(rules)

    print(f"成功生成：{OUTPUT_FILE}")
    print("规则格式：DOMAIN,")
    print("处理完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"执行失败：{error}", file=sys.stderr)
        sys.exit(1)
