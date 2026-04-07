# Interviewer

AI 面试官系统，基于 LangChain + LangGraph 的双 Agent 架构，通过 Manager Agent 编排流程、Interviewer Agent 执行面试，支持多种 LLM 后端。

## 架构

```
Frontend (localhost:3000)
  └── 反向代理 → Backend (localhost:8003)
                     │
                     ├── Manager Agent (流程编排)
                     │     └── 读取 SKILL.md 驱动四阶段面试
                     │
                     └── Interviewer Agent (面试执行)
                           └── 与候选人对话
```

**面试流程四阶段：** 基础知识考察 → 项目经历考察 → 岗位需求考察 → 面试总结

## 支持的 LLM

通过 `agents/modelFactory.py` 配置：

| Provider | 环境变量 | 模型 |
|----------|---------|------|
| 智谱 GLM | `ZHIPU_API_KEY` | GLM-5.1 |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat |
| 通义千问 | `DASHSCOPE_API_KEY` | qwen-plus |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

创建 PostgreSQL 数据库，执行 `db/schema.sql` 初始化表结构。

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 填入真实配置：

```env
# LLM（至少配置一个）
DASHSCOPE_API_KEY=your_key_here

# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=interview
```

### 4. 启动服务

```bash
# 双击运行（Windows）
start.bat

# 或手动启动
uvicorn web.api:app --host 0.0.0.0 --port 8003 --reload  # 后端
python frontend/server.py                                   # 前端
```

- 后端 API：http://localhost:8003
- 前端页面：http://localhost:3000

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/options` | 获取可选配置（技术栈、岗位、模式） |
| GET | `/styles` | 获取面试风格列表 |
| POST | `/interview` | 创建/继续面试会话 |
| POST | `/session/reset` | 重置会话 |
| GET | `/session/{id}/progress` | 查询面试进度 |
| GET | `/question-bank/tree` | 题库树形结构 |

## 项目结构

```
├── agents/               # Agent 定义
│   ├── manager_agent.py  # Manager Agent（流程编排）
│   ├── interviewer_agent.py
│   └── modelFactory.py   # LLM 工厂（多 provider 切换）
├── db/                   # 数据库
│   ├── connection.py     # 连接池
│   ├── schema.sql        # 表结构
│   └── repository.py     # 数据访问层
├── frontend/             # 前端静态文件 + 反向代理
├── prompt/               # 提示词模板
├── service/              # 业务逻辑
│   ├── api_service.py    # API 层
│   ├── dual_agent_service.py
│   ├── interview.py
│   └── question_manager.py
├── skills/
│   └── interviewManager/ # 双 Agent 面试流程定义
│       └── SKILL.md      # Manager Agent 读取的流程文件
├── tools/                # Agent 工具
├── web/                  # FastAPI 路由
└── start.bat             # 启动脚本
```

## 技术栈

- **Python 3.10+**
- **LangChain / LangGraph** — Agent 框架
- **FastAPI + Uvicorn** — Web 服务
- **PostgreSQL + psycopg2** — 数据存储
- **Pydantic v2** — 数据校验
