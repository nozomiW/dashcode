"""OpenAI 协议适配器。

封装 ``openai.AsyncOpenAI``，把统一消息转为 chat.completions 入参，首条插入
内置 system prompt，按流式 chunk 吐出 :class:`StreamEvent`。
thinking 字段对 OpenAI 协议无效，忽略。
"""

from collections.abc import AsyncIterator

import openai

from dashcode.config import ProviderConfig
from dashcode.llm import Message, StreamEvent
from dashcode.prompt import SYSTEM_PROMPT


class OpenAIProvider:
    """OpenAI 协议适配器。"""

    def __init__(self, cfg: ProviderConfig) -> None:
        self._client = openai.AsyncOpenAI(
            api_key=cfg.api_key,
            base_url=cfg.base_url or None,
        )
        self._name = cfg.name
        self._model = cfg.model

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    async def stream(self, msgs: list[Message]) -> AsyncIterator[StreamEvent]:
        """发起一轮流式对话。

        首条插入 system prompt；逐 chunk 取 delta.content 作为正文增量。
        异常（鉴权/限流/网络/模型不存在等）转为 ``StreamEvent(err=...)``。
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": m.role, "content": m.content} for m in msgs
        ]

        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield StreamEvent(text=delta)
            yield StreamEvent(done=True)
        except Exception as e:
            yield StreamEvent(err=e)
