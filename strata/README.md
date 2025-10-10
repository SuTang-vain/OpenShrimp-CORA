# Strata MCP Server (PoC)

本目录包含 Strata MCP Server 的最小可用实现，用于统一注册、聚合与路由 MCP 工具能力。

## 端点
- `GET /tools`：返回工具列表（name/description/schema）
- `POST /invoke`：根据 `tool` 字段调用对应 MCP 服务的 `/mcp/invoke`，请求体示例：
  ```json
  { "tool": "rag_query", "input": { "query": "如何优化中文嵌入？", "top_k": 5 } }
  ```

## 配置
- `config.yaml`：工具注册清单，示例见文件内容；可通过 `STRATA_CONFIG` 环境变量覆盖默认路径。

## 运行
- 本地：
  ```bash
  uvicorn strata.main:app --host 0.0.0.0 --port 8080
  ```
- Docker：
  见 `Dockerfile`，可在 `docker-compose.yml` 中添加 `strata` 服务：
  ```yaml
  services:
    strata:
      build: ./strata
      ports: ["8080:8080"]
  ```

## 约定
- MCP 子服务需实现：
  - `GET /mcp/tools`
  - `POST /mcp/invoke`（接受 `{tool, input}` 并返回 JSON）
- Strata 仅负责路由与聚合，不做具体业务处理。

## Roadmap
- 增加鉴权与配额控制（API Key / JWT）
- 增加可观测性（Prometheus 指标，OpenTelemetry 追踪）
- 支持 gRPC 协议与批量调用