## Why

当前三个 Agent（Manager、Interviewer、Tutor）均使用 `.invoke()` 阻塞调用，用户发送消息后需等待 10-30 秒才能看到完整回复。面试场景中这种长时间空白严重影响对话体验和沉浸感，用户无法判断系统是否仍在工作。流式输出能让用户在前 1-2 秒就看到文字逐步出现，显著改善交互体验。

## What Changes

- Agent 层新增流式调用函数，Interviewer Agent 和 Tutor Agent 使用 `.stream()` 替代 `.invoke()` 逐 token 输出
- Service 层将 Interviewer/Tutor 的最终输出改为 Generator，Manager 内部逻辑保持阻塞不变
- API 层新增 SSE（Server-Sent Events）端点替代原有的 JSON 同步端点，支持 `/interview`、`/tutor/start`、`/tutor/chat` 三个流式接口
- 前端 `fetch` 改为 `ReadableStream` 消费 SSE，`addMessage` 改为增量追加模式，用累积原文 + 防抖重渲染策略处理 Markdown

## Capabilities

### New Capabilities

- `streaming-protocol`: SSE 协议定义，包括事件类型（session、chunk、await、suggestions、error、done）、数据格式和错误处理规范
- `agent-streaming`: Agent 层流式调用封装，基于 LangGraph `CompiledStateGraph.stream(stream_mode="messages")` 的 token 级流式输出
- `frontend-streaming`: 前端 SSE 消费、增量 Markdown 渲染、流式消息 UI 更新

### Modified Capabilities

## Impact

- **API 层** (`web/api.py`): `/interview`、`/tutor/start`、`/tutor/chat` 端点从返回 JSON 改为 `StreamingResponse`
- **Service 层** (`service/dual_agent_service.py`, `service/tutor_service.py`): 最终输出步骤改为 Generator
- **Agent 层** (`agents/interviewer_agent.py`, `agents/tutor_agent.py`): 新增 `stream_interviewer` / `stream_tutor` 函数
- **前端** (`frontend/index.html`): 消息发送和渲染逻辑重写
- **非目标**: Manager Agent 不做流式改造；不引入 WebSocket；不做真正的流式 Markdown 解析器；不改动 `/options`、`/styles`、`/session/reset` 等非对话端点
