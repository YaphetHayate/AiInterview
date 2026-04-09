## ADDED Requirements

### Requirement: Tutor Agent 创建和调用
系统 SHALL 提供独立的 Tutor Agent（`agents/tutor_agent.py`），使用 Ollama deepseek-r1:8b 模型，专用于知识点讲解和追问预测。Tutor Agent SHALL NOT 依赖 Manager Agent 或 Interviewer Agent。

#### Scenario: 创建 Tutor Agent
- **WHEN** 系统接收到 `/tutor/start` 请求
- **THEN** 系统创建新的 Tutor Agent 实例，使用独立的教学导向 system prompt，生成唯一的 `tutor_session_id`

### Requirement: Tutor 会话管理
系统 SHALL 使用内存字典 + 线程锁管理 Tutor 会话，每个会话独立维护对话历史。会话 SHALL NOT 持久化到数据库。

#### Scenario: 会话创建
- **WHEN** 用户点击"学习一下"
- **THEN** 系统创建独立 Tutor 会话，包含 `tutor_session_id`、对话历史、关联的面试问题和技术栈信息，面试会话状态不受影响

#### Scenario: 会话销毁
- **WHEN** 用户关闭学习弹窗（前端调用 `/tutor/end`）
- **THEN** 系统从内存中移除该 Tutor 会话及其全部对话历史

#### Scenario: 会话自动清理
- **WHEN** Tutor 会话创建超过 30 分钟未被使用
- **THEN** 系统在下次访问时自动清理该过期会话

### Requirement: 知识点答疑
Tutor Agent SHALL 针对当前面试问题展开深入讲解，包括概念解释、原理分析、示例说明。答疑内容 SHALL 使用 Markdown 格式。

#### Scenario: 首次答疑
- **WHEN** 用户点击"学习一下"按钮
- **THEN** Tutor Agent 接收当前面试问题内容、技术栈和难度作为种子上下文，返回结构化的知识点讲解

#### Scenario: 多轮追问
- **WHEN** 用户点击追问按钮或在输入框输入追问
- **THEN** Tutor Agent 基于完整对话历史继续答疑，保持上下文连贯

### Requirement: 追问预测
Tutor Agent 每次回答后 SHALL 返回 3-4 个预测的追问建议，覆盖以下维度：设计动机（为什么要这样设计）、知识盲区（讲解中可能未讲清的点）、对比延伸（和其他方案的比较）、实践场景（实际应用）。追问建议 SHALL 以 `<suggestions>[...]</suggestions>` 标签包裹的 JSON 数组格式嵌入回答中。

#### Scenario: 答疑后生成追问
- **WHEN** Tutor Agent 返回答疑内容
- **THEN** 回答中包含 3-4 个追问建议，后端解析提取后作为 `suggested_questions` 字段返回给前端

#### Scenario: 追问解析失败
- **WHEN** Tutor Agent 的回答中未包含有效的 `<suggestions>` 标签
- **THEN** 系统返回空的 `suggested_questions` 列表，不影响答疑内容的正常展示

### Requirement: Tutor API 端点
系统 SHALL 提供三个独立的 API 端点：`/tutor/start`（创建会话并获取首次答疑）、`/tutor/chat`（多轮追问）、`/tutor/end`（销毁会话）。

#### Scenario: POST /tutor/start
- **WHEN** 前端发送 `{session_id, question, tech_stack, difficulty}`
- **THEN** 返回 `{tutor_session_id, explanation, suggested_questions}`

#### Scenario: POST /tutor/chat
- **WHEN** 前端发送 `{tutor_session_id, message}`
- **THEN** 返回 `{explanation, suggested_questions}`

#### Scenario: POST /tutor/end
- **WHEN** 前端发送 `{tutor_session_id}`
- **THEN** 销毁会话并返回 `{message: "Session ended"}`

### Requirement: 面试状态隔离
Tutor 会话 SHALL 完全独立于面试会话。Tutor 的创建、对话和销毁 SHALL NOT 修改面试会话的任何状态（manager_history、interviewer_history、exchange_count、pending_buffer 等）。面试官 SHALL NOT 知道用户是否使用了学习功能。

#### Scenario: 学习后继续面试
- **WHEN** 用户在 Tutor 弹窗中完成多轮学习后关闭弹窗
- **THEN** 面试会话的状态与弹窗打开前完全一致，用户可以正常回答当前面试问题
