## Context

当前系统采用双 Agent 架构（Manager + Interviewer），Manager 为全局单例，所有面试会话共享同一个 Manager Agent 实例。面试配置（技术栈、难度、风格等）通过第一条 user message 传入 Manager 的对话历史。服务层（`dual_agent_service.py`）承担了大量上下文拼装职责，包括手动构建包含配置、阶段、题目、追问次数等信息的上下文消息。

现有问题：
- 配置信息埋在对话历史中，随着对话增长可能被推远
- Manager 无法主动获取配置，完全依赖服务层喂入
- 全局单例在并发场景下存在潜在的 history 串扰风险
- Manager 对候选人回答的整合策略不够明确
- Interviewer 缺少对"知识点完整性和准确性"评估导向的强调

## Goals / Non-Goals

**Goals:**
- Manager 改为 per-session 实例化，每个面试会话拥有独立的 Manager
- Manager 通过工具主动获取 session 配置，减少对服务层上下文注入的依赖
- 明确 Manager 的回答整合边界：只排列不修改
- Interviewer prompt 强调知识点完整性和准确性评估

**Non-Goals:**
- Session 生命周期管理（超时清理、数量上限）
- Session 持久化与跨重启恢复
- 前端交互流程变更
- 数据库 schema 变更
- 阶段转换、面试总结等现有业务逻辑的重构

## Decisions

### D1: Per-session Manager 实例化

Manager 从全局单例改为 per-session 实例。每次创建面试会话时实例化一个新的 Manager Agent。

**方案选择：**
- ~~全局单例 + RunnableConfig 透传 session_id~~：可行但增加间接层，工具需要从 config 中提取 session_id 再查全局 map
- **Per-session 实例 + 工具闭包**：工具创建时捕获 session 引用，Manager 直接使用，零间接层 ✓

**实现方式：** `manager_agent.py` 导出 `create_manager_agent(session)` 工厂函数，返回绑定了 session-scoped 工具的 Agent 实例。Session 对象持有该 Manager 实例的引用。

### D2: 工具工厂模式

工具从模块级全局函数改为工厂模式创建。

**结构：**
```
tools/tool_factory.py
  └── create_session_tools(session) → list[BaseTool]
        ├── read_session_config()    ← 新增，闭包捕获 session.config
        ├── read_skill_md()          ← 无状态，可共享
        ├── read_stage_file(n)       ← 无状态，可共享
        └── fetch_questions_from_bank(...)  ← 无状态，可共享
```

仅 `read_session_config` 需要 per-session 创建（闭包捕获 session），其余工具本质上无状态，但为架构一致性统一通过工厂创建。

### D3: 双模式上下文传递

保留两种方式并存：
- **默认模式（工具主动获取）**：Manager 在需要时调用 `read_session_config()` 获取配置
- **备选模式（服务层注入）**：服务层仍可在 user message 中注入上下文，供手动切换验证

服务层在构建 Manager 输入消息时，从当前主动拼装全部上下文的方式，逐步过渡到只传用户回答和最小上下文。

### D4: Manager 回答整合策略

Manager 在判断候选人回答完整后，对散乱的回答做结构化整理再传给 Interviewer：

**允许的操作：**
- 将多段分散的回答合并为一段
- 将散乱的回答内容按子问题结构对齐排列

**禁止的操作：**
- 增加候选人未提及的内容
- 删除或修改候选人的原始表述
- 润色措辞或修正专业术语
- 补充隐含的语义扩展

### D5: Interviewer 评估导向

在 Interviewer 的 system_prompt 中明确：
- 评估重心是知识点的完整性和准确性
- 追问应聚焦于"这个知识点能否展开"而非"能否表达得更清楚"
- 不因表达不流畅而降低评价

## Risks / Trade-offs

- **[Per-session 内存开销]** → 每个 session 多一个 Manager 实例（约几 KB 的 prompt template 对象），在当前规模（单机、少量并发）下可忽略
- **[工具调用增加延迟]** → Manager 主动获取配置意味着多一轮工具调用，增加 token 消耗和响应时间。通过缓存和合理的使用时机控制
- **[LLM 整合不一致]** → Manager 整合回答时可能不严格遵守"只排列不修改"原则。需要在 system prompt 中给出明确的 do/don't 示例
- **[过渡期兼容性]** → 服务层上下文注入和工具主动获取两种模式并存，可能导致 Manager 收到重复信息。需要在 prompt 中说明"优先使用工具获取的信息"
