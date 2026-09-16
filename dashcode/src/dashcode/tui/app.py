"""DashCode TUI App：状态机、布局、装配。"""

from __future__ import annotations

import asyncio
import os
import time
from enum import Enum

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import OptionList, RichLog, Static
from textual.widgets.option_list import Option

from .. import __version__
from ..conversation import Conversation
from ..llm import Provider, new_provider
from ..prompt import render_banner
from .select import SelectMixin
from .stream import StreamMixin
from .view import InputArea, InputSubmitted, status_bar, user_block

_INPUT_PLACEHOLDER = "❯ Send a message..."


class SessionState(Enum):
    """会话状态。"""

    SELECTING = "selecting"  # 多 provider 时的选择界面
    IDLE = "idle"  # 等待用户输入
    STREAMING = "streaming"  # 等待/接收模型流（loading + 计时）


class DashCodeApp(App, StreamMixin, SelectMixin):
    """DashCode 终端 App。"""

    CSS = """
    Screen {
        layout: vertical;
    }
    #log {
        height: 1fr;
        width: 1fr;
    }
    #streaming {
        height: auto;
        width: 1fr;
        padding: 0 1;
    }
    #input {
        height: 5;
        width: 1fr;
        border: solid $primary;
        margin: 1 0 0 0;
    }
    #statusbar {
        height: 1;
        width: 1fr;
        background: $boost;
        padding: 0 1;
    }
    #selector {
        height: 1fr;
        width: 1fr;
    }
    """

    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=False, priority=True)]

    def __init__(self, providers: list) -> None:
        super().__init__()
        self.providers = providers
        self.provider: Provider | None = None
        self.conv = Conversation()
        self.state = SessionState.IDLE
        self.cur_reply = ""
        self.turn_start = 0.0
        self._stream_task: asyncio.Task | None = None
        self._timer = None

    def compose(self) -> ComposeResult:
        yield RichLog(id="log", wrap=True, markup=True)
        yield Static(id="streaming")
        yield InputArea(id="input", soft_wrap=True, show_line_numbers=False)
        yield Static(id="statusbar")
        yield OptionList(
            *[Option(f"{p.name} ({p.model})", id=str(i)) for i, p in enumerate(self.providers)],
            id="selector",
        )

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(render_banner(__version__, os.getcwd()))
        self.query_one("#input", InputArea).placeholder = _INPUT_PLACEHOLDER
        if len(self.providers) == 1:
            self.provider = new_provider(self.providers[0])
            self.query_one("#selector").display = False
            self._enter_idle()
        else:
            self._enter_selecting()

    def _enter_selecting(self) -> None:
        self.state = SessionState.SELECTING
        self.query_one("#log").display = False
        self.query_one("#input").display = False
        self.query_one("#streaming").display = False
        self.query_one("#selector").display = True
        self.query_one("#selector", OptionList).focus()
        self._update_statusbar()

    def _enter_idle(self) -> None:
        self.state = SessionState.IDLE
        self.query_one("#log").display = True
        self.query_one("#input").display = True
        self.query_one("#streaming").display = True
        self.query_one("#selector").display = False
        self.query_one("#input", InputArea).focus()
        self._update_statusbar()

    def _enter_streaming(self) -> None:
        self.state = SessionState.STREAMING

    @on(InputSubmitted)
    async def on_input_submitted(self, event: InputSubmitted) -> None:
        if self.state != SessionState.IDLE:
            return
        await self.submit(event.text)

    async def submit(self, text: str) -> None:
        """提交一轮对话。"""
        text = text.strip()
        if not text:
            return
        if text == "/exit":
            await self.action_quit()
            return
        self.conv.add_user(text)
        self.query_one("#log", RichLog).write(user_block(text))
        self.query_one("#input", InputArea).text = ""
        self.cur_reply = ""
        self.turn_start = time.monotonic()
        self._enter_streaming()
        self._stream_task = asyncio.create_task(self._consume_stream())
        self._timer = self.set_interval(0.1, self._tick)

    def _update_statusbar(self) -> None:
        name = self.provider.name if self.provider else "DashCode"
        model = self.provider.model if self.provider else ""
        self.query_one("#statusbar", Static).update(status_bar(name, model))

    async def action_quit(self) -> None:
        """安全退出：取消进行中的流，还原终端。"""
        if self._stream_task is not None:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        self.exit()
