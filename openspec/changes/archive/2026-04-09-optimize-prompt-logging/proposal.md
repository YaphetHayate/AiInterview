## Why

当前日志系统存在三个核心问题，严重阻碍 prompt 调优效率：

1. **内容被截断** — `_log()` 对超过 300 字符的内容强制截断，Manager 的 JSON 输出和 Interviewer 的完整提示词无法完整查看
2. **缺少 Manager System Prompt** — Manager 的系统提示词（130+ 行）从未被记录到日志，调试时需反复回看代码
3. **格式混杂** — JSON、纯文本、KV 对混在一起，单行塞入大量信息，难以阅读

开发调试时，核心诉求是：**完整看到 Manager 的输入输出，以及 Interviewer 收到的 system_prompt + user_message 和它的回复**。当前日志无法满足。

## What Changes

- 新增 `_log_section()` 函数，用分隔框 + 多行格式输出日志，不截断内容
- 删除旧的 `_log()` 函数
- 在 `start_dual_interview` 首次调用时记录 Manager 的完整 System Prompt
- 所有 `_log` 调用点改为 `_log_section`，拆分复合字段为独立段落
- 删除 `MANAGER_PARSED` 日志（与 Raw Output 重复）
- Interviewer 的 system_prompt 和 user_message 拆分为两条独立日志

## Capabilities

### New Capabilities

- `prompt-logging`: 分段式 prompt 日志系统，完整记录 Manager 输入输出和 Interviewer 提示词与回复

### Modified Capabilities

（无现有 spec 需修改）

## Impact

- **影响文件**: `service/dual_agent_service.py`（主要改动）
- **影响范围**: 仅日志输出格式，不影响业务逻辑和 API 接口
- **向后兼容**: 日志文件格式变更，现有日志文件不受影响
- **性能**: 无影响，仅在日志写入时多输出几行分隔符
