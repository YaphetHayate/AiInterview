## ADDED Requirements

### Requirement: Per-session Manager 实例化
系统 SHALL 为每个面试会话创建独立的 Manager Agent 实例。不同会话的 Manager 实例之间 SHALL 完全隔离，不共享对话历史或状态。

#### Scenario: 创建新面试会话时实例化 Manager
- **WHEN** 用户发起一个新的面试会话
- **THEN** 系统创建一个新的 Manager Agent 实例，绑定到该 session
- **AND** 该实例持有独立的对话历史和 session-scoped 工具

#### Scenario: 多会话隔离
- **WHEN** 同时存在两个活跃的面试会话 A 和 B
- **THEN** 会话 A 的 Manager 调用工具时只能访问会话 A 的配置和数据
- **AND** 会话 B 的 Manager 调用工具时只能访问会话 B 的配置和数据

### Requirement: 工具工厂模式
系统 SHALL 通过工厂函数为每个 session 创建工具列表。`read_session_config` 工具 SHALL 通过闭包捕获 session 引用，使其能返回当前会话的配置信息。其他无状态工具（`read_skill_md`、`read_stage_file`、`fetch_questions_from_bank`）SHALL 保持原有行为不变。

#### Scenario: read_session_config 返回当前会话配置
- **WHEN** Manager Agent 调用 `read_session_config()` 工具
- **THEN** 工具返回当前 session 的完整配置信息，包括 tech_stack、difficulty、style、position、mode

#### Scenario: 无状态工具行为不变
- **WHEN** Manager Agent 调用 `read_skill_md()`、`read_stage_file()` 或 `fetch_questions_from_bank()`
- **THEN** 工具行为与重构前完全一致，不受 per-session 实例化的影响

### Requirement: Manager system prompt 固定不变
Manager Agent 的 system prompt SHALL 保持固定，不包含任何面试配置信息。面试配置 SHALL 只通过 `read_session_config()` 工具在运行时获取。

#### Scenario: Manager 启动时不感知配置
- **WHEN** Manager Agent 被实例化
- **THEN** 其 system prompt 中不包含 tech_stack、difficulty、style 等动态配置信息
- **AND** Manager 通过调用 `read_session_config()` 工具获取配置

### Requirement: 双模式上下文传递
系统 SHALL 同时支持两种上下文传递方式：工具主动获取（默认）和服务层注入（备选）。用户可通过代码修改在两种模式间切换。

#### Scenario: 默认模式 - 工具主动获取
- **WHEN** Manager 需要面试配置信息
- **THEN** Manager 主动调用 `read_session_config()` 获取

#### Scenario: 备选模式 - 服务层注入
- **WHEN** 启用服务层注入模式
- **THEN** 服务层在构建 Manager 输入消息时将配置信息注入 user message 中
