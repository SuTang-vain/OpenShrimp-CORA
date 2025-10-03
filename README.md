# Shrimp Agent V2

🦐 **智能搜索与文档管理平台** - 基于先进 AI 技术的下一代知识管理解决方案

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)

## ✨ 特性

### 🔍 智能搜索
- **语义搜索**: 基于 AI 的自然语言理解
- **多策略搜索**: 相似度、混合、MMR、关键词等多种搜索策略
- **实时建议**: 智能搜索建议和自动补全
- **搜索历史**: 个性化搜索记录和分析

### 📄 文档管理
- **多格式支持**: PDF, Word, TXT, Markdown, HTML, JSON, CSV
- **智能分块**: 多种分块策略优化检索效果
- **批量处理**: 高效的文档批量上传和处理
- **版本控制**: 文档版本管理和变更追踪

### 🤖 RAG 引擎
- **模块化设计**: 可插拔的组件架构
- **多向量数据库**: 支持 FAISS, Chroma, 内存存储
- **多嵌入模型**: OpenAI, Sentence Transformers, BGE
- **智能检索**: 高精度的文档片段检索

### 🎨 现代化界面
- **响应式设计**: 完美适配桌面和移动设备
- **暗色模式**: 护眼的深色主题支持
- **实时交互**: 流畅的用户体验
- **无障碍访问**: 符合 WCAG 标准

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI + Python 3.11
- **数据库**: PostgreSQL + Redis
- **向量数据库**: FAISS / Chroma
- **AI 模型**: OpenAI GPT, Sentence Transformers
- **任务队列**: Celery + Redis
- **监控**: Prometheus + Grafana

### 前端技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **路由**: React Router
- **UI 组件**: 自定义组件库

### 部署架构
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **CI/CD**: GitHub Actions
- **云平台**: 支持 AWS, GCP, Azure

## 🚀 快速开始

### 环境要求

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 20.10+ (可选)
- **PostgreSQL**: 13+ (可选，可使用 SQLite)
- **Redis**: 6+ (可选)

### 1. 克隆项目

```bash
git clone https://github.com/shrimp-team/shrimp-agent-v2.git
cd shrimp-agent-v2
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 3. 使用 Docker 部署（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 4. 本地开发部署

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 5. 访问应用

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **监控面板**: http://localhost:3001 (如果启用)

## 📖 使用指南

### 基础使用

1. **注册账户**: 访问应用并创建新账户
2. **上传文档**: 在文档管理页面上传您的文档
3. **等待处理**: 系统自动分析和索引文档
4. **开始搜索**: 使用自然语言搜索您的内容

### 高级功能

#### 搜索策略配置

```python
# 相似度搜索
strategy = "similarity"
top_k = 5
threshold = 0.7

# 混合搜索
strategy = "hybrid"
alpha = 0.7  # 语义权重

# MMR 搜索
strategy = "mmr"
lambda_mult = 0.5  # 多样性参数
```

#### API 使用示例

```python
import httpx

# 搜索文档
response = httpx.post(
    "http://localhost:8000/api/search/query",
    json={
        "query": "人工智能的发展趋势",
        "strategy": "similarity",
        "top_k": 10
    }
)

results = response.json()
```

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/app.db` |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | - |
| `MAX_FILE_SIZE` | 最大文件大小 | `50MB` |

### 功能开关

```env
# 启用/禁用功能
ENABLE_USER_REGISTRATION=true
ENABLE_DOCUMENT_UPLOAD=true
ENABLE_RAG_SEARCH=true
ENABLE_WEB_SEARCH=false
```

## 🧪 测试

### 运行测试

```bash
# 后端测试
cd backend
pytest tests/ -v --cov=.

# 前端测试
cd frontend
npm test
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 📊 监控和日志

### 应用监控

- **健康检查**: `/api/health`
- **指标端点**: `/metrics`
- **Grafana 面板**: http://localhost:3001

### 日志管理

```bash
# 查看应用日志
tail -f logs/shrimp_agent.log

# 查看 Docker 日志
docker-compose logs -f app
```

## 🚀 部署指南

### 生产环境部署

1. **环境准备**
   ```bash
   # 设置生产环境变量
   export ENVIRONMENT=production
   export DEBUG=false
   ```

2. **数据库设置**
   ```bash
   # 运行数据库迁移
   alembic upgrade head
   ```

3. **启动服务**
   ```bash
   # 使用生产配置
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### 扩展部署

```yaml
# docker-compose.scale.yml
services:
  app:
    deploy:
      replicas: 3
  
  nginx:
    deploy:
      replicas: 2
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 开发流程

1. **Fork 项目**
2. **创建特性分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 代码规范

```bash
# 后端代码格式化
black backend/
isort backend/
flake8 backend/

# 前端代码格式化
npm run lint
npm run format
```

### 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

## 📝 更新日志

### v2.0.0 (2024-01-15)

#### 🎉 新功能
- 全新的模块化架构设计
- React + TypeScript 前端重构
- 增强的 RAG 引擎
- 多策略搜索支持
- 现代化 UI/UX 设计

#### 🐛 修复
- 修复文档处理的内存泄漏问题
- 优化搜索性能
- 改进错误处理机制

#### 💥 破坏性变更
- API 端点重新设计
- 数据库架构更新
- 配置文件格式变更

## 🆘 故障排除

### 常见问题

#### 1. 文档上传失败

```bash
# 检查文件大小限制
echo $MAX_FILE_SIZE

# 检查支持的文件格式
echo $SUPPORTED_FILE_TYPES
```

#### 2. 搜索结果为空

```bash
# 检查文档是否已处理
curl http://localhost:8000/api/documents/{doc_id}/status

# 检查向量数据库
curl http://localhost:8000/api/health/services
```

#### 3. 服务启动失败

```bash
# 检查端口占用
lsof -i :8000

# 检查环境变量
env | grep SHRIMP
```

### 性能优化

1. **数据库优化**
   - 添加适当的索引
   - 定期清理过期数据
   - 使用连接池

2. **缓存策略**
   - 启用 Redis 缓存
   - 配置适当的 TTL
   - 使用 CDN 加速静态资源

3. **搜索优化**
   - 调整分块大小
   - 优化嵌入模型
   - 使用异步处理

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

感谢以下开源项目的支持：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [React](https://reactjs.org/) - 用户界面构建库
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的 CSS 框架
- [OpenAI](https://openai.com/) - AI 模型和 API
- [Sentence Transformers](https://www.sbert.net/) - 语义文本嵌入

## 📞 联系我们

- **项目主页**: https://github.com/shrimp-team/shrimp-agent-v2
- **问题反馈**: https://github.com/shrimp-team/shrimp-agent-v2/issues
- **邮箱**: contact@shrimp-agent.com
- **文档**: https://docs.shrimp-agent.com

---

<div align="center">
  <p>Made with ❤️ by Shrimp Team</p>
  <p>© 2024 Shrimp Agent. All rights reserved.</p>
</div>