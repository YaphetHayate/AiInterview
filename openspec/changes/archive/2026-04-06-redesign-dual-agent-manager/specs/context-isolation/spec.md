## ADDED Requirements

### Requirement: simulation 模式按问题隔离上下文
在拟真模式下，传给 Interviewer 的上下文 SHALL 只包含当前问题的对话线程（question thread）。跨问题的对话内容不传给 Interviewer，但 Manager 持有所有问题的摘要信息用于阶段判断和最终总结。

#### Scenario: 当前问题的完整线程传递
- **WHEN** simulation 模式下，候选人正在回答问题 Z（已追问 2 次：Z, Z1, Z2）
- **THEN** 传给 Interviewer 的 `context_thread` 只包含 [Z, Z1, Z2]，不包含之前问题 X 和 Y 的对话

#### Scenario: 跨问题后上下文重置
- **WHEN** simulation 模式下，问题 X 结束，进入问题 Y
- **THEN** Interviewer 收到的 `context_thread` 为空（新问题开始），但 `system_prompt` 中可以包含 Manager 生成的简要上下文摘要（如"之前考察了基础知识，表现中等"）

#### Scenario: Manager 持有全量信息
- **WHEN** 面试进行到第 3 个问题
- **THEN** Manager 的 `manager_history` 包含所有轮次的完整对话，且 session 的 `questions` 列表中已完成的问题带有 `summary` 字段

### Requirement: learning 模式保留完整对话历史
在学习模式下，传给 Interviewer 的上下文 SHALL 包含完整的对话历史，不做隔离。

#### Scenario: 学习模式全量传递
- **WHEN** learning 模式下，候选人已讨论了 3 个知识点
- **THEN** 传给 Interviewer 的 `context_thread` 包含从面试开始到当前的所有对话

### Requirement: 会话状态数据结构
系统 SHALL 使用统一的会话状态数据结构管理面试进度，包含 `questions` 列表（每项含 id、content、status、thread、summary）、`current_question_idx`、`pending_buffer`（回答碎片缓冲）、`stage_summaries`（阶段摘要列表）。

#### Scenario: session 数据结构初始化
- **WHEN** 面试启动时
- **THEN** session 包含 `session_id`、`mode`、`stage`(1)、`style`、`difficulty`、`questions`(空)、`current_question_idx`(0)、`pending_buffer`(空)、`stage_summaries`(空)、`manager_history`(空)

#### Scenario: 问题完成后生成摘要
- **WHEN** simulation 模式下，一个问题被标记为 completed
- **THEN** Manager 为该问题生成 `summary`（如"候选人了解基本概念但缺乏深度"），存入 `questions[i].summary`
