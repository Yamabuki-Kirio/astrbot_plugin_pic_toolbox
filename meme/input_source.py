"""将 AstrBot 图片组件提供的远程 URL 或本地文件统一复制到工作路径。"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname


def _local_path_from_source(source: str) -> Path | None:
    if os.path.isabs(source):
        return Path(source)
    parsed = urlparse(source)
    if parsed.scheme == "file":
        path_text = url2pathname(unquote(parsed.path))
        if parsed.netloc and parsed.netloc.lower() != "localhost":
            path_text = f"//{parsed.netloc}{path_text}"
        if os.name == "nt" and path_text.startswith("/") and len(path_text) > 2:
            if path_text[2] == ":":
                path_text = path_text[1:]
        return Path(path_text)
    if not parsed.scheme:
        return Path(source)
    return None


def acquire_image(source: str, destination: str, max_bytes: int = 100 * 1024 * 1024) -> str:
    """读取图片来源并写入 destination。

    支持 http(s) URL、file:// URI 和 AstrBot 生成的本地绝对路径。
    """
    source = str(source or "").strip()
    if not source:
        raise ValueError("图片来源为空")

    target = Path(destination)
    local_path = _local_path_from_source(source)
    try:
        if local_path is not None:
            if not local_path.is_absolute():
                raise ValueError(f"不接受相对图片路径: {source}")
            if not local_path.is_file():
                raise FileNotFoundError(f"本地图片不存在: {local_path}")
            if local_path.stat().st_size > max_bytes:
                raise ValueError("图片超过 100 MB 限制")
            shutil.copyfile(local_path, target)
            return str(target)

        parsed = urlparse(source)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"不支持的图片来源协议: {parsed.scheme}")

        import requests

        with requests.get(
            source,
            timeout=30,
            headers={"User-Agent": "AstrBot/pic_toolbox"},
            stream=True,
        ) as response:
            response.raise_for_status()
            content_length = int(response.headers.get("Content-Length", 0) or 0)
            if content_length > max_bytes:
                raise ValueError("图片超过 100 MB 限制")
            written = 0
            with target.open("wb") as output:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > max_bytes:
                        raise ValueError("图片超过 100 MB 限制")
                    output.write(chunk)
        return str(target)
    except Exception:
        try:
            target.unlink()
        except OSError:
            pass
        raise
