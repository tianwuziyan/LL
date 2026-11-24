
import os
import urllib.request
from pathlib import Path

SOURCE_URL = os.environ["SOURCE_URL"]
REMOVE_TEXT = os.environ["REMOVE_TEXT"].encode("utf-8")
OUTPUT_FILE = Path(os.environ["OUTPUT_FILE"])

request = urllib.request.Request(
    SOURCE_URL,
    headers={"User-Agent": "GitHub-Actions"}
)

with urllib.request.urlopen(request, timeout=60) as response:
    content = response.read()

if not content:
    raise RuntimeError("下载内容为空，停止更新")

result = content.replace(REMOVE_TEXT, b"")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.write_bytes(result)

print(f"原始大小：{len(content)} bytes")
print(f"处理后大小：{len(result)} bytes")
print("规则文件更新完成")
