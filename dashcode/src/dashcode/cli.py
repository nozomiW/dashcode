"""DashCode CLI 入口：加载配置、启动 TUI。

配置错误打印可读信息并以非零码退出（不抛崩溃堆栈）。
banner 由 TUI 在 ``on_mount`` 时写入 RichLog，故此处不打印。
"""

import sys

from . import config
from .tui import DashCodeApp

CONFIG_PATH = ".dashcode/config.yaml"


def main() -> None:
    """入口：加载配置并启动 DashCode TUI。"""
    try:
        cfg = config.load(CONFIG_PATH)
    except config.ConfigError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(1)

    app = DashCodeApp(cfg.providers)
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"运行错误: {e}", file=sys.stderr)
        sys.exit(1)
