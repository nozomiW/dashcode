"""Anthropic 协议适配器。

封装 ``anthropic.AsyncAnthropic``，把统一消息转为 SDK 入参，注入内置 system
prompt 与 thinking 配置，按高层流式事件吐出 :class:`StreamEvent`。
思考增量（thinking 事件）内部丢弃，不混入正文。

参考：anthropic-sdk-python 的 ``messages.stream`` 高层事件（text / thinking / ...）。
"""

from collections.abc import AsyncIterator

import anthropic

from dashcode.config import ProviderConfig
from dashcode.llm import Message, StreamEvent
from dashcode.prompt import SYSTEM_PROMPT

_MAX_TOKENS = 4096
_THINKING_BUDGET_TOKENS = 2048  # 须小于 max_tokens


class AnthropicProvider:
    """Anthropic 协议适配器。"""

    def __init__(self, cfg: ProviderConfig) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=cfg.api_key,
            base_url=cfg.base_url or None,
        )
        self._name = cfg.name
        self._model = cfg.model
        self._thinking = cfg.thinking

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    async def stream(self, msgs: list[Message]) -> AsyncIterator[StreamEvent]:
        """发起一轮流式对话。

        注入内置 system prompt；按配置开启扩展思考。
        text 事件 -> 正文增量；thinking 事件及其它事件忽略。
        异常（鉴权/限流/网络/模型不存在等）转为 ``StreamEvent(err=...)``。
        """
        messages = [{"role": m.role, "content": m.content} for m in msgs]
        params: dict[str, object] = {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        }
        if self._thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": _THINKING_BUDGET_TOKENS,
            }

        try:
            async with self._client.messages.stream(**params) as stream:
                async for event in stream:
                    if event.type == "text":
                        yield StreamEvent(text=event.text)
            yield StreamEvent(done=True)
        except Exception as e:
            yield StreamEvent(err=e)
