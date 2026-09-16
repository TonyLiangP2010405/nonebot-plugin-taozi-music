from nonebug import App

import nonebot_plugin_taozi_music.scheduler as scheduler_mod
from nonebot_plugin_taozi_music.scheduler import (
    DAILY_JOB_ID,
    load_send_time,
    register_daily_job,
    save_send_time,
)


def test_send_time_roundtrip(tmp_path):
    assert load_send_time(tmp_path) is None
    save_send_time(tmp_path, "21:30")
    assert load_send_time(tmp_path) == "21:30"


def test_load_send_time_corrupted(tmp_path):
    (tmp_path / "settings.json").write_text("not-json", encoding="utf-8")
    assert load_send_time(tmp_path) is None


def test_register_daily_job():
    register_daily_job("21:30")
    job = scheduler_mod.scheduler.get_job(DAILY_JOB_ID)
    assert job is not None
    assert "hour='21'" in str(job.trigger)
    assert "minute='30'" in str(job.trigger)
    register_daily_job("8:05")
    job = scheduler_mod.scheduler.get_job(DAILY_JOB_ID)
    assert "hour='8'" in str(job.trigger)


async def test_daily_push_no_groups(app: App):
    # 默认配置 taozi_music_groups 为空，应直接返回不报错
    await scheduler_mod.daily_push()
