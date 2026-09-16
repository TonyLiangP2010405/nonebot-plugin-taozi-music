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
