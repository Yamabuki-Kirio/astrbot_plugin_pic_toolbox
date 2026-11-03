"""QQ 系统表情素材地址解析。"""

QQ_FACE_SCHEME = "qqface://"


def make_qq_face_source(face_id: object) -> str | None:
    """把 AstrBot Face 组件中的编号转换为内部图片源。"""
    value = str(face_id or "").strip()
    if not value.isdigit():
        return None
    return f"{QQ_FACE_SCHEME}{value}"


def qq_face_candidates(source: str) -> list[str]:
    """返回 QQ 表情素材候选地址，优先使用带动画的完整资源。"""
    if not source.startswith(QQ_FACE_SCHEME):
        return [source]

    face_id = source[len(QQ_FACE_SCHEME):]
    if not face_id.isdigit():
        return []

    return [
        # QFace 收录了 QQNT 新表情的 APNG，包含旧 qzone 地址没有的 4xx ID。
        f"https://koishi.js.org/QFace/assets/qq_emoji/{face_id}/apng/{face_id}.png",
        f"https://koishi.js.org/QFace/assets/qq_emoji/{face_id}/png/{face_id}.png",
        # 老版 QQ 系统表情保留腾讯官方地址作为回退。
        f"https://qzonestyle.gtimg.cn/qzone/em/e{face_id}.gif",
    ]
