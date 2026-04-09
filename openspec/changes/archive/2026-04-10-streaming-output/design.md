## Context

当前面试平台采用同步请求-响应模式。三个 Agent（Manager、Interviewer、Tutor）均通过 `.invoke()` 阻塞调用，用户发送消息后需等待 Manager 判断 + Interviewer 生成完整回复（10-30 秒），期间仅有 CSS 跳动动画提示。前端通过 `fetch` 发送 JSON，一次性渲染完整 Markdown 回复。

技术栈：FastAPI 后端，LangChain `create_agent` / LangGraph `create_react_agent` 创建 Agent，`ChatOpenAI` 模型实例，前端为纯 HTML/JS 单文件。

## Goals / Non-Goals

**Goals:**

- Interviewer Agent 和 Tutor Agent 的最终输出改为逐 token 流式推送给前端
- 用户在 Manager 处理完成后 1-2 秒内看到文字开始出现
- 统一 SSE 协议覆盖正常回复、追问（await）、Tutor 建议等所有场景
- 前端增量渲染 Markdown，无明显闪烁或跳动

**Non-Goals:**

- Manager Agent 流式化（其输出仅供系统内部消费）
- WebSocket 双向通信（当前场景是请求-响应模式，SSE 足够）
- 流式 Markdown 解析器（使用累积原文 + 防抖重渲染）
- 多模态流式（音频、视频）
- 修改非对话端点（`/options`、`/styles`、`/session/reset`）

## Decisions

### 1. 传输协议：SSE（Server-Sent Events）

**选择 SSE 而非 WebSocket。**

| 维度 | SSE | WebSocket |
|------|-----|-----------|
| 方向 | 服务端→客户端（单向） | 双向 |
| 复杂度 | 低，HTTP 协议 | 需要连接管理、心跳、重连 |
| 适配性 | FastAPI `StreamingResponse` 原生支持 | 需要 WebSocket 端点 |
| 场景匹配 | 请求→流式响应，完美匹配 | 过度设计 |

### 2. Agent 流式方式：`agent.stream(stream_mode="messages")`

Interviewer 和 Tutor 由 `create_agent` 创建，返回 `CompiledStateGraph`。其 `.stream(stream_mode="messages")` 会产生 `(AIMessageChunk, metadata)` 事件流，可逐 token 提取文本。

Manager 由 `create_react_agent` 创建，会调用工具（`read_skill_md` 等），流式事件包含工具调用过程。Manager 保持 `.invoke()` 不变，原因：
- 输出是内部元数据（完整性判断、prompt 组装），不面向用户
- 其工具调用过程对用户无意义
- 避免引入复杂的 event type 过滤逻辑

### 3. Service 层拆分：prepare + stream 两阶段

```
原流程:
  service_function() → dict

新流程:
  service_function_prepare() → (meta: dict, stream_params: dict)
  service_function_stream(stream_params) → Generator[str]
```

`prepare` 完成所有 Manager 调用和状态管理（阻塞），`stream` 只负责 Interviewer/Tutor 的流式输出。这样 Service 层的状态管理逻辑无需改为异步。

### 4. 前端 Markdown 渲染：累积原文 + 防抖重渲染

在 SSE 流中累积原始 Markdown 文本，每 50ms 用 `marked.parse()` 重新渲染整个内容。原因：
- `marked` 不支持流式解析，要实现真正的增量解析需要自己写 parser
- 50ms 重渲染一次，以 LLM 输出速度（~30-50 tokens/s），每帧新增 1-2 个 token，`innerHTML` 替换是同步的，人眼不会感知闪烁
- 实现简单，代码量约 30 行

### 5. SSE 协议统一处理 await 场景

Manager 判断回答不完整时返回 `[AWAIT]` 前缀，此时不需要 Interviewer 调用。统一走 SSE：

```
正常:     session → chunk × N → done
追问:     session → await → done
错误:     session → chunk × N → error → done
```

前端无需区分"这次请求是流式还是非流式"，只看 event type。

## Risks / Trade-offs

- **[防抖重渲染的性能] → 50ms 间隔限制渲染频率。** 当 Markdown 文本超过 ~5000 字时重渲染可能有延迟。缓解：在流结束后再做一次最终渲染。
- **[`stream_mode="messages"` 的事件过滤] → 需要正确识别 AIMessageChunk。** LangGraph 的 stream 事件包含多种类型（工具调用、AI 输出等），需要过滤出最终的 AI 文本 chunk。缓解：在 agent 层封装过滤逻辑，只 yield 纯文本。
- **[SSE 连接中断] → 前端需要处理断连。** 网络不稳定时 SSE 可能中断。缓解：显示已收到的部分 + 错误提示，用户可重新发送。
- **[线程安全] → Service 层的 session 修改仍在线程锁内。** `prepare` 阶段修改 session 状态（阻塞），`stream` 阶段只读取数据不改状态，不引入新的并发问题。
