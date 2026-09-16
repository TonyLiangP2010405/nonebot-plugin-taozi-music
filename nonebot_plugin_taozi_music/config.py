from pydantic import BaseModel


class Config(BaseModel):
    """桃乐插件配置"""

    taozi_music_groups: list[int] = []
    """每日推送群号初始列表，启动时写入 data/settings.json，之后用命令管理"""

    taozi_music_send_time: str = "21:00"
    """每日播放时间（HH:MM），可被 /桃乐 时间 命令修改并持久化"""
