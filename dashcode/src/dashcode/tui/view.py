"""TUI 渲染辅助与自定义输入 widget。

- ``user_block`` / ``assistant_block`` / ``error_block``：写入 RichLog 的完成块
- ``status_bar``：底部状态栏 renderable
- ``InputArea``：TextArea 子类，Enter 提交、Alt+Enter 换行
- ``InputSubmitted``：提交消息
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import TextArea


def user_block(text: str) -> RenderableType:
    """用户输入块（无 You 标签）。"""
    return Text("● " + text, style="bold")


def assistant_block(reply: str) -> RenderableType:
    """助手回复块：整段 markdown 渲染（无 DashCode 标签）。"""
    return Group(Text("●", style="cyan"), Markdown(reply))


def error_block(err: Exception) -> RenderableType:
    """错误块：红色可区分样式。"""
    msg = str(err).strip() or err.__class__.__name__
    return Text("● " + msg, style="bold red")


def status_bar(name: str, model: str) -> RenderableType:
    """状态栏：左 provider 名、右 模型名，两端对齐。"""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    grid.add_row(Text(name, style="bold cyan"), Text(model, style="dim"))
    return grid


class InputSubmitted(Message):
    """``InputArea`` 按 Enter 提交时发出，携带当前文本。"""

    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class InputArea(TextArea):
    """输入框：Enter 提交，Alt+Enter 插入换行。"""

    def _on_key(self, event: events.Key) -> None:
        # Textual 的 Key 对象没有 .alt/.ctrl/.shift 属性，修饰键在 event.key 前缀里
        # Alt+Enter：插入换行
        if event.key == "alt+enter":
            event.prevent_default()
            event.stop()
            self.insert("\n")
        # Enter：提交
        elif event.key == "enter":
            event.prevent_default()
            event.stop()
            self.post_message(InputSubmitted(self.text))
