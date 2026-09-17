from pathlib import Path

import httpx
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

    async def boom(*args, **kwargs):
        raise AssertionError("缓存命中时不应下载或执行外部命令")

    monkeypatch.setattr(audio, "_download_audio", boom)
    monkeypatch.setattr(audio, "_run", boom)
    assert await ensure_audio(_song(), tmp_path) == target


async def test_ensure_audio_missing_ffmpeg(tmp_path, monkeypatch):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    with pytest.raises(AudioError, match="ffmpeg"):
        await ensure_audio(_song(), tmp_path)


async def test_ensure_audio_clip_song(tmp_path, monkeypatch):
    async def fake_download(song, raw_path):
        raw_path.write_bytes(b"audio")

    async def fake_run(cmd):
        Path(cmd[-1]).write_bytes(b"mp3")

    monkeypatch.setattr(audio, "_download_audio", fake_download)
    monkeypatch.setattr(audio, "_run", fake_run)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    result = await ensure_audio(_song(), tmp_path)
    assert result == tmp_path / "1.mp3"
    assert result.read_bytes() == b"mp3"


async def test_ensure_audio_cut_song(tmp_path, monkeypatch):
    calls = []

    async def fake_download(song, raw_path):
        raw_path.write_bytes(b"audio")

    async def fake_run(cmd):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b"clip")

    monkeypatch.setattr(audio, "_download_audio", fake_download)
    monkeypatch.setattr(audio, "_run", fake_run)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    song = _song(start="12:30", end="14:05")
    result = await ensure_audio(song, tmp_path)
    assert result == tmp_path / "1.mp3"
    ffmpeg_cmd = calls[0]
    assert ffmpeg_cmd[ffmpeg_cmd.index("-ss") + 1] == "12:30"
    assert ffmpeg_cmd[ffmpeg_cmd.index("-to") + 1] == "14:05"


async def test_ensure_audio_download_failure(tmp_path, monkeypatch):
    async def fail_download(song, raw_path):
        raise AudioError("获取视频信息失败")

    monkeypatch.setattr(audio, "_download_audio", fail_download)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    with pytest.raises(AudioError):
        await ensure_audio(_song(), tmp_path)
    assert not (tmp_path / "1.mp3").exists()


async def test_ensure_audio_ffmpeg_failure_leaves_no_cache(tmp_path, monkeypatch):
    async def fake_download(song, raw_path):
        raw_path.write_bytes(b"audio")

    async def fail_run(cmd):
        # 模拟 ffmpeg 写了一部分然后失败
        Path(cmd[-1]).write_bytes(b"partial")
        raise AudioError("命令执行失败 (ffmpeg): boom")

    monkeypatch.setattr(audio, "_download_audio", fake_download)
    monkeypatch.setattr(audio, "_run", fail_run)
    monkeypatch.setattr(audio.shutil, "which", lambda name: "/usr/bin/" + name)
    with pytest.raises(AudioError):
        await ensure_audio(_song(), tmp_path)
    assert not (tmp_path / "1.mp3").exists()


async def test_fetch_audio_url_picks_highest_bandwidth():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(200, json={"code": 0, "data": {"cid": 123}})
        if "player/playurl" in url:
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "dash": {
                            "audio": [
                                {"baseUrl": "https://cdn/64k", "bandwidth": 64000},
                                {"baseUrl": "https://cdn/132k", "bandwidth": 132000},
                            ]
                        }
                    },
                },
            )
        return httpx.Response(200)  # 首页 cookie bootstrap

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        url = await audio._fetch_audio_url(client, "BV1xx411c7mD")
    assert url == "https://cdn/132k"


async def test_fetch_audio_url_view_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if "web-interface/view" in str(request.url):
            return httpx.Response(200, json={"code": -404, "message": "啥都木有"})
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError, match="获取视频信息失败"):
            await audio._fetch_audio_url(client, "BV1xx411c7mD")


async def test_fetch_audio_url_no_audio_stream():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(200, json={"code": 0, "data": {"cid": 123}})
        if "player/playurl" in url:
            return httpx.Response(200, json={"code": 0, "data": {"dash": {}}})
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError, match="未取到音频流"):
            await audio._fetch_audio_url(client, "BV1xx411c7mD")


async def test_fetch_audio_url_null_data():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(200, json={"code": 0, "data": None})
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError):
            await audio._fetch_audio_url(client, "BV1xx411c7mD")


async def test_fetch_audio_url_non_json_response():
    def handler(request: httpx.Request) -> httpx.Response:
        if "web-interface/view" in str(request.url):
            return httpx.Response(412, text="<html>blocked</html>")
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError):
            await audio._fetch_audio_url(client, "BV1xx411c7mD")


async def test_fetch_audio_url_part_uses_matching_page_cid():
    seen_cids = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "cid": 111,
                        "pages": [
                            {"page": 1, "cid": 111},
                            {"page": 2, "cid": 222},
                        ],
                    },
                },
            )
        if "player/playurl" in url:
            seen_cids.append(request.url.params.get("cid"))
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "dash": {
                            "audio": [
                                {"baseUrl": "https://cdn/p2", "bandwidth": 132000}
                            ]
                        }
                    },
                },
            )
        return httpx.Response(200)  # 首页 cookie bootstrap

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        url = await audio._fetch_audio_url(client, "BV1xx411c7mD", part=2)
    assert url == "https://cdn/p2"
    assert seen_cids == ["222"]


async def test_fetch_audio_url_part_out_of_range():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {"cid": 111, "pages": [{"page": 1, "cid": 111}]},
                },
            )
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError, match="不存在分P 3"):
            await audio._fetch_audio_url(client, "BV1xx411c7mD", part=3)


async def test_fetch_audio_url_part_pages_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(200, json={"code": 0, "data": {"cid": 111}})
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError, match="不存在分P 2"):
            await audio._fetch_audio_url(client, "BV1xx411c7mD", part=2)


async def test_fetch_audio_url_missing_cid():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "web-interface/view" in url:
            return httpx.Response(200, json={"code": 0, "data": {}})
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AudioError):
            await audio._fetch_audio_url(client, "BV1xx411c7mD")
