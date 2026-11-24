
import os
import re
import sys
import ipaddress
import urllib.request
from pathlib import Path


SOURCE_URL = os.getenv(
    "SOURCE_URL",
    "https://www.macat.vip/list.txt"
)

OUTPUT_FILE = Path(
    os.getenv("OUTPUT_FILE", "rules.list")
)

BLOCK_IP = "0.0.0.0"

MIN_DOMAIN_COUNT = int(
    os.getenv("MIN_DOMAIN_COUNT", "1")
)

MAX_DROP_PERCENT = int(
    os.getenv("MAX_DROP_PERCENT", "50")
)

LABEL_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


def normalize_domain(value):
    value = value.strip().rstrip(".")

    if not value or "*" in value:
        return None

    try:
        domain = value.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return None

    if len(domain) > 253:
        return None

    try:
        ipaddress.ip_address(domain)
        return None
    except ValueError:
        pass

    labels = domain.split(".")

    if len(labels) < 2:
        return None

    if not all(
        LABEL_PATTERN.fullmatch(label)
        for label in labels
    ):
        return None

    return domain


def download_source():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Surge-Hosts-Converter/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        if response.status != 200:
            raise RuntimeError(
                f"HTTP 状态异常: {response.status}"
            )

        content = response.read()

    if not content:
        raise RuntimeError("源文件为空")

    return content.decode("utf-8-sig")


def extract_domains(content):
    domains = set()

    for line in content.splitlines():

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        # 移除行尾注释
        line = line.split("#", 1)[0].strip()

        parts = line.split()

        if len(parts) < 2:
            continue

        # 只处理指定屏蔽 IP
        if parts[0] != BLOCK_IP:
            continue

        for item in parts[1:]:

            domain = normalize_domain(item)

            if domain:
                domains.add(domain)

    return sorted(domains)


def count_existing_rules(path):
    if not path.exists():
        return 0

    count = 0

    for line in path.read_text(
        encoding="utf-8"
    ).splitlines():

        if line.startswith("DOMAIN,"):
            count += 1

    return count


def validate_result(domains, old_count):

    if len(domains) < MIN_DOMAIN_COUNT:
        raise RuntimeError(
            f"有效域名数量不足: {len(domains)}"
        )

    if old_count > 0:

        minimum = int(
            old_count * (100 - MAX_DROP_PERCENT) / 100
        )

        if len(domains) < minimum:
            raise RuntimeError(
                f"规则数量异常下降: "
                f"旧数量={old_count}, "
                f"新数量={len(domains)}, "
                f"最低允许={minimum}"
            )


def save_rules(domains):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    content = "\n".join(
        f"DOMAIN,{domain}"
        for domain in domains
    ) + "\n"

    temp_file = OUTPUT_FILE.with_suffix(
        OUTPUT_FILE.suffix + ".tmp"
    )

    temp_file.write_text(
        content,
        encoding="utf-8",
        newline="\n"
    )

    os.replace(temp_file, OUTPUT_FILE)


def main():

    print("开始下载 Hosts 列表...")

    content = download_source()

    print("下载完成，开始提取域名...")

    domains = extract_domains(content)

    old_count = count_existing_rules(
        OUTPUT_FILE
    )

    validate_result(domains, old_count)

    save_rules(domains)

    print("=" * 40)
    print(f"原始文件大小: {len(content)} 字符")
    print(f"原有规则数量: {old_count}")
    print(f"生成规则数量: {len(domains)}")
    print(f"输出文件: {OUTPUT_FILE}")
    print("=" * 40)

    print("转换成功！")


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print(
            f"转换失败: {error}",
            file=sys.stderr
        )

        sys.exit(1)
