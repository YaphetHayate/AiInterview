## Context

当前 `dual_agent_service.py` 使用 `_log()` 函数记录 prompt 调试日志，格式为 `[TAG] key=val` 单行输出，超过 300 字符截断。日志写入 `logs/prompt_{session_id}.log`。

日志调用点分布在 `start_dual_interview`、`dual_interview_chat`、`_process_complete_answer`、`_handle_stage_advance`、`_handle_final_summary` 等函数中，约 20 处调用。

Manager 的 System Prompt（`MANAGER_SYSTEM_PROMPT`，定义于 `manager_agent.py:7-137`）从未被记录。Manager 的中间 tool call 过程被 `invoke_manager_with` 丢弃（只取 `messages[-1]`）。

## Goals / Non-Goals

**Goals:**

- 单文件日志，按时间顺序完整展示 Manager ↔ Interviewer 交互
- 不截断任何内容，prompt、response 完整可见
- Manager System Prompt 首次调用时记录一次
- Interviewer 的 system_prompt 和 user_message 拆分为独立段落
- 流程控制事件（PENDING_BUFFER、FORCE_COMPLETE、STAGE_ADVANCE、AWAIT_CONTINUATION）保留但简化格式

**Non-Goals:**

- 不记录 Manager 的 tool call 中间过程（read_skill_md、read_stage_file 等）
- 不记录 Manager 的思考链（thinking tokens）
- 不引入 JSON Lines 格式或额外日志查看工具
- 不影响业务逻辑和 API 接口

## Decisions

### D1: 用 `_log_section()` 替代 `_log()`

新函数签名：`_log_section(logger, tag, meta="", content="")`

输出格式：
```
2026-04-08 10:00:00
╔══════════════════════════════════════════════════════════════════╗
║ [MANAGER] Input (source=start)
╚══════════════════════════════════════════════════════════════════╝
<完整内容>
```

用 `╔═╗` / `╚═╝` 分隔框区分段落，tag 标识角色+事件类型，meta 附加上下文信息（如 source、stage），content 完整输出不截断。

**替代方案**: JSON Lines 格式 — 拒绝，因为用户直接看日志文件，纯文本更友好。

### D2: 日志事件类型

| 事件 | Tag 格式 | 内容 |
|------|----------|------|
| Manager 系统提示词 | `[MANAGER] System Prompt` | 完整 prompt |
| Manager 输入 | `[MANAGER] Input (source=xxx)` | 完整 message |
| Manager 输出 | `[MANAGER] Output` | 完整原始输出 |
| Interviewer 系统提示词 | `[INTERVIEWER] System Prompt` | 完整 prompt |
| Interviewer 用户消息 | `[INTERVIEWER] User Message` | 完整 message |
| Interviewer 回复 | `[INTERVIEWER] Response` | 完整回复 |
| 流程事件 | `[FLOW] event_name` | 简短描述 |

### D3: 删除 MANAGER_PARSED

Manager Output 已包含完整 JSON，Parsed 是冗余的解析结果。删除以减少日志噪音。

### D4: Manager System Prompt 只记录一次

在 `start_dual_interview` 函数开头调用 `_log_section` 记录 `MANAGER_SYSTEM_PROMPT`。后续轮次不再重复。因为当前 Manager prompt 是静态常量，记录一次足够。

## Risks / Trade-offs

- **[日志文件膨胀]** → 开发调试用途，用户会定期删除。日志文件包含完整 prompt 和 skill 文件内容，单个 session 日志可能达 100KB+，可接受。
- **[分隔框编码]** → `╔═╗` 等 Unicode 字符在 Windows 记事本中可能显示异常 → 用户在 IDE 或终端中查看，现代编辑器均支持。
