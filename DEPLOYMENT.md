# VoxRibbon Windows 完整部署指南

本文面向第一次接触项目的 Windows 用户。以下流程不需要预先安装 CUDA Toolkit；NVIDIA 版 PyTorch 自带所需的 CUDA 运行时，但显卡驱动必须正常。

## 1. 系统要求

- Windows 10/11 64 位
- Python 3.11 64 位（不支持 Microsoft Store 的占位别名）
- 至少 8 GB 内存，建议预留 6 GB 磁盘空间
- 能正常播放声音的 Windows 播放设备
- 可选：支持 CUDA 的 NVIDIA 显卡及较新的驱动
- 可选：DeepSeek API Key；不用 AI 时不需要，也不会产生 API 费用

安装 Python：

```powershell
winget install -e --id Python.Python.3.11
```

安装后重新打开 PowerShell，并确认：

```powershell
py -3.11 --version
```

## 2. 下载源码

```powershell
git clone https://github.com/lfss-zxj/ai-interview-tools.git
cd ai-interview-tools
```

没有 Git 时，也可以在 GitHub 点击 `Code → Download ZIP`，解压后在项目目录打开 PowerShell。

正式版本也可在 GitHub Releases 下载 `VoxRibbon-*-windows-source.zip`。发布包已包含编译好的 Overlay；安装脚本仍会在本机重新编译一次，以验证 Windows 环境完整可用。

## 3. 安装

NVIDIA 显卡推荐：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1 -Cuda
```

没有 NVIDIA 显卡或只想使用 CPU：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1 -Cpu
```

`-Cuda` 只在项目自己的 `.venv` 中安装 CUDA 版 PyTorch，不会重新安装显卡驱动，也不会修改系统 CUDA。CPU 与 CUDA 版本都使用经过验证的 PyTorch/TorchAudio 兼容组合。

安装结束会自动检查 Python 依赖并编译 WPF Overlay。也可以随时重新自检：

```powershell
.\verify_install.ps1
```

## 4. 一键启动

```powershell
.\launch.ps1
```

首次启动会下载 Paraformer 模型，耗时取决于网络。看到 `VoxRibbon 已就绪` 后：

- 字幕和服务状态：<http://127.0.0.1:8765>
- 设置页面：<http://127.0.0.1:8765/settings>
- WebSocket：`ws://127.0.0.1:8765/ws`
- 老板键：`Ctrl+Alt+H`
- 穿透/编辑切换：`Ctrl+Alt+O`

需要直接进入编辑或 AI 设置：

```powershell
.\launch.ps1 -Edit
.\launch.ps1 -AISettings
```

## 5. 配置 DeepSeek（可选）

打开 <http://127.0.0.1:8765/settings>，填写 API Key、选择模型和模式，点击保存并测试连接。VoxRibbon、本地 ASR 和桌面字幕完全免费；仅 DeepSeek API 调用由 DeepSeek 按实际用量收费。

API Key 使用 Windows DPAPI 按当前登录用户加密，保存在：

```text
%LOCALAPPDATA%\WasapiParaformerOverlay\deepseek.key
```

## 5.1 本地英文 → 中文实时翻译（可选）

打开设置页，勾选“启用英文 → 中文实时翻译”，再点击“下载并预热翻译模型”。首次会下载 OPUS-MT 英中模型；翻译在本机完成，不使用 DeepSeek、不需要 API Key、不产生 API 费用。NVIDIA 环境默认使用 CUDA，CPU 环境自动回退到 CPU。

## 6. 验证实际链路

1. 执行 `.\launch.ps1 -Edit`。
2. 浏览器播放一段普通话视频或语音。
3. 打开 <http://127.0.0.1:8765>，确认音量数值变化。
4. 确认桌面 Overlay 先更新 `partial`，停顿后形成 `final`。
5. 如果启用了 DeepSeek，等待设定的停顿时间，确认 AI 回答逐字出现。
6. 按 `Ctrl+Alt+H` 隐藏，再按一次恢复。

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-RestMethod http://127.0.0.1:8765/devices
```

健康状态中的 `state` 应最终为 `capturing`，且 `error` 应为 `null`。

## 7. 常见问题

### PowerShell 禁止运行脚本

只为当前 PowerShell 窗口放行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### 一直停在模型下载

保持首次启动窗口联网等待。ModelScope 不通时可尝试：

```powershell
.\.venv\Scripts\python.exe -m system_audio_asr --hub hf --model funasr/paraformer-zh-streaming
```

### 有 NVIDIA 显卡但显示 `cuda_available=False`

确认使用了 `.\install.ps1 -Cuda`，而不是 CPU 安装。再运行：

```powershell
nvidia-smi
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

系统安装了 CUDA Toolkit 并不代表 Python 虚拟环境中已经存在 CUDA 版 PyTorch；两者是不同组件。

### 没有字幕或音量不变化

列出播放设备：

```powershell
.\.venv\Scripts\python.exe -m system_audio_asr --list-devices
.\launch.ps1 -Speaker "设备名称中的一段"
```

确认播放软件与 VoxRibbon 选择的是同一个 Windows 输出设备。声音较小时可尝试 `.\launch.ps1 -SilenceDb -50`。

### 端口 8765 被占用

```powershell
.\launch.ps1 -Port 8876
```

### Overlay 没出现

先按 `Ctrl+Alt+H`，再按 `Ctrl+Alt+O`。检查 `.runtime\service.err.log`，并确认健康状态为 `capturing`。

## 8. 文件与隐私边界

- 模型缓存在当前 Windows 用户目录，不进入 Git 仓库。
- 运行日志位于项目的 `.runtime`，已被 Git 忽略。
- 外观、窗口位置和 AI 设置位于 `%LOCALAPPDATA%\WasapiParaformerOverlay\config.json`。
- 只有启用 AI 后，定稿文本和必要的上下文才会发送到配置的 AI API。
