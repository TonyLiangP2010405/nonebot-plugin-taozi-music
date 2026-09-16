from pydantic import BaseModel


class Config(BaseModel):
    """桃乐插件配置"""

    taozi_music_groups: list[int] = []
    """每日定时推送的群号列表，为空则不推送"""

    taozi_music_send_time: str = "21:00"
    """每日播放时间（HH:MM），可被 /桃乐 时间 命令修改并持久化"""
