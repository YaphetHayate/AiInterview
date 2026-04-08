## Why

Manager Agent 被要求在 system prompt 中"严格输出 JSON 格式"，代码侧通过正则 + `json.loads` 解析。但实际运行时，LLM 输出的 JSON 中 `system_prompt` 和 `user_message` 字段频繁为空或质量不足，4 个消费点中有 3 个的核心字段依赖 fallback 逻辑兜底。JSON 序列化/反序列化增加了 token 开销、解析异常风险和 prompt 复杂度，却没有带来实际的结构化收益。

## What Changes

- **移除 Manager system prompt 中的 JSON 输出格式要求**，改为自然语言输出
- **删除 `_parse_manager_response` 函数**及其全部 4 处调用
- **将 interviewer prompt 组装逻辑从 LLM 输出迁移到确定性 Python 代码**（现有 fallback 逻辑升级为主路径）
- **简化完整性判断路由**：用轻量文本标记替代 JSON `action` 字段

## Capabilities

### New Capabilities

- `manager-natural-output`: Manager Agent 以自然语言输出，确定性代码负责 prompt 组装和路由

### Modified Capabilities

（无已有 spec）

## Impact

- `agents/manager_agent.py`：移除 system prompt 中 JSON 格式要求，简化输出指令
- `service/dual_agent_service.py`：删除 `_parse_manager_response`，重写 4 处消费点为确定性组装逻辑
- 无 API 层面变更，无数据库变更，无前端变更

## 非目标

- 不改变 Manager 的 ReAct agent 架构（仍然使用 tools）
- 不改变完整性判断的业务语义（不完整仍追问，完整仍转交 Interviewer）
- 不优化 `_get_fallback_system_prompt` 的 prompt 质量本身
- 不引入 structured output / function calling 等新机制
