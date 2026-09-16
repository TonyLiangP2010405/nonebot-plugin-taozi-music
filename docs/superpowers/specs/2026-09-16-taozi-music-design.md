# nonebot-plugin-taozi-music 设计文档

日期：2026-09-16

## 1. 插件定位

NoneBot2 插件：每天定时在 QQ 群里以**语音条**形式播放主播「小小桃子呦」（B站 UID 6867955）唱过的歌，同时支持命令点歌。

核心约束：

- 必须是该主播本人演唱的片段
- 每天播放不同的歌（随机不重复，播完一轮后重置）
- 只下载音频不下载视频，且只保留唱歌片段（按时间戳裁剪），节省空间
- 播放使用 OneBot V11 的 record 消息段（QQ 语音条），不发文件

## 2. 歌源策略

- **主**：收集 B 站上切片 UP 主切好的唱歌视频（整段即整首歌，无需时间戳）
- **辅**：从她自己的视频/录播中手工标注唱歌时间段（BV 号 + 起止时间）
- 初始歌单由开发时联网调研收集，写入 `resources/songs.yaml` 随仓库分发，后续可持续补充

## 3. 数据文件：songs.yaml

每首歌一条记录：

```yaml
- id: 1                  # 整数编号，用于点歌
  title: 歌名
  bv: BVxxxxx            # 来源视频 BV 号
  start: "12:30"         # 唱歌开始时间（秒数或 mm:ss）；切片视频省略表示整段
  end: "14:05"           # 唱歌结束时间；与 start 成对出现或同时省略
  note: "来源说明"        # 可选，如切片 UP 主名
```

校验规则：

- id 全局唯一；title、bv 必填
- start/end 要么同时存在要么同时省略；end 必须大于 start
- 文件损坏或校验失败时插件 import 不失败，加载歌单时记录错误并对命令返回友好提示

## 4. 模块划分

```
nonebot_plugin_taozi_music/
├── __init__.py        # PluginMetadata、加载入口
├── config.py          # 配置项
├── library.py         # 歌单加载/校验、播放历史持久化、随机不重复选歌
├── audio.py           # yt-dlp 下载音频 + ffmpeg 裁剪 + 缓存管理
├── commands.py        # 命令处理
├── scheduler.py       # 每日定时推送（nonebot-plugin-apscheduler）
└── resources/
    └── songs.yaml     # 初始歌单
```

### library.py

- 加载并校验 songs.yaml
- 播放历史存插件 data 目录下的 `history.json`（已播 id 列表）
- 选歌：从未播过的歌中随机选；全部播过后重置历史重新开始
- 提供按 id / 按标题模糊查找

### audio.py

- 缓存目录：`data/cache/{id}.mp3`，命中缓存直接使用
- 未命中：调用 `yt-dlp -x --audio-format mp3` 只下载音频到临时文件
- 若有 start/end：调用 `ffmpeg -ss start -to end -i ...` 裁剪
- 产物移入缓存目录；下载/裁剪失败抛出自定义异常，命令层给出友好提示
- yt-dlp / ffmpeg 不存在时，加载不报错，执行播放命令时提示缺少依赖
- 阻塞子进程调用使用 `asyncio.create_subprocess_exec`，不阻塞事件循环

### commands.py

| 指令 | 权限 | 范围 | 说明 |
|---|---|---|---|
| /桃乐 | 所有人 | 群聊 | 随机放一首（与定时推送同一选歌逻辑，计入历史） |
| /桃乐 歌单 | 所有人 | 群聊/私聊 | 列出歌曲编号与歌名 |
| /桃乐 点歌 <编号或歌名> | 所有人 | 群聊/私聊 | 播放指定歌曲（不计入每日历史或计入，见实现备注） |
| /桃乐 时间 HH:MM | 管理员(SUPERUSER) | 群聊/私聊 | 修改每日播放时间，持久化到 data 目录 |

发送方式：`MessageSegment.record(cache_file)`，依赖 NapCat/Lagrange 等协议端自动转码为 QQ 语音。发送失败时提示可能协议端不支持语音。

### scheduler.py

- `require("nonebot_plugin_apscheduler")` 后使用其 scheduler
- 每天到配置时间向配置的群推送一首（随机不重复）
- 播放时间可被命令修改，修改后更新 cron 任务并持久化

## 5. 配置项（config.py）

| 配置 | 默认值 | 说明 |
|---|---|---|
| taozi_music_groups | [] | 每日推送的群号列表，空则不定时推送 |
| taozi_music_send_time | "21:00" | 每日播放时间（初始值，可被命令修改） |

配置项均有默认值，缺配置不影响 import。

## 6. 依赖

- nonebot2 >= 2.2.0
- nonebot-adapter-onebot >= 2.4.0
- nonebot-plugin-apscheduler
- httpx（备用网络请求）
- 外部命令：yt-dlp、ffmpeg（README 中说明安装方式）

## 7. 错误处理

- 歌单文件缺失/损坏：import 不失败，命令返回「歌单不可用」提示
- 下载失败：提示该首歌下载失败，不影响其他歌
- 协议端不支持语音：捕获发送异常，提示检查协议端
- 空参数、错误参数均有提示；不向用户暴露 traceback

## 8. 测试

- pytest + nonebug：插件加载测试
- 单测：songs.yaml 校验、随机不重复选歌、历史重置、标题模糊查找、时间格式解析
- 命令测试（mock Bot）：/桃乐、/桃乐 歌单、/桃乐 点歌、/桃乐 时间
- 不实际调用 yt-dlp（mock 掉），CI 环境无网络依赖

## 9. 初始歌单收集

开发阶段联网搜索「小小桃子呦 唱歌」「小小桃子呦 歌切」等关键词，收集切片 UP 主的唱歌视频与她本人视频中的唱歌片段，尽量多收，写入初始 songs.yaml。

## 10. 项目信息

- 项目名：nonebot-plugin-taozi-music
- 模块名：nonebot_plugin_taozi_music
- 适配器：OneBot V11
- Python >= 3.9，Poetry，MIT License
- 测试：pytest + nonebug；格式检查：ruff
