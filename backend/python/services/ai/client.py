"""
统一的 AI 客户端 —— 封装 OpenAI 兼容协议 API 调用。

所有与大模型交互的代码都应通过此模块进行，不应直接使用 openai SDK。
支持多智能体切换：根据 agent_id 自动加载对应的系统提示词和参数。

使用方式:
    from services.ai import ai_client

    response = ai_client.chat("chat", messages=[
        {"role": "user", "content": "你好"}
    ])
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from openai import OpenAI

import config
from .registry import AgentProfile, get_agent

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """AI 响应的统一包装。"""
    content: str
    model: str
    usage: dict = field(default_factory=dict)
    stop_reason: Optional[str] = None
    thinking: Optional[str] = None
    raw: Optional[object] = None


class EmptyToolInputError(RuntimeError):
    """模型触发工具调用，但未为必填参数工具提供输入。"""

    def __init__(self, tool_name: str, required_fields: list[str]):
        self.tool_name = tool_name
        self.required_fields = required_fields
        super().__init__(
            f"工具 {tool_name} 缺少必填参数：{', '.join(required_fields)}"
        )


def _convert_tools_anthropic_to_openai(tools: list[dict]) -> list[dict]:
    """将 Anthropic 格式的工具定义转换为 OpenAI 格式。"""
    result = []
    for tool in tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
            },
        }
        if "input_schema" in tool:
            openai_tool["function"]["parameters"] = tool["input_schema"]
        elif "parameters" in tool:
            openai_tool["function"]["parameters"] = tool["parameters"]
        result.append(openai_tool)
    return result


def _is_openai_tool_format(tools: list[dict]) -> bool:
    """检测工具定义是否已经是 OpenAI 格式。"""
    return bool(tools and tools[0].get("type") == "function")


class AIClient:
    """
    OpenAI 兼容协议的统一客户端。

    从 config 模块读取配置，模块加载时自动初始化。
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._default_model: str = getattr(config, "AI_MODEL", "") or getattr(config, "CHAT_MODEL", "")
        self._default_max_tokens: int = int(getattr(config, "AI_MAX_TOKENS", 4096))
        self._default_temperature: float = float(getattr(config, "AI_TEMPERATURE", 0.3))
        self._initialized: bool = False

        api_key = getattr(config, "AI_API_KEY", "ollama")
        base_url = getattr(config, "AI_API_BASE_URL", "") or "http://localhost:11434"
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        if not api_key:
            logger.warning("AI_API_KEY 未配置，AI 功能将不可用。")
            return

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self._initialized = True
        logger.info("AI 客户端初始化完成: base_url=%s, model=%s", base_url, self._default_model)

    @property
    def is_available(self) -> bool:
        return self._initialized and self._client is not None

    # ── 参数解析 ──

    def _resolve_params(
        self,
        agent: AgentProfile,
        model: Optional[str],
        max_tokens: Optional[int],
        temperature: Optional[float],
    ) -> tuple[str, int, float]:
        """按优先级: 调用参数 > 智能体配置 > 全局默认值"""
        resolved_model = model or agent.model or self._default_model
        resolved_max_tokens = max_tokens or agent.max_tokens or self._default_max_tokens
        resolved_temp = (
            temperature if temperature is not None
            else (agent.temperature if agent.temperature is not None else self._default_temperature)
        )
        return resolved_model, resolved_max_tokens, resolved_temp

    def _build_messages_with_system(
        self, system: str, messages: list[dict]
    ) -> list[dict]:
        """将系统提示词插入消息列表头部。"""
        result = []
        if system:
            result.append({"role": "system", "content": system})
        result.extend(messages)
        return result

    # ── <think> 标签解析 ──

    @staticmethod
    def _parse_think_tags(
        state: str, buf: str, text: str
    ) -> list[tuple[str, str]]:
        """
        根据当前状态和新增文本，产出 (event_type, content) 列表。
        兼容 Ollama qwen3 等通过 <think>...</think> 标签输出思考过程的模型。
        """
        results: list[tuple[str, str]] = []
        combined = buf + text if state != "text" else text

        if state == "detect":
            if "<think>" in combined:
                before, after = combined.split("<think>", 1)
                if before.strip():
                    results.append(("text", before))
                if "</think>" in after:
                    r_part, a_part = after.split("</think>", 1)
                    if r_part:
                        results.append(("thinking", r_part))
                    if a_part.strip():
                        results.append(("text", a_part))
                else:
                    if after:
                        results.append(("thinking", after))
            elif len(combined) > 20:
                results.append(("text", combined))
        elif state == "thinking":
            if "</think>" in combined:
                r_part, a_part = combined.split("</think>", 1)
                if r_part:
                    results.append(("thinking", r_part))
                if a_part.strip():
                    results.append(("text", a_part))
            else:
                results.append(("thinking", text))
        else:
            results.append(("text", text))

        return results

    @staticmethod
    def _advance_think_state(state: str, buf: str, text: str) -> tuple[str, str]:
        """更新 <think> 标签解析的状态机，返回 (new_state, new_buf)。"""
        combined = buf + text if state != "text" else text

        if state == "detect":
            if "<think>" in combined:
                after = combined.split("<think>", 1)[1]
                if "</think>" in after:
                    return "text", ""
                return "thinking", ""
            if len(combined) > 20:
                return "text", ""
            return "detect", combined
        elif state == "thinking":
            if "</think>" in combined:
                return "text", ""
            return "thinking", ""
        return "text", ""

    @staticmethod
    def _strip_think_tags(text: str) -> tuple[str, str]:
        """从完整文本中分离 <think>...</think> 标签内容。返回 (content, thinking)。"""
        import re
        thinking_parts = []
        content = text

        for m in re.finditer(r"<think>(.*?)</think>", text, re.DOTALL):
            thinking_parts.append(m.group(1))
        content = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        return content, "\n".join(thinking_parts) if thinking_parts else ""

    # ── 核心调用 ──

    def chat(
        self,
        agent_id: str,
        messages: list[dict],
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt_override: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        on_thinking_delta: Optional[Callable[[str], None]] = None,
    ) -> AIResponse:
        if not self.is_available:
            raise RuntimeError("AI 客户端未初始化，请检查配置")

        agent = get_agent(agent_id)
        r_model, r_max_tokens, r_temp = self._resolve_params(
            agent, model, max_tokens, temperature
        )
        system = system_prompt_override or agent.system_prompt
        full_messages = self._build_messages_with_system(system, messages)

        create_kw: dict = {
            "model": r_model,
            "max_tokens": r_max_tokens,
            "temperature": r_temp,
            "messages": full_messages,
        }
        if tools:
            openai_tools = tools if _is_openai_tool_format(tools) else _convert_tools_anthropic_to_openai(tools)
            create_kw["tools"] = openai_tools

        response = self._client.chat.completions.create(**create_kw)

        choice = response.choices[0]
        raw_content = choice.message.content or ""

        content, thinking = self._strip_think_tags(raw_content)
        if thinking and on_thinking_delta:
            on_thinking_delta(thinking)

        usage_dict = {}
        if response.usage:
            usage_dict = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return AIResponse(
            content=content,
            model=response.model,
            usage=usage_dict,
            stop_reason=choice.finish_reason,
            thinking=thinking or None,
            raw=response,
        )

    def chat_with_tools(
        self,
        agent_id: str,
        messages: list[dict],
        tools: list[dict],
        tool_executor: Callable[[str, dict], Any],
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt_override: Optional[str] = None,
        max_rounds: int = 10,
        on_tool_call: Optional[Callable[[str, dict, Any], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
    ) -> AIResponse:
        """带工具调用的多轮对话：自动循环处理 tool_calls 直到 AI 给出最终回答。"""
        if not self.is_available:
            raise RuntimeError("AI 客户端未初始化，请检查配置")

        agent = get_agent(agent_id)
        r_model, r_max_tokens, r_temp = self._resolve_params(
            agent, model, max_tokens, temperature
        )
        system = system_prompt_override or agent.system_prompt

        openai_tools = tools if _is_openai_tool_format(tools) else _convert_tools_anthropic_to_openai(tools)
        tool_required_fields: dict[str, list[str]] = {}
        for tool in tools:
            name = tool.get("name") or tool.get("function", {}).get("name", "")
            schema = tool.get("input_schema") or tool.get("function", {}).get("parameters", {})
            tool_required_fields[name] = list(schema.get("required", []))

        msgs = self._build_messages_with_system(system, messages)
        total_usage = {"input_tokens": 0, "output_tokens": 0}
        final_model = ""
        all_thinking = ""

        for _ in range(max_rounds):
            create_kw: dict = {
                "model": r_model,
                "max_tokens": r_max_tokens,
                "temperature": r_temp,
                "messages": msgs,
                "tools": openai_tools,
            }

            response = self._client.chat.completions.create(**create_kw)

            choice = response.choices[0]
            final_model = response.model
            if response.usage:
                total_usage["input_tokens"] += response.usage.prompt_tokens
                total_usage["output_tokens"] += response.usage.completion_tokens

            raw_content = choice.message.content or ""
            if raw_content:
                content_text, thinking_text = self._strip_think_tags(raw_content)
                if thinking_text:
                    all_thinking += thinking_text + "\n"
                    if on_thinking:
                        on_thinking(thinking_text)
            else:
                content_text = ""

            if choice.finish_reason != "tool_calls":
                return AIResponse(
                    content=content_text,
                    model=final_model,
                    usage=total_usage,
                    stop_reason=choice.finish_reason,
                    thinking=all_thinking or None,
                    raw=response,
                )

            assistant_msg: dict = {"role": "assistant", "content": raw_content or None}
            if choice.message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.message.tool_calls
                ]
            msgs.append(assistant_msg)

            for tc in (choice.message.tool_calls or []):
                tool_name = tc.function.name
                try:
                    tool_input = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    tool_input = {}

                required_fields = tool_required_fields.get(tool_name, [])
                if (not tool_input) and required_fields:
                    raise EmptyToolInputError(tool_name, required_fields)

                try:
                    result = tool_executor(tool_name, tool_input)
                    result_str = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
                except Exception as e:
                    result_str = json.dumps({"error": str(e)}, ensure_ascii=False)
                    result = {"error": str(e)}

                if on_tool_call:
                    on_tool_call(tool_name, tool_input, result)

                msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

        raise RuntimeError(f"工具调用超过 {max_rounds} 轮仍未结束")

    def chat_stream(
        self,
        agent_id: str,
        messages: list[dict],
        *,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt_override: Optional[str] = None,
    ):
        """
        流式对话（生成器），yield (event_type, text) 元组。

        event_type 为 "thinking" 或 "text"，调用方据此决定如何处理。
        """
        if not self.is_available:
            raise RuntimeError("AI 客户端未初始化，请检查配置")

        agent = get_agent(agent_id)
        r_model, r_max_tokens, r_temp = self._resolve_params(
            agent, model, max_tokens, temperature
        )
        system = system_prompt_override or agent.system_prompt
        full_messages = self._build_messages_with_system(system, messages)

        stream = self._client.chat.completions.create(
            model=r_model,
            max_tokens=r_max_tokens,
            temperature=r_temp,
            messages=full_messages,
            stream=True,
        )

        tag_state = "detect"
        detect_buf = ""

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            text = delta.content or ""
            if not text:
                continue

            yield from self._parse_think_tags(tag_state, detect_buf, text)
            tag_state, detect_buf = self._advance_think_state(
                tag_state, detect_buf, text
            )

        if tag_state == "detect" and detect_buf:
            yield ("text", detect_buf)


ai_client = AIClient()
