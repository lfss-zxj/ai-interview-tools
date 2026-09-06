# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

- 英文音频时间段成组 final 后裁剪缓存，避免长对话推理越来越慢。
- 英文字幕每段最多容纳两个完整句；使用稳定确认和更长停顿阈值，禁止句中切段。
- 启用实时翻译时随服务启动自动预热 OPUS-MT，避免首批译文排队。
- 增加当前用户级无窗口开机自启、设置页开关和命令行管理脚本。
- 增加不依赖 DeepSeek 的本地英文 → 中文 partial/final 实时翻译。
- 增加 Faster-Whisper 英文专用 ASR，并支持在设置页动态切换中英文识别引擎。
- 修复英文流式识别结果在单词边界处被错误拼接的问题。
- 增加字幕外框显示模式、颜色和透明度设置。
- 增加一键启动、安装自检和完整 Windows 部署文档。
- 固定兼容的 PyTorch/TorchAudio 版本，并对原生命令执行结果进行检查。
- 增加 Windows GitHub Actions、贡献指南、安全策略和 Issue 模板。

## [0.1.0] - 2026-08-28

- WASAPI Loopback 系统音频采集与 16 kHz 重采样。
- Paraformer Streaming 中文 `partial` / `final` 识别及 WebSocket 服务。
- WPF 桌面字幕、锁定/拖动/缩放、老板键与本地设置页面。
- DeepSeek SSE 流式回答、连续上下文和语音片段合并。
