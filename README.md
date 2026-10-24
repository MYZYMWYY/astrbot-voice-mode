# 按需语音 · AstrBot 插件

让 Bot **默认不出声**，只有你叫它说话时才用语音回。

> 常开的 TTS 会变成噪音：每句都念一遍，长回复还要等十几秒。
> 这个插件把"什么时候出声"交给你。

## 两种触发

**1. 关键词（最省事）**

消息里出现 `语音`、`说给我听`、`念给我听` 等词，这一条就用语音回，发完自动关。

```
你：今天刷到啥好玩的，说给我听
Bot：（语音）
你：那明天呢
Bot：（文字）← 自动恢复
```

**2. 指令**

| 指令 | 作用 |
| --- | --- |
| `/voice on` | 之后每条都语音 |
| `/voice off` | 关掉 |
| `/voice once` | 只说下一条 |
| `/voice` | 看当前状态 |

## 为什么不用全局 TTS 开关

AstrBot 自带的 TTS 是"开就全读"，粒度太粗。这个插件用的是它内部的**会话级开关**（`SessionServiceManager`），所以：

- 只影响当前会话，不动全局配置
- 状态存在数据库里，重启不丢
- `once` 模式在消息发完后自动复位

## 安装

放到 `AstrBot/data/plugins/astrbot_plugin_voice_mode/`，重启 AstrBot。

还需要在 AstrBot 里配好一个 TTS 提供商（插件不负责合成语音，只负责开关）。免费的可以用 **Edge TTS**：装 `pip install edge-tts`，在服务提供商里加一个 `edge_tts` 类型的 provider。

## 配置

| 配置项 | 默认 | 说明 |
| --- | --- | --- |
| `scope_prefix` | 空 | 只在这个 UMO 前缀的会话生效 |
| `keywords` | 见下 | 触发语音的关键词列表，可自定义 |

内置关键词：`语音`、`说给我听`、`念给我听`、`读给我听`、`用声音`、`出个声`、`说话给我听`

## 排查：关键词命中了，但只回文字不出声

按这个顺序查，能省一晚上。

### 1. TTS 提供商在"这个会话的配置档案"里真的启用了吗

> 这是最容易踩的坑，我自己就栽过。

AstrBot 支持**多套配置档案**（不同人格、不同 QQ 号可以用不同配置）。`provider_tts_settings` 和 provider 列表是**按档案分开存的**——只改默认配置没用，你的会话走的是自己那份档案。

检查面板 → 配置管理 → 逐个档案确认三件事：

- `provider_tts_settings.enable = true`
- `provider_tts_settings.provider_id` 指向一个真实存在的提供商
- 该档案的 **provider 列表里也有这个 TTS 提供商**（只改上面两项、列表里没有，照样找不到）

默认配置和档案的路径分别在：

```
AstrBot/data/cmd_config.json                  ← 默认
AstrBot/data/config/abconf_<uuid>.json        ← 各个档案
```

### 2. edge-tts 需要 ffmpeg

`edge_tts` 提供商生成 mp3 后要转成 wav，这一步**调用 ffmpeg**。系统里没有的话会失败（日志里是"音频生成失败"，不是"没装 TTS"）。

Windows 上最省事的做法：

```bash
pip install pyffmpeg
```

它自带一个 flac/ffmpeg 二进制，装完把 `C:\Users\<你>\.pyffmpeg\bin` 加进 PATH 即可。或者直接装系统版 ffmpeg。

### 3. 看日志确认卡在哪一环

正常应该出现：

```
TTS status for session ... was updated to enabled.
TTS request: ...
TTS result: .../edge_tts_xxxx.wav
```

| 日志现象 | 说明 |
| --- | --- |
| 有 `enabled`，没有 `TTS request` | 提供商没取到 → 回第 1 步 |
| 有 `TTS request`，报"音频生成失败" | ffmpeg 缺失或边缘服务不通 → 第 2 步 |
| 有 `TTS result`，但 QQ 没收到语音 | 平台侧发送问题，跟插件无关 |

### 4. 别信 Bot 说"我没有 TTS 工具"

TTS 是框架层在回复后自动做的，**不在模型可调用的工具列表里**。被问到时模型看不见这个能力，会编一个"我没有能出声的工具"之类听起来很合理的解释——那是猜的，不是事实。以日志为准。

## 注意

- 关键词是**字面匹配**。你说"我用语音输入法发的"也会触发——把那个词从列表里删掉就行。
- 这个插件只管"出不出声"，音色、语速在 TTS 提供商那边配。

## License

MIT
