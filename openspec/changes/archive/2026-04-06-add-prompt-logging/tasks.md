## 1. 日志基础设施

- [x] 1.1 在 `service/dual_agent_service.py` 中添加 `logging` 模块导入，创建 `_get_prompt_logger(session_id)` 函数：为每个 session 创建独立 logger（`prompt_debug.<session_id>`），绑定 `logs/prompt_<session_id>.log` 的 FileHandler，UTF-8 编码，自动创建 `logs/` 目录
- [x] 1.2 在 `.gitignore` 中添加 `logs/` 目录排除规则

## 2. Manager 输入输出日志

- [x] 2.1 在 `start_dual_interview` 中（`dual_agent_service.py:93`），`invoke_manager` 调用前后添加日志：记录 `[MANAGER INPUT]` 完整 history 和 `[MANAGER OUTPUT]` 原始响应
- [x] 2.2 在 `dual_interview_chat` 中（`dual_agent_service.py:150`），`invoke_manager` 调用前后添加同样的日志
- [x] 2.3 在 `_advance_stage` 中（`dual_agent_service.py:212`），`invoke_manager` 调用前后添加同样的日志

## 3. Manager 解析结果日志

- [x] 3.1 创建 `_log_parsed_result(logger, parsed, source)` 辅助函数，记录 `[MANAGER PARSED]` 标记及 current_stage、stage_name、stage_completed、system_prompt 摘要、user_message 摘要
- [x] 3.2 在三个调用点的 `_parse_manager_response` 之后调用该辅助函数

## 4. Interviewer 输入输出日志

- [x] 4.1 在 `start_dual_interview` 中（`dual_agent_service.py:116`），`invoke_interviewer` 调用前后添加日志：记录 `[INTERVIEWER INPUT]` system_prompt 和 user_message、`[INTERVIEWER OUTPUT]` 回复
- [x] 4.2 在 `dual_interview_chat` 中（`dual_agent_service.py:172`），`invoke_interviewer` 调用前后添加同样的日志
- [x] 4.3 在 `_advance_stage` 中（`dual_agent_service.py:237`），`invoke_interviewer` 调用前后添加同样的日志

## 5. Session 清理

- [x] 5.1 在 `reset_dual_session` 中添加 handler 清理逻辑：移除对应 session_id 的 logger 的 FileHandler 并关闭文件，释放资源
