## 1. 修改 Manager System Prompt

- [x] 1.1 修改 `agents/manager_agent.py` 中 `MANAGER_SYSTEM_PROMPT`：移除 "严格输出 JSON 格式" 要求和 JSON schema 定义（L107-L136），替换为自然语言输出指令——不完整时以 `[AWAIT]` 开头输出追问话术，完整时输出面试指导

## 2. 删除 JSON 解析并重写路由逻辑

- [x] 2.1 删除 `service/dual_agent_service.py` 中 `_parse_manager_response` 函数（L260-L295）
- [x] 2.2 新增辅助函数 `_is_await_continuation(response: str) -> bool` 和 `_extract_await_message(response: str) -> str`，用于检测 `[AWAIT]` 前缀并提取追问话术
- [x] 2.3 重写 `dual_interview_chat` 中的完整性检查调用点（L561-L575）：用 `_is_await_continuation` 替代 `parsed["action"]`，用 `_extract_await_message` 替代 `parsed["message_to_candidate"]`
- [x] 2.4 重写 `_process_complete_answer` 中的调用点（L600-L610）：用 `_get_fallback_system_prompt(session)` 作为 `system_prompt`，确定性拼接 `user_message`（含候选人回答 + Manager 指导 + 执行指令）
- [x] 2.5 重写 `start_dual_interview` 中的调用点（L454-L488）：用确定性代码组装 `system_prompt` 和 `user_message`，不再从 parsed dict 提取
- [x] 2.6 重写 `_handle_stage_advance` 中的调用点（L661-L691）：同上，用确定性代码组装

## 3. 清理无用代码

- [x] 3.1 检查 `dual_agent_service.py` 中 `import json` 和 `import re` 是否仍被其他代码使用，若无则移除
- [x] 3.2 运行 `ruff check` 和 `pyright` 确认无 lint/类型错误
