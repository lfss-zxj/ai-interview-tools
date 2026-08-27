# VoxRibbon（声幕）

[![CI](https://github.com/lfss-zxj/ai-interview-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/lfss-zxj/ai-interview-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)](DEPLOYMENT.md)

![VoxRibbon AI 面试助手封面](assets/cover-4x3.png)

**VoxRibbon** 是一款专为远程面试设计的开源桌面工具，它通过 **WASAPI Loopback** 捕获系统音频，利用本地 **Paraformer** 模型实现低延迟中文语音识别，并通过悬浮窗口（Overlay）实时显示字幕和 AI 生成的回答。

## ✨ 核心特性

- **💰 完全免费开源**：VoxRibbon 本身完全免费，本地语音识别与桌面字幕功能不收取任何费用；只有主动启用 DeepSeek AI 时，API 调用会由服务商按实际用量计费。
- **🔒 极致隐私**：仅在本地运行 ASR 引擎，只有定稿后的文本才会发送给 AI。支持 `Ctrl+Alt+H` “老板键”一键隐藏悬浮窗，后台服务继续运行。
- **🚀 本地化 ASR**：基于 FunASR/Paraformer Streaming，无需麦克风，直接捕获系统播放的声音，识别速度快，支持离线基础功能。
- **💬 流式 AI 对话**：集成 DeepSeek API，支持 SSE 流式输出。AI 会根据语境自动合并语音片段，提供连续的面试辅助回答。
- **🎨 高度可定制**：WPF 驱动的悬浮窗支持拖拽、缩放、透明度过渡。所有设置通过本地 Web 界面 (`http://127.0.0.1:8765`) 管理，无需重启。
- **🛡️ 安全设计**：API Key 使用 Windows DPAPI 加密存储，设置页仅允许本机访问，日志不记录敏感信息。

[NoTrack AI — https://notrack.ai/](https://notrack.ai/)

```text
系统播放声音 → WASAPI Loopback → 16 kHz PCM → Paraformer Streaming
                                              ↓
桌面字幕 Overlay ← WebSocket partial / final ←┘
       ↓
连续对话上下文 → DeepSeek SSE 流式回答
```

这个服务只采集 Windows 当前播放设备的系统声音，不采集麦克风。WASAPI loopback 音频先下混为单声道，再通过有状态 SoXR 重采样为 16 kHz PCM，交给 Paraformer 中文流式模型，最后把中文增量文本推送到 WebSocket。

## 安装与启动

需要 Windows 10/11 和 64 位 Python 3.11。PowerShell 进入本目录：

```powershell
# NVIDIA 显卡（推荐）
.\install.ps1 -Cuda

# 或 CPU 版
.\install.ps1 -Cpu

# 安装完成后一键启动 ASR 与 Overlay
.\launch.ps1
```

首次启动会从 ModelScope 下载模型，需要联网等待几分钟。启动后打开 <http://127.0.0.1:8765> 查看实时字幕，WebSocket 地址是 `ws://127.0.0.1:8765/ws`。

从 Python 安装、CUDA/CPU 选择到实际链路验收的说明，请查看 [Windows 完整部署指南](DEPLOYMENT.md)。安装后可运行 `.\verify_install.ps1` 执行依赖、测试、播放设备和 Overlay 编译自检。

## 播放设备

```powershell
.\.venv\Scripts\python.exe -m system_audio_asr --list-devices
.\start.ps1 -Speaker "扬声器 (Realtek"
```

默认用系统默认播放设备。如果音量条一直不动，先确认正在播放的应用输出到了同一个设备。如果音量很小而不触发识别，可降低门限：

```powershell
.\start.ps1 -SilenceDb -50
```

如果 ModelScope 下载较慢，也可以使用官方 Hugging Face 副本：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
.\.venv\Scripts\python.exe -m system_audio_asr --model funasr/paraformer-zh-streaming --hub hf
```

## WebSocket 协议

服务端只推送 UTF-8 JSON：

```json
{"type":"partial","segment_id":0,"text":"这是正在识别的"}
{"type":"final","segment_id":0,"text":"这是已经定稿的一句话。"}
{"type":"audio_level","dbfs":-23.4,"active":true}
{"type":"status","state":"capturing","speaker":"扬声器 (...)"}
{"type":"error","where":"wasapi","message":"..."}
```

同一 `segment_id` 的新 `partial` 应直接覆盖旧 partial；收到 `final` 后开始下一句。每条消息还包含递增的 `seq` 和 UTC `timestamp`。

## 延迟和接口

默认 Paraformer 块为 `[0, 8, 4]`，流式步长约 480 ms；实际总延迟还包含推理和播放端缓冲。连续静音 900 ms 后发送 `final`。

```powershell
.\.venv\Scripts\python.exe -m system_audio_asr --help
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-RestMethod http://127.0.0.1:8765/devices
.\.venv\Scripts\python.exe -m pytest
```

```text
WASAPI loopback（多声道 float32）
  → 下混 + 有状态 SoXR
  → 16 kHz / mono / float32 PCM
  → Paraformer Streaming
  → partial / final JSON WebSocket
```

## Windows 桌面字幕 Overlay

Overlay 直接订阅现有 `ws://127.0.0.1:8765/ws`。正常模式只有类似桌面歌词的字幕文字，没有背景框；默认置顶、鼠标穿透且不抢焦点。最后一句字幕会一直保留，直到下一段识别结果替换。

```powershell
.\build_overlay.ps1       # 首次或源码更新后构建
.\start_overlay.ps1       # 后台启动
.\start_overlay.ps1 -Edit # 启动并编辑位置/宽度/字体
.\start_overlay.ps1 -AISettings # 直接打开 AI 设置页
```

全局快捷键优先使用 `Ctrl+Alt+O`；若被其他软件占用，会自动回退为 `Ctrl+Shift+O`。字体、颜色、透明度和显示器可在设置页调整；字幕显示范围直接在桌面上拖动外框改变。配置保存在 `%LOCALAPPDATA%\WasapiParaformerOverlay\config.json`，托盘菜单可以预览、编辑或退出。

字幕正文使用类似普通 AI 聊天界面的常规字重，不使用粗体标题式正文。设置页的字号为手动数字输入，支持 `12–96 px`，不再使用滑杆。

老板键优先使用 `Ctrl+Alt+H`，冲突时自动回退为 `Ctrl+Shift+H`。按一次立即隐藏字幕，再按一次恢复；隐藏期间 ASR、WebSocket 和 AI 仍会继续工作。

字幕未锁定时可直接按住拖拽；鼠标移入字幕区域会显示半透明外框，以及无边框的“重置 / 锁定 / 隐藏”三个图标。拖动四条边或四个角可像缩放图片一样改变显示范围，文字自动换行，框高自动决定可见行数。点击锁定后外框消失，移动和缩放禁用，字幕主体恢复鼠标穿透；再次点击闭锁按钮即可解锁。重置会清空聊天记录、历史 user/assistant 上下文、等待队列和当前 AI 输出，但保留 system/附加提示词、模型、API Key、外观与窗口几何。`×` 只隐藏字幕，可用老板键恢复；真正退出仅通过系统托盘菜单。位置、宽高与锁定状态都会持久化。设置窗口中的“恢复默认位置”仍只负责窗口几何。

AI 设置页支持 DeepSeek API Key、模型、自动判断/总结/问答/解释/翻译模式、停顿触发时间和附加提示词。实际 AI 回答通过 SSE 流式返回并逐字更新 Overlay。API Key 使用 Windows DPAPI 按当前用户加密保存在 `%LOCALAPPDATA%\WasapiParaformerOverlay\deepseek.key`，不会写进 JSON、源码或运行日志。未设置 Key 时不会发送任何 API 请求。

字幕采用左对齐连续聊天视图：每段 `final` 追加为一条“语音”消息，DeepSeek 紧随其后追加一条“AI”消息。SSE delta 在后台读取并立即进入打字机缓冲，Overlay 每 35 ms 只显示 1–2 个完整字符，形成正常 AI 聊天的逐字效果。后续语音进入队列，上一轮不会被清空；最近多轮语音与 AI 回复会作为上下文继续发送，实现连续对话。显示范围不足时自动滚动到最新消息。

如果 AI 尚未开始显示回答，后续 `final` 会直接追加到上一条“语音”消息中，并取消后重新发起合并请求；不会额外生成一条“语音”记录。AI 已经开始显示文字后，后续语音才进入下一轮。AI 忙碌期间积累的连续片段会合并为一个 user turn，只生成一条整体回复。

滚动行为采用聊天软件的“粘住底部”规则：停留在底部时自动跟随新内容；手动向上滚动后立即暂停自动跟随，AI 继续生成但不会把视图拉回底部；手动滚回最底部后恢复自动跟随。

Overlay 在没有聊天内容、刚启动或重置上下文后不会消失，而是显示淡色 `等待语音…`。只有老板键会让整个 Overlay 完全隐藏；再次按老板键会恢复占位文字或最新聊天。

## 隐私与使用说明

- 语音识别默认在本机运行；模型首次使用时需要联网下载。
- 只有启用 AI 且配置 DeepSeek API Key 后，定稿文字和必要的对话上下文才会发送给 DeepSeek。
- 请在遵守适用法律、平台规则以及取得必要同意的前提下使用。AI 生成内容可能不准确，重要回答请自行核实。

## 开发与测试

```powershell
.\.venv\Scripts\python.exe -m pytest
.\build_overlay.ps1
```

项目主体包括 Python/FastAPI/FunASR ASR 服务与独立的 C# WPF Overlay。欢迎提交 Issue 和 Pull Request。

## License

[MIT License](LICENSE)

贡献代码请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；安全问题请按照 [SECURITY.md](SECURITY.md) 报告；版本变化见 [CHANGELOG.md](CHANGELOG.md)。
