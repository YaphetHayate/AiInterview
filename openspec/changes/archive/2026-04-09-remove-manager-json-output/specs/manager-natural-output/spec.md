## ADDED Requirements

### Requirement: Manager 输出自然语言而非 JSON
Manager Agent 的 system prompt SHALL NOT 要求输出 JSON 格式。Manager SHALL 以自然语言输出其判断和指导。

#### Scenario: 回答不完整时 Manager 输出追问话术
- **WHEN** 候选人回答不完整
- **THEN** Manager 输出以 `[AWAIT]` 开头的文本，后跟追问话术

#### Scenario: 回答完整时 Manager 输出面试指导
- **WHEN** 候选人回答完整
- **THEN** Manager 输出自然语言的面试指导内容，不带任何特殊前缀

### Requirement: 确定性代码解析 Manager 输出进行路由
系统 SHALL 通过文本前缀 `[AWAIT]` 判断 Manager 输出的路由方向，而非解析 JSON `action` 字段。

#### Scenario: 检测到 [AWAIT] 前缀进入追问分支
- **WHEN** Manager 输出以 `[AWAIT]` 开头（允许前后有空白字符）
- **THEN** 系统提取 `[AWAIT]` 之后的文本作为追问话术，直接返回给候选人

#### Scenario: 未检测到 [AWAIT] 前缀进入面试分支
- **WHEN** Manager 输出不以 `[AWAIT]` 开头
- **THEN** 系统将候选人的完整回答交给 Interviewer Agent 处理

### Requirement: Interviewer prompt 由确定性代码组装
`system_prompt` 和 `user_message` SHALL 由 Python 代码根据 session 配置生成，不依赖 Manager 输出的结构化字段。

#### Scenario: system_prompt 由代码生成
- **WHEN** 需要调用 Interviewer Agent
- **THEN** system_prompt 由 `_get_fallback_system_prompt(session)` 生成，基于 session 的技术栈、岗位、风格、阶段等配置

#### Scenario: user_message 由代码组装
- **WHEN** 需要调用 Interviewer Agent
- **THEN** user_message 由确定性代码拼接，包含候选人回答和执行指令

#### Scenario: Manager 输出作为指导附加到 user_message
- **WHEN** Manager 在回答完整时输出了自然语言指导内容
- **THEN** 该指导内容 SHALL 附加到 user_message 中，供 Interviewer 参考

### Requirement: 删除 JSON 解析逻辑
系统 SHALL NOT 包含 `_parse_manager_response` 函数或任何基于正则 + `json.loads` 的 Manager 输出解析逻辑。

#### Scenario: 代码中不存在 JSON 解析路径
- **WHEN** 完成重构后
- **THEN** `dual_agent_service.py` 中不存在 `import json`（除非其他功能需要）、不存在 `re.search(r"\{[\s\S]*\}", ...)` 模式、不存在 `_parse_manager_response` 函数

## REMOVED Requirements

### Requirement: Manager 输出严格 JSON 格式
**Reason**: JSON 格式对 LLM 不友好，实际运行中核心字段频繁缺失，3/4 调用点依赖 fallback 兜底。JSON 解析徒增 token 开销和异常风险。
**Migration**: Manager 改为自然语言输出，路由通过文本前缀 `[AWAIT]` 判断，prompt 组装由确定性代码完成。
