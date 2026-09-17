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
  part: 2                # 可选，分P序号（1 起）；多P录播指定要取的分P，省略表示第一P
  start: "12:30"         # 唱歌开始时间（秒数或 mm:ss）；切片视频省略表示整段
  end: "14:05"           # 唱歌结束时间；与 start 成对出现或同时省略
  note: "来源说明"        # 可选，如切片 UP 主名
```

校验规则：

- id 全局唯一；title、bv 必填
- part 可选；填写时必须 >= 1，音频下载按该分P 的 cid 取流
- start/end 要么同时存在要么同时省略；end 必须大于 start
- 文件损坏或校验失败时插件 import 不失败，加载歌单时记录错误并对命令返回友好提示

## 4. 模块划分

```
nonebot_plugin_taozi_music/
├── __init__.py        # PluginMetadata、加载入口
├── config.py          # 配置项
├── library.py         # 歌单加载/校验、播放历史持久化、随机不重复选歌
├── audio.py           # B站 API 下载音频 + ffmpeg 裁剪 + 缓存管理
├── commands.py        # 命令处理（点歌/歌单/时间/推送群管理）
├── scheduler.py       # 每日定时推送（nonebot-plugin-apscheduler）
├── settings.py        # settings.json 统一管理（推送时间、推送群开关）
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
- 未命中：经 B站官方 API 下载音频流（httpx：view 接口取 cid（song 带 part 时按分P 页码从 `data.pages` 取对应 cid）→ playurl `fnval=16` 取 DASH 最高码率音频 → 带 UA/Referer 下载 m4a 到临时文件；先访问首页拿 cookie 避免 412 风控）
- 用 ffmpeg 转码为 mp3；若有 start/end 同时按时间戳裁剪（`-ss`/`-to` 输出选项）
- 产物写入缓存目录；下载/裁剪失败抛出自定义异常，命令层给出友好提示
- ffmpeg 不存在时，加载不报错，执行播放命令时提示缺少依赖
- 不使用 yt-dlp：B站风控 412 已全面拦截（2026-09-16 实测确认）
- 阻塞子进程调用使用 `asyncio.create_subprocess_exec`，不阻塞事件循环

### commands.py

所有命令仅 SUPERUSER 可用（`permission=SUPERUSER`），非管理员触发时不响应。

| 指令 | 范围 | 说明 |
|---|---|---|
| /桃乐 | 群聊 | 随机放一首（与定时推送同一选歌逻辑，计入历史） |
| /桃乐 歌单 | 群聊/私聊 | 列出歌曲编号与歌名 |
| /桃乐 点歌 <编号或歌名> | 群聊/私聊 | 播放指定歌曲（同样计入播放历史，避免每日推送重复） |
| /桃乐 时间 HH:MM | 群聊/私聊 | 修改每日播放时间，持久化到 data 目录 |
| /桃乐 加群 [群号] | 群聊/私聊 | 加入每日推送并开启（私聊必须显式带群号；群聊省略群号时操作当前群） |
| /桃乐 删群 [群号] | 群聊/私聊 | 移出每日推送 |
| /桃乐 开启 [群号] | 群聊/私聊 | 开启该群每日推送 |
| /桃乐 关闭 [群号] | 群聊/私聊 | 关闭该群每日推送 |
| /桃乐 群列表 | 群聊/私聊 | 查看推送群及开关状态 |

发送方式：`MessageSegment.record(cache_file)`，依赖 NapCat/Lagrange 等协议端自动转码为 QQ 语音。发送失败时提示可能协议端不支持语音。

### scheduler.py

- `require("nonebot_plugin_apscheduler")` 后使用其 scheduler
- 每天到配置时间向 settings.json 中开启状态的群推送一首（随机不重复）
- 推送流程：先连发 5 条「警告！！！即将开始发送今日的桃歌」，再发送语音条；不再发送标题文本
- 群列表来自 `settings.get_groups`，只取开启状态的群
- 播放时间可被命令修改，修改后更新 cron 任务并持久化

### settings.py

统一读写 data 目录下的 `settings.json`：

```json
{"send_time": "21:30 或 null", "groups": {"123456": true, "789012": false}}
```

- 提供 load/save/get/set 接口：`load_settings`、`save_settings`、`get_send_time`、`set_send_time`、`get_groups`、`add_group`、`remove_group`、`set_group_enabled`
- 兼容旧格式（只有 `send_time` 没有 `groups`）
- 加载时清洗数据：groups 的 key 强转 int、value 必须为 bool，坏条目丢弃并记录警告；非法 send_time 重置为 None
- `add_group` 已存在时不覆盖原状态；`remove_group`/`set_group_enabled` 对不存在的群返回 False

## 5. 配置项（config.py）

| 配置 | 默认值 | 说明 |
|---|---|---|
| taozi_music_groups | [] | 每日推送群号的初始列表，启动时写入 data/settings.json（已存在的群不覆盖状态），之后用命令管理；为空则不初始化 |
| taozi_music_send_time | "21:00" | 每日播放时间（初始值，可被命令修改） |

配置项均有默认值，缺配置不影响 import。启动时会把 `taozi_music_groups` 里的群逐个加入 settings.json，推送群与播放时间此后统一由 settings.json 管理。

## 6. 依赖

- nonebot2 >= 2.2.0
- nonebot-adapter-onebot >= 2.4.0
- nonebot-plugin-apscheduler
- nonebot-plugin-localstore（插件数据目录：缓存、播放历史、设置）
- PyYAML
- httpx >= 0.27（B站 API 音频下载）
- 外部命令：ffmpeg（README 中说明安装方式）

## 7. 错误处理

- 歌单文件缺失/损坏：import 不失败，命令返回「歌单不可用」提示
- 下载失败：提示该首歌下载失败，不影响其他歌
- 协议端不支持语音：捕获发送异常，提示检查协议端
- 空参数、错误参数均有提示；不向用户暴露 traceback

## 8. 测试

- pytest + nonebug：插件加载测试
- 单测：songs.yaml 校验、随机不重复选歌、历史重置、标题模糊查找、时间格式解析、settings.json 读写/兼容/坏条目清洗
- 命令测试（mock Bot）：/桃乐、/桃乐 歌单、/桃乐 点歌、/桃乐 时间、推送群管理命令（群聊/私聊）
- 定时推送测试：monkeypatch Bot/歌单/音频，断言警告文本×5 + 语音、关闭的群不推送
- 下载/网络部分用 httpx MockTransport 测试，不实际访问网络，CI 环境无网络依赖

## 9. 初始歌单收集

开发阶段联网搜索「小小桃子呦 唱歌」「小小桃子呦 歌切」等关键词，收集切片 UP 主的唱歌视频与她本人视频中的唱歌片段，尽量多收，写入初始 songs.yaml。

## 10. 项目信息

- 项目名：nonebot-plugin-taozi-music
- 模块名：nonebot_plugin_taozi_music
- 适配器：OneBot V11
- Python >= 3.9，Poetry，MIT License
- 测试：pytest + nonebug；格式检查：ruff

## 11. 2026-09-16 v0.2 更新

- 新增命令管理推送群（仅 SUPERUSER，私聊可用）：加群/删群/开启/关闭/群列表；群聊省略群号时操作当前群，私聊必须显式带群号
- 新增 `settings.py` 统一管理 data 目录 `settings.json`（推送群开关 + 每日播放时间），兼容 0.1 的纯 `send_time` 旧格式
- 每日推送流程改为：向开启状态的群先连发 5 条「警告！！！即将开始发送今日的桃歌」，再发送语音条；不再发送标题文本
- 启动时把配置 `taozi_music_groups` 作为初始群列表写入 settings.json（已存在的群不覆盖状态）
- 版本号升至 0.2.0
