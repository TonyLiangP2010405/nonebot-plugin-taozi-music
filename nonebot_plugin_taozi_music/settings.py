"""settings.json 统一管理：每日推送时间与推送群开关

文件格式::

    {"send_time": "21:30 或 null", "groups": {"123456": true, "789012": false}}

兼容旧格式：只有 ``send_time`` 没有 ``groups`` 时按空群列表加载。
"""

import json
from pathlib import Path
from typing import Optional

from nonebot.log import logger

from .commands import _valid_hhmm

SETTINGS_FILE = "settings.json"


def _default_settings() -> dict:
    return {"send_time": None, "groups": {}}


def _settings_path(data_dir: Path) -> Path:
    return data_dir / SETTINGS_FILE


def load_settings(data_dir: Path) -> dict:
    """加载 settings.json；文件缺失/损坏返回默认值。

    groups 的 key 强转 int、value 必须是 bool，坏条目丢弃并记录警告。
    """
    path = _settings_path(data_dir)
    if not path.exists():
        return _default_settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        logger.warning(f"设置文件损坏，已重置为默认: {path}")
        return _default_settings()
    if not isinstance(data, dict):
        logger.warning(f"设置文件格式错误，已重置为默认: {path}")
        return _default_settings()

    send_time = data.get("send_time")
    if send_time is not None and not (
        isinstance(send_time, str) and _valid_hhmm(send_time)
    ):
        logger.warning(f"设置文件 send_time 非法，已重置: {send_time!r}")
        send_time = None

    groups: dict[int, bool] = {}
    groups_raw = data.get("groups")
    if groups_raw is None:
        pass
    elif not isinstance(groups_raw, dict):
        logger.warning(f"设置文件 groups 不是对象，已忽略: {groups_raw!r}")
    else:
        for key, value in groups_raw.items():
            try:
                group_id = int(str(key).strip())
            except (ValueError, TypeError):
                logger.warning(f"设置文件 groups 键非法，已忽略: {key!r}")
                continue
            if not isinstance(value, bool):
                logger.warning(
                    f"设置文件 groups[{group_id}] 值非法，已忽略: {value!r}"
                )
                continue
            groups[group_id] = value

    return {"send_time": send_time, "groups": groups}


def save_settings(data_dir: Path, settings: dict) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "send_time": settings.get("send_time"),
        "groups": {
            str(group_id): bool(enabled)
            for group_id, enabled in settings.get("groups", {}).items()
        },
    }
    _settings_path(data_dir).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_send_time(data_dir: Path) -> Optional[str]:
    send_time = load_settings(data_dir)["send_time"]
    if send_time is None:
        return None
    if not _valid_hhmm(send_time):
        return None
    return send_time


def set_send_time(data_dir: Path, send_time: str) -> None:
    settings = load_settings(data_dir)
    settings["send_time"] = send_time
    save_settings(data_dir, settings)


def get_groups(data_dir: Path) -> dict:
    """返回 {int群号: bool是否开启}"""
    return load_settings(data_dir)["groups"]


def add_group(data_dir: Path, group_id: int, enabled: bool = True) -> None:
    """加入推送列表；已存在时不覆盖原状态"""
    settings = load_settings(data_dir)
    groups = settings["groups"]
    if group_id not in groups:
        groups[group_id] = enabled
        save_settings(data_dir, settings)


def remove_group(data_dir: Path, group_id: int) -> bool:
    """移出推送列表；不存在返回 False"""
    settings = load_settings(data_dir)
    groups = settings["groups"]
    if group_id not in groups:
        return False
    del groups[group_id]
    save_settings(data_dir, settings)
    return True


def set_group_enabled(data_dir: Path, group_id: int, enabled: bool) -> bool:
    """开关指定群；群不在列表返回 False"""
    settings = load_settings(data_dir)
    groups = settings["groups"]
    if group_id not in groups:
        return False
    groups[group_id] = enabled
    save_settings(data_dir, settings)
    return True
