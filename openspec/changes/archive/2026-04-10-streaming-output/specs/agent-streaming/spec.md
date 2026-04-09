## ADDED Requirements

### Requirement: Interviewer 流式输出

系统 SHALL 提供 `stream_interviewer` 函数，使用 LangGraph agent 的 `.stream(stream_mode="messages")` 逐 token 输出 Interviewer 的回复文本。该函数 SHALL 返回 `Generator[str]`，每次 yield 一个文本片段。

#### Scenario: 流式输出面试回复
- **WHEN** 调用 `stream_interviewer` 并传入 system_prompt、user_message 和可选的 conversation_history
- **THEN** 函数 SHALL 返回 Generator，每次 yield 的文本片段为 LLM 产生的 token 文本

#### Scenario: 流式输出中的事件过滤
- **WHEN** LangGraph agent stream 产生事件
- **THEN** 系统 SHALL 过滤出 AIMessageChunk 类型的 content 文本，忽略工具调用和其他元数据事件

### Requirement: Tutor 流式输出

系统 SHALL 提供 `stream_tutor` 函数，与 `stream_interviewer` 同理，逐 token 输出 Tutor 的讲解内容。流结束后 SHALL 返回完整的原始文本，用于解析 `<suggestions>` 标签。

#### Scenario: 流式输出 Tutor 讲解
- **WHEN** 调用 `stream_tutor` 并传入 system_prompt、user_message 和可选的 conversation_history
- **THEN** 函数 SHALL 返回 Generator，每次 yield 一个文本片段

#### Scenario: Tutor 流结束后解析建议
- **WHEN** Tutor 流式输出完成
- **THEN** 系统 SHALL 收集完整文本并解析 `<suggestions>` 标签，提取追问建议列表

### Requirement: Manager Agent 保持阻塞调用

Manager Agent SHALL 继续使用 `.invoke()` 阻塞调用，不进行流式改造。

#### Scenario: Manager 判断完整性
- **WHEN** 需要判断候选人回答是否完整
- **THEN** 系统 SHALL 使用 `agent.invoke()` 阻塞调用 Manager，等待完整结果

### Requirement: Service 层 prepare-stream 分离

Service 层 SHALL 将业务逻辑分为 prepare（阻塞）和 stream（流式）两个阶段。prepare 阶段完成所有 Manager 调用和 session 状态修改，stream 阶段只进行 Interviewer/Tutor 的流式输出。

#### Scenario: 面试对话的 prepare-stream 分离
- **WHEN** 用户发送消息
- **THEN** 系统 SHALL 先执行 prepare（Manager 判断、状态更新），再执行 stream（Interviewer 流式输出）

#### Scenario: await 场景不触发 stream
- **WHEN** Manager 判断回答不完整（返回 `[AWAIT]`）
- **THEN** 系统 SHALL 直接返回追问信息，不调用 Interviewer，不进入 stream 阶段

#### Scenario: Tutor 的 prepare-stream 分离
- **WHEN** 调用 Tutor 服务
- **THEN** prepare 阶段 SHALL 准备参数和 session 状态，stream 阶段 SHALL 流式输出 Tutor 内容并在结束后解析 suggestions

### Requirement: session 状态安全

prepare 阶段对 session 的状态修改 SHALL 在 stream 阶段开始前完成。stream 阶段 SHALL NOT 修改 session 状态。

#### Scenario: stream 阶段不修改 session
- **WHEN** Interviewer 流式输出过程中
- **THEN** 系统 SHALL NOT 修改 session 的 questions、exchange_count、history 等状态字段。状态更新 SHALL 在流结束后由 API 层完成。
