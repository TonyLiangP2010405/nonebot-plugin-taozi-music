# 2026-11-18 曲库更新记录

两轮共追加 91 条可单独点播的歌切，曲库由 42 条增至 133 条。第一轮新增 19 条（编号 43–61），第二轮补录 72 条（编号 62–133）。

## 来源核验

使用 agent-reach 的 bili-cli 搜索视频，并通过其 `bili_cli.client.get_video_info` 读取完整元数据，核对主播主页、发布日、分P页码与 CID。以下三组视频均由「鸭鸭的呆毛」（UID 1989524）上传，简介均指向主播主页 <https://space.bilibili.com/6867955>。日期为北京时间的视频发布日期，不推定为演唱日期。

| 来源视频 | 发布日期 | 分P数量 |
|---|---|---:|
| [桃纸《沧海一声笑》《菊花台》《兰亭序》《丝路》《天下》](https://www.bilibili.com/video/BV1RAxE6VEdP/) | 2026-10-28 | 5 |
| [桃纸_《登神（GODS) 》《传奇永不熄\|Legends Never Die 》《RISE》 （rice饭来）](https://www.bilibili.com/video/BV1f5sp6tE4G/) | 2026-11-15 | 6 |
| [桃纸《麒麟》《来自天堂的魔鬼》《野火》《Poker Face》](https://www.bilibili.com/video/BV1b1s66cEUh/) | 2026-11-17 | 8 |

视频总标题未必列出所有曲目，按实际分P收录。例如《登神》所在视频共有六P，含标题未列出的《ENEMY》《Numb》《We Are the Champions》；11 月 17 日的合集在两次核验之间调换了前两个分P。已按 CID 将 54 号《雨爱》指向 P2，55 号《耀斑》指向 P1。

## 第一轮新增

下列时长为来源分P时长，可能包含少量开场或结束讲话。每条使用独立的 `part`，不把多P视频当作一个连续音频。

2026-11-18 通过 B站播放接口逐一核验，这 19 个分P均返回 DASH 音频流。本次未执行 QQ 语音发送实测。

| 编号 | 歌曲 | 来源分P | 时长 | CID（核验时） |
|---:|---|---|---:|---:|
| 43 | 沧海一声笑 | [BV1RAxE6VEdP P1](https://www.bilibili.com/video/BV1RAxE6VEdP/?p=1) | 2:44 | 43126687409 |
| 44 | 菊花台 | [BV1RAxE6VEdP P2](https://www.bilibili.com/video/BV1RAxE6VEdP/?p=2) | 4:22 | 43125312145 |
| 45 | 兰亭序 | [BV1RAxE6VEdP P3](https://www.bilibili.com/video/BV1RAxE6VEdP/?p=3) | 4:14 | 43125441541 |
| 46 | 丝路 | [BV1RAxE6VEdP P4](https://www.bilibili.com/video/BV1RAxE6VEdP/?p=4) | 4:56 | 43126557906 |
| 47 | 天下 | [BV1RAxE6VEdP P5](https://www.bilibili.com/video/BV1RAxE6VEdP/?p=5) | 3:41 | 43126752708 |
| 48 | 登神（GODS） | [BV1f5sp6tE4G P1](https://www.bilibili.com/video/BV1f5sp6tE4G/?p=1) | 3:38 | 43630332878 |
| 49 | 宿敌（ENEMY） | [BV1f5sp6tE4G P2](https://www.bilibili.com/video/BV1f5sp6tE4G/?p=2) | 2:48 | 43630922066 |
| 50 | Legends Never Die | [BV1f5sp6tE4G P3](https://www.bilibili.com/video/BV1f5sp6tE4G/?p=3) | 3:43 | 43629742886 |
| 51 | Numb | [BV1f5sp6tE4G P4](https://www.bilibili.com/video/BV1f5sp6tE4G/?p=4) | 2:45 | 43630005339 |
| 52 | RISE | [BV1f5sp6tE4G P5](https://www.bilibili.com/video/BV1f5sp6tE4G/?p=5) | 3:06 | 43629348435 |
| 53 | We Are the Champions | [BV1f5sp6tE4G P6](https://www.bilibili.com/video/BV1f5sp6tE4G/?p=6) | 3:03 | 43629609062 |
| 54 | 雨爱 | [BV1b1s66cEUh P2](https://www.bilibili.com/video/BV1b1s66cEUh/?p=2) | 4:20 | 43689708548 |
| 55 | 耀斑 | [BV1b1s66cEUh P1](https://www.bilibili.com/video/BV1b1s66cEUh/?p=1) | 3:32 | 43689773014 |
| 56 | 麒麟 | [BV1b1s66cEUh P3](https://www.bilibili.com/video/BV1b1s66cEUh/?p=3) | 3:08 | 43689641663 |
| 57 | Poker Face | [BV1b1s66cEUh P4](https://www.bilibili.com/video/BV1b1s66cEUh/?p=4) | 3:39 | 43689705761 |
| 58 | 不眠之夜 | [BV1b1s66cEUh P5](https://www.bilibili.com/video/BV1b1s66cEUh/?p=5) | 2:21 | 43689837783 |
| 59 | 来自天堂的魔鬼 | [BV1b1s66cEUh P6](https://www.bilibili.com/video/BV1b1s66cEUh/?p=6) | 4:06 | 43689840195 |
| 60 | 鲜花 | [BV1b1s66cEUh P7](https://www.bilibili.com/video/BV1b1s66cEUh/?p=7) | 7:44 | 43689906138 |
| 61 | 野火 | [BV1b1s66cEUh P8](https://www.bilibili.com/video/BV1b1s66cEUh/?p=8) | 3:51 | 43690035427 |

## 第二轮补录

从公开歌切和歌会合集补录 72 条，编号 62–133。对已有合集只补此前没有独立条目的分P，并避开疑似同一演唱的转载。分P标题为闲聊、AI 翻唱或听原唱的片段未收录。新条目均查到 DASH 音频流。

| 编号 | 歌曲 | 来源 | 切片 UP 主 | 时长 | CID（核验时） |
|---:|---|---|---|---:|---:|
| 62 | 红莲华（桃纸11.10 歌回） | [BV1xMWu6wEaX P1](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=1) | 鸭鸭的呆毛 | 4:36 | 43498868456 |
| 63 | 心湖（桃纸11.10 歌回） | [BV1xMWu6wEaX P3](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=3) | 鸭鸭的呆毛 | 4:37 | 43489952244 |
| 64 | 下雨天（桃纸11.10 歌回） | [BV1xMWu6wEaX P4](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=4) | 鸭鸭的呆毛 | 4:09 | 43489953673 |
| 65 | What Can I Do（桃纸11.10 歌回） | [BV1xMWu6wEaX P5](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=5) | 鸭鸭的呆毛 | 2:02 | 43490018543 |
| 66 | 光辉岁月（桃纸11.10 歌回） | [BV1xMWu6wEaX P6](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=6) | 鸭鸭的呆毛 | 4:39 | 43490018929 |
| 67 | 说散就散（桃纸11.10 歌回） | [BV1xMWu6wEaX P7](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=7) | 鸭鸭的呆毛 | 3:56 | 43490804423 |
| 68 | Reflection（桃纸11.10 歌回） | [BV1xMWu6wEaX P8](https://www.bilibili.com/video/BV1xMWu6wEaX/?p=8) | 鸭鸭的呆毛 | 4:34 | 43490806108 |
| 69 | 月半小夜曲（桃纸歌回） | [BV1Zv7H6zEDS P1](https://www.bilibili.com/video/BV1Zv7H6zEDS/?p=1) | 鸭鸭的呆毛 | 4:45 | 39686242615 |
| 70 | 王妃（桃纸歌回） | [BV1Zv7H6zEDS P2](https://www.bilibili.com/video/BV1Zv7H6zEDS/?p=2) | 鸭鸭的呆毛 | 3:40 | 39455623214 |
| 71 | 悟空（桃纸歌回） | [BV1Zv7H6zEDS P3](https://www.bilibili.com/video/BV1Zv7H6zEDS/?p=3) | 鸭鸭的呆毛 | 3:01 | 39455557827 |
| 72 | 突然好想你（桃纸歌回） | [BV1Zv7H6zEDS P4](https://www.bilibili.com/video/BV1Zv7H6zEDS/?p=4) | 鸭鸭的呆毛 | 4:22 | 39455623347 |
| 73 | 男孩（桃纸歌回） | [BV1Zv7H6zEDS P6](https://www.bilibili.com/video/BV1Zv7H6zEDS/?p=6) | 鸭鸭的呆毛 | 4:55 | 39677857596 |
| 74 | 月亮之上（桃纸歌回） | [BV1Zv7H6zEDS P7](https://www.bilibili.com/video/BV1Zv7H6zEDS/?p=7) | 鸭鸭的呆毛 | 3:56 | 39686242425 |
| 75 | 发如雪（桃纸live） | [BV1HYnh6CEiH](https://www.bilibili.com/video/BV1HYnh6CEiH/) | 魚鰐 | 4:53 | 42986507429 |
| 76 | 山海（桃纸live） | [BV1MrnR6xELH](https://www.bilibili.com/video/BV1MrnR6xELH/) | Saturniy | 5:17 | 43071569981 |
| 77 | 你是我的眼（桃纸live） | [BV1UqxK6aE4t](https://www.bilibili.com/video/BV1UqxK6aE4t/) | 高能游戏眼 | 5:59 | 43086318331 |
| 78 | 月光（桃纸live） | [BV1peGm6BEbR](https://www.bilibili.com/video/BV1peGm6BEbR/) | 双刀纸袋布 | 5:26 | 38659689710 |
| 79 | 煎熬（桃纸live） | [BV1Kz7a6mE8X](https://www.bilibili.com/video/BV1Kz7a6mE8X/) | 鸭鸭的呆毛 | 4:14 | 39401622716 |
| 80 | 丑八怪（桃纸live） | [BV1f4ZXBoEdP](https://www.bilibili.com/video/BV1f4ZXBoEdP/) | 嗤纸条 | 3:28 | 36143041110 |
| 81 | 爱错（桃纸live） | [BV1p5f3BUEFR](https://www.bilibili.com/video/BV1p5f3BUEFR/) | 嗤纸条 | 3:48 | 36180790883 |
| 82 | 麒麟（巴老师×桃纸合唱版） | [BV1P9riB7EfV](https://www.bilibili.com/video/BV1P9riB7EfV/) | 鸭鸭的呆毛 | 3:00 | 35349597950 |
| 83 | New Boy（桃纸live） | [BV1SXr6BeEte](https://www.bilibili.com/video/BV1SXr6BeEte/) | 寒洛茗 | 4:03 | 35425878983 |
| 84 | 麒麟（丝茉茉生日会桃纸独唱版） | [BV1VYJU6CEeT](https://www.bilibili.com/video/BV1VYJU6CEeT/) | 记录园长的芋头 | 3:51 | 42774171101 |
| 85 | 红色高跟鞋（桃纸歌切） | [BV1LdtU6TEgr P2](https://www.bilibili.com/video/BV1LdtU6TEgr/?p=2) | 鸭鸭的呆毛 | 3:24 | 41524923132 |
| 86 | Let It Go（桃纸歌切） | [BV1NBh56aEMn P3](https://www.bilibili.com/video/BV1NBh56aEMn/?p=3) | 鸭鸭的呆毛 | 3:41 | 41256420140 |
| 87 | 想你的夜（桃纸歌切） | [BV1NBh56aEMn P4](https://www.bilibili.com/video/BV1NBh56aEMn/?p=4) | 鸭鸭的呆毛 | 4:19 | 41255634909 |
| 88 | 连名带姓（桃纸歌切） | [BV1NBh56aEMn P5](https://www.bilibili.com/video/BV1NBh56aEMn/?p=5) | 鸭鸭的呆毛 | 4:49 | 41255963708 |
| 89 | 花海（桃纸歌切） | [BV1NBh56aEMn P6](https://www.bilibili.com/video/BV1NBh56aEMn/?p=6) | 鸭鸭的呆毛 | 4:23 | 41256157961 |
| 90 | Wrecking Ball（桃纸歌切） | [BV1NBh56aEMn P7](https://www.bilibili.com/video/BV1NBh56aEMn/?p=7) | 鸭鸭的呆毛 | 3:33 | 41256554201 |
| 91 | Rolling in the Deep（桃纸歌切） | [BV1NBh56aEMn P8](https://www.bilibili.com/video/BV1NBh56aEMn/?p=8) | 鸭鸭的呆毛 | 3:45 | 41257599951 |
| 92 | 灰色头像（桃纸歌切） | [BV1NBh56aEMn P9](https://www.bilibili.com/video/BV1NBh56aEMn/?p=9) | 鸭鸭的呆毛 | 4:45 | 41257731503 |
| 93 | 甲乙丙丁（桃纸歌切） | [BV1NBh56aEMn P10](https://www.bilibili.com/video/BV1NBh56aEMn/?p=10) | 鸭鸭的呆毛 | 3:29 | 41257864830 |
| 94 | 你把我灌醉（桃纸歌切） | [BV1JBq6BgEwD P3](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=3) | 鸭鸭的呆毛 | 4:42 | 34869742743 |
| 95 | 杀死那个石家庄人（桃纸歌切） | [BV1JBq6BgEwD P4](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=4) | 鸭鸭的呆毛 | 5:20 | 34870068628 |
| 96 | 你要跳舞吗（桃纸歌切） | [BV1JBq6BgEwD P5](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=5) | 鸭鸭的呆毛 | 3:12 | 34870070873 |
| 97 | 水星记（桃纸歌切） | [BV1JBq6BgEwD P6](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=6) | 鸭鸭的呆毛 | 5:06 | 34911620084 |
| 98 | 凄美地（桃纸歌切） | [BV1JBq6BgEwD P7](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=7) | 鸭鸭的呆毛 | 4:08 | 34911683368 |
| 99 | Christmas In My Heart（桃纸歌切） | [BV1JBq6BgEwD P9](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=9) | 鸭鸭的呆毛 | 4:45 | 34953692756 |
| 100 | 圣诞结（桃纸歌切） | [BV1JBq6BgEwD P10](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=10) | 鸭鸭的呆毛 | 4:01 | 35036663685 |
| 101 | Dear John（桃纸歌切） | [BV1JBq6BgEwD P11](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=11) | 鸭鸭的呆毛 | 5:07 | 35036727525 |
| 102 | 烟火里的尘埃（桃纸歌切） | [BV1JBq6BgEwD P13](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=13) | 鸭鸭的呆毛 | 5:10 | 35038692305 |
| 103 | 光年之外（桃纸歌切） | [BV1JBq6BgEwD P14](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=14) | 鸭鸭的呆毛 | 3:57 | 35038694138 |
| 104 | 我多想拥抱你（桃纸歌切） | [BV1JBq6BgEwD P16](https://www.bilibili.com/video/BV1JBq6BgEwD/?p=16) | 鸭鸭的呆毛 | 3:55 | 35039546138 |
| 105 | for ya（桃纸歌会） | [BV1rVXsBNEwJ P2](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=2) | 寒洛茗 | 2:13 | 36999727771 |
| 106 | 火红的萨日朗（桃纸歌会） | [BV1rVXsBNEwJ P5](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=5) | 寒洛茗 | 4:01 | 36999988118 |
| 107 | 站在草原望北京（桃纸歌会） | [BV1rVXsBNEwJ P6](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=6) | 寒洛茗 | 4:19 | 37000056426 |
| 108 | 素颜（桃纸歌会） | [BV1rVXsBNEwJ P10](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=10) | 寒洛茗 | 4:19 | 37001494615 |
| 109 | 有何不可（桃纸歌会） | [BV1rVXsBNEwJ P11](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=11) | 寒洛茗 | 3:59 | 37001691638 |
| 110 | 左手指月（桃纸歌会） | [BV1rVXsBNEwJ P12](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=12) | 寒洛茗 | 3:45 | 37001888266 |
| 111 | 晴天（桃纸歌会） | [BV1rVXsBNEwJ P13](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=13) | 寒洛茗 | 4:28 | 37002084667 |
| 112 | 孤单北半球（桃纸歌会） | [BV1rVXsBNEwJ P14](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=14) | 寒洛茗 | 4:02 | 37002608785 |
| 113 | 她的睫毛（桃纸歌会） | [BV1rVXsBNEwJ P15](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=15) | 寒洛茗 | 3:48 | 37003071022 |
| 114 | 宝贝（桃纸歌会） | [BV1rVXsBNEwJ P18](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=18) | 寒洛茗 | 2:21 | 37003792216 |
| 115 | 走马（桃纸歌会） | [BV1rVXsBNEwJ P19](https://www.bilibili.com/video/BV1rVXsBNEwJ/?p=19) | 寒洛茗 | 3:53 | 37003920016 |
| 116 | APT.（桃纸歌切） | [BV1L4fcYnEqn P5](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=5) | 三绿一百盒 | 2:29 | 29190455908 |
| 117 | Love Story（桃纸歌切） | [BV1L4fcYnEqn P7](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=7) | 三绿一百盒 | 3:53 | 29190456092 |
| 118 | 给你呀（桃纸歌切） | [BV1L4fcYnEqn P8](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=8) | 三绿一百盒 | 2:29 | 29190456266 |
| 119 | 不能说的秘密（桃纸歌切） | [BV1L4fcYnEqn P9](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=9) | 三绿一百盒 | 4:46 | 29190456167 |
| 120 | 反方向的钟（桃纸歌切） | [BV1L4fcYnEqn P11](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=11) | 三绿一百盒 | 4:12 | 29190456128 |
| 121 | 枫（桃纸歌切） | [BV1L4fcYnEqn P12](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=12) | 三绿一百盒 | 4:25 | 29190456139 |
| 122 | 告白气球（桃纸歌切） | [BV1L4fcYnEqn P13](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=13) | 三绿一百盒 | 3:31 | 29190456260 |
| 123 | 勾指起誓（桃纸歌切） | [BV1L4fcYnEqn P14](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=14) | 三绿一百盒 | 2:59 | 29190456272 |
| 124 | 关于夜晚和失眠的世界（桃纸歌切） | [BV1L4fcYnEqn P15](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=15) | 三绿一百盒 | 5:43 | 29190456276 |
| 125 | 坏女孩（桃纸歌切） | [BV1L4fcYnEqn P17](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=17) | 三绿一百盒 | 4:00 | 29190456294 |
| 126 | 没有理想的人不伤心（桃纸歌切） | [BV1L4fcYnEqn P18](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=18) | 三绿一百盒 | 5:39 | 29190456395 |
| 127 | 贤良（桃纸歌切） | [BV1L4fcYnEqn P20](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=20) | 三绿一百盒 | 5:32 | 29190456487 |
| 128 | 找自己（桃纸歌切） | [BV1L4fcYnEqn P21](https://www.bilibili.com/video/BV1L4fcYnEqn/?p=21) | 三绿一百盒 | 5:05 | 29190456549 |
| 129 | 理想（桃纸歌切） | [BV1GitV6PEJY P3](https://www.bilibili.com/video/BV1GitV6PEJY/?p=3) | 鸭鸭的呆毛 | 4:36 | 41496478912 |
| 130 | 怎么说我不爱你（桃纸歌切） | [BV1rTckzrE5H P3](https://www.bilibili.com/video/BV1rTckzrE5H/?p=3) | 鸭鸭的呆毛 | 4:32 | 36649896751 |
| 131 | Lemon Tree（桃纸歌切） | [BV1rTckzrE5H P4](https://www.bilibili.com/video/BV1rTckzrE5H/?p=4) | 鸭鸭的呆毛 | 3:09 | 36649960741 |
| 132 | Lovin' You（桃纸海豚音） | [BV1wcb163E9Y P2](https://www.bilibili.com/video/BV1wcb163E9Y/?p=2) | 鸭鸭的呆毛 | 3:08 | 40937587103 |
| 133 | Посвящение（桃纸海豚音） | [BV1wcb163E9Y P3](https://www.bilibili.com/video/BV1wcb163E9Y/?p=3) | 鸭鸭的呆毛 | 1:56 | 40937979919 |
