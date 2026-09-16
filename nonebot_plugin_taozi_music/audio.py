import asyncio
import shutil
import tempfile
from pathlib import Path

import httpx

from .library import Song

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
HOMEPAGE = "https://www.bilibili.com/"
VIEW_API = "https://api.bilibili.com/x/web-interface/view"
PLAYURL_API = "https://api.bilibili.com/x/player/playurl"


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


async def _fetch_audio_url(client: httpx.AsyncClient, bv: str) -> str:
    """经 B站官方 API 取最高码率音频流地址，失败抛 AudioError"""
    # 先访问首页拿 buvid3 等 cookie，避免 API 被 412 风控拦截
    await client.get(HOMEPAGE)

    resp = await client.get(VIEW_API, params={"bvid": bv})
    data = resp.json()
    if data.get("code") != 0:
        raise AudioError(f"获取视频信息失败 ({bv}): code={data.get('code')}")
    cid = data["data"]["cid"]

    resp = await client.get(
        PLAYURL_API, params={"bvid": bv, "cid": cid, "fnval": 16}
    )
    pdata = resp.json()
    audios = pdata.get("data", {}).get("dash", {}).get("audio") or []
    if not audios:
        raise AudioError(f"未取到音频流 ({bv})")
    best = max(audios, key=lambda a: a.get("bandwidth", 0))
    return best["baseUrl"]


async def _download_audio(song: Song, raw_path: Path) -> None:
    """下载歌曲来源视频的音频流到 raw_path，失败抛 AudioError"""
    headers = {"User-Agent": UA, "Referer": HOMEPAGE}
    try:
        async with httpx.AsyncClient(
            headers=headers, follow_redirects=True, timeout=60
        ) as client:
            url = await _fetch_audio_url(client, song.bv)
            async with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    raise AudioError(f"音频下载失败: HTTP {resp.status_code}")
                with open(raw_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(65536):
                        f.write(chunk)
    except httpx.HTTPError as e:
        raise AudioError(f"网络请求失败: {e}") from e


async def ensure_audio(song: Song, cache_dir: Path) -> Path:
    """确保歌曲音频已缓存，返回缓存文件路径；失败抛 AudioError"""
    target = cache_dir / f"{song.id}.mp3"
    if target.exists():
        return target

    if shutil.which("ffmpeg") is None:
        raise AudioError("运行环境未安装 ffmpeg，无法处理音频")

    cache_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        raw_path = Path(tmp) / "raw.m4a"
        await _download_audio(song, raw_path)

        cmd = ["ffmpeg", "-y", "-i", str(raw_path)]
        if not song.is_clip:
            cmd += ["-ss", str(song.start), "-to", str(song.end)]
        cmd += ["-acodec", "libmp3lame", str(target)]
        await _run(cmd)
    return target
