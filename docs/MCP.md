# MCP 集成说明（shrimp-agent-v2）

## 概述

`shrimp-agent-v2` 已封装为可独立部署的 MCP 服务，通过 `/api/mcp/info` 与 `/api/mcp/capabilities` 对外暴露服务信息与能力发现，便于在主架构中按需集成。

## 服务信息接口

- `GET /api/mcp/info`：返回服务名称、版本、基础 URL 与环境信息。
- `GET /api/mcp/capabilities`：返回当前可用能力与计划能力（如 GraphRAG、服务密钥管理等）。

## 当前能力

- `rag.query`：`POST /api/query`，支持 similarity/keyword/hybrid/mmr/semantic_hybrid 等策略
- `documents.upload`：`POST /api/documents/upload`，支持批量文件上传与中文元数据
- `rag.embedding.switch`：`POST /api/rag/embedding/switch`，支持嵌入模型热切换（本地/云端）
- `rag.stats`：`GET /api/rag/stats`，返回 RAG 统计（建议持续完善缓存命中率等指标）

## 计划能力

- `graph.build`：知识图谱构建（Neo4j），实体关系抽取与入库
- `graph.query`：图查询（自然语言 → Cypher → 图检索 → 文本融合）
- `services.credentials`：服务适配（LLM/Firecrawl/Neo4j/Ollama/LM Studio）的 API Key 统一管理

## 清单文件

根目录提供 `mcp.manifest.json`，包含基础路由与能力列表，可被主架构扫描并自动注册。

```json
{
  "name": "shrimp-agent-v2",
  "version": "0.1.0",
  "base_url": "http://127.0.0.1:8000/api",
  "routes": {
    "info": "/api/mcp/info",
    "capabilities": "/api/mcp/capabilities",
    "health": "/health"
  },
  "capabilities": ["rag.query", "documents.upload", "rag.embedding.switch", "rag.stats"],
  "planned_capabilities": ["graph.build", "graph.query", "services.credentials"]
}
```

## 主架构集成建议（Monorepo）

建议在主项目采用如下目录结构，以模块化方式纳入 `shrimp-agent-v2`：

```
apps/
  orchestrator/            # CAMEL 工作流编排与统一入口
  services/
    rag-service/           # shrimp-agent-v2（本项目），作为独立 MCP 服务
    graph-service/         # Neo4j GraphRAG 服务
    prompt-service/        # 提示词模板与上下文工程服务
    adapter-service/       # 服务适配（API Key 管理）
packages/
  ui/                      # 前端页面（Services、Prompt Lab、Workflow、Graph）
  shared/                  # 共享类型、工具库、配置
infra/
  docker-compose.yml       # 统一编排各服务
  gateway/                 # API 网关/路由聚合
```

在 `infra/gateway` 层读取各 MCP 服务的 `*.manifest.json` 文件，自动注册路由与能力，以实现松耦合集成。

## 环境变量（可选）

- `MCP_BASE_URL`：覆盖基础 URL（默认 `http://127.0.0.1:8000/api`）
- `MCP_VERSION`：服务版本号（默认 `0.1.0`）
- `ENVIRONMENT`：环境标识（默认 `dev`）

## 验证步骤

1. 后端已运行：`uvicorn backend.main:app --reload`
2. 访问 `GET http://127.0.0.1:8000/api/mcp/info`
3. 访问 `GET http://127.0.0.1:8000/api/mcp/capabilities`
4. 验证返回内容与清单一致

## 后续迭代

- 完善 `GET /api/rag/stats` 指标：补齐缓存命中率与延迟分位（p50/p95）
- 增加 `POST /api/graph/build` 与 `POST /api/graph/query` 路由
- 新增 `GET/POST /api/services/*` 路由：完成服务适配页后端支持