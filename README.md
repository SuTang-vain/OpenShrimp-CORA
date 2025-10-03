# Open-Shrimp KrillNet

🦐 全新下一代智能搜索与知识管理平台（MCP 集成 + RAG + 图检索）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-00a393.svg)](https://fastapi.tiangolo.com/)
[![Vite+React](https://img.shields.io/badge/Vite%2BReact-18+-61dafb.svg)](https://vitejs.dev/)

## 愿景与未来目标（Roadmap）

- MCP 集成增量（`feature/mcp-rag`）：统一工具/能力暴露，RAG 流水线接入 MCP 客户端。
- 图搜索（`feature/mcp-graph`）：对接 Neo4j，支持图查询与实体-关系检索，提供图接口网关。
- Prompt 体系（`feature/mcp-prompt`）：可组合提示模块与模板库，针对检索/生成优化与复用。
- Adapter 生态（`feature/mcp-adapter`）：对接不同模型/服务（LLM、Embedding、Search），实现能力适配。
- 网关增强：健康检查、服务发现、统一鉴权（JWT/Key）、跨服务路由与接口聚合。
- 前端生产化：构建优化、环境隔离（可选 `env/staging`/`env/prod`）、部署清单与灰度发布。
- 性能与可观测性：缓存与并发优化、指标采集（Prometheus）、统一日志与追踪。
- 测试与质量：后端 `pytest`、前端 `jest`，提升覆盖率与端到端联测。
- 发布与版本：`release/<version>` + Tag（如 `v2.1.0`），自动生成变更日志与发布说明。

## 仓库与分支策略

- 主分支：`main`（稳定可发布，集成已验证能力与文档）
- 集成分支：`develop`（跨服务联调、接口对齐与前后端联测）
- 功能分支：`feature/mcp-rag`、`feature/mcp-graph`、`feature/mcp-prompt`、`feature/mcp-adapter`
- 发布分支：`release/<version>` 配合 Tag（示例：`v2.1.0`）
- 环境分支（可选）：`env/staging`、`env/prod`
- 详细流程与保护规则见：`docs/BRANCHING.md`

## 目录结构（简）

```
shrimp-agent-v2/
├── backend/         # FastAPI 后端
├── frontend/        # Vite + React 前端
├── docs/            # 项目文档（API/架构/分支策略等）
├── config/          # 配置与模板
├── data/            # 数据与示例（不提交敏感/大文件）
├── docker/          # 镜像与部署相关
├── docker-compose.yml
└── README.md
```

## 快速开始

### 本地开发（推荐）

后端（FastAPI）：

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

前端（Vite + React）：

```bash
cd frontend
npm ci
npm run dev
# 访问 http://localhost:3000
```

### Docker Compose（一键启动）

```bash
docker compose up -d --build
docker compose ps
```

服务默认端口：
- 后端 API：`http://localhost:8000`
- 前端开发：`http://localhost:3000`

## CI 与质量保障

GitHub Actions 已启用：
- Backend CI：安装 `backend/requirements.txt` 并运行 `pytest`
- Frontend CI：Node 20，`npm ci`、`npm run build`、`npm test -- --passWithNoTests`

分支保护建议（在 GitHub Settings → Branches 配置）：
- `main`、`develop` 通过 PR 合并，禁止直接 push；至少 1–2 位评审；状态检查（Backend/Frontend CI）必须通过；合并前需 up-to-date；建议 `Squash merge`。

## 开发流程（摘要）

1) 从 `develop` 切出 `feature/*` 开发；
2) 本地/容器联测，提交 PR 回 `develop`；
3) 集成验证后合并 `main`；
4) 发布时从 `develop` 切 `release/<version>` 并打 Tag；完成回归与文档后合并 `main`。

## 配置与环境

- 使用 `.env.example` 复制生成 `.env`；敏感信息勿提交。
- 前后端支持本地与容器两种模式；生产部署建议开启统一鉴权与反向代理。

## 贡献指南（PR Checklist）

- 提交信息遵循 `feat/fix/docs/refactor/test/chore` 前缀。
- 本地通过：后端 `pytest`、前端 `npm test`、必要的构建检查。
- 更新相关文档（README、`docs/BRANCHING.md`）。
- 提供变更说明、影响范围、验证要点与截图（如有）。

## 发布与版本

- 发布分支：`release/<version>`；示例：`release/v2.1.0`
- 合并 `main` 后创建 Tag（如 `v2.1.0`），生成发布说明（建议启用 Release Drafter）。

## 致谢与许可证

- 许可证：MIT（见 `LICENSE`）
- 感谢 FastAPI、React、Tailwind、Camel-AI 等开源生态

---

Made with ❤ for better search & knowledge.
