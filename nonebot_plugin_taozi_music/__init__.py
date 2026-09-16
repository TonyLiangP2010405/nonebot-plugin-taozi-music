from nonebot import get_driver, get_plugin_config
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="桃乐",
    description="每天定时在群里语音播放小小桃子呦唱过的歌，支持点歌",
    usage=(
        "/桃乐 —— 随机放一首歌\n"
        "/桃乐 歌单 —— 查看歌曲列表\n"
        "/桃乐 点歌 <编号或歌名> —— 播放指定歌曲\n"
        "/桃乐 时间 HH:MM —— 设置每日播放时间\n"
        "/桃乐 加群 [群号] —— 加入每日推送（私聊需带群号）\n"
        "/桃乐 删群 [群号] —— 移出每日推送\n"
        "/桃乐 开启 [群号] —— 开启该群每日推送\n"
        "/桃乐 关闭 [群号] —— 关闭该群每日推送\n"
        "/桃乐 群列表 —— 查看推送群及开关状态\n"
        "（以上命令仅 SUPERUSER 可用）"
    ),
    type="application",
    homepage="https://github.com/TonyLiangP2010405/nonebot-plugin-taozi-music",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

from . import commands, scheduler, settings  # noqa: E402,F401

_driver = get_driver()
_config = get_plugin_config(Config)


@_driver.on_startup
async def _register_jobs() -> None:
    for group_id in _config.taozi_music_groups:
        settings.add_group(commands.DATA_DIR, group_id)
    send_time = (
        scheduler.load_send_time(commands.DATA_DIR) or _config.taozi_music_send_time
    )
    if not commands._valid_hhmm(send_time):
        logger.warning(
            f"配置 taozi_music_send_time 无效: {send_time}，已回退为默认 21:00"
        )
        send_time = "21:00"
    scheduler.register_daily_job(send_time)
