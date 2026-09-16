"""配置加载与校验。

从 YAML 文件读取 providers 列表，逐项校验必要字段，缺失或非法时抛出
携带可读信息的 ``ConfigError``，由上层在启动期处理（不抛崩溃堆栈）。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

import yaml

_VALID_PROTOCOLS = {"anthropic", "openai"}


class ConfigError(Exception):
    """配置错误：文件缺失、格式错误或字段校验失败。"""


@dataclass
class ProviderConfig:
    """单个 provider 的配置。"""

    name: str  # 状态栏左侧显示
    protocol: Literal["anthropic", "openai"]
    api_key: str
    model: str  # 状态栏右侧显示
    base_url: str | None = None  # None 则用 SDK 默认端点
    thinking: bool = False  # 仅 anthropic 生效


@dataclass
class Config:
    """整体配置：providers 列表。"""

    providers: list[ProviderConfig] = field(default_factory=list)


def load(path: str) -> Config:
    """从 YAML 文件加载并校验配置。失败抛出 :class:`ConfigError`。"""
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"配置文件不存在: {path}")

    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML 解析失败: {e}") from e

    if not isinstance(raw, dict):
        raise ConfigError("配置文件根节点应为映射")

    providers_raw = raw.get("providers")
    if not isinstance(providers_raw, list) or not providers_raw:
        raise ConfigError("providers 列表为空或缺失")

    providers = [_provider_from_dict(item, i) for i, item in enumerate(providers_raw)]
    return Config(providers=providers)


def _provider_from_dict(item: object, index: int) -> ProviderConfig:
    if not isinstance(item, dict):
        raise ConfigError(f"providers[{index}] 应为映射")

    name = _require_field(item, index, "name")
    protocol = _require_field(item, index, "protocol")
    api_key = _require_field(item, index, "api_key")
    model = _require_field(item, index, "model")

    if protocol not in _VALID_PROTOCOLS:
        raise ConfigError(
            f"providers[{index}].protocol 非法: {protocol}（应为 anthropic 或 openai）"
        )

    base_url_raw = item.get("base_url")
    base_url: str | None = None
    if isinstance(base_url_raw, str) and base_url_raw.strip():
        base_url = base_url_raw.strip()

    thinking = bool(item.get("thinking", False))

    return ProviderConfig(
        name=name,
        protocol=cast(Literal["anthropic", "openai"], protocol),
        api_key=api_key,
        model=model,
        base_url=base_url,
        thinking=thinking,
    )


def _require_field(item: dict, index: int, field_name: str) -> str:
    val = item.get(field_name)
    if not isinstance(val, str) or not val.strip():
        raise ConfigError(f"providers[{index}].{field_name} 不能为空")
    return val.strip()
