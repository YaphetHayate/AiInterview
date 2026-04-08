## Why

项目在迭代过程中积累了大量已废弃的代码：整个废弃模块（`service/guide.py`）、调试脚本（`check_db.py`）、未使用的模型实例和工具函数。这些代码约 650+ 行，增加了维护负担和认知成本，部分代码引用了不存在的方法（如 `TechStackRepository.exists()`），说明已经彻底失效。

## What Changes

- **删除整个废弃文件**：`service/guide.py`（早期面试启动逻辑，已被 `dual_agent_service.py` + `api_service.py` 取代）、`prompt/manager.py`（Manager 提示词已在 `agents/manager_agent.py` 中自包含）、`check_db.py`、`connect_db.py`、`sql_commands.sql`（开发调试残留）
- **清理 `agents/modelFactory.py`**：移除未使用的 Ollama 实例（`process_manager_ollama`、`interviewer_chat_ollama`）、未使用的 `get_zhipu_chat()`、`get_minimax_chat()` 及相关变量
- **清理 `service/interview.py`**：移除 `run()` 函数（独立 CLI 入口，已被 `main.py` 的 `run_cli()` 取代）
- **清理 `service/orchestrator.py`**：移除未使用的 `fetch_questions()`、`pick_knowledge_point()`（`guide.py` 的配套函数）
- **清理 `service/learning.py`**：移除未使用的 `_LEARNING_CLEAN_SYSTEM_PROMPT`、`_learning_sessions_lock`、`_learning_sessions`、以及 `_ask_llm` 中未使用的导入
- **清理 `skills/base.py`**：移除从未调用的基类方法（`build_user_message`、`build_question_context`、`get_evaluation_prompt`、`get_stage_by_name`、`get_next_stage`、`get_stage_index`）和 `EvaluationResult` 数据类
- **清理 `prompt/initialization.py`**：移除未使用的 `get_style_names()`、`build_interview_prompt()` 便捷函数
- **清理 `skills/registry.py` / `skills/__init__.py`**：移除未使用的 `list_skills()`、`get_skill_names()` 导出

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

（无规格变更 — 本次清理仅移除死代码，不改变任何现有功能行为）

## Impact

- **代码体积**：预计净减少 650+ 行
- **风险评估**：极低。所有被移除的代码均无调用者，`guide.py` 甚至引用了不存在的方法无法运行
- **受影响模块**：`agents/`、`service/`、`prompt/`、`skills/`、项目根目录
- **API 兼容性**：无影响，所有 API 端点不变
- **数据库**：无影响

## 非目标

- 不重构现有有效代码的架构或逻辑
- 不修改面试流程或提示词内容
- 不清理 `web/` 目录下的日志文件
- 不更新 `pyproject.toml` 或 `requirements.txt` 中的依赖
