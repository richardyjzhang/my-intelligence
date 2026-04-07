"""
知识问答智能体 —— 基于 ChromaDB 的 RAG 问答。

职责：
  1. 注册智能体配置
  2. 编排检索 → 构建消息 → 流式生成
  3. 输出 SSE：reasoning_delta / answer_delta / done / error（meta 由 router 统一发送）
"""

import logging
import re
import uuid
from typing import Generator

import config
from services.agents import sse_event
from services.ai import ai_client, register_agent, AgentProfile
from services.personalization_prompt import compose_system_with_persona
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
4. 回答要简洁、准确、有条理。
5. 在回答末尾，请用以下格式标注你实际引用了哪些参考文档（编号对应「【参考N】」中的 N，多个用英文逗号分隔）：
   [CITED: 1,3]
   如果没有引用任何参考文档，请输出 [CITED: NONE]。
   该标记必须单独占一行，放在全部正文与 Markdown 之后，不要写在段落中间。"""

# 匹配整段回答末尾的引用标记（$ 为字符串结尾，勿用 MULTILINE）
_CITED_TAIL_RE = re.compile(r"\[CITED:\s*([^\]]+)\]\s*$", re.IGNORECASE)


def _doc_id_key(item: dict) -> int | None:
    raw = item.get("documentId")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _dedupe_sources_by_document_id(items: list[dict]) -> list[dict]:
    """同一 documentId 只保留首次出现，避免 LLM 输出 [CITED: 1,3] 而 1 与 3 实为同一文档时出现重复标签。"""
    seen: set[int] = set()
    out: list[dict] = []
    for it in items:
        k = _doc_id_key(it)
        if k is None:
            out.append(dict(it))
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(dict(it))
    return out


def _split_cited_sources(
    full_answer: str,
    sources: list[dict],
) -> tuple[list[dict], list[dict], str]:
    """
    根据全文末尾的 [CITED: ...] 将 sources 分为已引用与可能相关，并返回需从前端正文末尾裁掉的字符串。
    若未找到合法标记，则视为全部已引用（兼容旧模型行为）。
    """
    if not sources:
        return [], [], ""

    text = full_answer.rstrip()
    m = _CITED_TAIL_RE.search(text)
    if m is None:
        return _dedupe_sources_by_document_id([dict(s) for s in sources]), [], ""

    tail_after = text[m.end() :].strip()
    if tail_after:
        return _dedupe_sources_by_document_id([dict(s) for s in sources]), [], ""

    inner = (m.group(1) or "").strip()
    trim_suffix = text[m.start() :]

    cited_nums: list[int] = []
    if inner.upper() != "NONE" and inner:
        for part in inner.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                cited_nums.append(int(part))
            except ValueError:
                pass

    n = len(sources)
    cited_set = {i for i in cited_nums if 1 <= i <= n}

    cited_sources = [dict(sources[i - 1]) for i in sorted(cited_set)]
    related_sources = [dict(sources[i]) for i in range(n) if (i + 1) not in cited_set]

    cited_sources = _dedupe_sources_by_document_id(cited_sources)
    cited_ids = {k for k in (_doc_id_key(s) for s in cited_sources) if k is not None}
    related_sources = _dedupe_sources_by_document_id(
        [s for s in related_sources if _doc_id_key(s) not in cited_ids],
    )

    return cited_sources, related_sources, trim_suffix

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
    document_id: int | None = None,
    *,
    ai_persona_title: str | None = None,
    ai_custom_instruction: str | None = None,
) -> Generator[str, None, None]:
    """
    流式问答，yield SSE 格式的事件行（不含 meta）。
    """
    request_id = str(uuid.uuid4())
    history = history or []
    model = model or getattr(config, "CHAT_MODEL", "qwen3:8b")

    logger.info(
        "[%s] 知识问答: query=%s, model=%s, document_id=%s",
        request_id,
        query[:80],
        model,
        document_id,
    )

    try:
        logger.info("[%s] 检索并扩展上下文...", request_id)
        contexts = retrieve_context_expanded(query, document_id=document_id)
        if document_id is not None:
            contexts = [
                c for c in contexts
                if _doc_id_key(c) == document_id
            ]
        if contexts:
            total_chars = sum(len(c.get("content", "")) for c in contexts)
            logger.info("[%s] 命中 %s 篇文档, 上下文总长 %s 字符", request_id, len(contexts), total_chars)
        else:
            logger.info("[%s] 未检索到相关片段，将直接回答", request_id)

        sources = [
            {"title": c.get("title", ""), "documentId": c.get("documentId")}
            for c in contexts
        ]

        single_doc = document_id if document_id is not None else None
        messages = build_messages(query, contexts, history, single_document_id=single_doc)
        logger.info("[%s] 构建消息完成, 共 %s 条消息, 调用模型...", request_id, len(messages))

        system_override = compose_system_with_persona(
            SYSTEM_PROMPT,
            ai_persona_title=ai_persona_title,
            ai_custom_instruction=ai_custom_instruction,
        )
        reasoning_chunks = 0
        answer_chunks = 0
        full_answer_parts: list[str] = []
        for event_type, text in ai_client.chat_stream(
            AGENT_ID,
            messages,
            model=model,
            system_prompt_override=system_override,
        ):
            if event_type == "thinking":
                reasoning_chunks += 1
                yield sse_event("reasoning_delta", {"content": text})
            else:
                answer_chunks += 1
                full_answer_parts.append(text)
                yield sse_event("answer_delta", {"content": text})

        full_answer = "".join(full_answer_parts)
        cited_sources, related_sources, trim_suffix = _split_cited_sources(full_answer, sources)

        if document_id is not None:
            cited_sources = [
                s for s in cited_sources
                if _doc_id_key(s) == document_id
            ]
            related_sources = []

        done_payload: dict = {
            "citedSources": cited_sources,
            "relatedSources": related_sources,
        }
        if trim_suffix:
            done_payload["trimSuffix"] = trim_suffix

        logger.info("[%s] 问答完成: reasoning=%s chunks, answer=%s chunks, cited=%s related=%s",
                    request_id, reasoning_chunks, answer_chunks,
                    len(cited_sources), len(related_sources))
        yield sse_event("done", done_payload)

    except Exception as e:
        logger.error("知识问答流式异常: %s", e, exc_info=True)
        yield sse_event("error", {"message": str(e)})
