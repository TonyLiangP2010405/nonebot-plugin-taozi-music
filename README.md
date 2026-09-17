# nonebot-plugin-taozi-music

每天定时在 QQ 群里以语音条形式播放主播「小小桃子呦」（B站 UID 6867955）唱过的歌，支持命令点歌。随机不重复，播完一轮自动重置。

## 功能

- 每日定时推送一首歌（QQ 语音条，非文件）；推送前先连发 5 条「警告！！！即将开始发送今日的桃歌」
- 只推送到开启状态的群，群列表用命令管理（加群/删群/开启/关闭）
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

协议端需支持语音消息（推荐 NapCat / Lagrange，会自动转码）。语音以 base64 内联发送，协议端（NapCat/Lagrange 等）可以与 bot 不在同一台机器，无需共享文件系统。

## 配置

在 NoneBot 项目的 `.env` 文件中添加（均有默认值，可省略）：

```env
# 每日推送的群号初始列表（JSON 数组格式）；启动时写入 data/settings.json，之后用命令管理
taozi_music_groups=["123456789"]
# 每日播放时间（初始值，可用命令修改）
taozi_music_send_time="21:00"
```

群设置与每日播放时间统一持久化在插件 data 目录的 `settings.json` 中：

```json
{"send_time": "21:30", "groups": {"123456789": true, "987654321": false}}
```

## 使用方法

以下命令均仅 SUPERUSER 可用；群管理命令在私聊里使用时必须显式带群号：

| 指令 | 范围 | 说明 |
|---|---|---|
| /桃乐 | 群聊/私聊 | 随机放一首（计入历史，不重复） |
| /桃乐 歌单 | 群聊/私聊 | 列出歌曲编号与歌名 |
| /桃乐 点歌 <编号或歌名> | 群聊/私聊 | 播放指定歌曲 |
| /桃乐 时间 HH:MM | 群聊/私聊 | 修改每日播放时间（持久化） |
| /桃乐 加群 [群号] | 群聊/私聊 | 加入每日推送并开启；省略群号时操作当前群 |
| /桃乐 删群 [群号] | 群聊/私聊 | 移出每日推送 |
| /桃乐 开启 [群号] | 群聊/私聊 | 开启该群每日推送 |
| /桃乐 关闭 [群号] | 群聊/私聊 | 关闭该群每日推送 |
| /桃乐 群列表 | 群聊/私聊 | 查看推送群及开关状态 |

## 歌单

歌单在 `nonebot_plugin_taozi_music/resources/songs.yaml`，每条记录：

```yaml
- id: 1
  title: 歌名
  bv: BVxxxxx        # 来源视频
  part: 2            # 可选：分P序号（多P录播视频）；省略表示取视频第一P
  start: "12:30"     # 可选：唱歌开始时间（录播片段）
  end: "14:05"       # 可选：唱歌结束时间；与 start 成对出现
  note: 来源说明
```

切片 UP 主切好的唱歌视频省略 start/end（整段即歌）；多P录播视频用 part 指定要取的分P（1 开始计数）。欢迎 PR 补充更多歌。

## 常见问题

### 发送语音时报「语音转换失败, 请检查语音文件是否正常」（retcode 1200）

这个报错的真正原因通常不是音频文件坏了，而是**协议端读不到音频文件**。已在 v0.2.1 根治：语音改为 base64 内联发送，协议端（NapCat 等）不再读取 bot 机器上的文件路径，以下问题全部不再出现。请升级：

```bash
pip install -U nonebot-plugin-taozi-music
```

<details>
<summary>如果你还在用 v0.2.0 或更早版本（file:// 路径发送），可能踩到的三层坑</summary>

当时插件发送的是 `MessageSegment.record("file:///bot机器上的路径")`，需要协议端自己去读这个文件。在 macOS 上实际踩到过三层问题：

1. **bot 机器缺 ffmpeg**：音频转码直接失败。安装原生 ffmpeg（如 arm64 版）即可。
2. **NapCat 的 ffmpeg 原生组件未加载**：macOS 对未签名的 `ffmpegAddon.darwin.arm64.node` 会拦截，需要补 adhoc 签名后重启 QQ。
3. **QQ 沙盒拦截**：macOS 版 QQ 带沙盒，读不了插件缓存目录里的 mp3。绕过方法：把语音缓存目录挪到沙盒允许读取的位置（如 `~/Downloads/qq_voice_cache/`），原位置放软链接，插件代码不用动：

   ```bash
   mkdir -p ~/Downloads/qq_voice_cache
   # 假设插件数据目录是 ~/Library/Application Support/nonebot2/nonebot_plugin_taozi_music
   mv "$HOME/Library/Application Support/nonebot2/nonebot_plugin_taozi_music/cache" ~/Downloads/qq_voice_cache/
   ln -s ~/Downloads/qq_voice_cache "$HOME/Library/Application Support/nonebot2/nonebot_plugin_taozi_music/cache"
   ```

**这些绕过只对旧版本有效。v0.2.1+ 使用 base64 内联发送，音频数据直接随消息传给协议端，不经过文件系统，换机器、Docker、沙盒都不受影响，上面的 workaround 全部不再需要。**

</details>

## 许可证

MIT
