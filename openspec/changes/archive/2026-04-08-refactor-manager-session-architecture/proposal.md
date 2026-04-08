## Why

当前 Manager Agent 采用全局单例模式，面试配置（技术栈、难度、风格等）通过第一条 user message 传入对话历史，随着对话增长配置信息逐渐被推远，Manager 对配置的感知减弱。同时服务层承担了过多的上下文拼装职责，Manager 缺乏主动获取配置的能力。此外，Manager 对候选人回答的整合策略不够明确，Interviewer 的评估导向也缺少对"知识点完整性和准确性"的强调。

## What Changes

- **BREAKING**: Manager Agent 从全局单例改为 per-session 实例化，每个面试会话拥有独立的 Manager 实例
- **BREAKING**: 新增 `read_session_config()` 工具，Manager 通过工具主动获取当前 session 的面试配置，替代通过 user message 传入的方式
- 工具创建方式从模块级全局函数改为 factory 模式，支持闭包捕获 session 上下文
- 明确 Manager 的回答整合策略：只做分段合并和子问题对齐，不增删、不润色候选人回答内容
- 优化 Interviewer 的 system_prompt，强调评估重心为知识点的完整性和准确性
- 保留服务层上下文注入作为备选方式，默认使用工具主动获取

## Capabilities

### New Capabilities
- `session-scoped-manager`: per-session Manager 实例化、工具工厂模式、session 配置的主动获取
- `answer-integration`: 候选人回答的完整性判断与结构化整合策略

### Modified Capabilities

## Impact

- `agents/manager_agent.py`: 从单例改为 factory 模式，接收 session-scoped 工具列表
- `agents/interviewer_agent.py`: 优化 INTERVIEWER_BASE_PROMPT，强调知识点评估导向
- `tools/file_reader.py`: 重构为 tool factory，新增 `read_session_config()` 工具
- `service/dual_agent_service.py`: session 结构调整，简化上下文拼装逻辑
- `prompt/initialization.py`: Interviewer prompt 模板增加知识点评估相关指导

## 非目标

- Session 生命周期管理（超时清理、数量上限）后续单独处理
- Session 持久化与恢复功能后续单独处理
- 不改变现有的数据库 schema
- 不改变前端交互流程
