"""
文档查找智能体 —— ES 检索 + 流式生成文档列表说明。
"""

import json
import logging
import uuid
from typing import Generator

import config
from services.agents import sse_event
from services.ai import ai_client, register_agent, AgentProfile
from services.personalization_prompt import compose_system_with_persona
from .es_tools import search_documents

logger = logging.getLogger(__name__)

AGENT_ID = "doc_search"

SYSTEM_PROMPT = """你是「拾知」知识管理系统的 AI 助手，帮助用户根据检索结果找到相关文档。

规则：
1. 下面会提供「检索到的文档列表」（JSON），每项含 documentId、title、tags、fileName。请用 Markdown 整理成清晰列表或表格，方便用户点击前预览。
2. 若列表为空，说明没有匹配文档，请礼貌说明并建议用户换关键词或检查是否已上传/索引完成。
3. 不要编造不存在的文档；只根据提供的数据回答。
4. 语气简洁、专业。"""

register_agent(AGENT_ID, AgentProfile(
    name="文档查找智能体",
    description="基于 ES 的文档检索",
    system_prompt=SYSTEM_PROMPT,
    thinking_budget=1024,
))


def _build_user_content(query: str, docs: list[dict]) -> str:
    payload = json.dumps(docs, ensure_ascii=False, indent=2)
    return f"用户查找需求：{query}\n\n检索到的文档（JSON）：\n{payload}"


def _build_messages(query: str, docs: list[dict], history: list[dict]) -> list[dict]:
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": _build_user_content(query, docs)})
    return messages


def doc_search_stream(
    query: str,
    history: list[dict] | None = None,
    model: str | None = None,
    *,
    ai_persona_title: str | None = None,
    ai_custom_instruction: str | None = None,
) -> Generator[str, None, None]:
    history = history or []
    model = model or getattr(config, "CHAT_MODEL", "qwen3:8b")
    request_id = str(uuid.uuid4())

    try:
        docs = search_documents(query)
        logger.info("[%s] 文档检索: query=%s, hits=%s", request_id, query[:80], len(docs))

        sources = [
            {
                "title": d.get("title") or "",
                "documentId": d.get("documentId"),
                "fileName": d.get("fileName") or "",
            }
            for d in docs
            if d.get("documentId") is not None
        ]

        messages = _build_messages(query, docs, history)

        system_override = compose_system_with_persona(
            SYSTEM_PROMPT,
            ai_persona_title=ai_persona_title,
            ai_custom_instruction=ai_custom_instruction,
        )
        for event_type, text in ai_client.chat_stream(
            AGENT_ID,
            messages,
            model=model,
            system_prompt_override=system_override,
        ):
            if event_type == "thinking":
                yield sse_event("reasoning_delta", {"content": text})
            else:
                yield sse_event("answer_delta", {"content": text})

        yield sse_event("done", {"sources": sources})

    except Exception as e:
        logger.error("文档查找流式异常: %s", e, exc_info=True)
        yield sse_event("error", {"message": str(e)})
