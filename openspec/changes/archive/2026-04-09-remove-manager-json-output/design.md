## Context

当前 Manager Agent 使用 LangGraph `create_react_agent` 创建，system prompt 要求其"严格输出 JSON 格式"。`dual_agent_service.py` 中 `_parse_manager_response` 函数通过正则 `\{[\s\S]*\}` 提取 JSON，再用 `json.loads` 解析，最终路由到 `await_continuation` 或 `interview` 分支。

实际运行中，LLM 输出的 JSON `system_prompt` 和 `user_message` 字段频繁缺失或质量不足，3/4 调用点依赖 fallback 兜底（`_get_fallback_system_prompt` + 默认 `user_message` 拼接）。仅 `action` 字段和 `message_to_candidate` 字段被有效消费。

```
当前数据流:

Manager Agent ──"严格JSON"──▶ raw text ──regex+json.loads──▶ dict
                                                               │
                                    ┌──────────────────────────┘
                                    ▼
                        3/4 调用点: system_prompt/user_message 为空
                                    → fallback 兜底
                        1/4 调用点: action 路由有效
```

## Goals / Non-Goals

**Goals:**

- 消除 JSON 序列化/反序列化带来的 token 开销和解析异常风险
- 将 prompt 组装（system_prompt、user_message）完全交给确定性代码
- 保留 Manager 的完整性判断能力，用更轻量的方式路由

**Non-Goals:**

- 不改变 Manager 的 ReAct agent 架构和 tools 能力
- 不引入 structured output / function calling 等新机制
- 不优化 `_get_fallback_system_prompt` 的 prompt 内容质量
- 不修改 Interviewer Agent 的任何逻辑

## Decisions

### D1: Manager 输出自然语言，用文本标记 `[AWAIT]` 路由

Manager prompt 改为：判断回答不完整时，以 `[AWAIT]` 开头后跟追问话术；判断回答完整时，输出对面试官的自然语言指导（或直接输出任何内容）。

代码侧判断逻辑：`response.startswith("[AWAIT]")` → 追问分支，否则 → 完整回答分支。

**为什么不用 LLM 做路由**：路由是一个二元决策，不需要 LLM 的创造力。用文本标记把决策权交给 LLM 的判断能力，但解析权交给确定性代码。

**为什么不用正则**：单一前缀标记比正则更简单可靠，不存在贪婪匹配或意外匹配的风险。

### D2: system_prompt 和 user_message 由确定性代码组装

现有的 fallback 逻辑升级为主路径：
- `system_prompt`：由 `_get_fallback_system_prompt(session)` 生成（基于 session 配置 + 阶段信息）
- `user_message`：由确定性代码拼接（候选人回答 + 执行指令 + 模式提示）

Manager 在完整性判断通过后的输出，作为面试指导附加到 `user_message` 中，供 Interviewer 参考。如果 Manager 输出为空或无实质内容，仍然使用默认指令。

**为什么不保留 Manager 组装 prompt 的能力**：LLM 不擅长严格按 schema 输出，Python 天然擅长。把 LLM 从"填表"工作中解放出来，让它专注于判断和指导。

### D3: `_handle_final_summary` 不变

该函数已经不解析 JSON，直接使用 Manager 原文，无需修改。

## Risks / Trade-offs

**[风险] LLM 可能不稳定输出 `[AWAIT]` 标记** → 标记放在回答最开头，是最简单的指令之一。如果 LLM 忽略标记，最坏情况是把不完整的回答当作完整回答处理，Interviewer 会自然追问，不会导致系统崩溃。

**[权衡] Manager 输出的面试指导可能更难结构化传递给 Interviewer** → 作为自然语言附加到 `user_message` 中，Interviewer 本身就是 LLM，能理解自然语言指导。比 JSON 包裹更自然。

**[风险] 删除 JSON 解析后，失去对 Manager 输出的结构化校验能力** → 原本的 JSON 校验也从未真正生效过（fallback 兜底），所以没有实际损失。
