"""LLM 协议层：协议无关的 Provider 抽象与统一消息/事件类型。

定义 :class:`Message` / :class:`StreamEvent` / :class:`Provider` 协议，以及
按配置分派适配器的 :func:`new_provider` 工厂。anthropic 与 openai 两个适配器
各自封装官方 SDK，统一吐出文本增量（思考增量内部丢弃）。
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol

from dashcode.config import ProviderConfig


@dataclass
class Message:
    """一条对话消息。"""

    role: Literal["user", "assistant"]
    content: str


@dataclass
class StreamEvent:
    """流式事件。

    - text: 正文文本增量
    - done: 本轮正常结束
    - err: 出错（与 done 互斥）
    """

    text: str = ""
    done: bool = False
    err: Exception | None = None


class Provider(Protocol):
    """协议无关的对话 provider。"""

    @property
    def name(self) -> str:
        """状态栏左侧显示的名称。"""
        ...

    @property
    def model(self) -> str:
        """状态栏右侧显示的模型名。"""
        ...

    def stream(self, msgs: list[Message]) -> AsyncIterator[StreamEvent]:
        """发起一轮流式对话，吐出 :class:`StreamEvent`。

        内部注入内置 system prompt 与 thinking 配置；思考增量内部丢弃。
        调用方 cancel 对应 task 时，async for 自然抛 CancelledError，
        SDK 流由适配器内部的上下文管理器自动清理。
        """
        ...


def new_provider(cfg: ProviderConfig) -> Provider:
    """按 ``cfg.protocol`` 构造对应的适配器。未知协议抛 :class:`ValueError`。"""
    if cfg.protocol == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(cfg)
    if cfg.protocol == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(cfg)
    raise ValueError(f"未知协议: {cfg.protocol}")
