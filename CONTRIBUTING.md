# Contributing to VoxRibbon

感谢你帮助改进 VoxRibbon。请先搜索现有 Issue，较大的功能改动建议先开 Issue 说明使用场景和方案。

## 本地开发

```powershell
git clone https://github.com/lfss-zxj/ai-interview-tools.git
cd ai-interview-tools
.\install.ps1 -Cpu
.\verify_install.ps1
```

NVIDIA 环境可把 `-Cpu` 换成 `-Cuda`。提交前至少执行：

```powershell
.\.venv\Scripts\python.exe -m pytest
.\build_overlay.ps1
git diff --check
```

## 修改边界

- 不要提交 `.venv`、模型、编译产物、运行日志、API Key 或个人设置。
- 不要在测试中发起真实 DeepSeek 计费请求。
- 涉及 WebSocket 消息时保持向后兼容，并为新增字段补测试或协议说明。
- 涉及录音、网络或密钥时，在 PR 中说明隐私边界和失败行为。
- UI 修改应至少在 100%、125% 和 150% DPI 下人工检查。

## Pull Request

PR 请包含：问题背景、修改内容、验证命令、界面改动截图（如适用）和已知限制。一次 PR 尽量只解决一个主题。
