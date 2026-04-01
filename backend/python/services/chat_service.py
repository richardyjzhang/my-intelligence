import json
import logging
import uuid
from typing import Generator

from openai import OpenAI

import config
from services.chroma_service import get_collection, get_embeddings

logger = logging.getLogger(__name__)

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


def _get_chat_client() -> OpenAI:
    return OpenAI(
        base_url=config.OLLAMA_BASE_URL,
        api_key="ollama",
    )


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


def _build_messages(query: str, contexts: list[dict], history: list[dict]) -> list[dict]:
    """构建发送给模型的消息列表"""
    context_text = ""
    if contexts:
        snippets = []
        for i, ctx in enumerate(contexts, 1):
            title = ctx.get("title", "未知文档")
            snippets.append(f"【片段{i}】来源：{title}\n{ctx['content']}")
        context_text = "\n\n".join(snippets)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = query
    if context_text:
        user_content = f"以下是相关知识片段：\n\n{context_text}\n\n用户问题：{query}"

    messages.append({"role": "user", "content": user_content})
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
        client = _get_chat_client()

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        logger.info("[%s] 模型流开始返回", request_id)

        # 状态: "detect" -> "reasoning" -> "answering"
        # detect: 前几个 chunk 判断是否有 <think> 标签
        # 如果没有，直接进 answering；如果有，进 reasoning 直到 </think>
        state = "detect"
        detect_buffer = ""
        reasoning_chunks = 0
        answer_chunks = 0

        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            if choice is None:
                continue

            delta = choice.delta

            # 优先检查 reasoning_content 字段（OpenAI / 硅基流动格式）
            reasoning_content = getattr(delta, "reasoning_content", None)
            if reasoning_content:
                if state != "reasoning":
                    state = "reasoning"
                    logger.info("[%s] 开始输出思考过程(reasoning_content)", request_id)
                reasoning_chunks += 1
                yield _sse_event("reasoning_delta", {"content": reasoning_content})
                continue

            content = delta.content
            if not content:
                if choice.finish_reason:
                    if state == "detect" and detect_buffer:
                        answer_chunks += 1
                        yield _sse_event("answer_delta", {"content": detect_buffer})
                        detect_buffer = ""
                    logger.info("[%s] 模型完成: finish_reason=%s", request_id, choice.finish_reason)
                    break
                continue

            if state == "detect":
                detect_buffer += content
                # 已经明确包含 <think>
                if "<think>" in detect_buffer:
                    before_think = detect_buffer.split("<think>", 1)[0]
                    after_think = detect_buffer.split("<think>", 1)[1]
                    if before_think.strip():
                        answer_chunks += 1
                        yield _sse_event("answer_delta", {"content": before_think})
                    state = "reasoning"
                    logger.info("[%s] 开始输出思考过程(<think>标签)", request_id)
                    # after_think 可能已包含 </think>
                    if "</think>" in after_think:
                        r_part, a_part = after_think.split("</think>", 1)
                        if r_part:
                            reasoning_chunks += 1
                            yield _sse_event("reasoning_delta", {"content": r_part})
                        state = "answering"
                        logger.info("[%s] 思考过程结束(%s chunks)", request_id, reasoning_chunks)
                        if a_part.strip():
                            answer_chunks += 1
                            yield _sse_event("answer_delta", {"content": a_part})
                    elif after_think:
                        reasoning_chunks += 1
                        yield _sse_event("reasoning_delta", {"content": after_think})
                # 缓冲超过 20 个字符还没看到 <think>，判定为无思考过程
                elif len(detect_buffer) > 20:
                    state = "answering"
                    answer_chunks += 1
                    yield _sse_event("answer_delta", {"content": detect_buffer})

            elif state == "reasoning":
                detect_buffer += content
                if "</think>" in detect_buffer:
                    r_part, a_part = detect_buffer.split("</think>", 1)
                    if r_part:
                        reasoning_chunks += 1
                        yield _sse_event("reasoning_delta", {"content": r_part})
                    state = "answering"
                    detect_buffer = ""
                    logger.info("[%s] 思考过程结束(%s chunks)", request_id, reasoning_chunks)
                    if a_part.strip():
                        answer_chunks += 1
                        yield _sse_event("answer_delta", {"content": a_part})
                else:
                    reasoning_chunks += 1
                    yield _sse_event("reasoning_delta", {"content": content})
                    detect_buffer = ""

            else:  # answering
                answer_chunks += 1
                yield _sse_event("answer_delta", {"content": content})

            if choice.finish_reason:
                logger.info("[%s] 模型完成: finish_reason=%s", request_id, choice.finish_reason)
                break

        # detect 阶段就结束了（极短回答且没有 <think>）
        if state == "detect" and detect_buffer:
            answer_chunks += 1
            yield _sse_event("answer_delta", {"content": detect_buffer})

        logger.info("[%s] 问答完成: reasoning=%s chunks, answer=%s chunks", request_id, reasoning_chunks, answer_chunks)
        yield _sse_event("done", {"sources": sources})

    except Exception as e:
        logger.error("Chat 流式异常: %s", e, exc_info=True)
        yield _sse_event("error", {"message": str(e)})


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
