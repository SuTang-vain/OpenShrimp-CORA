# Strata 集成指南（CORA + MCP 架构）

本指南介绍如何在开发模式下集成 Strata MCP Server，并将各 MCP 子服务以工具形式注册。

## 架构概览
- CORA（Agent Orchestrator）：统一业务入口，暴露 `/api/*` 能力
- MCP 子服务：`mcp-rag`、`mcp-graph` 等，提供标准化 `/mcp/tools` 与 `/mcp/invoke`
- Strata：聚合工具注册与统一路由入口（`/tools`、`/invoke`）

## 端点规范
- MCP 子服务：
  - `GET /mcp/tools` 返回工具列表与参数 schema
  - `POST /mcp/invoke` 接受 `{ tool, input }` 并返回 JSON 结果
- Strata：
  - `GET /tools` 聚合工具列表（来自 `config.yaml`）
  - `POST /invoke` 根据 `tool` 路由到对应 MCP 服务 `url`

## 配置与部署
- `strata/config.yaml` 定义工具注册：
  - `rag_query` → `http://mcp-rag:8001/mcp/invoke`
  - `graph_explain` → `http://mcp-graph:8002/mcp/invoke`
- `docker-compose.yml` 中新增服务：
  - `strata`、`mcp-rag`、`mcp-graph`
  - MCP 子服务通过 `CORA_URL=http://app:8000` 代理调用主应用能力

## 开发模式调用示例
```python
import httpx

result = httpx.post("http://localhost:8080/invoke", json={
    "tool": "rag_query",
    "input": {"query": "如何优化中文嵌入？", "top_k": 5}
}).json()
```

## Roadmap
- 将 MCP 子服务从代理模式过渡为直接集成核心引擎（RAG/Graph）
- 增加观测（Prometheus 指标、OpenTelemetry 追踪）
- 引入鉴权中间件（API Key/JWT），并与 Gateway 统一
- 扩展 `strata/config.yaml` schema（分组、标签、版本、鉴权策略）