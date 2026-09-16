# nonebot-plugin-taozi-music 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发 NoneBot2 插件 nonebot-plugin-taozi-music：每天定时在 QQ 群以语音条播放小小桃子呦唱过的歌（随机不重复），支持 SUPERUSER 命令点歌/歌单/设置时间。

**Architecture:** 歌单数据（resources/songs.yaml，含 BV 号与起止时间戳）→ library.py 负责歌单校验/播放历史/随机不重复选歌 → audio.py 用 yt-dlp 只下音频、ffmpeg 按时间戳裁剪并缓存 → commands.py 提供 /桃乐 系列命令（仅 SUPERUSER）→ scheduler.py 用 nonebot-plugin-apscheduler 每日定时推送到配置群。

**Tech Stack:** NoneBot2 >= 2.2.0、OneBot V11、Poetry、pytest + nonebug、yt-dlp + ffmpeg（外部命令）。

**Spec:** `docs/superpowers/specs/2026-09-16-taozi-music-design.md`（相对 spec 的依赖调整：新增 nonebot-plugin-localstore 作为插件数据目录方案，移除未使用的 httpx；spec 已同步更新）。

## Global Constraints

- Python >= 3.9：禁止使用 3.10+ 语法（如 `X | Y` 类型注解、`match` 语句）；可选类型用 `Optional[X]`。
- NoneBot2 官方 API（禁 v1 写法）；所有事件处理保持异步，网络/子进程禁止同步阻塞（子进程用 `asyncio.create_subprocess_exec`）。
- 所有命令 `permission=SUPERUSER`，非管理员触发不响应。
- 播放一律用 `MessageSegment.record()` 发语音条，禁止发文件消息。
- 依赖固定为：`nonebot2 = ">=2.2.0"`、`nonebot-adapter-onebot = ">=2.4.0"`、`nonebot-plugin-apscheduler = ">=0.5.0"`、`nonebot-plugin-localstore = ">=0.7.0"`、`PyYAML = ">=6.0"`；不新增其他运行依赖。
- 配置项全部有默认值，缺配置 import 不失败；不写死任何 token/cookie。
- 每个 Task 结束时按给出的命令提交一次 git commit。

---
### Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `nonebot_plugin_taozi_music/__init__.py`
- Create: `nonebot_plugin_taozi_music/config.py`
- Create: `tests/conftest.py`
- Create: `tests/test_load.py`

**Interfaces:**
- Produces: `nonebot_plugin_taozi_music.config.Config`，字段 `taozi_music_groups: list[int] = []`、`taozi_music_send_time: str = "21:00"`。后续 Task 全部依赖这两个字段名。

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[tool.poetry]
name = "nonebot-plugin-taozi-music"
version = "0.1.0"
description = "每天定时在群里语音播放小小桃子呦唱过的歌"
authors = ["taozi-fan"]
license = "MIT"
readme = "README.md"
packages = [{ include = "nonebot_plugin_taozi_music" }]

[tool.poetry.dependencies]
python = ">=3.9"
nonebot2 = ">=2.2.0"
nonebot-adapter-onebot = ">=2.4.0"
nonebot-plugin-apscheduler = ">=0.5.0"
nonebot-plugin-localstore = ">=0.7.0"
PyYAML = ">=6.0"

[tool.poetry.group.dev.dependencies]
pytest = ">=8.0"
pytest-asyncio = ">=0.23"
nonebug = ">=0.3.7"
ruff = ">=0.6"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
__pycache__/
*.pyc
.venv/
dist/
data/
.pytest_cache/
.ruff_cache/
```

- [ ] **Step 3: 创建包骨架 `nonebot_plugin_taozi_music/__init__.py`（本任务不含 commands/scheduler 导入）**

```python
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="桃乐",
    description="每天定时在群里语音播放小小桃子呦唱过的歌，支持点歌",
    usage=(
        "/桃乐 —— 随机放一首歌\n"
        "/桃乐 歌单 —— 查看歌曲列表\n"
        "/桃乐 点歌 <编号或歌名> —— 播放指定歌曲\n"
        "/桃乐 时间 HH:MM —— 设置每日播放时间\n"
        "（以上命令仅 SUPERUSER 可用）"
    ),
    type="application",
    homepage="https://github.com/taozi-fan/nonebot-plugin-taozi-music",
    config=Config,
    supported_adapters={"~onebot.v11"},
)
```

- [ ] **Step 4: 创建 `nonebot_plugin_taozi_music/config.py`**

```python
from pydantic import BaseModel


class Config(BaseModel):
    """桃乐插件配置"""

    taozi_music_groups: list[int] = []
    """每日定时推送的群号列表，为空则不推送"""

    taozi_music_send_time: str = "21:00"
    """每日播放时间（HH:MM），可被 /桃乐 时间 命令修改并持久化"""
```

- [ ] **Step 5: 创建 `tests/conftest.py`**

```python
import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {"driver": "~none", "superusers": {"10001"}}


@pytest.fixture(scope="session", autouse=True)
def load_plugin(nonebug_init: None) -> None:
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)
    nonebot.load_plugin("nonebot_plugin_taozi_music")
```

- [ ] **Step 6: 创建 `tests/test_load.py`**

```python
import nonebot


def test_plugin_loaded():
    assert nonebot.get_plugin("nonebot_plugin_taozi_music") is not None
```

- [ ] **Step 7: 安装依赖并跑测试**

Run: `cd nonebot-plugin-taozi-music && poetry install`
Expected: 成功（若无 poetry，先 `pip install poetry`）

Run: `poetry run python -m compileall nonebot_plugin_taozi_music`
Expected: 无错误

Run: `poetry run pytest tests/test_load.py -v`
Expected: 1 passed

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore nonebot_plugin_taozi_music tests poetry.lock
git commit -m "feat: project scaffold with plugin metadata and config"
```

---

### Task 2: library.py — 时间解析与歌单加载校验

**Files:**
- Create: `nonebot_plugin_taozi_music/library.py`
- Create: `nonebot_plugin_taozi_music/resources/songs.yaml`（临时 1 条占位，Task 4 替换为真实歌单）
- Test: `tests/test_library.py`

**Interfaces:**
- Produces:
  - `class LibraryError(Exception)`
  - `parse_time(value: str) -> int`：接受 `"90"`、`"1:30"`、`"1:02:03"`，非法输入抛 `ValueError`
  - `class Song(BaseModel)`：字段 `id: int`、`title: str`、`bv: str`、`start: Optional[str] = None`、`end: Optional[str] = None`、`note: str = ""`；属性 `start_seconds -> Optional[int]`、`end_seconds -> Optional[int]`、`is_clip -> bool`（start 为 None 即整段视频是歌）
  - `load_songs(path: Path) -> list[Song]`：文件缺失/YAML 错误/空列表/条目校验失败/id 重复/start-end 不成对/end<=start 时抛 `LibraryError`
  - 模块常量 `SONGS_FILE = Path(__file__).parent / "resources" / "songs.yaml"`

- [ ] **Step 1: 写失败测试 `tests/test_library.py`（第一部分）**

```python
from pathlib import Path

import pytest

from nonebot_plugin_taozi_music.library import (
    LibraryError,
    Song,
    load_songs,
    parse_time,
)


def test_parse_time_seconds_only():
    assert parse_time("90") == 90


def test_parse_time_mm_ss():
    assert parse_time("1:30") == 90


def test_parse_time_hh_mm_ss():
    assert parse_time("1:02:03") == 3723


@pytest.mark.parametrize("bad", ["", "abc", "1:2:3:4", "1:99", "-5"])
def test_parse_time_invalid(bad):
    with pytest.raises(ValueError):
        parse_time(bad)


def _write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "songs.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_songs_ok(tmp_path):
    path = _write_yaml(
        tmp_path,
        """
- id: 1
  title: 歌A
  bv: BV1xx411c7mD
- id: 2
  title: 歌B
  bv: BV1xx411c7mE
  start: "12:30"
  end: "14:05"
""",
    )
    songs = load_songs(path)
    assert len(songs) == 2
    assert songs[0].is_clip is True
    assert songs[0].start_seconds is None
    assert songs[1].is_clip is False
    assert songs[1].start_seconds == 750
    assert songs[1].end_seconds == 845


def test_load_songs_missing_file(tmp_path):
    with pytest.raises(LibraryError):
        load_songs(tmp_path / "nope.yaml")


def test_load_songs_empty(tmp_path):
    with pytest.raises(LibraryError):
        load_songs(_write_yaml(tmp_path, ""))


def test_load_songs_duplicate_id(tmp_path):
    with pytest.raises(LibraryError):
        load_songs(
            _write_yaml(
                tmp_path,
                "- id: 1\n  title: 歌A\n  bv: BV1xx411c7mD\n"
                "- id: 1\n  title: 歌B\n  bv: BV1xx411c7mE\n",
            )
        )


def test_load_songs_unpaired_start_end(tmp_path):
    with pytest.raises(LibraryError):
        load_songs(
            _write_yaml(
                tmp_path,
                '- id: 1\n  title: 歌A\n  bv: BV1xx411c7mD\n  start: "1:00"\n',
            )
        )


def test_load_songs_end_before_start(tmp_path):
    with pytest.raises(LibraryError):
        load_songs(
            _write_yaml(
                tmp_path,
                '- id: 1\n  title: 歌A\n  bv: BV1xx411c7mD\n'
                '  start: "14:05"\n  end: "12:30"\n',
            )
        )


def test_song_invalid_bv():
    with pytest.raises(Exception):
        Song(id=1, title="歌A", bv="av12345")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `poetry run pytest tests/test_library.py -v`
Expected: FAIL（ModuleNotFoundError: nonebot_plugin_taozi_music.library）

- [ ] **Step 3: 实现 `nonebot_plugin_taozi_music/library.py`（第一部分）**

```python
from pathlib import Path
from typing import Optional

import yaml
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
    start: Optional[str] = None
    end: Optional[str] = None
    note: str = ""

    @field_validator("bv")
    @classmethod
    def _check_bv(cls, v: str) -> str:
        if not v.startswith("BV"):
            raise ValueError(f"非法 BV 号: {v!r}")
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
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
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
```

- [ ] **Step 4: 创建占位歌单 `nonebot_plugin_taozi_music/resources/songs.yaml`**

```yaml
# 占位条目，Task 4 会替换为真实收集的歌单
- id: 1
  title: 占位歌
  bv: BV1xx411c7mD
  note: 占位
```

- [ ] **Step 5: 跑测试确认通过**

Run: `poetry run pytest tests/test_library.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add nonebot_plugin_taozi_music/library.py nonebot_plugin_taozi_music/resources/songs.yaml tests/test_library.py
git commit -m "feat: song model and songs.yaml loading with validation"
```

---
### Task 3: library.py — Library 类（历史、随机不重复、查找）

**Files:**
- Modify: `nonebot_plugin_taozi_music/library.py`
- Test: `tests/test_library.py`（追加）

**Interfaces:**
- Consumes: Task 2 的 `Song`、`LibraryError`
- Produces:
  - `class Library`：构造 `Library(songs: list[Song], data_dir: Path)`；属性 `songs -> list[Song]`、`played_ids -> set[int]`；方法 `get(song_id: int) -> Optional[Song]`、`find(keyword: str) -> list[Song]`（纯数字按 id 查，否则按标题包含模糊查）、`mark_played(song_id: int) -> None`、`reset_history() -> None`、`pick_random() -> Optional[Song]`（从未播过的歌中随机选并计入历史；全部播过则重置历史后重新选）
  - `get_library(data_dir: Path, songs_path: Path = SONGS_FILE) -> Library`（模块级缓存）
  - `_reset_library_cache() -> None`（测试用）

- [ ] **Step 1: 追加失败测试到 `tests/test_library.py`**

先把 `Library` 加进文件顶部已有的 `from nonebot_plugin_taozi_music.library import (...)` 导入列表（避免文件中部 import 触发 ruff E402），然后追加：

```python
def _make_library(tmp_path: Path, count: int = 3) -> Library:
    songs = [
        Song(id=i, title=f"歌{i}", bv=f"BV1xx411c7m{i}") for i in range(1, count + 1)
    ]
    return Library(songs, tmp_path)


def test_get_by_id(tmp_path):
    lib = _make_library(tmp_path)
    assert lib.get(2).title == "歌2"
    assert lib.get(99) is None


def test_find_by_id_and_title(tmp_path):
    lib = _make_library(tmp_path)
    assert [s.id for s in lib.find("2")] == [2]
    assert [s.id for s in lib.find("歌")] == [1, 2, 3]
    assert lib.find("不存在") == []


def test_pick_random_no_repeat_until_exhausted(tmp_path):
    lib = _make_library(tmp_path, count=3)
    picked = [lib.pick_random().id for _ in range(3)]
    assert sorted(picked) == [1, 2, 3]
    assert lib.played_ids == {1, 2, 3}


def test_pick_random_resets_after_full_round(tmp_path):
    lib = _make_library(tmp_path, count=2)
    lib.pick_random()
    lib.pick_random()
    song = lib.pick_random()  # 触发重置
    assert song.id in {1, 2}
    assert lib.played_ids == {song.id}


def test_history_persists_across_instances(tmp_path):
    lib = _make_library(tmp_path, count=3)
    lib.mark_played(1)
    lib2 = _make_library(tmp_path, count=3)
    assert lib2.played_ids == {1}


def test_pick_random_empty_library(tmp_path):
    lib = Library([], tmp_path)
    assert lib.pick_random() is None


def test_corrupted_history_ignored(tmp_path):
    lib = _make_library(tmp_path)
    (tmp_path / "history.json").write_text("not-json", encoding="utf-8")
    assert lib.played_ids == set()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `poetry run pytest tests/test_library.py -v`
Expected: 新增测试 FAIL（ImportError: cannot import name 'Library'）

- [ ] **Step 3: 在 `library.py` 追加实现**

文件顶部 import 区补充 `import json`、`import random`、`from nonebot.log import logger`，然后在文件末尾追加：

```python
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
        if keyword.isdigit():
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `poetry run pytest tests/test_library.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add nonebot_plugin_taozi_music/library.py tests/test_library.py
git commit -m "feat: Library with play history and non-repeating random pick"
```

---

### Task 4: 收集真实初始歌单 songs.yaml

**Files:**
- Modify: `nonebot_plugin_taozi_music/resources/songs.yaml`
- Test: `tests/test_songs_yaml.py`

**Interfaces:**
- Consumes: Task 2 的 `load_songs`、`SONGS_FILE`
- Produces: 真实歌单数据，供 Task 5/6/7 的集成路径使用

- [ ] **Step 1: 联网调研收集唱歌视频**

使用 agent-reach 技能（或直接 WebSearch/FetchURL）搜索以下关键词，收集候选视频：
- `小小桃子呦 唱歌`
- `小小桃子呦 歌切`
- `小小桃子呦 翻唱`
- site:bilibili.com 范围内优先

收集规则：
- 只收确实由小小桃子呦本人演唱的片段（标题/简介/UP主说明佐证）
- 切片 UP 主切好的唱歌视频：start/end 省略（整段即歌）
- 她自己的录播/视频里的唱歌段：记录 start/end（mm:ss），来自视频简介、评论区时间戳或弹幕指路；无法确认时间戳的不要编造，宁可不收该条
- 目标：尽量多收，至少 5 条

- [ ] **Step 2: 逐条验证 BV 号真实存在**

对每条记录执行：

```bash
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=<BV号>" | head -c 300
```

Expected: 返回 JSON 中 `"code":0` 且标题与唱歌内容相符。若触发 -799 限频，sleep 几秒重试。验证失败或标题不符的条目丢弃。

- [ ] **Step 3: 写真实 `resources/songs.yaml`**

格式：

```yaml
- id: 1
  title: 真实歌名
  bv: BVxxxxxxxxx
  note: 来源说明（如"切片UP主：xxx"或"主播录播 2026-xx-xx"）
# 需要裁剪的条目额外带：
#   start: "12:30"
#   end: "14:05"
```

id 从 1 开始连续递增。

- [ ] **Step 4: 写校验测试 `tests/test_songs_yaml.py`**

```python
from nonebot_plugin_taozi_music.library import SONGS_FILE, load_songs


def test_songs_yaml_valid_and_non_empty():
    songs = load_songs(SONGS_FILE)
    assert len(songs) >= 5
    for song in songs:
        assert song.title
        assert song.bv.startswith("BV")
```

- [ ] **Step 5: 跑测试确认通过**

Run: `poetry run pytest tests/test_songs_yaml.py tests/test_library.py -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add nonebot_plugin_taozi_music/resources/songs.yaml tests/test_songs_yaml.py
git commit -m "feat: initial real song library collected from bilibili"
```

---

### Task 5: audio.py — 下载与裁剪

**Files:**
- Create: `nonebot_plugin_taozi_music/audio.py`
- Test: `tests/test_audio.py`

**Interfaces:**
- Consumes: Task 2 的 `Song`（`id`、`bv`、`is_clip`、`start`、`end`）
- Produces:
  - `class AudioError(Exception)`
  - `async ensure_audio(song: Song, cache_dir: Path) -> Path`：缓存命中直接返回 `{cache_dir}/{song.id}.mp3`；未命中则 yt-dlp 只下音频，非切片歌再用 ffmpeg 按 start/end 裁剪；失败抛 `AudioError`

- [ ] **Step 1: 写失败测试 `tests/test_audio.py`**

```python
from pathlib import Path

import pytest

import nonebot_plugin_taozi_music.audio as audio
from nonebot_plugin_taozi_music.audio import AudioError, ensure_audio
from nonebot_plugin_taozi_music.library import Song


def _song(**kwargs) -> Song:
    base = {"id": 1, "title": "歌A", "bv": "BV1xx411c7mD"}
    base.update(kwargs)
    return Song(**base)


async def test_ensure_audio_cache_hit(tmp_path, monkeypatch):
    target = tmp_path / "1.mp3"
    target.write_bytes(b"cached")

    async def boom(cmd):
        raise AssertionError("不应执行任何外部命令")

    monkeypatch.setattr(audio, "_run", boom)
    assert await ensure_audio(_song(), tmp_path) == target


async def test_ensure_audio_missing_yt_dlp(tmp_path, monkeypatch):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    with pytest.raises(AudioError, match="yt-dlp"):
        await ensure_audio(_song(), tmp_path)


async def test_ensure_audio_clip_song(tmp_path, monkeypatch):
    async def fake_run(cmd):
        if cmd[0] == "yt-dlp":
            template = Path(cmd[cmd.index("-o") + 1])
            template.with_suffix(".mp3").write_bytes(b"audio")

    monkeypatch.setattr(audio, "_run", fake_run)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    result = await ensure_audio(_song(), tmp_path)
    assert result == tmp_path / "1.mp3"
    assert result.read_bytes() == b"audio"


async def test_ensure_audio_cut_song(tmp_path, monkeypatch):
    calls = []

    async def fake_run(cmd):
        calls.append(cmd)
        if cmd[0] == "yt-dlp":
            template = Path(cmd[cmd.index("-o") + 1])
            template.with_suffix(".mp3").write_bytes(b"audio")
        elif cmd[0] == "ffmpeg":
            Path(cmd[-1]).write_bytes(b"clip")

    monkeypatch.setattr(audio, "_run", fake_run)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    song = _song(start="12:30", end="14:05")
    result = await ensure_audio(song, tmp_path)
    assert result == tmp_path / "1.mp3"
    ffmpeg_cmd = next(c for c in calls if c[0] == "ffmpeg")
    assert ffmpeg_cmd[ffmpeg_cmd.index("-ss") + 1] == "12:30"
    assert ffmpeg_cmd[ffmpeg_cmd.index("-to") + 1] == "14:05"


async def test_ensure_audio_command_failure(tmp_path, monkeypatch):
    async def fail_run(cmd):
        raise AudioError("命令执行失败 (yt-dlp): boom")

    monkeypatch.setattr(audio, "_run", fail_run)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    with pytest.raises(AudioError):
        await ensure_audio(_song(), tmp_path)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `poetry run pytest tests/test_audio.py -v`
Expected: FAIL（ModuleNotFoundError: nonebot_plugin_taozi_music.audio）

- [ ] **Step 3: 实现 `nonebot_plugin_taozi_music/audio.py`**

```python
import asyncio
import shutil
import tempfile
from pathlib import Path

from .library import Song


class AudioError(Exception):
    """音频下载或处理失败"""


async def _run(cmd: list) -> None:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        tail = stderr.decode(errors="ignore")[-200:]
        raise AudioError(f"命令执行失败 ({cmd[0]}): {tail}")


async def ensure_audio(song: Song, cache_dir: Path) -> Path:
    """确保歌曲音频已缓存，返回缓存文件路径；失败抛 AudioError"""
    target = cache_dir / f"{song.id}.mp3"
    if target.exists():
        return target

    if shutil.which("yt-dlp") is None:
        raise AudioError("运行环境未安装 yt-dlp，无法下载音频")

    cache_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.bilibili.com/video/{song.bv}"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_template = str(tmp_path / "raw.%(ext)s")
        await _run(
            [
                "yt-dlp", "-x", "--audio-format", "mp3",
                "--no-playlist", "-o", raw_template, url,
            ]
        )
        raws = list(tmp_path.glob("raw.*"))
        if not raws:
            raise AudioError("yt-dlp 未产出音频文件")

        if song.is_clip:
            shutil.move(str(raws[0]), str(target))
        else:
            if shutil.which("ffmpeg") is None:
                raise AudioError("运行环境未安装 ffmpeg，无法裁剪音频")
            await _run(
                [
                    "ffmpeg", "-y", "-i", str(raws[0]),
                    "-ss", str(song.start), "-to", str(song.end),
                    "-acodec", "libmp3lame", str(target),
                ]
            )
    return target
```

（`-ss`/`-to` 作为输出选项放在 `-i` 之后，时间轴按原始视频计算，语义与歌单时间戳一致。）

- [ ] **Step 4: 跑测试确认通过**

Run: `poetry run pytest tests/test_audio.py -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add nonebot_plugin_taozi_music/audio.py tests/test_audio.py
git commit -m "feat: audio download and clipping pipeline"
```

---
### Task 6: commands.py — /桃乐 系列命令（不含「时间」的 scheduler 联动）

**Files:**
- Create: `nonebot_plugin_taozi_music/commands.py`
- Test: `tests/test_commands.py`

**Interfaces:**
- Consumes: `library.Library / get_library / LibraryError / Song`、`audio.ensure_audio / AudioError`
- Produces:
  - `music`：matcher（`on_command("桃乐", permission=SUPERUSER, priority=10, block=True)`）
  - `DATA_DIR`、`CACHE_DIR`（Path，来自 localstore）
  - `async play_song(song: Song) -> MessageSegment`：准备音频并返回语音消息段
  - `_valid_hhmm(value: str) -> bool`
  - 命令行为：`/桃乐`（随机放）、`/桃乐 歌单`、`/桃乐 点歌 <编号或歌名>`、`/桃乐 时间 HH:MM`（本任务只做参数校验和提示文本，Task 7 接 scheduler）
- 注意：Task 7 的 scheduler.py 会 `from .commands import DATA_DIR, play_song`，commands.py 内部对 scheduler 的引用必须放在函数内 lazy import。

- [ ] **Step 1: 写失败测试 `tests/test_commands.py`**

```python
from nonebug import App
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    Sender,
)

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
    assert "Superuser" in names


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
    _patch_library(monkeypatch, tmp_path, songs=[Song(id=1, title="歌A", bv="BV1xx411c7mD")])

    async def fake_play(song):
        return MessageSegment.record("file:///fake/1.mp3")

    monkeypatch.setattr(commands, "play_song", fake_play)
    async with app.test_matcher(commands.music) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10002")
        event = make_group_event("/桃乐")
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "🎵 正在播放：歌A", result=None, bot=bot)
        ctx.should_call_send(
            event, Message(MessageSegment.record("file:///fake/1.mp3")),
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
            event, Message(MessageSegment.record("file:///fake/2.mp3")),
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `poetry run pytest tests/test_commands.py -v`
Expected: FAIL（ModuleNotFoundError: nonebot_plugin_taozi_music.commands）

- [ ] **Step 3: 实现 `nonebot_plugin_taozi_music/commands.py`**

```python
from nonebot import on_command
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot_plugin_localstore import get_plugin_data_dir

from nonebot.adapters.onebot.v11 import Message, MessageSegment

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
        await music.finish("语音发送失败，请检查协议端（NapCat/Lagrange）是否支持语音消息")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `poetry run pytest tests/test_commands.py -v`
Expected: 全部 PASS（「时间」分支此时调用 scheduler 会 ImportError，但本任务测试只覆盖非法格式路径，不触发该 import）

- [ ] **Step 5: Commit**

```bash
git add nonebot_plugin_taozi_music/commands.py tests/test_commands.py
git commit -m "feat: /桃乐 commands (random play, list, on-demand, time validation)"
```

---

### Task 7: scheduler.py + __init__ 定时接线

**Files:**
- Create: `nonebot_plugin_taozi_music/scheduler.py`
- Modify: `nonebot_plugin_taozi_music/__init__.py`
- Test: `tests/test_scheduler.py`、修改 `tests/test_commands.py`（追加「时间」成功路径测试）

**Interfaces:**
- Consumes: `commands.DATA_DIR`、`commands.play_song`、`library.get_library / LibraryError`、`config.Config`
- Produces:
  - `DAILY_JOB_ID = "taozi_music_daily"`
  - `load_send_time(data_dir: Path) -> Optional[str]`、`save_send_time(data_dir: Path, send_time: str) -> None`
  - `register_daily_job(send_time: str) -> None`（cron，`replace_existing=True`）
  - `update_send_time(send_time: str) -> None`（持久化 + 重注册 job）
  - `async daily_push() -> None`（向 `taozi_music_groups` 推送随机不重复一首歌）

- [ ] **Step 1: 写失败测试 `tests/test_scheduler.py`**

```python
import nonebot
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `poetry run pytest tests/test_scheduler.py -v`
Expected: FAIL（ModuleNotFoundError: nonebot_plugin_taozi_music.scheduler）

- [ ] **Step 3: 实现 `nonebot_plugin_taozi_music/scheduler.py`**

```python
import json
from pathlib import Path
from typing import Optional

from nonebot import get_bots, get_plugin_config, logger, require

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from .audio import AudioError
from .commands import DATA_DIR, play_song
from .config import Config
from .library import LibraryError, get_library

DAILY_JOB_ID = "taozi_music_daily"
SETTINGS_FILE = "settings.json"


def load_send_time(data_dir: Path) -> Optional[str]:
    path = data_dir / SETTINGS_FILE
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["send_time"]
        return str(value)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


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
            await bot.send_group_msg(
                group_id=group,
                message=f"今日桃乐放送失败：《{song.title}》{e}",
            )
        return

    for group in config.taozi_music_groups:
        try:
            await bot.send_group_msg(
                group_id=group, message=f"🎵 今日桃乐：{song.title}"
            )
            await bot.send_group_msg(group_id=group, message=segment)
        except Exception:
            logger.exception(f"每日桃乐推送到群 {group} 失败")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `poetry run pytest tests/test_scheduler.py -v`
Expected: 全部 PASS

- [ ] **Step 5: 修改 `nonebot_plugin_taozi_music/__init__.py` 接入命令与定时任务**

完整替换为：

```python
from nonebot import get_driver, get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="桃乐",
    description="每天定时在群里语音播放小小桃子呦唱过的歌，支持点歌",
    usage=(
        "/桃乐 —— 随机放一首歌\n"
        "/桃乐 歌单 —— 查看歌曲列表\n"
        "/桃乐 点歌 <编号或歌名> —— 播放指定歌曲\n"
        "/桃乐 时间 HH:MM —— 设置每日播放时间\n"
        "（以上命令仅 SUPERUSER 可用）"
    ),
    type="application",
    homepage="https://github.com/taozi-fan/nonebot-plugin-taozi-music",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

from . import commands, scheduler  # noqa: E402,F401

_driver = get_driver()
_config = get_plugin_config(Config)


@_driver.on_startup
async def _register_jobs() -> None:
    send_time = (
        scheduler.load_send_time(commands.DATA_DIR) or _config.taozi_music_send_time
    )
    scheduler.register_daily_job(send_time)
```

- [ ] **Step 6: 追加「时间」成功路径测试到 `tests/test_commands.py`**

```python
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
```

- [ ] **Step 7: 跑全量测试**

Run: `poetry run pytest -v`
Expected: 全部 PASS

- [ ] **Step 8: Commit**

```bash
git add nonebot_plugin_taozi_music/scheduler.py nonebot_plugin_taozi_music/__init__.py tests/test_scheduler.py tests/test_commands.py
git commit -m "feat: daily scheduled push and send-time persistence"
```

---

### Task 8: README、格式检查与收尾

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Modify（如需）: 任意文件

**Interfaces:**
- Consumes: 全部前序任务

- [ ] **Step 1: 写 README.md**

````markdown
# nonebot-plugin-taozi-music

每天定时在 QQ 群里以语音条形式播放主播「小小桃子呦」（B站 UID 6867955）唱过的歌，支持命令点歌。随机不重复，播完一轮自动重置。

## 功能

- 每日定时推送一首歌（QQ 语音条，非文件）
- 随机不重复选歌，播完一轮自动重置历史
- 命令点歌、查看歌单、修改每日播放时间
- 音频提前下载缓存：只下音频（yt-dlp），录播片段按时间戳裁剪（ffmpeg），不存视频

## 安装

```bash
nb plugin install nonebot-plugin-taozi-music
# 或
pip install nonebot-plugin-taozi-music
# 或
poetry add nonebot-plugin-taozi-music
```

运行环境还需安装外部命令：

```bash
pip install yt-dlp
# ffmpeg 见 https://ffmpeg.org/download.html
```

协议端需支持语音消息（推荐 NapCat / Lagrange，会自动转码）。

## 配置

在 NoneBot 项目的 `.env` 文件中添加（均有默认值，可省略）：

```env
# 每日推送的群号，逗号分隔；留空则不定时推送
taozi_music_groups=["123456789"]
# 每日播放时间（初始值，可用命令修改）
taozi_music_send_time="21:00"
```

## 使用方法

以下命令均仅 SUPERUSER 可用：

| 指令 | 范围 | 说明 |
|---|---|---|
| /桃乐 | 群聊 | 随机放一首（计入历史，不重复） |
| /桃乐 歌单 | 群聊/私聊 | 列出歌曲编号与歌名 |
| /桃乐 点歌 <编号或歌名> | 群聊/私聊 | 播放指定歌曲 |
| /桃乐 时间 HH:MM | 群聊/私聊 | 修改每日播放时间（持久化） |

## 歌单

歌单在 `nonebot_plugin_taozi_music/resources/songs.yaml`，每条记录：

```yaml
- id: 1
  title: 歌名
  bv: BVxxxxx        # 来源视频
  start: "12:30"     # 可选：唱歌开始时间（录播片段）
  end: "14:05"       # 可选：唱歌结束时间；与 start 成对出现
  note: 来源说明
```

切片 UP 主切好的唱歌视频省略 start/end（整段即歌）。欢迎 PR 补充更多歌。

## 许可证

MIT
````

- [ ] **Step 2: 创建 LICENSE（MIT）**

标准 MIT 文本，copyright 行写 `Copyright (c) 2026 taozi-fan`。

- [ ] **Step 3: ruff 检查**

Run: `poetry run ruff check .`
Expected: 无错误（有则修复后重跑）

- [ ] **Step 4: 全量检查**

Run: `poetry run python -m compileall nonebot_plugin_taozi_music && poetry run pytest -v`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add README.md LICENSE
git commit -m "docs: README and LICENSE"
```

---
