## ADDED Requirements

### Requirement: SSE 事件类型定义

系统 SHALL 定义以下 SSE 事件类型，每个事件为 JSON 格式，通过 `data:` 行发送：

| type | 用途 | 必需字段 |
|------|------|----------|
| `session` | 会话元信息 | `session_id`, `current_stage`, `stage_name` |
| `chunk` | 文本片段 | `content` |
| `await` | 追问（回答不完整） | `message` |
| `suggestions` | Tutor 追问建议 | `items` (string[]) |
| `error` | 错误信息 | `message` |
| `done` | 流结束 | 无 |

#### Scenario: 正常面试回复的 SSE 流
- **WHEN** 用户发送消息且 Manager 判断回答完整
- **THEN** SSE 流 SHALL 依次发送 `session` → 一个或多个 `chunk` → `done` 事件

#### Scenario: 追问场景的 SSE 流
- **WHEN** Manager 判断候选人回答不完整
- **THEN** SSE 流 SHALL 依次发送 `session` → `await` → `done` 事件，`await` 事件包含追问文本

#### Scenario: Tutor 回复的 SSE 流
- **WHEN** Tutor Agent 生成讲解内容
- **THEN** SSE 流 SHALL 依次发送 `session`（含 `tutor_session_id`）→ 一个或多个 `chunk` → `suggestions`（如有） → `done` 事件

#### Scenario: 流中途出错
- **WHEN** LLM 调用过程中发生异常
- **THEN** SSE 流 SHALL 发送已产生的 `chunk` 事件，然后发送 `error` 事件（含错误描述），最后发送 `done` 事件

### Requirement: SSE 端点

系统 SHALL 将以下端点改为返回 `text/event-stream` 的 SSE 流：

- `POST /interview` — 面试对话（含开始新会话和继续会话）
- `POST /tutor/start` — 开始 Tutor 会话
- `POST /tutor/chat` — Tutor 对话

#### Scenario: 面试端点返回 SSE
- **WHEN** 前端调用 `POST /interview`
- **THEN** 响应 Content-Type SHALL 为 `text/event-stream`，响应体为 SSE 事件流

#### Scenario: Tutor 端点返回 SSE
- **WHEN** 前端调用 `POST /tutor/start` 或 `POST /tutor/chat`
- **THEN** 响应 Content-Type SHALL 为 `text/event-stream`，响应体为 SSE 事件流

### Requirement: SSE 数据格式

每个 SSE 事件 SHALL 为 `data: <JSON>\n\n` 格式。JSON MUST 包含 `type` 字段标识事件类型。

#### Scenario: chunk 事件格式
- **WHEN** 系统发送一个文本片段
- **THEN** 事件格式 SHALL 为 `data: {"type":"chunk","content":"<文本>"}\n\n`

#### Scenario: done 事件格式
- **WHEN** 流结束
- **THEN** 事件格式 SHALL 为 `data: {"type":"done"}\n\n`
