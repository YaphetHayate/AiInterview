## ADDED Requirements

### Requirement: 回答完整性检测
系统 SHALL 在每次用户发送消息后，由 Manager LLM 判断候选人回答是否完整。判断依据包括语言特征（如"首先..."无后续）、内容深度（是否展开了原理）、与当前问题的匹配程度。

#### Scenario: 回答完整，直接推进
- **WHEN** 候选人发送了一个完整的回答，覆盖了问题的核心要点
- **THEN** Manager 输出 `action: "interview"`，组装 prompt 传给 Interviewer 执行

#### Scenario: 回答不完整，等待继续
- **WHEN** 候选人的回答明显不完整（如"第一点..."没有后续，或末尾是省略号）
- **THEN** Manager 输出 `action: "await_continuation"`，返回追问话术给用户，不调用 Interviewer

#### Scenario: 用户强制确认回答完毕
- **WHEN** 用户发送"完毕"、"回复完毕"等确认关键词
- **THEN** 系统将 pending_buffer 中的所有碎片拼接为完整回答，跳过完整性判断，直接传给 Manager 组装 prompt

### Requirement: 追问话术受面试风格影响
Manager 在检测到回答不完整时，生成的追问话术 SHALL 根据当前面试风格调整语气和方式。

#### Scenario: challenging 风格施压追问
- **WHEN** 面试风格为 challenging，且候选人回答看似完整
- **THEN** Manager 可以输出"还有吗？"施加压力，即使判断回答已完整

#### Scenario: friendly 风格温和追问
- **WHEN** 面试风格为 friendly，且候选人回答不完整
- **THEN** Manager 输出"没关系，想到什么说什么就好"等鼓励性话术

#### Scenario: professional 风格客观追问
- **WHEN** 面试风格为 professional，且候选人回答不完整
- **THEN** Manager 输出"请继续补充"等中性话术

### Requirement: 回答碎片拼接
系统 SHALL 支持候选人分多次发送回答。Python 层将多次发送的内容存入 pending_buffer，拼接后交给 Manager 判断完整性。

#### Scenario: 多段拼接后完整
- **WHEN** 候选人分 3 次发送回答，Manager 在第 3 次判断完整
- **THEN** 系统将 3 段文本拼接为完整回答，传给 Manager 组装 prompt 发给 Interviewer

#### Scenario: 拼接后发现重复或不通顺
- **WHEN** Python 层拼接后发现内容有明显重复或逻辑不通顺
- **THEN** Manager 可以要求用户重新完整回答，或由 Manager LLM 重构语言后再发给 Interviewer

### Requirement: 不完整回答在点评中体现
当候选人在拟真模式下的回答被判定为不完整但仍推进时，Manager SHALL 在给 Interviewer 的 prompt 中标注回答不完整，Interviewer 的点评 SHALL 体现这一点。

#### Scenario: 拟真模式下不完整回答被点评
- **WHEN** 拟真模式中候选人的回答不完整但用户确认完毕
- **THEN** Interviewer 的 prompt 中包含"候选人回答不完整"的提示，Interviewer 在反馈中指出回答未覆盖的要点
