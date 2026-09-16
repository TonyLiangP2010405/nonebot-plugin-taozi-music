# nonebot-plugin-taozi-music

每天定时在 QQ 群里以语音条形式播放主播「小小桃子呦」（B站 UID 6867955）唱过的歌，支持命令点歌。随机不重复，播完一轮自动重置。

## 功能

- 每日定时推送一首歌（QQ 语音条，非文件）
- 随机不重复选歌，播完一轮自动重置历史
- 命令点歌、查看歌单、修改每日播放时间
- 音频提前下载缓存：经 B站官方 API 只下音频流（不存视频），录播片段按时间戳裁剪（ffmpeg）

## 安装

```bash
nb plugin install nonebot-plugin-taozi-music
# 或
pip install nonebot-plugin-taozi-music
# 或
poetry add nonebot-plugin-taozi-music
```

运行环境还需安装 ffmpeg（见 https://ffmpeg.org/download.html 或 `brew install ffmpeg`）。音频下载走插件内置的 B站 API 流程，无需 yt-dlp。

协议端需支持语音消息（推荐 NapCat / Lagrange，会自动转码）。

## 配置

在 NoneBot 项目的 `.env` 文件中添加（均有默认值，可省略）：

```env
# 每日推送的群号列表（JSON 数组格式）；留空则不定时推送
taozi_music_groups=["123456789"]
# 每日播放时间（初始值，可用命令修改）
taozi_music_send_time="21:00"
```

## 使用方法

以下命令均仅 SUPERUSER 可用：

| 指令 | 范围 | 说明 |
|---|---|---|
| /桃乐 | 群聊/私聊 | 随机放一首（计入历史，不重复） |
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
