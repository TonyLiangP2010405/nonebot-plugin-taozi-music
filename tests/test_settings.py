import json

from nonebot_plugin_taozi_music.settings import (
    add_group,
    get_groups,
    get_send_time,
    load_settings,
    remove_group,
    save_settings,
    set_group_enabled,
    set_send_time,
)

SETTINGS_FILE = "settings.json"


def _write(tmp_path, data: dict) -> None:
    (tmp_path / SETTINGS_FILE).write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


def test_default_when_file_missing(tmp_path):
    assert load_settings(tmp_path) == {"send_time": None, "groups": {}}


def test_default_when_file_corrupted(tmp_path):
    (tmp_path / SETTINGS_FILE).write_text("not-json", encoding="utf-8")
    assert load_settings(tmp_path) == {"send_time": None, "groups": {}}


def test_default_when_file_not_a_dict(tmp_path):
    _write(tmp_path, ["a", "b"])
    assert load_settings(tmp_path) == {"send_time": None, "groups": {}}


def test_legacy_format_without_groups(tmp_path):
    _write(tmp_path, {"send_time": "21:30"})
    assert load_settings(tmp_path) == {"send_time": "21:30", "groups": {}}


def test_load_settings_drops_bad_group_entries(tmp_path):
    _write(
        tmp_path,
        {
            "send_time": "21:30",
            "groups": {
                "123456": True,
                "abc": True,  # key 非数字
                "789012": "yes",  # value 非 bool
                "999": 1,  # value 非 bool（int）
            },
        },
    )
    assert load_settings(tmp_path) == {
        "send_time": "21:30",
        "groups": {123456: True},
    }


def test_load_settings_normalizes_invalid_send_time(tmp_path):
    _write(tmp_path, {"send_time": "25:00", "groups": {"123456": True}})
    assert load_settings(tmp_path) == {"send_time": None, "groups": {123456: True}}


def test_save_settings_writes_string_keys(tmp_path):
    save_settings(
        tmp_path, {"send_time": "8:05", "groups": {123456: True, 789012: False}}
    )
    raw = json.loads((tmp_path / SETTINGS_FILE).read_text(encoding="utf-8"))
    assert raw == {
        "send_time": "8:05",
        "groups": {"123456": True, "789012": False},
    }
    assert load_settings(tmp_path) == {
        "send_time": "8:05",
        "groups": {123456: True, 789012: False},
    }


def test_send_time_get_set(tmp_path):
    assert get_send_time(tmp_path) is None
    set_send_time(tmp_path, "21:30")
    assert get_send_time(tmp_path) == "21:30"


def test_set_send_time_preserves_groups(tmp_path):
    add_group(tmp_path, 123456, enabled=False)
    set_send_time(tmp_path, "10:00")
    assert get_groups(tmp_path) == {123456: False}
    assert get_send_time(tmp_path) == "10:00"


def test_get_groups_empty(tmp_path):
    assert get_groups(tmp_path) == {}


def test_groups_roundtrip(tmp_path):
    add_group(tmp_path, 123456)
    add_group(tmp_path, 789012, enabled=False)
    assert get_groups(tmp_path) == {123456: True, 789012: False}
    raw = json.loads((tmp_path / SETTINGS_FILE).read_text(encoding="utf-8"))
    assert raw["groups"] == {"123456": True, "789012": False}


def test_add_group_does_not_overwrite(tmp_path):
    add_group(tmp_path, 123456, enabled=False)
    add_group(tmp_path, 123456, enabled=True)
    assert get_groups(tmp_path) == {123456: False}


def test_remove_group(tmp_path):
    add_group(tmp_path, 123456)
    assert remove_group(tmp_path, 123456) is True
    assert get_groups(tmp_path) == {}
    assert remove_group(tmp_path, 123456) is False


def test_set_group_enabled(tmp_path):
    add_group(tmp_path, 123456, enabled=False)
    assert set_group_enabled(tmp_path, 123456, True) is True
    assert get_groups(tmp_path) == {123456: True}
    assert set_group_enabled(tmp_path, 999999, True) is False
    assert get_groups(tmp_path) == {123456: True}
