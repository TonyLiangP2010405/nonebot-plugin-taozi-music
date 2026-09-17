import json
import random
from pathlib import Path
from typing import Optional

import yaml
from nonebot.log import logger
from pydantic import BaseModel, field_validator

SONGS_FILE = Path(__file__).parent / "resources" / "songs.yaml"


class LibraryError(Exception):
    """歌单加载或校验失败"""


def parse_time(value: str) -> int:
    """把 "ss" / "mm:ss" / "hh:mm:ss" 解析为秒数，非法输入抛 ValueError"""
    parts = value.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"非法时间格式: {value!r}")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        raise ValueError(f"非法时间格式: {value!r}") from None
    if any(n < 0 for n in nums) or any(n >= 60 for n in nums[1:]):
        raise ValueError(f"非法时间格式: {value!r}")
    seconds = 0
    for n in nums:
        seconds = seconds * 60 + n
    return seconds


class Song(BaseModel):
    id: int
    title: str
    bv: str
    part: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None
    note: str = ""

    @field_validator("bv")
    @classmethod
    def _check_bv(cls, v: str) -> str:
        if not v.startswith("BV"):
            raise ValueError(f"非法 BV 号: {v!r}")
        return v

    @field_validator("part")
    @classmethod
    def _check_part(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError(f"分P序号必须 >= 1: {v}")
        return v

    @property
    def start_seconds(self) -> Optional[int]:
        return parse_time(self.start) if self.start is not None else None

    @property
    def end_seconds(self) -> Optional[int]:
        return parse_time(self.end) if self.end is not None else None

    @property
    def is_clip(self) -> bool:
        """True 表示整段视频都是唱歌（切片视频），无需裁剪"""
        return self.start is None


def load_songs(path: Path = SONGS_FILE) -> list[Song]:
    if not path.exists():
        raise LibraryError(f"歌单文件不存在: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise LibraryError(f"歌单文件读取失败: {e}") from e
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise LibraryError(f"歌单 YAML 解析失败: {e}") from e
    if not isinstance(raw, list) or not raw:
        raise LibraryError("歌单为空或格式错误（应为非空列表）")

    songs: list[Song] = []
    seen_ids: set[int] = set()
    for i, item in enumerate(raw, start=1):
        try:
            song = Song.model_validate(item)
        except Exception as e:
            raise LibraryError(f"歌单第 {i} 条校验失败: {e}") from e
        if song.id in seen_ids:
            raise LibraryError(f"歌单第 {i} 条 id 重复: {song.id}")
        seen_ids.add(song.id)
        if (song.start is None) != (song.end is None):
            raise LibraryError(
                f"歌单第 {i} 条 start/end 必须同时存在或同时省略: {song.title}"
            )
        if song.start is not None:
            try:
                start_s = song.start_seconds
                end_s = song.end_seconds
            except ValueError as e:
                raise LibraryError(f"歌单第 {i} 条时间格式错误: {e}") from e
            if start_s is not None and end_s is not None and end_s <= start_s:
                raise LibraryError(f"歌单第 {i} 条 end 必须大于 start: {song.title}")
        songs.append(song)
    return songs


HISTORY_FILE = "history.json"


class Library:
    def __init__(self, songs: list[Song], data_dir: Path):
        self._songs = songs
        self._data_dir = data_dir
        self._history_path = data_dir / HISTORY_FILE

    @property
    def songs(self) -> list[Song]:
        return self._songs

    def get(self, song_id: int) -> Optional[Song]:
        return next((s for s in self._songs if s.id == song_id), None)

    def find(self, keyword: str) -> list[Song]:
        keyword = keyword.strip()
        if keyword.isdecimal():
            song = self.get(int(keyword))
            return [song] if song else []
        return [s for s in self._songs if keyword in s.title]

    @property
    def played_ids(self) -> set[int]:
        if not self._history_path.exists():
            return set()
        try:
            data = json.loads(self._history_path.read_text(encoding="utf-8"))
            return {int(i) for i in data.get("played", [])}
        except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
            logger.warning(f"播放历史文件损坏，已忽略: {self._history_path}")
            return set()

    def _save_history(self, played: set[int]) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._history_path.write_text(
            json.dumps({"played": sorted(played)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def mark_played(self, song_id: int) -> None:
        played = self.played_ids
        played.add(song_id)
        self._save_history(played)

    def reset_history(self) -> None:
        self._save_history(set())

    def pick_random(self) -> Optional[Song]:
        """随机选一首没播过的并计入历史；全部播过则重置历史后重新选"""
        if not self._songs:
            return None
        played = self.played_ids
        candidates = [s for s in self._songs if s.id not in played]
        if not candidates:
            self.reset_history()
            candidates = list(self._songs)
        song = random.choice(candidates)
        self.mark_played(song.id)
        return song


_library: Optional[Library] = None


def get_library(data_dir: Path, songs_path: Path = SONGS_FILE) -> Library:
    global _library
    if _library is None:
        _library = Library(load_songs(songs_path), data_dir)
    return _library


def _reset_library_cache() -> None:
    global _library
    _library = None
