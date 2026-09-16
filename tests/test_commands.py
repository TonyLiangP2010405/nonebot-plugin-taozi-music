from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.adapters.onebot.v11.event import Sender
from nonebug import App

import nonebot_plugin_taozi_music.commands as commands
from nonebot_plugin_taozi_music.library import Library, LibraryError, Song


def make_group_event(text: str, user_id: int = 10001) -> GroupMessageEvent:
    return GroupMessageEvent(
        time=1700000000,
        self_id=10002,
        post_type="message",
        message_type="group",
        sub_type="normal",
        message_id=1,
        group_id=88888,
        user_id=user_id,
        message=Message(text),
        raw_message=text,
        original_message=Message(text),
        font=0,
        sender=Sender(user_id=user_id, nickname="测试"),
    )


def _patch_library(monkeypatch, tmp_path, songs=None):
    songs = songs if songs is not None else [
        Song(id=1, title="歌A", bv="BV1xx411c7mD"),
        Song(id=2, title="歌B", bv="BV1xx411c7mE"),
    ]
    library = Library(songs, tmp_path)
    monkeypatch.setattr(commands, "get_library", lambda data_dir: library)
    return library


def test_commands_superuser_only():
    names = [type(c.call).__name__ for c in commands.music.permission.checkers]
    assert "SuperUser" in names


async def test_song_list(app: App, monkeypatch, tmp_path):
    _patch_library(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 歌单")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "🎵 桃乐歌单（共 2 首）：\n1. 歌A\n2. 歌B", result=None, bot=bot
        )
        ctx.should_finished()


async def test_random_play(app: App, monkeypatch, tmp_path):
    _patch_library(
        monkeypatch, tmp_path, songs=[Song(id=1, title="歌A", bv="BV1xx411c7mD")]
    )

    async def fake_play(song):
        return MessageSegment.record("file:///fake/1.mp3")

    monkeypatch.setattr(commands, "play_song", fake_play)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "🎵 正在播放：歌A", result=None, bot=bot)
        ctx.should_call_send(
            event, MessageSegment.record("file:///fake/1.mp3"),
            result=None, bot=bot,
        )
        ctx.should_finished()


async def test_play_by_id(app: App, monkeypatch, tmp_path):
    library = _patch_library(monkeypatch, tmp_path)

    async def fake_play(song):
        return MessageSegment.record("file:///fake/2.mp3")

    monkeypatch.setattr(commands, "play_song", fake_play)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 点歌 2")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "🎵 正在播放：歌B", result=None, bot=bot)
        ctx.should_call_send(
            event, MessageSegment.record("file:///fake/2.mp3"),
            result=None, bot=bot,
        )
        ctx.should_finished()
    assert library.played_ids == {2}


async def test_play_not_found(app: App, monkeypatch, tmp_path):
    _patch_library(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 点歌 不存在的歌")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "没有找到《不存在的歌》，发送 /桃乐 歌单 查看列表",
            result=None, bot=bot,
        )
        ctx.should_finished()


async def test_play_empty_arg(app: App, monkeypatch, tmp_path):
    _patch_library(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 点歌")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "用法：/桃乐 点歌 <编号或歌名>", result=None, bot=bot
        )
        ctx.should_finished()


async def test_library_broken(app: App, monkeypatch):
    def broken(data_dir):
        raise LibraryError("歌单文件不存在")

    monkeypatch.setattr(commands, "get_library", broken)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 歌单")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "歌单不可用：歌单文件不存在", result=None, bot=bot
        )
        ctx.should_finished()


async def test_time_invalid_format(app: App, monkeypatch, tmp_path):
    _patch_library(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 时间 25:00")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "时间格式不对：25:00，应为 HH:MM（如 21:30）",
            result=None, bot=bot,
        )
        ctx.should_finished()
