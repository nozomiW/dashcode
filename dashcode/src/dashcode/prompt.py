"""内置 system prompt 与启动 banner（ASCII 猫）。"""

SYSTEM_PROMPT = """你是 DashCode，一个运行在终端里的 AI 编程助手。
你用中文与用户交流，回答简洁、准确。遇到编程问题时，给出清晰的解释与可运行的代码示例。
当前你只能进行纯文本对话，不具备调用工具或访问文件的能力。"""


# ASCII 猫咪图案
CAT_BANNER = r"""
 /\_/\
( o.o )
 > ^ <
""".strip("\n")


def render_banner(version: str, cwd: str) -> str:
    """拼出启动横幅：猫 + 应用名与版本 + 工作目录 + 就绪提示行。"""
    return (
        f"{CAT_BANNER}\n"
        f" DashCode v{version}\n"
        f" cwd: {cwd}\n"
        f"\n"
        f" 就绪。输入消息开始对话；输入 /exit 或按 Ctrl+C 退出。"
    )
