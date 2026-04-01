"""
统一的 AI 客户端 —— 封装 Anthropic 风格 API 调用。

所有与大模型交互的代码都应通过此模块进行，不应直接使用 anthropic SDK。
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

import anthropic

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


class AIClient:
    """
    Anthropic 风格 API 的统一客户端。

    从 config 模块读取配置，模块加载时自动初始化。
    """

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._default_model: str = getattr(config, "AI_MODEL", "") or getattr(config, "CHAT_MODEL", "")
        self._default_max_tokens: int = int(getattr(config, "AI_MAX_TOKENS", 4096))
        self._default_temperature: float = float(getattr(config, "AI_TEMPERATURE", 0.3))
        self._initialized: bool = False

        api_key = getattr(config, "AI_API_KEY", "ollama")
        base_url = getattr(config, "AI_API_BASE_URL", "") or getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")
        # Anthropic SDK 需要不带 /v1 后缀的 base_url
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]

        if not api_key:
            logger.warning("AI_API_KEY 未配置，AI 功能将不可用。")
            return

        self._client = anthropic.Anthropic(
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

    def _adjust_max_tokens_for_thinking(
        self, agent: AgentProfile, max_tokens: int
    ) -> int:
        """extended thinking 时 budget_tokens 必须小于 max_tokens；不足则自动抬高。"""
        if (
            agent.thinking_budget
            and not agent.thinking_disabled
            and max_tokens <= agent.thinking_budget
        ):
            adjusted = agent.thinking_budget + 4096
            logger.warning(
                "max_tokens %s <= thinking_budget %s，已自动调整为 %s",
                max_tokens,
                agent.thinking_budget,
                adjusted,
            )
            return adjusted
        return max_tokens

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
        r_max_tokens = self._adjust_max_tokens_for_thinking(agent, r_max_tokens)
        system = system_prompt_override or agent.system_prompt

        create_kw: dict = {
            "model": r_model,
            "max_tokens": r_max_tokens,
            "temperature": r_temp,
            "system": system,
            "messages": messages,
        }
        if tools:
            create_kw["tools"] = tools
        if agent.thinking_disabled:
            create_kw["thinking"] = {"type": "disabled"}
        elif agent.thinking_budget:
            create_kw["thinking"] = {
                "type": "enabled",
                "budget_tokens": agent.thinking_budget,
            }

        use_thinking_stream = bool(agent.thinking_budget and not agent.thinking_disabled)

        if use_thinking_stream:
            try:
                stream_ctx = self._client.messages.stream(**create_kw)
            except TypeError:
                create_kw.pop("thinking", None)
                stream_ctx = self._client.messages.stream(**create_kw)
            with stream_ctx as stream:
                for event in stream:
                    if getattr(event, "type", None) == "thinking" and on_thinking_delta:
                        piece = getattr(event, "thinking", "") or ""
                        if piece:
                            on_thinking_delta(piece)
                final = stream.get_final_message()
            content = ""
            thinking = ""
            for block in final.content:
                block_type = getattr(block, "type", "")
                if block_type == "text":
                    content += getattr(block, "text", "") or ""
                elif block_type == "thinking":
                    thinking += getattr(block, "thinking", "") or ""
            return AIResponse(
                content=content,
                model=final.model,
                usage={
                    "input_tokens": final.usage.input_tokens,
                    "output_tokens": final.usage.output_tokens,
                },
                stop_reason=final.stop_reason,
                thinking=thinking or None,
                raw=final,
            )

        try:
            response = self._client.messages.create(**create_kw)
        except TypeError:
            create_kw.pop("thinking", None)
            response = self._client.messages.create(**create_kw)

        content = ""
        thinking = ""
        for block in response.content:
            block_type = getattr(block, "type", "")
            if block_type == "text":
                content += block.text or ""
            elif block_type == "thinking":
                thinking += getattr(block, "thinking", "") or ""

        return AIResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            stop_reason=response.stop_reason,
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
        """带工具调用的多轮对话：自动循环处理 tool_use 直到 AI 给出最终回答。"""
        if not self.is_available:
            raise RuntimeError("AI 客户端未初始化，请检查配置")

        agent = get_agent(agent_id)
        r_model, r_max_tokens, r_temp = self._resolve_params(
            agent, model, max_tokens, temperature
        )
        r_max_tokens = self._adjust_max_tokens_for_thinking(agent, r_max_tokens)
        system = system_prompt_override or agent.system_prompt
        msgs = list(messages)
        tool_required_fields = {
            tool.get("name"): list(
                ((tool.get("input_schema") or {}).get("required") or [])
            )
            for tool in tools
        }

        total_usage = {"input_tokens": 0, "output_tokens": 0}
        final_model = ""
        all_thinking = ""

        use_thinking_stream = bool(agent.thinking_budget and not agent.thinking_disabled)

        for _ in range(max_rounds):
            create_kw: dict = {
                "model": r_model,
                "max_tokens": r_max_tokens,
                "temperature": r_temp,
                "system": system,
                "messages": msgs,
                "tools": tools,
            }
            if agent.thinking_disabled:
                create_kw["thinking"] = {"type": "disabled"}
            elif agent.thinking_budget:
                create_kw["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": agent.thinking_budget,
                }

            if use_thinking_stream:
                try:
                    stream_ctx = self._client.messages.stream(**create_kw)
                except TypeError:
                    create_kw.pop("thinking", None)
                    stream_ctx = self._client.messages.stream(**create_kw)
                with stream_ctx as stream:
                    for event in stream:
                        if getattr(event, "type", None) == "thinking" and on_thinking:
                            piece = getattr(event, "thinking", "") or ""
                            if piece:
                                all_thinking += piece
                                on_thinking(piece)
                    response = stream.get_final_message()
            else:
                try:
                    response = self._client.messages.create(**create_kw)
                except TypeError:
                    create_kw.pop("thinking", None)
                    response = self._client.messages.create(**create_kw)

                for block in response.content:
                    if getattr(block, "type", "") == "thinking":
                        text = getattr(block, "thinking", "") or ""
                        if text:
                            all_thinking += text + "\n"
                            if on_thinking:
                                on_thinking(text)

            final_model = response.model
            total_usage["input_tokens"] += response.usage.input_tokens
            total_usage["output_tokens"] += response.usage.output_tokens

            if response.stop_reason != "tool_use":
                content = ""
                for block in response.content:
                    if getattr(block, "type", "") == "text":
                        content += block.text or ""
                return AIResponse(
                    content=content,
                    model=final_model,
                    usage=total_usage,
                    stop_reason=response.stop_reason,
                    thinking=all_thinking or None,
                    raw=response,
                )

            msgs.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if getattr(block, "type", "") != "tool_use":
                    continue
                tool_name = block.name
                tool_input = block.input
                required_fields = tool_required_fields.get(tool_name) or []

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

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

            msgs.append({"role": "user", "content": tool_results})

        raise RuntimeError(f"工具调用超过 {max_rounds} 轮仍未结束")

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
        r_max_tokens = self._adjust_max_tokens_for_thinking(agent, r_max_tokens)
        system = system_prompt_override or agent.system_prompt

        stream_kw: dict = {
            "model": r_model,
            "max_tokens": r_max_tokens,
            "temperature": r_temp,
            "system": system,
            "messages": messages,
        }
        if agent.thinking_disabled:
            stream_kw["thinking"] = {"type": "disabled"}
        elif agent.thinking_budget:
            stream_kw["thinking"] = {
                "type": "enabled",
                "budget_tokens": agent.thinking_budget,
            }
        try:
            stream_ctx = self._client.messages.stream(**stream_kw)
        except TypeError:
            stream_kw.pop("thinking", None)
            stream_ctx = self._client.messages.stream(**stream_kw)

        with stream_ctx as stream:
            had_native_thinking = False
            # <think> 标签解析状态：detect → thinking → text
            tag_state = "detect"
            detect_buf = ""

            for event in stream:
                event_type = getattr(event, "type", "")
                if event_type != "content_block_delta":
                    continue
                delta = getattr(event, "delta", None)
                if delta is None:
                    continue
                delta_type = getattr(delta, "type", "")

                if delta_type == "thinking_delta":
                    had_native_thinking = True
                    thinking = getattr(delta, "thinking", "")
                    if thinking:
                        yield ("thinking", thinking)
                    continue

                if delta_type != "text_delta":
                    continue
                text = getattr(delta, "text", "")
                if not text:
                    continue

                if had_native_thinking:
                    yield ("text", text)
                    continue

                yield from self._parse_think_tags(tag_state, detect_buf, text)
                tag_state, detect_buf = self._advance_think_state(
                    tag_state, detect_buf, text
                )

            if tag_state == "detect" and detect_buf:
                yield ("text", detect_buf)


ai_client = AIClient()
