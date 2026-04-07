## Context

当前系统有两套并行的技能系统：Python 类技能（`skills/simulation.py`、`skills/learning.py`）被 orchestrator 使用于单 Agent 模式；Markdown 技能（`skills/interviewProcess/SKILL.md`）被 Manager Agent 通过 file_reader tools 读取。两者互不联通，`dual_agent_service.py` 不区分 mode。

Manager Agent 当前职责过重——同时负责阶段判断、mode 分辨、JSON 结构化输出，且每次对话都读取 SKILL.md，LLM 输出格式不稳定导致 `dual_agent_service.py` 中大量容错代码（正则提取 JSON、fallback 默认值）。

## Goals / Non-Goals

**Goals:**
- Manager 职责聚焦为：回答完整性判断（受面试风格影响）+ 为 Interviewer 组装干净 prompt
- Python 确定性层接管：阶段状态机、mode 分辨、DB 获取问题、回答碎片拼接、上下文隔离
- 新 SKILL.md 以自然语言为主供 Manager LLM 读取，后续版本迭代迁移确定性部分到 Python
- Interviewer 只接收最干净的 prompt，不感知 mode、阶段、策略的存在
- 支持回答完整性检测：LLM 判断 + 用户确认，追问方式受面试风格影响

**Non-Goals:**
- 不改造单 Agent 模式（interview.py、orchestrator.py）和学习模式（learning.py）
- 不改动数据库 schema
- 不做前端适配（前端改动由后续迭代处理）
- 不迁移 Python 类技能系统（simulation.py/learning.py）的代码，保持原有单 Agent 流程可用
- 不实现会话数据库持久化（本次仍使用内存 dict + 日志）

## Decisions

### D1: Manager 每轮调用但职责更轻

**决定**：Manager 每轮对话都被调用，但只做两件事——判断回答完整性 + 组装 prompt。

**替代方案**：Manager 只在阶段转换时调用，每轮 prompt 由纯模板组装。
**不选原因**：用户明确要求 Manager 负责完整性检测，这是语义理解任务，无法模板化。

Manager 输出格式：
```json
{
  "action": "await_continuation" | "interview",
  "message_to_user": "...",
  "await_confirmation": false,
  "interviewer_prompt": {
    "system_prompt": "...",
    "user_message": "...",
    "context_thread": [...],
    "instructions": { ... }
  }
}
```

### D2: 会话状态数据结构重新设计

**决定**：session 内部按 `question_threads` 组织对话，支持按问题隔离上下文。

```
Session
├── meta: session_id, mode, stage, style, difficulty, ...
├── questions: [
│     { id, content, status, thread: [...], summary }
│   ]
├── current_question_idx: int
├── pending_buffer: [...]      ← 回答碎片拼接缓冲区
├── stage_summaries: [...]
└── manager_history: [...]     ← Manager 完整对话历史
```

simulation 模式：传给 Interviewer 的 `context_thread` 只含当前问题的对话。
learning 模式：传完整 `interviewer_history`。

### D3: 回答完整性检测流程

**决定**：Python 层拼接碎片 → Manager 判断完整性 → 不完整则返回 `await_continuation` → 用户确认或继续发送 → 完整后 Manager 组装 prompt 传给 Interviewer。

追问话术受面试风格影响（challenging 即使完整也可能追问"还有吗"），策略写在 SKILL.md 中。
Python 层拼接后如果发现重复或不通顺，Manager 可以要求用户重新完整回答或 LLM 重构语言。

### D4: 新 SKILL.md 结构

**决定**：分层引用，SKILL.md 包含高频策略（完整性判断、mode 差异、prompt 规范），stage 文件按需读取。

```
skills/interviewManager/
├── SKILL.md                              ← 总览 + 核心策略
└── references/
    └── stages/
        ├── stage1_basic_knowledge.md
        ├── stage2_project_experience.md
        ├── stage3_job_matching.md
        └── stage4_summary.md
```

面试开始时 Manager 读 SKILL.md + 对应 mode 策略，阶段内每轮不读文件。阶段转换时读下一个 stage 文件。

### D5: Manager Agent 实现方式

**决定**：继续使用 `create_react_agent` + file_reader tools，但 tools 适配新目录结构。新增 `read_skill_md` 指向 `skills/interviewManager/SKILL.md`，`read_stage_file` 指向新 stage 文件。

## Risks / Trade-offs

**[Manager JSON 输出不稳定]** → Python 层解析时保留容错逻辑（正则提取 + fallback），但 Manager 输出格式更简单（只有 action + 两个字段），不稳定风险降低。

**[完整性检测误判]** → 允许用户通过发送"完毕"/"回复完毕"强制确认，降低误判影响。后续版本可加入用户超时自动推进。

**[SKILL.md 内容过多导致 token 浪费]** → 首次读取后 Manager 在 history 中保留了 SKILL.md 内容，后续轮次不需要重新读取。如果 token 压力大，后续版本可将 stage 文件改为 Python 解析。

**[两套技能系统并存]** → 本次不迁移旧技能代码，双 Agent 模式使用新 skill，单 Agent 模式继续使用旧技能。后续统一。

## Open Questions

- 阶段摘要（stage_summaries）是 Manager 在阶段转换时一次性生成，还是每题结束后逐步积累？
- 面试总结报告是一次 LLM 调用还是拆成多次（先各阶段汇总，再综合评价）？
- 前端如何展示 `await_continuation` 状态——是聊天气泡还是输入框提示？
