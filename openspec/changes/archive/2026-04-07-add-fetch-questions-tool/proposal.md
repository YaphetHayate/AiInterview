## Why

当前面试系统在 stage1（基础知识考察）阶段，虽然 `orchestrator` 层已能从 PostgreSQL `question_bank` 表获取题目并管理进度，但 Manager Agent 的技能文件（`SKILL.md`）和阶段指引（`stage1_basic_knowledge.md`）中没有任何机制让 Agent 在组装 prompt 时主动获取和使用真实题库题目。面试官 Agent 收到的 prompt 缺乏具体题目内容，只能泛泛提问。

需要让 Manager Agent 在 stage1 开始时，通过工具调用从题库获取真实题目，并将题目注入到 `interviewer_prompt.user_message` 中，使面试基于结构化的真实题目进行。

## What Changes

- 新增 `scripts/fetch_questions.py`：独立可运行的取题脚本（符合 skill-creator 的 `scripts/` 目录规范），从 `question_bank` 表按技术栈+难度随机获取题目
- 新增 LangChain Tool `fetch_questions_from_bank`：注册到 `tools/file_reader.py`，供 Manager Agent 调用，底层走已有的 `QuestionBankRepository`
- 修改 `stage1_basic_knowledge.md`：增加"先调用取题工具获取题目"的执行指令和题目注入 prompt 的格式模板
- 修改 `SKILL.md`：在工具列表和 stage1 流程描述中引用新的取题工具

## Capabilities

### New Capabilities
- `fetch-questions-tool`: Manager Agent 在 stage1 阶段从 PostgreSQL question_bank 表获取真实题目并注入 prompt 的能力

### Modified Capabilities

## Impact

- `skills/interviewManager/scripts/`：新增目录和脚本文件
- `tools/file_reader.py`：新增一个 tool 函数，`ALL_TOOLS` 列表需更新
- `skills/interviewManager/SKILL.md`：内容更新（stage1 流程描述）
- `skills/interviewManager/references/stages/stage1_basic_knowledge.md`：内容更新（取题指令）
- `db/repository.py`：不修改，复用 `QuestionBankRepository.get_random_questions()`
- `orchestrator.py` / `question_manager.py`：不修改，进度追踪逻辑不受影响

## 非目标

- 不修改 orchestrator 或 question_manager 的取题/进度追踪逻辑
- 不影响 stage2/3/4 的现有流程
- 不修改 `simulation.py` / `learning.py` 的 stage prompt 模板
- 不修改数据库 schema 或 Repository 层
