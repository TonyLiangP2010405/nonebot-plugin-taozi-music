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
        "（以上命令仅 SUPERUSER 可用）"
    ),
    type="application",
    homepage="https://github.com/taozi-fan/nonebot-plugin-taozi-music",
    config=Config,
    supported_adapters={"~onebot.v11"},
)
