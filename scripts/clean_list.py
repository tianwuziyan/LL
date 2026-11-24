
import os
import urllib.request
from pathlib import Path

source_url = os.environ["SOURCE_URL"]
target_file = Path(os.environ["OUTPUT_FILE"])
remove_text = os.environ["REMOVE_TEXT"].encode("ascii")

request = urllib.request.Request(
    source_url,
    headers={"User-Agent": "GitHub-Actions"}
)

with urllib.request.urlopen(request, timeout=60) as response:
    content = response.read()

if not content:
    raise RuntimeError("下载内容为空，取消更新")

cleaned = content.replace(remove_text, b"")

target_file.parent.mkdir(parents=True, exist_ok=True)
target_file.write_bytes(cleaned)

print(f"原始大小：{len(content)} bytes")
print(f"处理后大小：{len(cleaned)} bytes")
print(f"删除数量：{(len(content) - len(cleaned)) // len(remove_text)}")
print(f"输出文件：{target_file}")
