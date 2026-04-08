## 1. 删除整个废弃文件

- [x] 1.1 删除 `service/guide.py` — 早期面试启动逻辑，无外部引用，内含不存在的方法调用（`TechStackRepository.exists()`、`QuestionBankRepository.pick_questions()`、`SessionRepository.get_by_session_id()`）
- [x] 1.2 删除 `prompt/manager.py` — Manager 提示词模块，`get_manager_prompt()` 零调用，Manager Agent 在 `agents/manager_agent.py` 中自包含提示词
- [x] 1.3 删除 `check_db.py` — 数据库调试脚本，非项目功能代码
- [x] 1.4 删除 `connect_db.py` — 数据库连接调试脚本，非项目功能代码
- [x] 1.5 删除 `sql_commands.sql` — 调试用 SQL 片段，`db/schema.py` 已包含完整 DDL

## 2. 清理 `agents/modelFactory.py`

- [x] 2.1 删除顶层 Ollama 实例 `process_manager_ollama`（L11-16）和 `interviewer_chat_ollama`（L18-23）— 模块加载时创建但从未使用，且可能导致 Ollama 未运行时启动异常
- [x] 2.2 删除 `zhipu_chat` 变量声明（L130）、`_minimax_chat` 变量声明（L131）、`get_zhipu_chat()` 函数（L134-143）、`get_minimax_chat()` 函数（L146-154）— 零引用
- [x] 2.3 移除 `from langchain_community.chat_models import MiniMaxChat` 导入（L4）— `MiniMaxChat` 仅在已删除的 `get_minimax_chat()` 中使用

## 3. 清理 `service/interview.py`

- [x] 3.1 删除 `run()` 函数（L258-326）— 独立 CLI 入口，已被 `main.py` 的 `run_cli()` 取代，零外部调用

## 4. 清理 `service/orchestrator.py`

- [x] 4.1 删除 `fetch_questions()` 函数（L43-54）— `guide.py` 的配套函数，guide 删除后零调用。`dual_agent_service.py` 有自己的 `_fetch_questions`
- [x] 4.2 删除 `pick_knowledge_point()` 函数（L57-68）— 同上，`learning.py` 有自己的 `_pick_knowledge_point`
- [x] 4.3 移除 `import random` 导入（L1）— 仅在已删除的 `pick_knowledge_point()` 中使用

## 5. 清理 `service/learning.py`

- [ ] 5.1 删除 `_LEARNING_CLEAN_SYSTEM_PROMPT` 常量（L12-24）— 从未引用
- [ ] 5.2 删除 `_learning_sessions_lock`（L26）和 `_learning_sessions`（L27）— 声明后从未使用
- [ ] 5.3 修复 `_ask_llm()` 函数（L206-216）中的导入：移除未使用的 `_get_session_config, _set_session_config`，仅保留 `from service.interview import chat_once`

## 6. 清理 `skills/base.py`

- [ ] 6.1 删除 `EvaluationResult` 数据类（L46-52）— 零引用
- [ ] 6.2 删除 `build_user_message()` 方法（L86-95）— 无外部调用者
- [ ] 6.3 删除 `build_question_context()` 方法（L97-112）— 无外部调用者
- [ ] 6.4 删除 `get_evaluation_prompt()` 方法（L114-122）— 无外部调用者
- [ ] 6.5 删除 `get_stage_by_name()` 方法（L124-128）— 仅被其他已删除方法内部调用
- [ ] 6.6 删除 `get_next_stage()` 方法（L134-139）— 无外部调用者
- [ ] 6.7 删除 `get_stage_index()` 方法（L141-145）— 无外部调用者

## 7. 清理 `prompt/initialization.py`

- [ ] 7.1 删除 `get_style_names()` 函数（L210-212）— 零调用
- [ ] 7.2 删除 `build_interview_prompt()` 函数（L215-229）— 零调用，仅是 `get_system_prompt` 的包装

## 8. 清理 `skills/registry.py` 和 `skills/__init__.py`

- [ ] 8.1 在 `skills/registry.py` 中删除 `list_skills()` 函数（L21-22）和 `get_skill_names()` 函数（L25-26）— 零外部调用
- [ ] 8.2 在 `skills/__init__.py` 中移除 `list_skills`、`get_skill_names` 的导入和 `__all__` 导出

## 9. 验证

- [ ] 9.1 运行 `python -c "from main import main"` 验证所有模块可正常导入，无 ImportError
- [ ] 9.2 运行 `python -c "from skills.registry import get_skill; assert get_skill('simulation') is not None; assert get_skill('learning') is not None"` 验证技能注册正常
- [ ] 9.3 运行 `python -c "from web.api import app; print('API OK')"` 验证 Web API 模块正常
