## Context

当前双 Agent 面试模式（`dual_agent_service.py`）中，Manager Agent 和 Interviewer Agent 的提示词组装和传递缺乏可观测性。开发过程中无法确认 Manager 生成的 system_prompt 是否合理、Interviewer 收到的完整输入是否符合预期。

现有的 `service/interview.py`（单 Agent 模式）使用 `print()` 做 debug 输出，但这在 Web 模式下不可见且无持久化。

## Goals / Non-Goals

**Goals:**
- 按 session_id 独立记录每次双 Agent 交互中 Manager 和 Interviewer 的完整输入输出
- 日志持久化到文件，支持 Web 模式下事后查看
- 日志内容完整不截断，包括 Manager 的累积 history

**Non-Goals:**
- 不做日志 UI 展示
- 不做日志轮转或自动清理
- 不修改单 Agent 模式的现有 print 逻辑
- 不做日志级别动态配置或远程日志收集

## Decisions

### 1. 使用 Python logging 模块而非 print

**选择**: `logging` 模块 + `FileHandler`

**备选**: 直接 `open()` 写文件

**理由**: `logging` 模块线程安全（项目大量使用 `threading.Lock`），自带时间戳格式化，且可独立配置 Handler 不影响 stdout。直接写文件需要手动处理并发和格式。

### 2. 日志加在 dual_agent_service.py 调用层而非 agents 层

**选择**: 在 `dual_agent_service.py` 的 `start_dual_interview`、`dual_interview_chat`、`_advance_stage` 三个函数中添加日志

**备选**: 在 `agents/manager_agent.py` 和 `agents/interviewer_agent.py` 的 invoke 函数中添加

**理由**: `dual_agent_service.py` 是提示词组装的地方，能看到 system_prompt 的拼接过程（base_prompt + stage_prompt）、Manager history 的完整内容、以及解析后的结构化结果。agents 层只能看到最终传入的参数，丢失了上下文。

### 3. 每个 session 独立一个日志文件

**选择**: `logs/prompt_<session_id>.log`

**备选**: 按日期单文件 `logs/prompt_2026-04-06.log`

**理由**: 按 session 隔离便于单独查看每个用户/面试的完整流程，不会被其他 session 的日志穿插干扰。session_id 本身已具备唯一性。

### 4. Logger 命名与获取方式

**选择**: 使用 `logging.getLogger(f"prompt_debug.{session_id}")` 为每个 session 创建独立 logger，每个 logger 绑定独立的 FileHandler

**备选**: 单一 logger + 所有 session 写同一文件用 session_id 前缀区分

**理由**: 独立 logger + 独立文件实现最简单，避免文件内容的混合，且 logger 可在 session 结束后移除 handler 释放资源。

## Risks / Trade-offs

- **[磁盘占用]** 每次 Manager 调用都带完整累积 history，面试越长单次日志越大 → 当前非目标中不含自动清理，手动管理即可
- **[Handler 泄漏]** session 结束后不移除 handler 可能导致文件句柄累积 → 在 `reset_dual_session` 中移除对应 handler
- **[日志编码]** Windows 环境下中文写入 → FileHandler 默认使用系统编码，显式指定 `encoding="utf-8"`
