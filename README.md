# OpenShrimp CORA

<img src="https://github.com/user-attachments/assets/4c77b644-d3ea-4ff0-9619-1c3a9dbfd832" alt="OpenShrimp CORA 截图 1" width="200"><img src="https://github.com/user-attachments/assets/1c5fdca7-ee37-42ba-9fd8-fd8a71871df3" alt="OpenShrimp CORA 截图 2" width="200">

全新一代智能搜索与知识管理平台（MCP 集成 + RAG + 图检索）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-00a393.svg)](https://fastapi.tiangolo.com/)
[![Vite+React](https://img.shields.io/badge/Vite%2BReact-18+-61dafb.svg)](https://vitejs.dev/)

## 项目概述

- 目标：以 CAMEL 框架为基底，构建“多代理协作 + Graphic RAG + 提示词可视化”的白盒交互系统，支持用户通过可视化工作流补齐工程所需材料，并由系统自动完成“Define（合理定义与定位）→ 构建工作流 → 执行”的闭环。
- 核心思想：以工具化视角把 RAG、知识图谱、提示词工程、服务适配和多代理编排拆解为可插拔的 MCP 子系统，既能独立演化，又能统一编排。
- 可行性：后端 API 已运行稳定，RAG 基础链路可用；前端存在资源报错但不影响 API 验证，可在迭代中修复。中文语义检索需优化嵌入模型与分块策略，属于可控工程问题。
- 架构更新：引入 Strata MCP Server（统一工具注册/聚合/路由）与 MCP 子服务（RAG、Graph），通过 `strata/config.yaml` 配置工具，统一暴露 `/tools` 与 `/invoke` 端点。

## 最新进展与架构更新（Strata + MCP）

- 新增组件
  - `strata/`：Strata MCP Server（端口 `8080`），统一列出工具（`GET /tools`）与转发调用（`POST /invoke`）。
  - `backend/mcp/rag`：RAG 子服务（内部端口 `8001`），暴露 `GET /mcp/tools` 与 `POST /mcp/invoke`，代理到主应用 `app:8000` 的 `/api/rag`。
  - `backend/mcp/graph`：Graph 子服务（内部端口 `8002`），暴露 `GET /mcp/tools` 与 `POST /mcp/invoke`，代理到主应用 `app:8000` 的 `/api/graph/query` 等。
- 端口与路由
  - 主应用（FastAPI）：`http://localhost:8000`
  - Strata MCP：`http://localhost:8080`
  - MCP-RAG：容器内 `http://mcp-rag:8001`（通过 Strata 路由）
  - MCP-Graph：容器内 `http://mcp-graph:8002`（通过 Strata 路由）
- 工具注册（示例）
  - 在 `strata/config.yaml` 中声明工具：
    - `rag_query` → `POST http://mcp-rag:8001/mcp/invoke`
    - `graph_explain` → `POST http://mcp-graph:8002/mcp/invoke`
- 统一端点示例（Strata）
  - 列出工具：`GET http://localhost:8080/tools`
  - 调用工具：`POST http://localhost:8080/invoke`，请求体示例见下文“API 快速示例”。

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

## 开发阶段（Milestones）

- M1（本周）：服务适配页后端接口打底（保存/连接测试）；中文友好嵌入切换与重新索引；强化 `rag/stats` 指标（embedding cache 命中率、查询延时 p50/p95、索引规模）。
- M2（下周）：Prompt Lab 与模板库上线；支持变量注入与评估；CAMEL 多代理最小闭环（Define → Retrieve → Draft → Evaluate）。
- M3（2–3 周）：GraphRAG 基础版（构建/查询/解释），图谱页面联动；工作流画布初版（节点配置与持久化）。
- M4（4 周）：全局观测与审计；权限与密钥管理完善；性能优化与中文检索全量验证（similarity/MMR/semantic_hybrid）。

## 子系统划分与 MCP 设计（摘要）

- Context Engineering MCP（上下文工程）
  - 职责：提示词模板管理、变量注入、策略（few-shot、cot、plan→solve）、对话记忆聚合与个性化偏好。
  - 接口：`GET /api/prompts/templates`、`POST /api/prompts/render`、`POST /api/prompts/evaluate`、`POST /api/context/profile`。

- Multimodal RAG MCP（多模态检索）
  - 职责：文档/图片/PDF/OCR/网页快照的切片、索引、重排与生成；支持 `semantic_hybrid`、`mmr`。
  - 接口：`POST /api/documents/upload`（已有）、`POST /api/rag/index`、`POST /api/query`（已有）、`GET /api/rag/stats`（建议强化）。

- GraphicRAG MCP（图谱增强检索）
  - 职责：实体/关系抽取、Neo4j 存储、图检索与边解释、图+文本融合（GraphRAG）。
  - 接口：`POST /api/graph/build`、`GET /api/graph/nodes|edges`、`POST /api/graph/query`（自然语言→Cypher）、`POST /api/graph/explain`。

- Agent Orchestrator MCP（CAMEL 多代理编排）
  - 职责：Planner / PromptEngineer / Retriever / GraphBuilder / Executor / Evaluator 协作，定义与执行工作流。
  - 接口：`POST /api/agents/workflow/define`、`POST /api/agents/workflow/execute`、`GET /api/agents/workflow/status`。

- Service Adapter MCP（服务适配）
  - 职责：统一管理第三方服务配置与连通性测试（LLM、Firecrawl、Neo4j、Ollama/LM Studio）。
  - 接口：`GET /api/services/providers`、`POST /api/services/credentials`、`GET /api/services/status|test`。

- Observability MCP（观测与度量）
  - 职责：检索链路时延、缓存命中率（embedding cache）、索引规模、图查询耗时、代理对话步数与失败率。
  - 接口：`GET /api/rag/stats`（继续完善）、`GET /api/agents/stats`、`GET /api/graph/stats`。

完整设计详见 `docs/MCP.md`。

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
├── strata/          # Strata MCP Server（/tools, /invoke, config.yaml）
└── backend/mcp/     # MCP 子服务（rag/graph 等）
README.md
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
- Strata MCP：`http://localhost:8080`

健康检查与快速验证：
- 列出工具（Strata）：`curl http://localhost:8080/tools`
- 代理调用示例（RAG，通过 Strata）：
  ```bash
  curl -X POST http://localhost:8080/invoke \
    -H "Content-Type: application/json" \
    -d '{
      "tool": "rag_query",
      "input": {"query": "Explain vector databases", "top_k": 5}
    }'
  ```
  预期返回：来自 RAG 子服务代理到主应用 `/api/rag` 的结果。

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
- Windows 环境提示：如需将 pip 缓存迁移至数据盘，可设置 `PIP_CACHE_DIR` 指向如 `G:\Python_ai_project\pip-cache`，以减少系统盘占用。

## API 快速示例（Strata MCP）

- 列出工具
  - `GET /tools`
  - 响应：注册于 `strata/config.yaml` 的工具列表（示例：`rag_query`, `graph_explain`）。
- 调用工具
  - `POST /invoke`
  - 示例：调用 `graph_explain`
    ```json
    {
      "tool": "graph_explain",
      "input": {
        "query": "Find connection between OpenAI and Microsoft in the graph",
        "limit": 10
      }
    }
    ```
  - 返回：由 MCP-Graph 代理到主应用图接口的解释与路径结果。

更多细节与扩展方式请参阅 `docs/STRATA_INTEGRATION.md`。

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
- 感谢 FastAPI、React、Tailwind 等开源生态

---

Made with ❤ for better search & knowledge.
