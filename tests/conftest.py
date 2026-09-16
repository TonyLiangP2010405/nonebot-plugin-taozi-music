import nonebot
import pytest
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from nonebug import NONEBOT_INIT_KWARGS

_NONEBOT_INIT = {"driver": "~none", "superusers": {"10001"}}


def pytest_configure(config: pytest.Config) -> None:
    # 插件必须在测试模块被导入前加载：测试模块 import 插件包会把它写进
    # sys.modules，导致之后 nonebot.load_plugin 找不到 __plugin__ 而失败
    config.stash[NONEBOT_INIT_KWARGS] = _NONEBOT_INIT
    nonebot.init(**_NONEBOT_INIT)
    nonebot.get_driver().register_adapter(OneBotV11Adapter)
    nonebot.load_plugin("nonebot_plugin_taozi_music")
