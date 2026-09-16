from nonebot.adapters.onebot.v11 import MessageSegment
from nonebug import App

import nonebot_plugin_taozi_music.scheduler as scheduler_mod
from nonebot_plugin_taozi_music import settings
from nonebot_plugin_taozi_music.audio import AudioError
from nonebot_plugin_taozi_music.library import Song
from nonebot_plugin_taozi_music.scheduler import (
    DAILY_JOB_ID,
    load_send_time,
    register_daily_job,
    save_send_time,
)

PUSH_WARNING = "警告！！！即将开始发送今日的桃歌"


def test_send_time_roundtrip(tmp_path):
    assert load_send_time(tmp_path) is None
    save_send_time(tmp_path, "21:30")
    assert load_send_time(tmp_path) == "21:30"


def test_load_send_time_corrupted(tmp_path):
    (tmp_path / "settings.json").write_text("not-json", encoding="utf-8")
    assert load_send_time(tmp_path) is None


def test_load_send_time_invalid_values(tmp_path):
    bad_values = (
        '{"send_time": {"a": 1}}',
        '{"send_time": 123}',
        '{"send_time": "25:00"}',
        '{"send_time": "abc"}',
    )
    for bad in bad_values:
        (tmp_path / "settings.json").write_text(bad, encoding="utf-8")
        assert load_send_time(tmp_path) is None


def test_load_send_time_valid(tmp_path):
    (tmp_path / "settings.json").write_text('{"send_time": "8:05"}', encoding="utf-8")
    assert load_send_time(tmp_path) == "8:05"


def test_register_daily_job():
    register_daily_job("21:30")
    job = scheduler_mod.scheduler.get_job(DAILY_JOB_ID)
    assert job is not None
    assert "hour='21'" in str(job.trigger)
    assert "minute='30'" in str(job.trigger)
    register_daily_job("8:05")
    job = scheduler_mod.scheduler.get_job(DAILY_JOB_ID)
    assert "hour='8'" in str(job.trigger)


class _FakeBot:
    def __init__(self):
        self.calls = []

    async def send_group_msg(self, group_id, message):
        self.calls.append((group_id, message))


class _FakeLibrary:
    def __init__(self, song):
        self._song = song

    def pick_random(self):
        return self._song


def _setup_push(monkeypatch, tmp_path, song):
    monkeypatch.setattr(scheduler_mod, "DATA_DIR", tmp_path)
    bot = _FakeBot()
    monkeypatch.setattr(scheduler_mod, "get_bots", lambda: {"10002": bot})

    async def fake_play(song_):
        return MessageSegment.record("file:///fake/1.mp3")

    monkeypatch.setattr(
        scheduler_mod, "get_library", lambda data_dir: _FakeLibrary(song)
    )
    monkeypatch.setattr(scheduler_mod, "play_song", fake_play)
    return bot


async def test_daily_push_no_groups(app: App, monkeypatch, tmp_path):
    # settings 无推送群时直接返回，不报错
    monkeypatch.setattr(scheduler_mod, "DATA_DIR", tmp_path)
    await scheduler_mod.daily_push()


async def test_daily_push_sends_warnings_then_voice(app: App, monkeypatch, tmp_path):
    song = Song(id=1, title="歌A", bv="BV1xx411c7mD")
    bot = _setup_push(monkeypatch, tmp_path, song)
    settings.add_group(tmp_path, 88888, enabled=True)
    settings.add_group(tmp_path, 99999, enabled=False)
    await scheduler_mod.daily_push()
    voice = MessageSegment.record("file:///fake/1.mp3")
    assert bot.calls == [(88888, PUSH_WARNING)] * 5 + [(88888, voice)]


async def test_daily_push_skips_disabled_group(app: App, monkeypatch, tmp_path):
    song = Song(id=1, title="歌A", bv="BV1xx411c7mD")
    bot = _setup_push(monkeypatch, tmp_path, song)
    settings.add_group(tmp_path, 88888, enabled=False)
    await scheduler_mod.daily_push()
    assert bot.calls == []


async def test_daily_push_audio_failure_notifies_enabled_groups(
    app: App, monkeypatch, tmp_path
):
    song = Song(id=1, title="歌A", bv="BV1xx411c7mD")
    monkeypatch.setattr(scheduler_mod, "DATA_DIR", tmp_path)
    bot = _FakeBot()
    monkeypatch.setattr(scheduler_mod, "get_bots", lambda: {"10002": bot})
    monkeypatch.setattr(
        scheduler_mod, "get_library", lambda data_dir: _FakeLibrary(song)
    )

    async def broken_play(song_):
        raise AudioError("boom")

    monkeypatch.setattr(scheduler_mod, "play_song", broken_play)
    settings.add_group(tmp_path, 88888, enabled=True)
    settings.add_group(tmp_path, 99999, enabled=False)
    await scheduler_mod.daily_push()
    assert bot.calls == [(88888, "今日桃乐放送失败：《歌A》boom")]


async def test_daily_push_no_bots(app: App, monkeypatch, tmp_path):
    song = Song(id=1, title="歌A", bv="BV1xx411c7mD")
    monkeypatch.setattr(scheduler_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(scheduler_mod, "get_bots", lambda: {})
    library_calls = []
    monkeypatch.setattr(
        scheduler_mod,
        "get_library",
        lambda data_dir: library_calls.append("called") or _FakeLibrary(song),
    )
    settings.add_group(tmp_path, 88888, enabled=True)
    await scheduler_mod.daily_push()
    assert library_calls == []
