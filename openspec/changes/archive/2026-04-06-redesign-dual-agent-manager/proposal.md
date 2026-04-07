## Why

当前双 Agent 模式存在三个核心问题：
1. **Manager 职责过重且不可靠**：Manager 需要同时做阶段判断、mode 分辨、JSON 输出，每次都读 SKILL.md，输出格式不稳定导致大量容错代码。
2. **两套技能系统割裂**：Python 类技能（simulation.py/learning.py）与 Markdown 技能（interviewProcess/SKILL.md）互不联通，dual_agent_service 不区分 mode。
3. **缺少回答完整性检测**：候选人分段发送回答时直接进入 LLM 处理，无法识别不完整回答，也无法根据面试风格调整追问策略。

## What Changes

- **新建 interviewManager SKILL.md**：替换旧的 interviewProcess SKILL.md，包含流程总览、mode 差异定义、完整性判断策略（按 style + difficulty 分表）、prompt 组装规范、上下文隔离策略。
- **重写 dual_agent_service.py**：引入 Python 确定性层负责阶段状态机、mode 分辨、DB 获取问题、回答碎片拼接、上下文隔离（simulation 按问题隔离，learning 保留全量）。Manager 只负责完整性判断 + prompt 组装。
- **重写 manager_agent.py**：Manager 每轮调用，读新 SKILL.md 获取策略知识，判断回答完整性（受面试风格影响），组装干净 prompt 给 Interviewer。新增 `await_continuation` action 用于不完整回答处理。
- **重写 api_service.py**：适配新的 dual_agent_service 接口，支持完整性检测的中间态响应。
- **更新 file_reader tools**：适配新 skill 目录结构。
- **移除旧 interviewProcess SKILL.md**。

## Capabilities

### New Capabilities
- `answer-completeness`: 回答完整性检测——Manager 判断候选人回答是否完整，不完整时根据面试风格生成追问话术，支持碎片拼接和语言重构，完整后再传递给 Interviewer。
- `manager-prompt-assembly`: Manager prompt 组装——Manager 读取 skill 策略知识，结合 mode、stage、面试风格，为 Interviewer 组装最干净的 system_prompt 和 user_message，Interviewer 无需感知 mode 和阶段。
- `context-isolation`: 上下文隔离策略——simulation 模式按问题隔离上下文（跨问题不传但 Manager 持有摘要），learning 模式保留完整对话历史。

### Modified Capabilities
（无既有 spec 需要修改）

## Impact

- **agents/manager_agent.py**：重写 Manager 系统提示词和输出格式
- **agents/interviewer_agent.py**：调整接收参数（更干净的 prompt）
- **service/dual_agent_service.py**：大幅重写，引入确定性层和会话状态数据结构
- **service/api_service.py**：适配新接口，支持 `await_continuation` 响应
- **tools/file_reader.py**：适配新 skill 目录
- **skills/interviewManager/**：新建目录和 SKILL.md
- **skills/interviewProcess/**：移除（旧 skill）
- **web/api.py**：响应模型增加中间态字段
