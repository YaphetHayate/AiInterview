## ADDED Requirements

### Requirement: 废弃文件删除
系统 SHALL 不包含以下文件：`service/guide.py`、`prompt/manager.py`、`check_db.py`、`connect_db.py`、`sql_commands.sql`。这些文件无外部引用且包含调用不存在方法的死代码。

#### Scenario: 项目启动不受影响
- **WHEN** 执行 `python main.py cli` 或 `python main.py web`
- **THEN** 系统正常启动，无 ImportError 或 ModuleNotFoundError

#### Scenario: API 端点功能完整
- **WHEN** 向 `/interview`、`/session/reset`、`/options`、`/styles`、`/question-bank/tree`、`/session/{id}/progress` 发送请求
- **THEN** 所有端点行为与删除前完全一致

### Requirement: 模型工厂清理
`agents/modelFactory.py` SHALL 不包含模块级 Ollama 实例（`process_manager_ollama`、`interviewer_chat_ollama`）和未使用的 `get_zhipu_chat()`、`get_minimax_chat()` 函数及其关联变量。

#### Scenario: 模型按需创建不受影响
- **WHEN** 调用 `process_manager()` 或 `interviewer_chat()` 
- **THEN** 通过 factory map 正常返回对应的 ChatModel 实例

#### Scenario: import 时无外部依赖
- **WHEN** 执行 `from agents.modelFactory import process_manager, interviewer_chat`
- **THEN** 不触发任何 Ollama 连接或外部服务请求

### Requirement: 单文件内死代码清理
以下文件 SHALL 移除内部未使用的代码段，且保留的所有代码功能不变：
- `service/interview.py`：移除 `run()` 函数
- `service/orchestrator.py`：移除 `fetch_questions()`、`pick_knowledge_point()` 函数
- `service/learning.py`：移除 `_LEARNING_CLEAN_SYSTEM_PROMPT`、`_learning_sessions_lock`、`_learning_sessions`，清理 `_ask_llm` 中无效导入
- `skills/base.py`：移除 `EvaluationResult` 数据类和 `build_user_message`、`build_question_context`、`get_evaluation_prompt`、`get_stage_by_name`、`get_next_stage`、`get_stage_index` 方法
- `prompt/initialization.py`：移除 `get_style_names()`、`build_interview_prompt()` 函数
- `skills/registry.py`：移除 `list_skills()`、`get_skill_names()` 函数
- `skills/__init__.py`：移除 `list_skills`、`get_skill_names` 导入和导出

#### Scenario: 面试核心流程不变
- **WHEN** 通过 dual_agent 模式启动面试并完成一轮完整对话
- **THEN** Manager Agent 和 Interviewer Agent 行为与清理前完全一致

#### Scenario: 技能注册正常
- **WHEN** `skills/registry.py` 模块加载时自动注册
- **THEN** `simulation` 和 `learning` 技能正常注册且可通过 `get_skill()` 获取
