## 1. 替换日志核心函数

- [x] 1.1 在 `service/dual_agent_service.py` 中新增 `_log_section(logger, tag, meta="", content="")` 函数，实现分隔框格式输出，不截断内容
- [x] 1.2 删除旧的 `_log()` 函数（第 66-73 行）

## 2. 改造 start_dual_interview 日志

- [x] 2.1 在 `start_dual_interview` 函数开头，增加 `_log_section(logger, "[MANAGER] System Prompt", content=MANAGER_SYSTEM_PROMPT)` 调用，需从 `agents/manager_agent.py` 导入 `MANAGER_SYSTEM_PROMPT`
- [x] 2.2 替换 `start_dual_interview` 中所有 `_log` 调用为 `_log_section`：MANAGER_INPUT → `[MANAGER] Input (source=start)`，MANAGER_OUTPUT → `[MANAGER] Output`，INTERVIEWER_INPUT → 拆分为 `[INTERVIEWER] System Prompt` + `[INTERVIEWER] User Message`，INTERVIEWER_OUTPUT → `[INTERVIEWER] Response`
- [x] 2.3 删除 `start_dual_interview` 中的 `MANAGER_PARSED` 日志调用（约第 446 行）

## 3. 改造 dual_interview_chat 日志

- [x] 3.1 替换 `dual_interview_chat` 中所有 `_log` 调用：PENDING_BUFFER → `[FLOW] Pending Buffer`，FORCE_COMPLETE → `[FLOW] Force Complete`，MANAGER_INPUT → `[MANAGER] Input (source=completeness_check)`，MANAGER_OUTPUT → `[MANAGER] Output`，AWAIT_CONTINUATION → `[FLOW] Await Continuation`
- [x] 3.2 删除 `dual_interview_chat` 中的 `MANAGER_PARSED` 日志调用（如存在）

## 4. 改造 _process_complete_answer 日志

- [x] 4.1 替换 `_process_complete_answer` 中所有 `_log` 调用：MANAGER_INPUT → `[MANAGER] Input (source=chat)`，MANAGER_OUTPUT → `[MANAGER] Output`，INTERVIEWER_INPUT → 拆分为 `[INTERVIEWER] System Prompt` + `[INTERVIEWER] User Message`，INTERVIEWER_OUTPUT → `[INTERVIEWER] Response`
- [x] 4.2 删除 `_process_complete_answer` 中的 `MANAGER_PARSED` 日志调用（约第 586 行）

## 5. 改造 _handle_stage_advance 和 _handle_final_summary 日志

- [x] 5.1 替换 `_advance_stage` 中的 STAGE_ADVANCE → `[FLOW] Stage Advance`
- [x] 5.2 替换 `_handle_stage_advance` 中的所有 `_log` 调用：MANAGER_INPUT → `[MANAGER] Input (source=stage_advance)`，MANAGER_OUTPUT → `[MANAGER] Output`，INTERVIEWER_INPUT → 拆分为 `[INTERVIEWER] System Prompt` + `[INTERVIEWER] User Message`，INTERVIEWER_OUTPUT → `[INTERVIEWER] Response`
- [x] 5.3 替换 `_handle_final_summary` 中的所有 `_log` 调用：MANAGER_INPUT → `[MANAGER] Input (source=final_summary)`，MANAGER_OUTPUT → `[MANAGER] Output`

## 6. 验证

- [x] 6.1 运行 ruff lint 检查 `service/dual_agent_service.py` 无报错
- [ ] 6.2 启动服务并发起一次面试，确认 `logs/` 目录下生成的新日志格式正确：包含 System Prompt、Input/Output 分段、无截断、无 MANAGER_PARSED
