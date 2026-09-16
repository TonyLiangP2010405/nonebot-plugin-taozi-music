import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {"driver": "~none", "superusers": {"10001"}}


@pytest.fixture(scope="session", autouse=True)
def load_plugin(nonebug_init: None) -> None:
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)
    nonebot.load_plugin("nonebot_plugin_taozi_music")
