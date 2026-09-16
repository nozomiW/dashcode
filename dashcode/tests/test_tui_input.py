"""InputArea 按键集成测试。

直接把键盘事件送到 InputArea，覆盖 ``_on_key`` 路径（Enter 提交 / Alt+Enter 换行）。
之前的 headless 联调直接调用 ``app.submit()``，绕过了按键处理，导致
``event.alt`` 这类凭空臆造的属性访问未被捕获。本测试用 ``pilot.press`` 真正走按键路径。
"""

from collections.abc import AsyncIterator

from dashcode.config import ProviderConfig
from dashcode.llm import StreamEvent
from dashcode.tui.app import DashCodeApp
from dashcode.tui.view import InputArea


class _FakeProvider:
    """测试用 provider：吐出固定回复，不触网。"""

    name = "fake"
    model = "fake-model"

    def stream(self, msgs: list) -> AsyncIterator[StreamEvent]:
        return self._gen()

    async def _gen(self) -> AsyncIterator[StreamEvent]:
        yield StreamEvent(text="喵~")
        yield StreamEvent(done=True)


def _cfg() -> ProviderConfig:
    return ProviderConfig(name="fake", protocol="openai", api_key="sk-test", model="m")


async def test_enter_key_submits_and_streams() -> None:
    """按 Enter 走 _on_key 提交路径，触发流并写回 assistant 历史。"""
    app = DashCodeApp([_cfg()])
    async with app.run_test() as pilot:
        app.provider = _FakeProvider()  # 替换真实 provider，避免触网
        inp = app.query_one("#input", InputArea)
        inp.focus()
        await pilot.press("a", "b")
        await pilot.press("enter")
        # 让异步流任务跑完
        for _ in range(20):
            await pilot.pause()

    roles = [m.role for m in app.conv.messages()]
    contents = [m.content for m in app.conv.messages()]
    assert "ab" in contents
    assert roles[-1] == "assistant"
    assert contents[-1] == "喵~"


async def test_alt_enter_inserts_newline_without_submitting() -> None:
    """按 Alt+Enter 走 _on_key 换行路径，不提交。"""
    app = DashCodeApp([_cfg()])
    async with app.run_test() as pilot:
        app.provider = _FakeProvider()
        inp = app.query_one("#input", InputArea)
        inp.focus()
        await pilot.press("a", "b")
        await pilot.press("alt+enter")
        await pilot.pause()
        text_after = inp.text
        msgs = list(app.conv.messages())

    assert "\n" in text_after
    assert msgs == []


async def test_empty_enter_does_not_submit() -> None:
    """空输入按 Enter 不提交（submit 早返回）。"""
    app = DashCodeApp([_cfg()])
    async with app.run_test() as pilot:
        app.provider = _FakeProvider()
        app.query_one("#input", InputArea).focus()
        await pilot.press("enter")
        await pilot.pause()

    assert app.conv.messages() == []
