## Why

双 Agent 面试模式下，Manager 和 Interviewer 的提示词对面试质量至关重要，但目前缺乏可观测性。开发调试时无法看到每个 Agent 实际收到的 system_prompt、user_message 和完整 history，导致难以判断提示词是否符合预期、问题出在流程管理还是面试执行环节。

## What Changes

- 在 `dual_agent_service.py` 的三个关键调用点（`start_dual_interview`、`dual_interview_chat`、`_advance_stage`）添加 prompt 日志记录
- 每条日志按 session 独立写入文件：`logs/prompt_<session_id>.log`
- 记录 Manager 的输入 history、原始响应、解析结果，以及 Interviewer 的 system_prompt 和 user_message
- 使用 Python `logging` 模块，配置独立的 FileHandler，不影响现有 stdout 输出

## Capabilities

### New Capabilities
- `prompt-logging`: 按 session 独立记录双 Agent 模式下 Manager 和 Interviewer 的完整输入输出，用于调试和提示词优化

### Modified Capabilities

（无）

## Impact

- 修改文件：`service/dual_agent_service.py`（主要改动）
- 新增文件：`logs/` 目录（.gitignore 排除）
- 无 API 变更、无数据库变更、无依赖变更

## 非目标

- 不做日志的 UI 展示，仅输出到文件
- 不做日志轮转或自动清理
- 不修改单 Agent 模式（simulation/learning）的现有 debug print
- 不做日志级别动态配置
