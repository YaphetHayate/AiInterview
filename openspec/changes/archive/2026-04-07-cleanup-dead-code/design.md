## Context

项目经过多次迭代，核心面试流程从单 Agent 架构演变为双 Agent 架构（`dual_agent_service.py`），面试启动逻辑从 `service/guide.py` 迁移到 `service/api_service.py`。旧代码未被清理，导致项目中存在约 650+ 行完全无引用的死代码，部分甚至引用了不存在的方法（运行时必崩）。此外，早期多模型试验（Ollama、MiniMax）留下的实例化代码在模块加载时就会创建连接，如果本地 Ollama 未运行可能导致启动异常。

当前活跃的调用链：

```
main.py → run_cli() / run_web()
  ├── service/dual_agent_service.py  (双 Agent 核心)
  │     ├── agents/manager_agent.py
  │     └── agents/interviewer_agent.py
  ├── service/api_service.py         (Web API 业务层)
  │     ├── service/dual_agent_service.py
  │     ├── service/interview.py     (单 Agent 模式)
  │     └── service/learning.py
  └── web/api.py                     (FastAPI 路由)
```

## Goals / Non-Goals

**Goals:**

- 移除所有零引用的代码，降低项目认知负担
- 移除模块加载时即实例化的 Ollama 连接（`process_manager_ollama`、`interviewer_chat_ollama`），避免启动时对 Ollama 的硬依赖
- 移除引用不存在方法的代码（`guide.py` 中的 `TechStackRepository.exists()` 等）
- 清理未使用的基类方法，缩小 `InterviewSkill` 接口面积

**Non-Goals:**

- 不重构保留代码的架构或内部实现
- 不修改任何面试流程、提示词内容或 API 行为
- 不清理 `web/` 下的日志文件或 `__pycache__`
- 不修改依赖声明（`pyproject.toml`、`requirements.txt`）
- 不添加新功能或新类型注解

## Decisions

### D1: 删除策略 — 整文件删除 vs 精确裁剪

**决策**: 对完全无外部引用的文件执行整文件删除；对部分无用的文件执行精确行级裁剪。

**理由**: `guide.py`、`prompt/manager.py`、`check_db.py`、`connect_db.py`、`sql_commands.sql` 全文件零引用，整删最安全。`modelFactory.py`、`interview.py` 等文件包含活跃代码和死代码混合，需精确裁剪。

### D2: Ollama 实例处理

**决策**: 删除 `modelFactory.py` 顶层的 `process_manager_ollama` 和 `interviewer_chat_ollama` 两个实例。保留 `_MANAGER_FACTORY_MAP` / `_INTERVIEWER_FACTORY_MAP` 按需实例化的架构。

**理由**: 这两个 Ollama 实例在模块 `import` 时就会创建连接。当前项目已切换为通过 factory map 按需创建模型实例，顶层 Ollama 实例纯属残留。且如果本地 Ollama 未运行，import 阶段可能触发异常。

### D3: `InterviewSkill` 基类方法保留策略

**决策**: 仅保留被外部实际调用的方法：`name`、`display_name`、`description`、`get_stages`、`get_chat_guidance`、`build_system_prompt`、`build_stage_prompt`、`get_first_stage`。移除 `build_user_message`、`build_question_context`、`get_evaluation_prompt`、`get_stage_by_name`、`get_next_stage`、`get_stage_index` 和 `EvaluationResult` 数据类。

**理由**: 这些方法从未被任何外部代码调用。`get_stage_by_name`、`get_next_stage`、`get_stage_index` 仅在彼此之间内部调用，形成死循环式的死代码。移除后 `InterviewSkill` 接口更精简，降低实现者的负担。

**替代方案**: 保留这些方法作为"未来扩展点"。**否决**——YAGNI 原则，未来需要时再添加成本极低。

### D4: `service/learning.py` 中未使用变量的处理

**决策**: 移除 `_LEARNING_CLEAN_SYSTEM_PROMPT`、`_learning_sessions_lock`、`_learning_sessions` 以及 `_ask_llm` 中对 `_get_session_config`/`_set_session_config` 的无效导入。

**理由**: 这些变量/导入在模块中声明后从未被使用。`_learning_sessions` 字典和锁看起来是早期会话管理的残留，当前会话状态由调用方管理。

## Risks / Trade-offs

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 误删有隐式依赖的代码 | 低 | 中 | 所有删除项均已通过全局 `grep` 验证零引用 |
| 未来需要被删的基类方法 | 低 | 低 | 从 git 历史恢复成本极低 |
| `guide.py` 中有需迁移的逻辑 | 低 | 中 | `guide.py` 已调用不存在的方法，说明逻辑已不可用，无需迁移 |
