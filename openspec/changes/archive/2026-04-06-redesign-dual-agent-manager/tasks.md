## 1. 新建 interviewManager Skill

- [x] 1.1 创建 `skills/interviewManager/SKILL.md`
- [x] 1.2 创建 `skills/interviewManager/references/stages/stage1_basic_knowledge.md`
- [x] 1.3 创建 `skills/interviewManager/references/stages/stage2_project_experience.md`
- [x] 1.4 创建 `skills/interviewManager/references/stages/stage3_job_matching.md`
- [x] 1.5 创建 `skills/interviewManager/references/stages/stage4_summary.md`

## 2. 更新 file_reader tools

- [x] 2.1 修改 `tools/file_reader.py`：将 `SKILLS_DIR` 指向 `skills/interviewManager`

## 3. 重写 Manager Agent

- [x] 3.1 重写 `agents/manager_agent.py` 系统提示词和输出格式
- [x] 3.2 更新 `agents/manager_agent.py` 的 `invoke_manager` 函数签名

## 4. 重写 dual_agent_service.py

- [x] 4.1 设计并实现新的 session 数据结构
- [x] 4.2 实现 Python 确定性层——阶段状态机
- [x] 4.3 实现回答碎片拼接逻辑
- [x] 4.4 实现上下文隔离策略
- [x] 4.5 重写 `start_dual_interview`
- [x] 4.6 重写 `dual_interview_chat`
- [x] 4.7 实现阶段转换流程
- [x] 4.8 实现面试总结流程

## 5. 更新 api_service.py 和 API 层

- [x] 5.1 合并 `/interview/start` 和 `/interview/chat` 为 `/interview`，支持 `await_continuation`
- [x] 5.2 重写 `web/api.py`：统一接口，新增 `action`/`message_to_user` 字段

## 6. 清理旧 skill

- [ ] 6.1 移除 `skills/interviewProcess/` 目录

## 7. 测试与验证

- [ ] 7.1 手动测试完整面试流程（simulation 模式）
- [ ] 7.2 手动测试完整面试流程（learning 模式）
- [ ] 7.3 测试面试风格差异化
- [ ] 7.4 验证 API 响应格式
