"""
智能体注册表 —— 管理各智能体的系统提示词与默认参数。

各业务模块在自己的 agent.py 中调用 register_agent() 注册智能体。

使用方式:
    # 注册（在各 agent 模块中）
    from services.ai.agents import register_agent, AgentProfile
    register_agent("chat", AgentProfile(
        name="对话智能体",
        system_prompt="...",
    ))

    # 调用
    from services.ai import ai_client
    response = ai_client.chat("chat", messages=[...])
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AgentProfile:
    """单个智能体的完整配置。"""

    name: str
    system_prompt: str
    description: str = ""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model: Optional[str] = None
    thinking_disabled: Optional[bool] = None
    thinking_budget: Optional[int] = None
    extra: dict = field(default_factory=dict)


_AGENTS: dict[str, AgentProfile] = {}


def register_agent(agent_id: str, profile: AgentProfile) -> None:
    _AGENTS[agent_id] = profile


def get_agent(agent_id: str) -> AgentProfile:
    if agent_id not in _AGENTS:
        raise KeyError(f"未注册的智能体: {agent_id}")
    return _AGENTS[agent_id]


def list_agents() -> dict[str, AgentProfile]:
    return dict(_AGENTS)
