from pathlib import Path

import pytest

from nonebot_plugin_taozi_music.library import (
    Library,
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
