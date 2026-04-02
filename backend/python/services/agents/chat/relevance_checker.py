"""
对话历史相关性判断 —— 轻量 LLM 调用，判断当前问题是否依赖前文上下文。

若判断为不依赖，则后续流程可丢弃 history 以节省 token。
"""

from __future__ import annotations

import json
import logging
import re

from services.ai import ai_client, register_agent, AgentProfile

logger = logging.getLogger(__name__)

AGENT_ID = "relevance_checker"

HISTORY_HINT_MESSAGE = (
    "当前问题与之前的对话关联度较低，已自动忽略历史上下文。"
    "建议点击清空对话，开始新话题，给你们老板省点钱。"
)

MIN_HISTORY_MESSAGES = 4
"""至少 4 条消息（约 2 轮）才触发检查，避免短对话浪费调用。"""

LAST_MESSAGES_MAX = 8
"""最多取最近 8 条（约 4 轮），控制判断模型的输入长度。"""

SNIPPET_MAX_LEN = 100
"""每条消息截取的最大字符数。"""

RELEVANCE_PROMPT = """你是一个对话上下文相关性判断器。根据「近期对话摘要」和「当前用户问题」，判断当前问题是否**必须结合之前的对话才能正确理解或回答**。

只输出一行 JSON，不要其他文字。

判断规则：
- relevant 为 true：当前问题依赖前文。例如：代词/省略（「它」「上面那个」「第三点呢」）、追问（「继续说」「再详细」「为什么」）、明确延续同一话题的短句。
- relevant 为 false：当前问题可独立理解，不依赖前文。例如：全新话题、完整独立的问题（如「Python 列表怎么排序」「今天天气」）、与上文明显无关的新问题。

只输出形如：{"relevant":true} 或 {"relevant":false}
"""

register_agent(AGENT_ID, AgentProfile(
    name="对话相关性判断",
    description="判断当前问题是否依赖历史对话",
    system_prompt=RELEVANCE_PROMPT,
    thinking_disabled=True,
    max_tokens=50,
    temperature=0.0,
))


def _truncate(text: str, max_len: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _summarize_history_for_check(history: list[dict]) -> str:
    """取最近若干条消息，每条截断，拼成摘要文本。"""
    if not history:
        return ""
    tail = history[-LAST_MESSAGES_MAX:]
    lines: list[str] = []
    for msg in tail:
        role = msg.get("role", "")
        content = _truncate(str(msg.get("content", "")), SNIPPET_MAX_LEN)
        if not content:
            continue
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}：{content}")
    return "\n".join(lines)


def _parse_relevant_json(text: str) -> bool | None:
    """解析 {"relevant": true/false}，失败返回 None。"""
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        v = obj.get("relevant")
        if isinstance(v, bool):
            return v
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[^{}]*\"relevant\"[^{}]*\}", text)
    if m:
        try:
            obj = json.loads(m.group())
            v = obj.get("relevant")
            if isinstance(v, bool):
                return v
        except json.JSONDecodeError:
            pass
    return None


def check_relevance(query: str, history: list[dict] | None, model: str | None = None) -> bool:
    """
    判断当前问题是否依赖历史对话（需要保留 history）。

    返回 True：应保留 history（与上文相关或需要上下文）。
    返回 False：可丢弃 history（独立问题）。

    当 history 条数不足 MIN_HISTORY_MESSAGES 时，直接返回 True（不检查）。
    当 LLM 调用或解析失败时，返回 True（保守保留 history）。
    """
    history = history or []
    if len(history) < MIN_HISTORY_MESSAGES:
        return True

    q = (query or "").strip()
    if not q:
        return True

    summary = _summarize_history_for_check(history)
    if not summary:
        return True

    user_payload = (
        f"【近期对话摘要】\n{summary}\n\n"
        f"【当前用户问题】\n{q}"
    )

    try:
        resp = ai_client.chat(
            AGENT_ID,
            [{"role": "user", "content": user_payload}],
            model=model,
            max_tokens=50,
            temperature=0.0,
        )
        logger.info(
            "相关性判断原始回复: query=%s -> content=%r",
            q[:80],
            resp.content[:200],
        )
        parsed = _parse_relevant_json(resp.content)
        if parsed is not None:
            logger.info("相关性判断结果: relevant=%s (True=保留历史)", parsed)
            return parsed
        logger.warning(
            "相关性判断解析失败，保留 history: content=%r",
            resp.content[:200],
        )
    except Exception as e:
        logger.warning("相关性判断异常，保留 history: %s", e)

    return True
