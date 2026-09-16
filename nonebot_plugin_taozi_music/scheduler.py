import json
from pathlib import Path
from typing import Optional

from nonebot import get_bots, get_plugin_config, logger, require

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .audio import AudioError  # noqa: E402
from .commands import DATA_DIR, _valid_hhmm, play_song  # noqa: E402
from .config import Config  # noqa: E402
from .library import LibraryError, get_library  # noqa: E402

DAILY_JOB_ID = "taozi_music_daily"
SETTINGS_FILE = "settings.json"


def load_send_time(data_dir: Path) -> Optional[str]:
    path = data_dir / SETTINGS_FILE
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["send_time"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    send_time = str(value)
    if not _valid_hhmm(send_time):
        return None
    return send_time


def save_send_time(data_dir: Path, send_time: str) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / SETTINGS_FILE).write_text(
        json.dumps({"send_time": send_time}, ensure_ascii=False), encoding="utf-8"
    )


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
    save_send_time(DATA_DIR, send_time)
    register_daily_job(send_time)


async def daily_push() -> None:
    config = get_plugin_config(Config)
    if not config.taozi_music_groups:
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
        for group in config.taozi_music_groups:
            try:
                await bot.send_group_msg(
                    group_id=group,
                    message=f"今日桃乐放送失败：《{song.title}》{e}",
                )
            except Exception:
                logger.exception(f"每日桃乐推送到群 {group} 失败")
        return

    for group in config.taozi_music_groups:
        try:
            await bot.send_group_msg(
                group_id=group, message=f"🎵 今日桃乐：{song.title}"
            )
            await bot.send_group_msg(group_id=group, message=segment)
        except Exception:
            logger.exception(f"每日桃乐推送到群 {group} 失败")
