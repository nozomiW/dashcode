"""单会话多轮对话历史（进程内维护，不持久化）。"""

from dashcode.llm import Message


class Conversation:
    """维护 user/assistant 交替的多轮历史。

    退出后历史不保留；每一轮新请求通过 :meth:`messages` 取回完整上下文。
    """

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add_user(self, text: str) -> None:
        """追加一条用户消息。"""
        self._messages.append(Message(role="user", content=text))

    def add_assistant(self, text: str) -> None:
        """追加一条助手消息。"""
        self._messages.append(Message(role="assistant", content=text))

    def messages(self) -> list[Message]:
        """返回历史副本（调用方可自由修改）。"""
        return list(self._messages)
