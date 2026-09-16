from pathlib import Path
from typing import Optional

from nonebot import get_bots, logger, require

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .audio import AudioError  # noqa: E402
from .commands import DATA_DIR, play_song  # noqa: E402
from .library import LibraryError, get_library  # noqa: E402
from .settings import get_groups, get_send_time, set_send_time  # noqa: E402

DAILY_JOB_ID = "taozi_music_daily"
PUSH_WARNING = "警告！！！即将开始发送今日的桃歌"
WARNING_COUNT = 5


def load_send_time(data_dir: Path) -> Optional[str]:
    return get_send_time(data_dir)


def save_send_time(data_dir: Path, send_time: str) -> None:
    set_send_time(data_dir, send_time)


def register_daily_job(send_time: str) -> None:
    hour, minute = send_time.split(":")
    scheduler.add_job(
        daily_push,
        "cron",
        hour=int(hour),
        minute=int(minute),
        id=DAILY_JOB_ID,
        replace_existing=True,
    )


def update_send_time(send_time: str) -> None:
    set_send_time(DATA_DIR, send_time)
    register_daily_job(send_time)


async def daily_push() -> None:
    enabled_groups = [
        group_id for group_id, enabled in get_groups(DATA_DIR).items() if enabled
    ]
    if not enabled_groups:
        return
    bots = get_bots()
    if not bots:
        logger.warning("每日桃乐推送：没有可用的 Bot")
        return
    bot = next(iter(bots.values()))

    try:
        library = get_library(DATA_DIR)
    except LibraryError as e:
        logger.warning(f"每日桃乐推送失败：{e}")
        return
    song = library.pick_random()
    if song is None:
        logger.warning("每日桃乐推送失败：歌单为空")
        return

    try:
        segment = await play_song(song)
    except AudioError as e:
        logger.warning(f"每日桃乐推送音频准备失败：{e}")
        for group in enabled_groups:
            try:
                await bot.send_group_msg(
                    group_id=group,
                    message=f"今日桃乐放送失败：《{song.title}》{e}",
                )
            except Exception:
                logger.exception(f"每日桃乐推送到群 {group} 失败")
        return

    for group in enabled_groups:
        try:
            for _ in range(WARNING_COUNT):
                await bot.send_group_msg(group_id=group, message=PUSH_WARNING)
            await bot.send_group_msg(group_id=group, message=segment)
        except Exception:
            logger.exception(f"每日桃乐推送到群 {group} 失败")
