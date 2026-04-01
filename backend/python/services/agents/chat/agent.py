"""
对话智能体 —— 基于知识库的 RAG 问答。

职责：
  1. 从 ChromaDB 检索相关文档片段
  2. 构建带上下文的消息列表
  3. 调用 AIClient 流式生成回答
  4. 输出 SSE 格式事件流（meta / reasoning_delta / answer_delta / done / error）
"""

import json
import logging
import uuid
from typing import Generator

import config
from services.ai import ai_client, register_agent, AgentProfile
from services.chroma_service import get_collection, get_embeddings

logger = logging.getLogger(__name__)

AGENT_ID = "chat"

SYSTEM_PROMPT = """你是"拾知"知识管理系统的 AI 助手。请基于提供的知识片段回答用户问题。

规则：
1. 优先使用知识片段中的内容回答，如果知识片段不足以回答，可以结合你的通用知识进行补充，但需注明。
2. 回答使用 Markdown 格式。
3. 如果用户要求生成图表，请在回答中包含一个 ECharts 配置块，格式为：
   ```echarts
   { ... ECharts option JSON ... }
   ```
   图表配置必须是合法的 ECharts option 对象。
4. 回答要简洁、准确、有条理。"""

register_agent(AGENT_ID, AgentProfile(
    name="对话智能体",
    description="基于知识库的 RAG 问答",
    system_prompt=SYSTEM_PROMPT,
    thinking_budget=1024,
))


def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    """从 ChromaDB 检索与问题相关的文档片段"""
    try:
        collection = get_collection()
        query_embedding = get_embeddings([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        contexts = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else None
                contexts.append({
                    "content": doc,
                    "title": meta.get("title", ""),
                    "documentId": meta.get("documentId"),
                    "chunkIndex": meta.get("chunkIndex"),
                    "distance": distance,
                })
        return contexts
    except Exception as e:
        logger.warning("ChromaDB 检索失败: %s", e)
        return []


def _build_user_content(query: str, contexts: list[dict]) -> str:
    """构建带知识片段上下文的用户消息内容"""
    if not contexts:
        return query

    snippets = []
    for i, ctx in enumerate(contexts, 1):
        title = ctx.get("title", "未知文档")
        snippets.append(f"【片段{i}】来源：{title}\n{ctx['content']}")
    context_text = "\n\n".join(snippets)
    return f"以下是相关知识片段：\n\n{context_text}\n\n用户问题：{query}"


def _build_messages(query: str, contexts: list[dict], history: list[dict]) -> list[dict]:
    """构建 Anthropic Messages API 格式的消息列表（不含 system）"""
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": _build_user_content(query, contexts)})
    return messages


def chat_stream(query: str, history: list[dict] | None = None,
                model: str | None = None) -> Generator[str, None, None]:
    """
    流式问答，yield SSE 格式的事件行。
    事件类型：meta / reasoning_delta / answer_delta / done / error
    """
    request_id = str(uuid.uuid4())
    history = history or []
    model = model or getattr(config, "CHAT_MODEL", "qwen3:8b")

    logger.info("[%s] 开始处理问答: query=%s, model=%s", request_id, query[:80], model)
    yield _sse_event("meta", {"requestId": request_id, "model": model})

    try:
        logger.info("[%s] 检索知识片段...", request_id)
        contexts = retrieve_context(query)
        logger.info("[%s] 检索到 %s 个片段", request_id, len(contexts))
        sources = [
            {"title": c.get("title", ""), "documentId": c.get("documentId")}
            for c in contexts
        ]

        messages = _build_messages(query, contexts, history)
        logger.info("[%s] 构建消息完成, 共 %s 条消息, 调用模型...", request_id, len(messages))

        reasoning_chunks = 0
        answer_chunks = 0
        for event_type, text in ai_client.chat_stream(AGENT_ID, messages, model=model):
            if event_type == "thinking":
                reasoning_chunks += 1
                yield _sse_event("reasoning_delta", {"content": text})
            else:
                answer_chunks += 1
                yield _sse_event("answer_delta", {"content": text})

        logger.info("[%s] 问答完成: reasoning=%s chunks, answer=%s chunks",
                    request_id, reasoning_chunks, answer_chunks)
        yield _sse_event("done", {"sources": sources})

    except Exception as e:
        logger.error("Chat 流式异常: %s", e, exc_info=True)
        yield _sse_event("error", {"message": str(e)})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
