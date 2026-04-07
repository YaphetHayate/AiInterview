## 1. 脚本层：创建独立取题脚本

- [x] 1.1 创建 `skills/interviewManager/scripts/` 目录，编写 `fetch_questions.py`，支持 `--tech-stacks`、`--difficulty`、`--limit` 命令行参数，通过 `QuestionBankRepository.get_random_questions()` 查询题目并输出格式化文本到 stdout
- [x] 1.2 验证脚本可独立运行：`python skills/interviewManager/scripts/fetch_questions.py --tech-stacks Java --difficulty medium --limit 3`，确认输出格式符合 spec

## 2. Tool 层：注册 LangChain Tool

- [x] 2.1 在 `tools/file_reader.py` 中新增 `fetch_questions_from_bank` tool 函数，参数为 `tech_stacks`（str）、`difficulty`（str）、`limit`（int=5），内部调用 `QuestionBankRepository.get_random_questions()` 并返回格式化中文文本
- [x] 2.2 将新 tool 加入 `ALL_TOOLS` 列表，确保 Manager Agent 创建时能获取到该工具
- [x] 2.3 处理边界情况：题库无匹配时返回友好提示文本，limit 超过可用数时返回实际可用题目

## 3. Skill 层：更新 SKILL.md 和 stage1 指引

- [x] 3.1 更新 `skills/interviewManager/SKILL.md`：在工具相关章节新增 `fetch_questions_from_bank` 工具说明（用途、参数、调用时机为 stage1 开始时）
- [x] 3.2 更新 `skills/interviewManager/references/stages/stage1_basic_knowledge.md`：在执行流程中新增"第一步：调用 fetch_questions_from_bank 获取题目"的指令，增加题目注入 prompt 的格式模板，增加获取题目失败的回退策略
