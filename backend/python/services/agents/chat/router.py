"""
对话路由 —— 根据 mode / 意图分类，分发到闲聊、文档查找或知识问答。
"""

from __future__ import annotations

import logging
import uuid
from typing import Generator

import config
from services.agents import sse_event
from .classifier import classify_intent
from .casual_agent import casual_stream
from .doc_search_agent import doc_search_stream
from .knowledge_agent import knowledge_stream

logger = logging.getLogger(__name__)

VALID_MODES = frozenset({"auto", "casual", "doc_search", "knowledge_qa"})


def resolve_intent(mode: str | None, query: str, model: str | None) -> str:
    """返回 casual | doc_search | knowledge_qa。"""
    m = (mode or "auto").strip().lower()
    if m not in VALID_MODES:
        m = "auto"
    if m != "auto":
        return m
    return classify_intent(query, model=model)


def chat_stream(
    query: str,
    history: list[dict] | None = None,
    model: str | None = None,
    mode: str | None = None,
) -> Generator[str, None, None]:
    """
    流式对话入口。先发送 meta（含 intent），再转发子智能体事件。
    """
    request_id = str(uuid.uuid4())
    history = history or []
    model = model or getattr(config, "CHAT_MODEL", "qwen3:8b")

    intent = resolve_intent(mode, query, model)
    logger.info("[%s] 路由 intent=%s, mode=%s", request_id, intent, mode)

    yield sse_event("meta", {"requestId": request_id, "model": model, "intent": intent})

    if intent == "casual":
        yield from casual_stream(query, history, model)
    elif intent == "doc_search":
        yield from doc_search_stream(query, history, model)
    else:
        yield from knowledge_stream(query, history, model)
