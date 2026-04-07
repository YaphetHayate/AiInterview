## Context

当前面试系统采用双 Agent 架构：Manager Agent 负责流程管理和 prompt 组装，Interviewer Agent 负责面试执行。

在 stage1（基础知识考察）阶段，`orchestrator.py` 已通过 `QuestionBankRepository.get_random_questions()` 从 PostgreSQL `question_bank` 表获取题目，并通过 `question_manager` 存入 `interview_questions` 表用于进度追踪（"下一题"/"跳过"/"进度"等命令）。但 Manager Agent 没有获取题目的工具，组装给 Interviewer 的 prompt 中缺少具体题目内容。

现有工具层（`tools/file_reader.py`）仅提供 `read_skill_md` 和 `read_stage_file` 两个只读工具，Agent 无法主动查询数据库。

## Goals / Non-Goals

**Goals:**

- Manager Agent 在 stage1 开始时能通过 tool 调用从 question_bank 获取真实题目
- 获取的题目能被注入到 `interviewer_prompt.user_message` 中，让面试官基于具体题目提问
- 脚本遵循 skill-creator 格式，放在 `scripts/` 目录下，可独立运行

**Non-Goals:**

- 不修改 orchestrator 或 question_manager 的现有逻辑
- 不影响 stage2/3/4 的流程
- 不修改 `simulation.py` / `learning.py` 的 stage prompt 模板
- 不修改数据库 schema 或 db/ 层代码

## Decisions

### 1. Tool 直接调用 Repository（不通过 subprocess）

**选择**：Tool 函数直接调用 `QuestionBankRepository.get_random_questions()`

**理由**：
- 复用已有连接池（5 连接），无需为每次查询新建连接
- 避免子进程开销，查询延迟从百毫秒级降到毫秒级
- 事务安全由 `db_cursor` 上下文管理器保证

**备选方案**：Tool 通过 subprocess 调用 `scripts/fetch_questions.py`
- 放弃原因：每次起子进程 + 单独建连接，开销大且不符合 LangChain tool 惯例

### 2. 脚本作为独立可运行的参考实现

**选择**：`scripts/fetch_questions.py` 可独立 `python fetch_questions.py` 运行，带命令行参数

**理由**：
- 符合 skill-creator 对 `scripts/` 目录的定义（确定性/重复性任务的执行代码）
- 方便开发时独立测试和调试，不依赖 Agent 运行环境
- Tool 和脚本共享同一套查询逻辑（Repository），保证结果一致

### 3. 题目格式化输出

**选择**：Tool 返回格式化的中文文本，而非原始 JSON

**格式**：
```
已从题库获取 5 道题目（技术栈：Java, Redis | 难度：medium）：

问题1：请简要介绍Java的四大基本特性（封装、继承、多态、抽象）。
问题2：JVM的内存模型是怎样的？堆内存是如何划分的？
问题3：HashMap的底层实现原理是什么？JDK1.8做了哪些优化？
问题4：Redis支持哪些数据类型？各自适合什么场景？
问题5：什么是缓存穿透、缓存击穿和缓存雪崩？分别如何解决？
```

**理由**：Manager Agent 是 LLM，结构化文本比 JSON 更容易被理解和编织进 prompt

### 4. 与 orchestrator 取题并存

**选择**：Tool 取题用于 prompt 内容编排，orchestrator 取题用于进度追踪，两者独立

**理由**：
- `question_manager` 的进度追踪（状态机、"下一题"命令等）完全依赖 orchestrator 预存的题目
- 解耦两者职责：orchestrator 管进度，Manager Agent 管 prompt 内容
- 题目来源相同（question_bank），但随机性导致具体题目可能不同——这是可接受的，因为 Manager 注入的是"参考题库"，面试官可以灵活使用

## Risks / Trade-offs

**[题目不一致]** → orchestrator 取的题目和 Tool 取的题目可能不同（RANDOM 排序）。但两者目的不同：orchestrator 追踪的是"本次面试问了哪些"，Manager 注入的是"建议问哪些"。实际运作中面试官基于 Manager 提供的题目列表提问，orchestrator 侧的进度追踪依然有效（"下一题"命令基于 question_manager 的顺序推进）。

**[LLM 不调用 Tool]** → Manager Agent 可能在 stage1 开始时忘记调用取题工具。缓解：在 `stage1_basic_knowledge.md` 的执行流程中明确标注"第一步必须调用 fetch_questions_from_bank"。

**[题库为空]** → 如果指定技术栈+难度没有题目，Tool 返回空列表提示。Manager Agent 应能回退到自主提问模式。
