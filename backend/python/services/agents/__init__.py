"""
智能体包 —— 导入各子模块以触发智能体注册。

新增智能体时，在此处添加 import 即可。
"""

import json


def sse_event(event: str, data: dict) -> str:
    """格式化 SSE 事件行，所有流式智能体通用。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


from . import chat  # noqa: F401, E402 — 加载 router 与各子智能体注册
