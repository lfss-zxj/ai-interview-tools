# VoxRibbon（声幕）

[![CI](https://github.com/lfss-zxj/ai-interview-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/lfss-zxj/ai-interview-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-0078D4.svg)](DEPLOYMENT.md)

![VoxRibbon AI 面试助手封面](assets/cover-4x3.png)

**VoxRibbon** 是一款专为远程面试设计的开源桌面工具，它通过 **WASAPI Loopback** 捕获系统音频，使用 Paraformer 识别中文、Faster-Whisper 识别英文，并通过悬浮窗口（Overlay）实时显示字幕、本地英中译文和 AI 回答。

## ✨ 核心特性

- **💰 完全免费开源**：VoxRibbon 本身完全免费，本地语音识别与桌面字幕功能不收取任何费用；只有主动启用 DeepSeek AI 时，API 调用会由服务商按实际用量计费。
- **🔒 极致隐私**：仅在本地运行 ASR 引擎，只有定稿后的文本才会发送给 AI。按 `Ctrl+Alt+H` 会隐藏悬浮窗并暂停接收新语音，再按一次从下一段语音恢复。
- **🚀 本地化 ASR**：基于 FunASR/Paraformer Streaming，无需麦克风，直接捕获系统播放的声音，识别速度快，支持离线基础功能。
- **💬 流式 AI 对话**：集成 DeepSeek API，支持 SSE 流式输出。AI 会根据语境自动合并语音片段，提供连续的面试辅助回答。
- **🌐 本地英中实时翻译**：英文模式使用 Faster-Whisper 专用 ASR，再由 OPUS-MT 将每次 `partial/final` 翻译为简体中文；不调用 DeepSeek，不需要 API Key，也不产生费用。
- **🎨 高度可定制**：WPF 驱动的悬浮窗支持拖拽、缩放、透明度过渡。所有设置通过本地 Web 界面 (`http://127.0.0.1:8765`) 管理，无需重启。
- **🖼️ 可定制字幕外框**：外框可选择仅悬停显示或始终显示，并可单独设置颜色与透明度。
- **🛡️ 安全设计**：API Key 使用 Windows DPAPI 加密存储，设置页仅允许本机访问，日志不记录敏感信息。

[NoTrack AI — https://notrack.ai/](https://notrack.ai/)

## 🚀 新手安装教程（Windows）

不会编程也可以使用。整个过程只需要下载项目、安装 Python，然后复制几条命令。

### 第 1 步：确认电脑系统

VoxRibbon 目前只支持 **64 位 Windows 10/11**。建议至少准备 6 GB 可用磁盘空间。

- 有 NVIDIA 显卡：后面选择 CUDA 版，识别速度更快。
- 没有 NVIDIA 显卡：选择 CPU 版，也能使用，但识别速度会慢一些。
- DeepSeek API Key 不是必需的；不填写也可以免费使用本地实时字幕。

不知道自己有没有 NVIDIA 显卡时，按 `Ctrl + Shift + Esc` 打开任务管理器，在“性能 → GPU”中查看名称。

### 第 2 步：安装 Python 3.11

打开 PowerShell：按下 `Win + R`，输入 `powershell`，按回车，然后复制执行：

```powershell
winget install -e --id Python.Python.3.11
```

安装结束后，**关闭 PowerShell 并重新打开一个窗口**，执行：

```powershell
py -3.11 --version
```

如果看到类似 `Python 3.11.x`，说明安装成功。如果提示找不到 `winget`，请从 [Python 官网](https://www.python.org/downloads/release/python-3119/) 安装 64 位 Python 3.11，并在安装界面勾选 `Add Python to PATH`。

### 第 3 步：下载 VoxRibbon

不熟悉 Git 的用户直接点击：

**[下载 VoxRibbon ZIP](https://github.com/lfss-zxj/ai-interview-tools/archive/refs/heads/main.zip)**

下载完成后：

1. 右键 ZIP，选择“全部解压缩”。
2. 打开解压后的 `ai-interview-tools-main` 文件夹。
3. 点击资源管理器顶部的地址栏，输入 `powershell`，按回车。
4. 此时打开的蓝色窗口应位于项目目录，不需要再输入 `cd`。

熟悉 Git 的用户也可以执行：

```powershell
git clone https://github.com/lfss-zxj/ai-interview-tools.git
cd ai-interview-tools
```

### 第 4 步：允许当前窗口运行安装脚本

复制执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

这个设置只对当前 PowerShell 窗口有效，不会永久修改系统策略。

### 第 5 步：安装依赖

有 NVIDIA 显卡时执行：

```powershell
.\install.ps1 -Cuda
```

没有 NVIDIA 显卡时执行：

```powershell
.\install.ps1 -Cpu
```

安装通常需要几分钟。CUDA 版 PyTorch 会安装在项目自己的 `.venv` 中，**不会重新安装显卡驱动，也不会修改系统 CUDA**。看到下面这句话才表示安装完成：

```text
安装和自检完成。运行 .\launch.ps1，首次启动会下载 Paraformer 模型。
```

如果中途出现红色错误，不要继续启动；先查看下方“常见问题”，或者提交 Issue 时附上错误内容。

### 第 6 步：一键启动

继续在同一个 PowerShell 窗口执行：

```powershell
.\launch.ps1
```

第一次启动会联网下载 Paraformer 模型，需要耐心等待。看到 `VoxRibbon 已就绪` 后，桌面会出现字幕区域。

然后播放一段普通话视频或语音：

1. 打开 <http://127.0.0.1:8765>，确认页面上的音量数值会变化。
2. 电脑扬声器中出现中文声音后，桌面 Overlay 应显示实时字幕。
3. 按 `Ctrl + Alt + O` 解锁并拖动字幕；调整完成后点击锁图标。
4. 按 `Ctrl + Alt + H` 隐藏字幕并暂停接收语音，再按一次恢复。

### 第 7 步：启用 AI 面试回答（可选）

打开设置页：<http://127.0.0.1:8765/settings>

填写自己的 DeepSeek API Key，选择模型和回答模式，点击“保存”并测试连接。VoxRibbon、本地 ASR 和桌面字幕完全免费；只有启用 DeepSeek 后产生的 API 调用由 DeepSeek 按实际用量收费。

API Key 会使用 Windows DPAPI 加密保存在本机，不会写入项目源码或日志。

### 启用本地英文实时翻译（可选）

打开 <http://127.0.0.1:8765/settings>，勾选“启用英文 → 中文实时翻译”，点击“下载并预热翻译模型”，完成后保存设置。

- 翻译完全在本机运行，不使用 DeepSeek，也不需要 API Key。
- 首次使用会下载约 78 MB 的英文 ASR 和约 300 MB 的 OPUS-MT 英中模型，之后可以离线识别和翻译。
- 英文 partial 更新时中文译文会实时替换，final 到达后稳定定稿。
- 原英文直接显示，中文结果标为“译文”。

### 以后怎么启动

以后不需要重复安装。打开项目文件夹，在地址栏输入 `powershell`，然后执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\launch.ps1
```

### 新手常见问题

| 现象 | 处理方法 |
| --- | --- |
| `无法将 py 识别为命令` | 重新安装 Python 3.11，勾选 `Add Python to PATH`，安装后重开 PowerShell。 |
| `禁止运行脚本` | 先执行 `Set-ExecutionPolicy -Scope Process Bypass`。 |
| 有 NVIDIA 显卡但显示 `cuda_available=False` | 确认执行的是 `.\install.ps1 -Cuda`；系统有 CUDA 不等于虚拟环境已有 CUDA 版 PyTorch。 |
| 一直在下载模型 | 首次运行需要联网下载，请继续等待；网络慢时可参考 [完整部署指南](DEPLOYMENT.md)。 |
| 页面显示正常但没有字幕 | 确认电脑正在播放中文声音，并检查播放软件是否使用了系统默认输出设备。 |
| 字幕不见了 | 按一次 `Ctrl + Alt + H`，再按 `Ctrl + Alt + O`。 |
| 端口 8765 被占用 | 执行 `.\launch.ps1 -Port 8876`，设置页相应改为 `http://127.0.0.1:8876/settings`。 |

需要进一步排查时运行：

```powershell
.\verify_install.ps1
```

更详细的显卡、播放设备、模型下载和故障处理说明见 [Windows 完整部署指南](DEPLOYMENT.md)。

```text
系统播放声音 → WASAPI Loopback → 16 kHz PCM → Paraformer Streaming
                                              ↓
桌面字幕 Overlay ← WebSocket partial / final ←┘
       ↓
连续对话上下文 → DeepSeek SSE 流式回答
```

这个服务只采集 Windows 当前播放设备的系统声音，不采集麦克风。WASAPI loopback 音频先下混为单声道，再通过有状态 SoXR 重采样为 16 kHz PCM，交给 Paraformer 中文流式模型，最后把中文增量文本推送到 WebSocket。

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

老板键优先使用 `Ctrl+Alt+H`，冲突时自动回退为 `Ctrl+Shift+H`。按一次立即隐藏字幕并停止接收新的 `partial/final`，再按一次恢复。底层 ASR 服务仍保持运行，避免恢复时重新加载模型；隐藏期间的语音及其尚未结束的尾句不会补进聊天记录，也不会触发新的 AI 请求。

字幕未锁定时可直接按住拖拽；鼠标移入字幕区域会显示外框，以及无边框的“重置 / 锁定 / 隐藏”三个图标。拖动四条边或四个角可像缩放图片一样改变显示范围，文字自动换行，框高自动决定可见行数。设置页可以选择外框仅在悬停时显示或始终显示，并单独调整外框颜色与透明度。锁定后移动和缩放禁用，字幕主体恢复鼠标穿透；如果选择“始终显示”，锁定后外框仍会保留。重置会清空聊天记录、历史 user/assistant 上下文、等待队列和当前 AI 输出，但保留 system/附加提示词、模型、API Key、外观与窗口几何。`×` 只隐藏字幕，可用老板键恢复；真正退出仅通过系统托盘菜单。位置、宽高与锁定状态都会持久化。

设置页将“本地实时翻译”和“DeepSeek AI”分开。本地英文 → 中文翻译直接处理每次 `partial/final`，不调用 API；DeepSeek 仍负责自动判断/总结/问答/解释和中文翻译为英文。AI 回答通过 SSE 流式返回。API Key 使用 Windows DPAPI 按当前用户加密保存在 `%LOCALAPPDATA%\WasapiParaformerOverlay\deepseek.key`，不会写进 JSON、源码或运行日志。

识别语言可以在设置页切换：中文使用 Paraformer Streaming，英文使用 Faster-Whisper Tiny English。切换时只重启本地识别引擎，Web 页面、WebSocket 和 Overlay 不退出。英文模型保存在 `%LOCALAPPDATA%\VoxRibbon\models\faster-whisper-tiny.en`。

字幕采用左对齐连续视图：每段 `final` 直接显示原文，不再添加“语音”标签；本地翻译结果标为“译文”，DeepSeek 回答标为“AI”。英文 partial 变化时会丢弃过期翻译结果，只显示最新版本；final 到达后生成稳定译文。显示范围不足时自动滚动到最新消息。

如果 AI 尚未开始显示回答，后续 `final` 会直接追加到上一条原文记录中，并取消后重新发起合并请求；不会额外生成一条记录。AI 已经开始显示文字后，后续内容才进入下一轮。AI 忙碌期间积累的连续片段会合并为一个 user turn，只生成一条整体回复或译文。

滚动行为采用聊天软件的“粘住底部”规则：停留在底部时自动跟随新内容；手动向上滚动后立即暂停自动跟随，AI 继续生成但不会把视图拉回底部；手动滚回最底部后恢复自动跟随。

Overlay 在没有内容、刚启动或重置上下文后不会消失，而是显示淡色 `等待字幕…`。只有老板键会让整个 Overlay 完全隐藏；再次按老板键会恢复占位文字或最新内容。

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
