"""
意图分类器 —— 单次 LLM 调用，输出 casual / doc_search / knowledge_qa。
"""

from __future__ import annotations

import json
import logging
import re

from services.ai import ai_client, register_agent, AgentProfile

logger = logging.getLogger(__name__)

AGENT_ID = "classifier"

CLASSIFIER_PROMPT = """你是一个意图分类器。根据用户输入，只输出一行 JSON，不要其他文字。

分类规则：
- casual: 闲聊、打招呼、闲扯、与知识库无关的对话（如「哈喽」「讲个笑话」「今天心情不好」）
- doc_search: 用户想查找、定位某篇文档或文件（如「帮我找XX文件」「有没有关于预算的文档」）
- knowledge_qa: 用户在问具体知识、需要从知识库中检索信息来回答（如「XX的流程是什么」「第三条怎么写」）

只输出形如：{"intent":"casual"} 或 {"intent":"doc_search"} 或 {"intent":"knowledge_qa"}
"""

register_agent(AGENT_ID, AgentProfile(
    name="意图分类器",
    description="对话意图分类",
    system_prompt=CLASSIFIER_PROMPT,
    thinking_disabled=True,
    thinking_budget=0,
    max_tokens=80,
    temperature=0.0,
))

VALID_INTENTS = frozenset({"casual", "doc_search", "knowledge_qa"})


def _parse_intent_json(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None
    # 尝试直接解析
    try:
        obj = json.loads(text)
        v = obj.get("intent")
        if isinstance(v, str) and v in VALID_INTENTS:
            return v
    except json.JSONDecodeError:
        pass
    # 从文本中提取第一个 JSON 对象
    m = re.search(r"\{[^{}]*\"intent\"[^{}]*\}", text)
    if m:
        try:
            obj = json.loads(m.group())
            v = obj.get("intent")
            if isinstance(v, str) and v in VALID_INTENTS:
                return v
        except json.JSONDecodeError:
            pass
    return None


def classify_intent(query: str, model: str | None = None) -> str:
    """返回 casual | doc_search | knowledge_qa。失败时默认 knowledge_qa。"""
    q = (query or "").strip()
    if not q:
        return "casual"

    try:
        resp = ai_client.chat(
            AGENT_ID,
            [{"role": "user", "content": q}],
            model=model,
            max_tokens=80,
            temperature=0.0,
        )
        intent = _parse_intent_json(resp.content)
        if intent:
            logger.info("意图分类: query=%s -> %s", q[:80], intent)
            return intent
    except Exception as e:
        logger.warning("意图分类失败，使用 knowledge_qa: %s", e)

    return "knowledge_qa"
