## ADDED Requirements

### Requirement: 回答完整性判断
Manager SHALL 判断候选人的回答是否完整，覆盖以下三种场景：物理性不完整（话没说完误触发送）、多子问题部分回答、完整回答。

#### Scenario: 物理性不完整 - 话没说完
- **WHEN** 候选人发送了一条语义断裂的消息（如句子在中途截断）
- **THEN** Manager 判断为不完整，提示候选人继续补充
- **AND** 等待候选人补充后将多段内容合并作为完整回答

#### Scenario: 多子问题部分回答
- **WHEN** 面试官的问题包含多个子问题，且候选人只回答了部分子问题
- **THEN** Manager 判断为不完整，提示候选人回答剩余部分
- **AND** 提示中具体指出哪些子问题尚未回答

#### Scenario: 回答完整
- **WHEN** 候选人的回答覆盖了所有子问题或单个问题的回答语义完整
- **THEN** Manager 判断为完整，将回答传递给 Interviewer

### Requirement: 回答整合策略
Manager 在判断回答完整后，SHALL 对散乱的回答进行结构化整理。整合操作 SHALL 只包含分段合并和子问题对齐排列，SHALL NOT 包含内容增删、措辞润色或语义扩展。

#### Scenario: 分段合并
- **WHEN** 候选人分多条消息回答同一个问题
- **THEN** Manager 将多条消息的内容合并为一段完整的回答
- **AND** 合并后的内容不包含 Manager 自己添加的任何文字

#### Scenario: 子问题对齐排列
- **WHEN** 面试官的问题包含多个子问题，候选人做了完整但散乱的回答
- **THEN** Manager 将回答内容按子问题结构重新排列对齐
- **AND** 排列后的每个子问题对应部分只包含候选人的原始表述

#### Scenario: 禁止修改原始回答
- **WHEN** Manager 整合候选人回答时
- **THEN** SHALL NOT 增加候选人未提及的内容
- **AND** SHALL NOT 删除或修改候选人的原始表述
- **AND** SHALL NOT 润色措辞或修正专业术语

### Requirement: Interviewer 知识点评估导向
Interviewer 的 system_prompt SHALL 明确评估重心为知识点的完整性和准确性。追问策略 SHALL 聚焦于知识点的深入展开，而非表达方式的改进。

#### Scenario: 追问聚焦知识点
- **WHEN** Interviewer 对候选人的回答进行追问
- **THEN** 追问内容聚焦于"能否展开某个知识点"或"某个概念的细节"
- **AND** SHALL NOT 因表达不流畅而降低评价或要求重新表述

#### Scenario: 评估维度
- **WHEN** Interviewer 评估候选人回答质量
- **THEN** 评估维度以知识点覆盖度、准确性、深度为主
- **AND** 表达流畅度、措辞专业性不作为主要评估维度
