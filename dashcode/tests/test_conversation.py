"""conversation 模块单测。"""

from dashcode.conversation import Conversation


def test_empty() -> None:
    conv = Conversation()
    assert conv.messages() == []


def test_order_and_roles() -> None:
    conv = Conversation()
    conv.add_user("你好")
    conv.add_assistant("你好！有什么可以帮你？")
    conv.add_user("再问一句")
    conv.add_assistant("好的")

    msgs = conv.messages()
    assert [m.role for m in msgs] == ["user", "assistant", "user", "assistant"]
    assert [m.content for m in msgs] == [
        "你好",
        "你好！有什么可以帮你？",
        "再问一句",
        "好的",
    ]


def test_messages_returns_copy() -> None:
    conv = Conversation()
    conv.add_user("hi")

    snapshot = conv.messages()
    snapshot.clear()

    # 清空副本不应影响内部历史
    assert len(conv.messages()) == 1
