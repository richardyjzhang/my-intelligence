"""
知识问答智能体 —— 基于 ChromaDB 的 RAG 问答。

职责：
  1. 注册智能体配置
  2. 编排检索 → 构建消息 → 流式生成
  3. 输出 SSE：reasoning_delta / answer_delta / done / error（meta 由 router 统一发送）
"""

import logging
import uuid
from typing import Generator

import config
from services.agents import sse_event
from services.ai import ai_client, register_agent, AgentProfile
from .tools import retrieve_context_expanded, build_messages

logger = logging.getLogger(__name__)

AGENT_ID = "knowledge"

SYSTEM_PROMPT = """你是"拾知"知识管理系统的 AI 助手。请基于提供的参考文档内容回答用户问题。

规则：
1. 优先使用参考文档中的内容回答，如果参考文档不足以回答，可以结合你的通用知识进行补充，但需注明。
2. 回答使用 Markdown 格式。
3. 如果用户要求生成图表，请在回答中包含一个 ECharts 配置块，格式为：
   ```echarts
   { ... ECharts option JSON ... }
   ```
   图表配置必须是合法的 ECharts option 对象。
4. 回答要简洁、准确、有条理。"""

register_agent(AGENT_ID, AgentProfile(
    name="知识问答智能体",
    description="基于知识库的 RAG 问答",
    system_prompt=SYSTEM_PROMPT,
    thinking_disabled=True,
))


def knowledge_stream(
    query: str,
    history: list[dict] | None = None,
    model: str | None = None,
) -> Generator[str, None, None]:
    """
    流式问答，yield SSE 格式的事件行（不含 meta）。
    """
    request_id = str(uuid.uuid4())
    history = history or []
    model = model or getattr(config, "CHAT_MODEL", "qwen3:8b")

    logger.info("[%s] 知识问答: query=%s, model=%s", request_id, query[:80], model)

    try:
        logger.info("[%s] 检索并扩展上下文...", request_id)
        contexts = retrieve_context_expanded(query)
        if contexts:
            total_chars = sum(len(c.get("content", "")) for c in contexts)
            logger.info("[%s] 命中 %s 篇文档, 上下文总长 %s 字符", request_id, len(contexts), total_chars)
        else:
            logger.info("[%s] 未检索到相关片段，将直接回答", request_id)

        sources = [
            {"title": c.get("title", ""), "documentId": c.get("documentId")}
            for c in contexts
        ]

        messages = build_messages(query, contexts, history)
        logger.info("[%s] 构建消息完成, 共 %s 条消息, 调用模型...", request_id, len(messages))

        reasoning_chunks = 0
        answer_chunks = 0
        for event_type, text in ai_client.chat_stream(AGENT_ID, messages, model=model):
            if event_type == "thinking":
                reasoning_chunks += 1
                yield sse_event("reasoning_delta", {"content": text})
            else:
                answer_chunks += 1
                yield sse_event("answer_delta", {"content": text})

        logger.info("[%s] 问答完成: reasoning=%s chunks, answer=%s chunks",
                    request_id, reasoning_chunks, answer_chunks)
        yield sse_event("done", {"sources": sources})

    except Exception as e:
        logger.error("知识问答流式异常: %s", e, exc_info=True)
        yield sse_event("error", {"message": str(e)})
