## ADDED Requirements

### Requirement: 前端 SSE 消费

前端 SHALL 使用 `fetch` + `ReadableStream` 消费 SSE 流，解析每个 `data:` 行为 JSON 对象，根据 `type` 字段分发处理。

#### Scenario: 消费 SSE 流
- **WHEN** 前端发送 POST 请求到 `/interview` 或 `/tutor/*` 端点
- **THEN** SHALL 通过 `response.body.getReader()` 逐块读取响应，解析 SSE `data:` 行

#### Scenario: 解析 SSE 事件
- **WHEN** 读取到 `data: {...}\n\n` 格式的行
- **THEN** SHALL 解析 JSON 并根据 `type` 字段分发到对应处理逻辑

### Requirement: 流式消息增量渲染

前端 SHALL 采用累积原文 + 防抖重渲染策略处理流式 Markdown。具体：

1. 维护一个累积文本 buffer
2. 收到 `chunk` 事件时追加到 buffer
3. 以 50ms 间隔使用 `marked.parse(buffer)` 重新渲染消息区域

#### Scenario: chunk 事件处理
- **WHEN** 前端收到 `{"type":"chunk","content":"<text>"}` 事件
- **THEN** SHALL 将 content 追加到 buffer，触发防抖渲染

#### Scenario: 防抖渲染执行
- **WHEN** 距离上次渲染已过 50ms 且有新内容
- **THEN** SHALL 使用 `marked.parse(buffer)` 重新渲染消息区域的 innerHTML

#### Scenario: 流结束的最终渲染
- **WHEN** 收到 `done` 事件
- **THEN** SHALL 立即用完整 buffer 做一次最终 Markdown 渲染，确保最终显示正确

### Requirement: 流式消息 UI 行为

前端在流式输出期间 SHALL 展示已收到的文本，而非跳动动画。流结束后恢复可交互状态。

#### Scenario: 流开始时创建消息区域
- **WHEN** 收到第一个 `chunk` 或 `await` 事件
- **THEN** SHALL 创建 AI 消息气泡，隐藏 typing indicator

#### Scenario: 流进行中禁止用户操作
- **WHEN** 流式输出正在进行
- **THEN** 发送按钮和输入框 SHALL 处于 disabled 状态

#### Scenario: 流结束后恢复交互
- **WHEN** 收到 `done` 事件
- **THEN** SHALL 启用发送按钮和输入框，聚焦输入框

### Requirement: await 事件处理

前端收到 `await` 事件时 SHALL 直接显示追问文本作为 AI 消息，不做流式渲染。

#### Scenario: 显示追问消息
- **WHEN** 前端收到 `{"type":"await","message":"请继续补充"}` 事件
- **THEN** SHALL 将 message 文本作为 AI 消息直接渲染（使用 Markdown 渲染）

### Requirement: suggestions 事件处理

前端收到 `suggestions` 事件时 SHALL 渲染追问建议按钮。

#### Scenario: 显示追问建议
- **WHEN** 前端收到 `{"type":"suggestions","items":["为什么...","它和..."]}` 事件
- **THEN** SHALL 渲染对应的建议按钮，按钮可点击触发 Tutor 对话

### Requirement: error 事件处理

前端收到 `error` 事件时 SHALL 保留已显示的内容，并追加错误提示。

#### Scenario: 流中途出错
- **WHEN** 前端收到 `{"type":"error","message":"LLM 连接超时"}` 事件
- **THEN** SHALL 保留已渲染的内容，在消息区域追加错误提示（红色样式），后续收到 `done` 事件时恢复正常状态

### Requirement: session 事件处理

前端收到 `session` 事件时 SHALL 更新本地 session 状态。

#### Scenario: 更新 session_id
- **WHEN** 前端收到 `{"type":"session","session_id":"abc",...}` 事件
- **THEN** SHALL 更新本地 `sessionId` 变量

#### Scenario: 更新阶段信息
- **WHEN** 前端收到包含 `current_stage` 和 `stage_name` 的 session 事件
- **THEN** SHALL 更新页面上的阶段显示信息
