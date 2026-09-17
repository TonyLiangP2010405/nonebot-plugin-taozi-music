import base64

from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.event import Sender
from nonebug import App

import nonebot_plugin_taozi_music.commands as commands
from nonebot_plugin_taozi_music import settings
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


def make_private_event(text: str, user_id: int = 10001) -> PrivateMessageEvent:
    return PrivateMessageEvent(
        time=1700000000,
        self_id=10002,
        post_type="message",
        message_type="private",
        sub_type="friend",
        message_id=1,
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


async def test_time_set_ok(app: App, monkeypatch, tmp_path):
    _patch_library(monkeypatch, tmp_path)
    from nonebot_plugin_taozi_music import scheduler as scheduler_mod

    recorded = []
    monkeypatch.setattr(
        scheduler_mod, "update_send_time", lambda t: recorded.append(t)
    )
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 时间 21:30")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "每日播放时间已设置为 21:30", result=None, bot=bot
        )
        ctx.should_finished()
    assert recorded == ["21:30"]


def _use_tmp_data_dir(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(commands, "DATA_DIR", tmp_path)


async def test_add_group_no_arg_uses_current_group(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 加群")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "已添加并开启每日推送：88888", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {88888: True}


async def test_add_group_with_explicit_id(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 加群 12345")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "已添加并开启每日推送：12345", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {12345: True}


async def test_add_group_duplicate_keeps_state(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    settings.add_group(tmp_path, 88888, enabled=False)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 加群")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "该群已在推送列表，状态：关闭", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {88888: False}


async def test_add_group_private(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_private_event("/桃乐 加群 12345")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "已添加并开启每日推送：12345", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {12345: True}


async def test_add_group_private_requires_group_id(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_private_event("/桃乐 加群")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "私聊里请带上群号，例如 /桃乐 加群 123456", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {}


async def test_private_remove_requires_group_id(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_private_event("/桃乐 删群")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "私聊里请带上群号，例如 /桃乐 加群 123456", result=None, bot=bot
        )
        ctx.should_finished()


async def test_remove_group_in_group_chat(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    settings.add_group(tmp_path, 88888)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 删群")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "已从推送列表删除：88888", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {}


async def test_remove_group_not_in_list(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 删群 55555")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "该群不在推送列表", result=None, bot=bot)
        ctx.should_finished()


async def test_enable_group(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    settings.add_group(tmp_path, 88888, enabled=False)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 开启")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "已开启每日推送：88888", result=None, bot=bot)
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {88888: True}


async def test_disable_group(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    settings.add_group(tmp_path, 88888)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 关闭")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "已关闭每日推送：88888", result=None, bot=bot)
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {88888: False}


async def test_enable_unknown_group(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 开启 12345")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "该群不在推送列表，先用 /桃乐 加群", result=None, bot=bot
        )
        ctx.should_finished()


async def test_disable_unknown_group(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 关闭 12345")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "该群不在推送列表，先用 /桃乐 加群", result=None, bot=bot
        )
        ctx.should_finished()


async def test_private_disable_group(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    settings.add_group(tmp_path, 12345, enabled=True)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_private_event("/桃乐 关闭 12345")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event, "已关闭每日推送：12345", result=None, bot=bot
        )
        ctx.should_finished()
    assert settings.get_groups(tmp_path) == {12345: False}


async def test_group_list(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    settings.add_group(tmp_path, 123456)
    settings.add_group(tmp_path, 789012, enabled=False)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 群列表")
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "🎵 推送群列表：\n123456（开启）\n789012（关闭）",
            result=None,
            bot=bot,
        )
        ctx.should_finished()


async def test_group_list_empty(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 群列表")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "还没有配置推送群", result=None, bot=bot)
        ctx.should_finished()


async def test_group_id_not_decimal(app, monkeypatch, tmp_path):
    _use_tmp_data_dir(monkeypatch, tmp_path)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐 加群 abc")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "群号格式不对：abc", result=None, bot=bot)
        ctx.should_finished()


async def test_play_song_returns_base64_record(monkeypatch, tmp_path):
    fake = tmp_path / "1.mp3"
    fake.write_bytes(b"fake-audio")

    async def fake_ensure(song, cache_dir):
        return fake

    monkeypatch.setattr(commands, "ensure_audio", fake_ensure)
    segment = await commands.play_song(Song(id=1, title="歌A", bv="BV1xx411c7mD"))
    expected = "base64://" + base64.b64encode(b"fake-audio").decode()
    assert segment.data["file"] == expected
