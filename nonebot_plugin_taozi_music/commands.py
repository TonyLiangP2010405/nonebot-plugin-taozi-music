from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot_plugin_localstore import get_plugin_data_dir

from .audio import AudioError, ensure_audio
from .library import LibraryError, Song, get_library

music = on_command("桃乐", permission=SUPERUSER, priority=10, block=True)

DATA_DIR = get_plugin_data_dir()
CACHE_DIR = DATA_DIR / "cache"


async def play_song(song: Song) -> MessageSegment:
    """准备音频并返回语音消息段，失败抛 AudioError"""
    path = await ensure_audio(song, CACHE_DIR)
    return MessageSegment.record(path.as_uri())


def _valid_hhmm(value: str) -> bool:
    parts = value.split(":")
    if len(parts) != 2:
        return False
    if not (parts[0].isdigit() and parts[1].isdigit()):
        return False
    return 0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59


@music.handle()
async def handle_music(args: Message = CommandArg()):
    text = args.extract_plain_text().strip()

    try:
        library = get_library(DATA_DIR)
    except LibraryError as e:
        await music.finish(f"歌单不可用：{e}")
        return

    if not text:
        song = library.pick_random()
        if song is None:
            await music.finish("歌单为空")
            return
        await _send_song(song)
        return

    cmd, _, rest = text.partition(" ")
    rest = rest.strip()

    if cmd == "歌单":
        lines = [f"{s.id}. {s.title}" for s in library.songs]
        await music.finish(
            "🎵 桃乐歌单（共 {} 首）：\n{}".format(len(lines), "\n".join(lines))
        )
        return

    if cmd == "点歌":
        if not rest:
            await music.finish("用法：/桃乐 点歌 <编号或歌名>")
            return
        songs = library.find(rest)
        if not songs:
            await music.finish(f"没有找到《{rest}》，发送 /桃乐 歌单 查看列表")
            return
        song = songs[0]
        library.mark_played(song.id)
        await _send_song(song)
        return

    if cmd == "时间":
        if not rest:
            await music.finish("用法：/桃乐 时间 HH:MM，例如 /桃乐 时间 21:30")
            return
        if not _valid_hhmm(rest):
            await music.finish(f"时间格式不对：{rest}，应为 HH:MM（如 21:30）")
            return
        from .scheduler import update_send_time

        update_send_time(rest)
        await music.finish(f"每日播放时间已设置为 {rest}")
        return

    await music.finish(
        "未知指令，可用：/桃乐、/桃乐 歌单、/桃乐 点歌 <编号或歌名>、/桃乐 时间 HH:MM"
    )


async def _send_song(song: Song) -> None:
    await music.send(f"🎵 正在播放：{song.title}")
    try:
        segment = await play_song(song)
    except AudioError as e:
        logger.warning(f"歌曲 {song.id} 准备失败: {e}")
        await music.finish(f"《{song.title}》下载失败了：{e}")
        return
    try:
        await music.send(segment)
    except Exception:
        logger.exception("语音发送失败")
        await music.finish(
            "语音发送失败，请检查协议端（NapCat/Lagrange）是否支持语音消息"
        )
