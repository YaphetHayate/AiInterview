## ADDED Requirements

### Requirement: 学习弹窗覆盖层
前端 SHALL 在用户点击"学习一下"按钮后，在面试页面上层显示全屏覆盖弹窗（Overlay）。弹窗 SHALL 使用 `position: fixed` 定位，覆盖面试内容区，面试输入区 SHALL 在弹窗打开期间被 disabled。

#### Scenario: 打开学习弹窗
- **WHEN** 用户在学习模式下点击面试问题下方的"学习一下"按钮
- **THEN** 弹窗从面试页面上层弹出，面试输入区被 disabled，弹窗显示当前面试问题标题、答疑内容区、追问按钮区、自由输入区和关闭按钮

#### Scenario: 关闭学习弹窗
- **WHEN** 用户点击弹窗内的关闭按钮
- **THEN** 弹窗消失，面试输入区恢复可用，面试状态无变化，用户可正常回答面试问题

### Requirement: 答疑内容展示
弹窗 SHALL 将 Tutor Agent 返回的 explanation 以 Markdown 格式渲染展示，样式与面试页面的 AI 消息一致。

#### Scenario: 首次答疑展示
- **WHEN** 弹窗打开，Tutor Agent 返回首次答疑内容
- **THEN** 弹窗内容区显示渲染后的 Markdown 答疑内容，底部显示 typing indicator 直到内容返回

### Requirement: 追问按钮展示
弹窗 SHALL 在每次答疑内容下方展示 3-4 个追问按钮，按钮标签为 Tutor Agent 预测的追问文本。用户点击按钮后，该问题作为追问发送给 Tutor Agent，按钮区刷新为新返回的追问建议。

#### Scenario: 追问按钮点击
- **WHEN** 用户点击某个追问按钮（如"为什么要这样设计？"）
- **THEN** 按钮文本作为追问消息发送给 Tutor Agent，弹窗内容区追加用户消息和 AI 回复，追问按钮区刷新为新预测的追问

#### Scenario: 无追问建议
- **WHEN** Tutor Agent 未返回有效的追问建议
- **THEN** 追问按钮区不显示任何按钮，仅显示自由输入框

### Requirement: 自由输入追问
弹窗 SHALL 提供文本输入框，允许用户输入自定义追问。输入框支持 Enter 发送、Shift+Enter 换行。

#### Scenario: 自由输入发送
- **WHEN** 用户在输入框中输入文本并按 Enter 或点击发送
- **THEN** 文本作为追问发送给 Tutor Agent，弹窗内容区追加用户消息和 AI 回复，追问按钮区刷新

### Requirement: "学习一下"按钮仅在首次出现
"学习一下"按钮 SHALL 仅在面试官提出新问题时出现。弹窗打开期间按钮隐藏。弹窗关闭后，按钮 SHALL NOT 重新出现（因为用户已回到面试回答环节）。

#### Scenario: 按钮出现时机
- **WHEN** 面试官提出新的面试问题
- **THEN** 问题消息下方出现"学习一下"按钮

#### Scenario: 弹窗期间按钮状态
- **WHEN** 学习弹窗打开
- **THEN** "学习一下"按钮隐藏，面试输入区 disabled

#### Scenario: 弹窗关闭后按钮状态
- **WHEN** 学习弹窗关闭
- **THEN** "学习一下"按钮不重新出现，面试输入区恢复，等待用户回答面试问题
