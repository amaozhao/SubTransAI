# SubTransAI Backend

智能字幕翻译系统后端

## 技术栈

- Python 3.12
- FastAPI
- FastAPI-Users
- SQLAlchemy
- Alembic
- Agno 1.4.4（智能体框架）
- StructLog（结构化日志）

## 目录结构

```
backend/
├── app/                    # 应用代码
│   ├── agents/             # 智能体实现
│   │   ├── srt_validator.py  # SRT 校验智能体
│   │   ├── srt_splitter.py   # SRT 分块智能体
│   │   ├── translator.py     # 翻译执行智能体
│   │   ├── srt_reassembler.py # SRT 重组智能体
│   │   ├── notification.py   # 通知服务智能体
│   │   └── workflow.py       # 工作流管理器
│   ├── api/                # API 路由
│   │   └── api_v1/         # API v1 版本
│   │       └── endpoints/  # API 端点
│   ├── core/               # 核心配置
│   ├── db/                 # 数据库设置
│   ├── models/             # 数据库模型
│   ├── schemas/            # Pydantic 模式
│   ├── services/           # 业务逻辑服务
│   └── utils/              # 工具函数
├── migrations/             # Alembic 数据库迁移
│   └── versions/           # 迁移版本
└── tests/                  # 测试代码
```

## 安装与设置

1. 创建并激活虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件

```bash
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=subtransai

# 安全配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# API 配置
RATE_LIMIT_PER_SECOND=50

# DeepSeek API 配置 (可选)
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions

```

4. 初始化数据库

```bash
cd backend
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 运行服务

```bash
cd backend
uvicorn app.main:app --reload
```

服务将在 http://localhost:8000 运行，API 文档可在 http://localhost:8000/docs 访问。

## 核心功能

- **用户管理**: 注册、登录、权限控制（支持邮箱/用户名/手机号三种登录方式）
- **术语表管理**: 创建和管理翻译术语表
- **翻译作业**: 上传 SRT 文件进行翻译
- **智能翻译**: 基于 Agno 的事件驱动翻译流程
- **敏感词过滤**: 自动过滤敏感内容
- **软删除**: 所有数据模型支持软删除功能

## API 端点

- `/api/v1/users/*`: 用户管理 API
- `/api/v1/glossaries/*`: 术语表管理 API
- `/api/v1/translations/*`: 翻译作业 API
- `/api/v1/translate/*`: 翻译 API（智能体集成）

## 智能体架构

本系统使用 Agno 框架实现了一套智能体协作系统，用于处理 SRT 文件的翻译流程：

1. **SRT 校验智能体**：验证 SRT 文件格式是否正确，并提供错误定位
2. **SRT 分块智能体**：将 SRT 文件分成更小的块进行处理，保留上下文关系
3. **翻译执行智能体**：将分块后的 SRT 内容翻译成目标语言，支持多种翻译引擎和术语表替换
4. **SRT 重组智能体**：将翻译后的 SRT 块重新组合成完整的 SRT 文件，确保字幕 ID 连续
5. **通知服务智能体**：生成下载 URL 和发送状态通知

这些智能体通过工作流管理器进行协调，形成一个完整的翻译流程。系统支持两种翻译引擎：

- **DeepSeek API**：用于高资源语言（英、中、日、韩、西、法等）
- **本地 LLAMA 模型**：用于低资源语言

### 工作流程

1. 用户上传 SRT 文件并指定源语言和目标语言
2. 系统验证 SRT 文件格式
3. 系统将 SRT 文件分成更小的块
4. 系统并行翻译每个块
5. 系统将翻译后的块重新组合成完整的 SRT 文件
6. 系统生成下载 URL 并通知用户

### 配置智能体

智能体配置在 `.env` 文件中：

```
# 智能体配置
AGNO_CHUNK_SIZE=100        # 每个块的最大字幕数量
AGNO_DEFAULT_ENGINE=deepseek  # 默认翻译引擎
AGNO_URL_EXPIRY_HOURS=24   # 下载 URL 过期时间（小时）
AGNO_MAX_RETRIES=3         # 最大重试次数
AGNO_RETRY_DELAY=5         # 重试延迟（秒）
```

## 开发指南

### 添加新的 API 端点

1. 在 `app/api/api_v1/endpoints/` 创建新的路由文件
2. 在 `app/api/api_v1/api.py` 中注册路由
3. 实现相应的服务层逻辑

### 添加新的智能体

1. 在 `app/agents/` 创建新的智能体文件
2. 实现智能体类和相关工具函数
3. 在 `app/agents/workflow.py` 中集成新的智能体
4. 更新 API 端点以使用新的智能体

### 添加新的数据库模型

1. 在 `app/models/` 创建新的模型文件
2. 在 `app/db/base.py` 中导入模型
3. 创建 Alembic 迁移: `alembic revision --autogenerate -m "Add new model"`
4. 应用迁移: `alembic upgrade head`

### 添加新的翻译语言

只需扩展 `ModelRouter` 类中的 `high_resource_languages` 集合，并确保相应的模型支持该语言。
