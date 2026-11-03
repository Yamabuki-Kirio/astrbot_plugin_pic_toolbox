"""从 OneBot get_msg 返回值中提取可处理的图片源。"""

from .qq_face import make_qq_face_source


def _message_segments(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    for key in ("message", "original_message"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, dict):
        return _message_segments(data)
    return []


def extract_onebot_media_source(payload: object) -> str | None:
    """优先返回真实媒体地址，最后才回退到系统 Face ID。"""
    segments = _message_segments(payload)

    for segment in segments:
        seg_type = str(segment.get("type") or "").lower()
        if seg_type not in {"image", "mface", "marketface"}:
            continue
        data = segment.get("data")
        if not isinstance(data, dict):
            continue
        for attr in ("url", "path", "file"):
            value = data.get(attr)
            if not isinstance(value, str) or not value.strip():
                continue
            value = value.strip()
            # NapCat/SnowLuma 可能用这些哨兵值标记商城表情，不是可下载文件。
            if value.lower() in {"marketface", "mface"}:
                continue
            return value

    for segment in segments:
        if str(segment.get("type") or "").lower() != "face":
            continue
        data = segment.get("data")
        if isinstance(data, dict):
            source = make_qq_face_source(data.get("id"))
            if source:
                return source
    return None
