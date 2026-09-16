"""TUI 流式消费与计时逻辑（DashCodeApp 的 mixin）。"""

from __future__ import annotations

import asyncio
import time

from rich.text import Text
from textual.widgets import RichLog, Static

from .view import assistant_block, error_block


class StreamMixin:
    """流式消费、计时、收尾逻辑。

    依赖 DashCodeApp 提供的属性/方法：``provider``、``conv``、``state``、
    ``cur_reply``、``turn_start``、``_stream_task``、``_timer``、
    ``query_one``、``_enter_idle``。
    """

    # 由 DashCodeApp 提供的属性（类型提示）
    cur_reply: str
    turn_start: float

    async def _consume_stream(self) -> None:
        """消费 ``provider.stream`` 的事件，更新界面。"""
        try:
            async for ev in self.provider.stream(self.conv.messages()):
                if ev.err is not None:
                    self._finish_with_error(ev.err)
                    return
                if ev.text:
                    self.cur_reply += ev.text
                    self._refresh_streaming_view()
                if ev.done:
                    self._finish_with_assistant(self.cur_reply)
                    return
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._finish_with_error(e)

    def _tick(self) -> None:
        """计时刷新回调。"""
        if self.state.value != "streaming":
            return
        self._refresh_streaming_view()

    def _elapsed(self) -> float:
        return time.monotonic() - self.turn_start

    def _refresh_streaming_view(self) -> None:
        """更新动态区：流式正文（纯文本）+ Imagining… (Ns)。"""
        streaming = self.query_one("#streaming", Static)
        seconds = int(self._elapsed())
        if self.cur_reply:
            streaming.update(Text(self.cur_reply + f"\n\nImagining… ({seconds}s)"))
        else:
            streaming.update(Text(f"Imagining… ({seconds}s)"))

    def _finish_with_assistant(self, reply: str) -> None:
        """本轮正常结束：markdown 定型追加到 RichLog，记录历史。"""
        self.query_one("#log", RichLog).write(assistant_block(reply))
        self.conv.add_assistant(reply)
        self._reset_turn()

    def _finish_with_error(self, err: Exception) -> None:
        """本轮出错：错误块追加到 RichLog，不退出。"""
        self.query_one("#log", RichLog).write(error_block(err))
        self._reset_turn()

    def _reset_turn(self) -> None:
        """本轮结束：停计时、清缓冲、回 IDLE。"""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._stream_task = None
        self.cur_reply = ""
        self.query_one("#streaming", Static).update("")
        self._enter_idle()
