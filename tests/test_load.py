import nonebot


def test_plugin_loaded():
    assert nonebot.get_plugin("nonebot_plugin_taozi_music") is not None
