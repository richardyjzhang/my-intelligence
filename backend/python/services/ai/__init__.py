"""
AI 服务模块 —— 统一管理大模型调用、智能体配置和提示词。

公共接口:
    ai_client       统一的 AI 客户端实例
    get_agent        获取智能体配置
    list_agents      列出所有已注册的智能体
    register_agent   注册自定义智能体
    AgentProfile     智能体配置数据类
    AIResponse       AI 响应包装类
"""

from .client import ai_client, AIClient, AIResponse
from .registry import get_agent, list_agents, register_agent, AgentProfile

__all__ = [
    "ai_client",
    "AIClient",
    "AIResponse",
    "get_agent",
    "list_agents",
    "register_agent",
    "AgentProfile",
]
