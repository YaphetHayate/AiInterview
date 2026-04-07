## ADDED Requirements

### Requirement: Manager 读取 SKILL.md 获取策略知识
Manager Agent SHALL 在面试开始时读取 `skills/interviewManager/SKILL.md`，获取面试流程定义、mode 差异策略、完整性判断策略、prompt 组装规范等知识。

#### Scenario: 面试启动时加载 SKILL
- **WHEN** 面试会话启动（`start_interview` 调用）
- **THEN** Manager 读取 `skills/interviewManager/SKILL.md`，将内容存入对话历史，后续轮次无需重复读取

### Requirement: Manager 组装干净 prompt 给 Interviewer
Manager SHALL 为 Interviewer 组装 prompt，确保 Interviewer 不感知 mode、阶段、策略的存在。prompt 只包含面试官人设、当前考察方向、候选人完整回答、具体执行指令。

#### Scenario: 拟真模式 prompt 组装
- **WHEN** mode 为 simulation，候选人在阶段 1 回答了一个基础知识问题
- **THEN** Manager 输出的 `interviewer_prompt.system_prompt` 只包含面试官人设 + 当前考察要点，不包含"这是拟真模式"或"这是阶段1"等信息

#### Scenario: 学习模式 prompt 组装
- **WHEN** mode 为 learning，候选人在回答一个知识点
- **THEN** Manager 输出的 `interviewer_prompt.instructions.mode_hint` 包含"可以适当引导和提供参考答案"的提示，Interviewer 据此调整行为

### Requirement: Manager 阶段转换时读取 stage 文件
Manager SHALL 在阶段转换时通过 tool 调用读取对应阶段的指引文件，获取该阶段的考察要点和提问建议。

#### Scenario: 从阶段 1 进入阶段 2
- **WHEN** Python 确定性层判断阶段 1 已完成，推进到阶段 2
- **THEN** Manager 调用 `read_stage_file(2)` 读取阶段 2 指引，基于指引组装下一阶段的 prompt 给 Interviewer

### Requirement: Manager 输出格式
Manager SHALL 输出 JSON 格式的响应，包含 `action` 字段（`await_continuation` 或 `interview`），以及对应的详细字段。

#### Scenario: 回答完整时的输出
- **WHEN** Manager 判断候选人回答完整
- **THEN** 输出 `{"action": "interview", "interviewer_prompt": {"system_prompt": "...", "user_message": "...", "context_thread": [...], "instructions": {...}}}`

#### Scenario: 回答不完整时的输出
- **WHEN** Manager 判断候选人回答不完整
- **THEN** 输出 `{"action": "await_continuation", "message_to_user": "...", "await_confirmation": false}`

### Requirement: Python 确定性层处理阶段状态机
`dual_agent_service.py` SHALL 由 Python 代码负责阶段推进判断，不依赖 Manager LLM 判断当前阶段。阶段推进条件基于问题完成数量和交互次数。

#### Scenario: 阶段 1 问题全部完成
- **WHEN** 阶段 1 的所有问题已回答完毕（DB 中无剩余问题或达到配置数量）
- **THEN** Python 层自动推进到阶段 2，通知 Manager 读取阶段 2 指引

#### Scenario: 候选人说"下一阶段"
- **WHEN** 候选人发送"下一阶段"关键词
- **THEN** Python 层直接推进阶段，无需 Manager 判断
