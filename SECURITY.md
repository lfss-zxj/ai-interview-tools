# Security Policy

## 支持范围

安全修复优先应用于 `main` 分支的最新版本。

## 报告安全问题

请不要在公开 Issue 中粘贴 API Key、完整日志、语音转写、系统路径或其他个人信息。优先使用 GitHub 仓库的 Private vulnerability reporting；如果该入口暂未开启，请只提交不含敏感细节的 Issue，请求维护者提供私下联系渠道。

报告请包含受影响版本、复现条件、影响范围和建议修复方式。不要在未取得许可的设备或账户上测试。

## 当前安全边界

- ASR 默认完全在本机运行。
- 设置写接口只接受本机来源。
- DeepSeek API Key 使用 Windows DPAPI 按当前用户加密。
- 启用 AI 后，定稿文本及必要上下文会发送到用户配置的 API 服务。
- Overlay 的老板键只隐藏窗口，不会停止后台识别或已经启用的 AI 请求。
