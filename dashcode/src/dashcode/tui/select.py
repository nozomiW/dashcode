"""TUI provider 选择逻辑（DashCodeApp 的 mixin）。"""

from __future__ import annotations

from textual.widgets import OptionList

from ..llm import new_provider


class SelectMixin:
    """多 provider 选择。

    依赖 DashCodeApp 提供的属性/方法：``providers``、``provider``、
    ``query_one``、``_enter_idle``、``_update_statusbar``。
    """

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """用户选定一个 provider：构造适配器，进入对话。"""
        if event.option.id is None:
            return
        idx = int(event.option.id)
        cfg = self.providers[idx]
        self.provider = new_provider(cfg)
        self.query_one("#selector", OptionList).display = False
        self._enter_idle()
