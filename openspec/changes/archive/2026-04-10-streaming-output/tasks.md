## 1. Agent 层流式封装

- [x] 1.1 在 `agents/interviewer_agent.py` 中新增 `stream_interviewer` 函数，使用 `agent.stream(stream_mode="messages")` 逐 token yield 文本，过滤出 AIMessageChunk 的 content，保持与 `invoke_interviewer` 相同的输入签名（system_prompt, user_message, conversation_history）
- [x] 1.2 在 `agents/tutor_agent.py` 中新增 `stream_tutor` 函数，同理逐 token yield 文本，流结束后收集完整文本用于 `<suggestions>` 标签解析，返回 `Generator[tuple[str, bool]]`（bool 标识是否为最后一个 chunk，最后一个 chunk 携带完整文本用于解析）

## 2. Service 层 prepare-stream 拆分

- [x] 2.1 在 `service/dual_agent_service.py` 中新增 `prepare_dual_interview_start(config)` 函数，提取 `start_dual_interview` 中 Manager 调用和 session 初始化逻辑（阻塞），返回 `(session_meta: dict, stream_params: dict)`，stream_params 包含 agent、system_prompt、user_message 等
- [x] 2.2 在 `service/dual_agent_service.py` 中新增 `stream_interview_reply(stream_params)` 函数，接收 stream_params 调用 `stream_interviewer`，yield 文本片段
- [x] 2.3 在 `service/dual_agent_service.py` 中新增 `prepare_dual_interview_chat(session_id, user_input)` 函数，提取 `dual_interview_chat` 中 Manager 判断完整性的逻辑，返回 `(meta: dict, action: str, stream_params_or_message)`。当 action 为 `await` 时直接返回追问文本；当 action 为 `interview` 时返回 stream_params
- [x] 2.4 在 `service/dual_agent_service.py` 中新增 `finalize_interview_chat(session_id, full_reply)` 函数，流结束后更新 session 状态（history、exchange_count、question thread 等）
- [x] 2.5 在 `service/tutor_service.py` 中新增 `prepare_tutor_start(...)` 和 `stream_tutor_reply(stream_params)` 函数，拆分 `start_tutor_session` 为 prepare-stream 两阶段
- [x] 2.6 在 `service/tutor_service.py` 中新增 `prepare_tutor_chat(...)` 和 `stream_tutor_chat_reply(stream_params)` 函数，拆分 `chat_tutor_session` 为 prepare-stream 两阶段

## 3. API 层 SSE 端点

- [x] 3.1 在 `web/api.py` 中新增 SSE 事件格式化工具函数 `sse_event(event_type, data) -> str`，将 dict 转为 `data: <json>\n\n` 格式
- [x] 3.2 修改 `web/api.py` 中的 `interview_session_view` 端点，改为返回 `StreamingResponse(media_type="text/event-stream")`，内部调用 prepare → yield SSE events → stream chunks → finalize
- [x] 3.3 修改 `web/api.py` 中的 `tutor_start_view` 端点，改为返回 `StreamingResponse`，调用 prepare_tutor_start → stream_tutor_reply，流结束后 yield suggestions 事件
- [x] 3.4 修改 `web/api.py` 中的 `tutor_chat_view` 端点，改为返回 `StreamingResponse`，调用 prepare_tutor_chat → stream_tutor_chat_reply，流结束后 yield suggestions 事件
- [x] 3.5 在 `web/api.py` 的流式端点中添加异常处理：捕获 LLM 调用异常，yield error 事件后再 yield done 事件

## 4. 前端流式消费

- [x] 4.1 在 `frontend/index.html` 中新增 `consumeSSE(response, handlers)` 工具函数，使用 `ReadableStream.getReader()` 解析 SSE `data:` 行，根据 `type` 字段调用对应 handler（onSession、onChunk、onAwait、onSuggestions、onError、onDone）
- [x] 4.2 修改 `sendMessage()` 函数，将 `fetch` 调用改为使用 `consumeSSE`，处理 session/chunk/await/error/done 事件
- [x] 4.3 新增 `createStreamingMessage()` 函数，创建空的 AI 消息 DOM 元素并返回，用于增量更新 innerHTML
- [x] 4.4 实现防抖 Markdown 渲染：在 chunk handler 中累积 buffer，使用 50ms 间隔的 `requestAnimationFrame` 或 `setTimeout` 调用 `marked.parse(buffer)` 更新消息 innerHTML，done 事件触发最终渲染
- [x] 4.5 修改 `requestExplain()` 函数，Tutor start 走 SSE 流，处理 session/chunk/suggestions/error/done 事件
- [x] 4.6 修改 `sendTutorChat()` 函数，Tutor chat 走 SSE 流，处理 session/chunk/suggestions/error/done 事件

## 5. 验证

- [x] 5.1 启动服务端，测试 `/interview` 开始新会话的 SSE 流输出是否正常（session → chunk × N → done）
- [x] 5.2 测试 `/interview` 继续对话时 await 场景
- [x] 5.3 测试 `/tutor/start` 和 `/tutor/chat` 的 SSE 流输出
- [x] 5.4 测试流中途出错时前端显示
- [x] 5.5 验证流结束后 session 状态
