### Requirement: 按 session 创建独立日志文件
系统 SHALL 为每个双 Agent 面试 session 创建独立的日志文件，路径为 `logs/prompt_<session_id>.log`，使用 UTF-8 编码写入。

#### Scenario: 新 session 启动时创建日志文件
- **WHEN** `start_dual_interview` 被调用并获得新的 session_id
- **THEN** 系统 SHALL 在 `logs/` 目录下创建 `prompt_<session_id>.log` 文件

#### Scenario: logs 目录不存在时自动创建
- **WHEN** `logs/` 目录不存在
- **THEN** 系统 SHALL 自动创建该目录

### Requirement: 记录 Manager Agent 输入
系统 SHALL 在每次调用 `invoke_manager` 前，将完整的 manager_history（所有历史消息）写入当前 session 的日志文件。每条消息 SHALL 记录 role 和 content。

#### Scenario: start_dual_interview 中记录 Manager 输入
- **WHEN** `start_dual_interview` 调用 `invoke_manager` 前
- **THEN** 日志 SHALL 包含标记 `[MANAGER INPUT]`、调用来源函数名、以及 manager_history 中所有消息的 role 和完整 content

#### Scenario: dual_interview_chat 中记录 Manager 输入
- **WHEN** `dual_interview_chat` 调用 `invoke_manager` 前
- **THEN** 日志 SHALL 包含标记 `[MANAGER INPUT]`、调用来源函数名、以及 manager_history 中所有消息的 role 和完整 content（不截断）

#### Scenario: _advance_stage 中记录 Manager 输入
- **WHEN** `_advance_stage` 调用 `invoke_manager` 前
- **THEN** 日志 SHALL 包含标记 `[MANAGER INPUT]`、调用来源函数名、以及 manager_history 中所有消息的 role 和完整 content（不截断）

### Requirement: 记录 Manager Agent 原始响应
系统 SHALL 在每次 `invoke_manager` 返回后，将原始响应文本写入日志文件。

#### Scenario: 记录 Manager 响应
- **WHEN** `invoke_manager` 返回结果
- **THEN** 日志 SHALL 包含标记 `[MANAGER OUTPUT]` 和完整的原始响应文本（不截断）

### Requirement: 记录 Manager 响应解析结果
系统 SHALL 在 `_parse_manager_response` 解析完成后，将解析出的结构化字段写入日志文件。

#### Scenario: 记录解析结果
- **WHEN** Manager 响应被解析为结构化数据
- **THEN** 日志 SHALL 包含标记 `[MANAGER PARSED]` 以及 current_stage、stage_name、stage_completed、system_prompt（前200字符摘要）、user_message（前200字符摘要）

### Requirement: 记录 Interviewer Agent 输入
系统 SHALL 在每次调用 `invoke_interviewer` 前，将 system_prompt 和 user_message 写入当前 session 的日志文件。

#### Scenario: 记录 Interviewer system_prompt
- **WHEN** `invoke_interviewer` 被调用前
- **THEN** 日志 SHALL 包含标记 `[INTERVIEWER INPUT]` 和完整的 system_prompt（不截断）

#### Scenario: 记录 Interviewer user_message
- **WHEN** `invoke_interviewer` 被调用前
- **THEN** 日志 SHALL 包含标记 `[INTERVIEWER INPUT]` 和完整的 user_message（不截断）

### Requirement: 记录 Interviewer Agent 响应
系统 SHALL 在每次 `invoke_interviewer` 返回后，将面试官回复写入日志文件。

#### Scenario: 记录 Interviewer 回复
- **WHEN** `invoke_interviewer` 返回结果
- **THEN** 日志 SHALL 包含标记 `[INTERVIEWER OUTPUT]` 和完整的回复文本（不截断）

### Requirement: 日志格式包含时间戳和分隔线
系统 SHALL 为每条日志记录添加时间戳和清晰的分隔标记，便于阅读定位。

#### Scenario: 日志条目格式
- **WHEN** 任何日志被写入
- **THEN** 每条日志条目 SHALL 以 ISO 格式时间戳开头，不同调用轮次之间 SHALL 使用分隔线区分

### Requirement: Session 重置时清理日志 Handler
系统 SHALL 在 session 重置时关闭并移除对应的 FileHandler，释放文件句柄。

#### Scenario: 重置 session 时清理
- **WHEN** `reset_dual_session` 被调用
- **THEN** 系统 SHALL 移除该 session_id 对应 logger 的 FileHandler 并关闭文件
