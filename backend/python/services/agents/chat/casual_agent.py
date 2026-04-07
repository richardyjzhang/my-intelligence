"""
闲聊智能体 —— 不检索知识库，纯对话。
"""

import logging
import uuid
from typing import Generator

import config
from services.agents import sse_event
from services.ai import ai_client, register_agent, AgentProfile
from services.personalization_prompt import compose_system_with_persona

logger = logging.getLogger(__name__)

AGENT_ID = "casual"

SYSTEM_PROMPT = """你是「拾知」知识管理系统的 AI 助手，正在与用户轻松闲聊。

规则：
1. 语气友好、自然，可以适度幽默，适合陪伴用户放松、划水聊天。
2. 不要假装检索了知识库；若用户问起系统内文档或专业资料，可温和建议切换到「文档检索」或「知识问答」模式。
3. 回答使用 Markdown 格式（需要时）。
4. 回答简洁，不要长篇大论。"""

register_agent(AGENT_ID, AgentProfile(
    name="闲聊智能体",
    description="无知识检索的闲聊",
    system_prompt=SYSTEM_PROMPT,
    thinking_disabled=True,
))


def _build_messages(query: str, history: list[dict]) -> list[dict]:
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query})
    return messages


def casual_stream(
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
        messages = _build_messages(query, history)
        logger.info("[%s] 闲聊: query=%s", request_id, query[:80])

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

        yield sse_event("done", {"sources": []})

    except Exception as e:
        logger.error("闲聊流式异常: %s", e, exc_info=True)
        yield sse_event("error", {"message": str(e)})
