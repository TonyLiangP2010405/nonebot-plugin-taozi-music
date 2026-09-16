from nonebot_plugin_taozi_music.library import SONGS_FILE, load_songs


def test_songs_yaml_valid_and_non_empty():
    songs = load_songs(SONGS_FILE)
    assert len(songs) >= 5
    for song in songs:
        assert song.title
        assert song.bv.startswith("BV")
