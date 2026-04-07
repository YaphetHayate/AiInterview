## ADDED Requirements

### Requirement: Manager Agent 获取题库题目工具

系统 SHALL 提供一个 LangChain Tool `fetch_questions_from_bank`，供 Manager Agent 在 stage1 阶段调用，从 PostgreSQL `question_bank` 表按技术栈和难度随机获取面试题目。

Tool 参数：
- `tech_stacks`（str）：逗号分隔的技术栈名称，如 "Java,Redis"
- `difficulty`（str）：难度级别，取值为 "basic"、"medium"、"hard"
- `limit`（int）：获取题目数量，默认 5

Tool SHALL 返回格式化的中文文本，包含题目编号和内容。

#### Scenario: 正常获取题目
- **WHEN** Manager Agent 调用 `fetch_questions_from_bank(tech_stacks="Java,Redis", difficulty="medium", limit=5)`
- **THEN** Tool 返回格式化文本，包含 5 道题目，每题带编号和内容，头部显示技术栈和难度信息

#### Scenario: 题库无匹配题目
- **WHEN** Manager Agent 调用 `fetch_questions_from_bank(tech_stacks="Go", difficulty="hard", limit=5)` 且 question_bank 中无 Go hard 难度题目
- **THEN** Tool 返回提示文本"未找到匹配的题目（技术栈：Go | 难度：hard）。请尝试其他技术栈或难度。"

#### Scenario: limit 超过可用题目数
- **WHEN** question_bank 中 Java basic 只有 3 道题，但请求 limit=5
- **THEN** Tool 返回实际可用的 3 道题目，格式与正常情况一致

### Requirement: 独立可运行的取题脚本

系统 SHALL 在 `skills/interviewManager/scripts/` 目录下提供 `fetch_questions.py` 脚本，可独立通过命令行运行，从 question_bank 表获取题目。

脚本参数：
- `--tech-stacks`：逗号分隔的技术栈（必需）
- `--difficulty`：难度级别（默认 "medium"）
- `--limit`：题目数量（默认 5）

脚本 SHALL 输出与 Tool 相同格式的文本到 stdout。

#### Scenario: 命令行独立运行
- **WHEN** 执行 `python skills/interviewManager/scripts/fetch_questions.py --tech-stacks Java --difficulty medium --limit 3`
- **THEN** 脚本输出 3 道格式化的 Java medium 难度题目到 stdout

#### Scenario: 缺少必需参数
- **WHEN** 执行 `python skills/interviewManager/scripts/fetch_questions.py` 不带任何参数
- **THEN** 脚本输出用法提示并退出

### Requirement: stage1 阶段指引包含取题指令

`skills/interviewManager/references/stages/stage1_basic_knowledge.md` SHALL 在执行流程中明确标注：进入 stage1 后，Manager Agent 必须首先调用 `fetch_questions_from_bank` 工具获取题目，然后将获取到的题目列表注入 `interviewer_prompt.user_message` 中。

题目注入 prompt 的格式 SHALL 为：
```
当前阶段：基础知识考察
技术栈：{tech_stacks}
难度：{difficulty}

请按顺序对候选人提出以下问题（每次只问一个，等回答后再问下一个）：

问题1：{题目内容}
问题2：{题目内容}
...

候选人当前回答：{answer}
```

#### Scenario: Manager Agent 按 stage1 指引执行取题
- **WHEN** 面试进入 stage1 且 Manager Agent 读取了 stage1_basic_knowledge.md
- **THEN** Manager Agent 调用 fetch_questions_from_bank 获取题目，并将题目列表按指定格式注入 interviewer_prompt.user_message

#### Scenario: 获取题目失败时的回退
- **WHEN** fetch_questions_from_bank 返回空结果（题库无匹配）
- **THEN** Manager Agent 使用通用提问方式继续面试，不阻塞流程

### Requirement: SKILL.md 引用新工具

`skills/interviewManager/SKILL.md` SHALL 在工具相关章节中列出 `fetch_questions_from_bank` 工具，说明其用途和调用时机（stage1 开始时）。

#### Scenario: Manager Agent 了解可用工具
- **WHEN** Manager Agent 读取 SKILL.md
- **THEN** 能看到 fetch_questions_from_bank 工具的说明：用途、参数、调用时机
