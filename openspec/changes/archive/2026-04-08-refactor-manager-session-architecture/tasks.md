## 1. 工具工厂模式

- [x] 1.1 创建 `tools/tool_factory.py`，实现 `create_session_tools(session_config: dict)` 工厂函数，返回包含 `read_session_config`、`read_skill_md`、`read_stage_file`、`fetch_questions_from_bank` 的工具列表。其中 `read_session_config` 通过闭包捕获 `session_config`，其余工具保持原有逻辑。
- [x] 1.2 保留 `tools/file_reader.py` 不删除（向后兼容），在其中添加弃用提示，引导使用 `tool_factory.py`。

## 2. Manager Agent 重构为 Per-session

- [x] 2.1 重构 `agents/manager_agent.py`：移除全局单例缓存 `_manager_agents` 和 `_lock`，新增 `create_manager_agent(session_config: dict)` 工厂函数，调用 `create_session_tools(session_config)` 获取工具列表并创建 Agent 实例。保留 `MANAGER_SYSTEM_PROMPT` 不变。
- [x] 2.2 移除 `invoke_manager(messages)` 单例入口函数，改为在 session 中直接持有 Manager Agent 实例并调用。

## 3. Session 结构与 dual_agent_service 适配

- [x] 3.1 修改 `service/dual_agent_service.py` 中 `_sessions` 的 session 结构：新增 `manager_agent` 字段持有 per-session Manager 实例，新增 `config` 字段持久化面试配置（tech_stack, difficulty, style, position, mode）。
- [x] 3.2 修改 `start_dual_interview(config)` 函数：将 config 存入 session，调用 `create_manager_agent(session.config)` 创建 Manager 实例并存入 session。
- [x] 3.3 修改 `dual_interview_chat(session_id, user_input)` 及相关内部函数：从 session 中获取 Manager 实例调用，不再使用全局 `invoke_manager`。
- [x] 3.4 简化服务层上下文拼装逻辑：将当前手动拼入 user message 的配置信息（tech_stack, difficulty, style 等）改为可选注入，默认依赖 Manager 工具主动获取。保留注入路径作为备选模式。

## 4. Manager 提示词 - 回答整合策略

- [x] 4.1 在 `agents/manager_agent.py` 的 `MANAGER_SYSTEM_PROMPT` 中补充回答整合策略章节：明确只做分段合并和子问题对齐，给出 do/don't 具体示例，强调不增删内容、不润色措辞。

## 5. Interviewer 提示词 - 知识点评估导向

- [x] 5.1 修改 `prompt/initialization.py` 中的 `SYSTEM_PROMPT_TEMPLATE`：在交互规则章节中增加"评估重心为知识点的完整性和准确性，追问聚焦于知识点的深入展开，不因表达方式降低评价"。
- [x] 5.2 修改 `agents/interviewer_agent.py` 中的 `INTERVIEWER_BASE_PROMPT`：增加知识点评估导向的行为准则。
