# Orchestrator 工作流 DSL 与节点配置

## 概述

本文定义 Shrimp Agent Orchestrator 的工作流 DSL（JSON/YAML）与节点配置规范，用于描述检索、推理、执行、服务调用、并行与条件路由等能力。DSL 目标：可读、可审计、可复用、可演化。

## 顶层结构

```yaml
name: 检索-推理-执行
version: "1"            # DSL 版本（向后兼容）
description: 标准检索-推理-执行流程
inputs:                  # 运行时输入定义
  question:
    type: string
    required: true
outputs:                 # 运行完成后的标准输出
  answer:
    type: string
    description: 最终回答文本
settings:                # 全局设置（可选）
  concurrency: 4
  timeout_ms: 60000
  retry: { max_attempts: 2, backoff_ms: 500 }
nodes:                   # 节点列表
  - id: ret
    type: retriever
    params:
      engine: hybrid
      top_k: 8
      query_from: "$inputs.question"   # 支持变量引用
  - id: rsn
    type: reasoner
    params:
      model: gpt-4
      prompt: |
        你是资深分析师，基于检索结果回答：
        {{ret.items}}
      temperature: 0.7
      max_tokens: 800
      tools: []
  - id: exe
    type: executor
    params:
      format: markdown
edges:                   # 有向边与条件路由
  - from: ret
    to: rsn
  - from: rsn
    to: exe
hooks:                   # 事件钩子（可选）
  on_start: []
  on_node_error: []
```

JSON 形式与 YAML 等价；运行时会进行模式校验（JSON Schema）。

## 变量与上下文

- 变量命名空间：`$inputs.*`、`$nodes.<id>.*`、`$ctx.*`（上下文存储）。
- 允许在 `params`、`edges.condition`、`prompt` 中使用插值：`{{ ... }}` 或 `$var.path`。
- 上下文持久化：节点可写入 `$ctx`，用于后续节点访问。

## 节点类型与参数

### retriever（检索）
- 作用：从向量库/关键词/图检索，返回候选项。
- 关键参数：
  - `engine`: `semantic|keyword|hybrid|graph`
  - `top_k`: 数量（默认 10）
  - `filters`: 结构化过滤（可选）
  - `query_from`: 变量引用或静态字符串
  - `include_content`: 是否返回片段内容（默认 true）
- 输出：`items`（数组，含 `document/chunk/score/source`）

### reasoner（推理/生成）
- 作用：LLM 推理，支持模板渲染与流式输出。
- 关键参数：
  - `model`: 模型名称
  - `prompt`: 模板，支持 `{{nodes.ret.items}}` 等引用
  - `temperature|max_tokens|stop`
  - `tools`: 工具调用白名单（可选）
  - `stream`: 是否开启流式（默认 false）
- 输出：`text`（字符串），`tokens|latency_ms`（元信息）

### executor（执行/汇总）
- 作用：将上游结果汇总为最终输出。
- 关键参数：
  - `format`: `markdown|json|text`
  - `schema`: 当 `json` 输出时的结构约束（可选）
- 输出：`result`（统一输出对象，通常映射到 `outputs.answer`）

### adapter_call（服务适配调用）
- 作用：调用外部服务（如 OpenAI/Azure/自建服务）。
- 关键参数：
  - `provider`: 提供方 ID（如 `openai`）
  - `service`: 服务名称（如 `chat|embeddings`）
  - `method`: 方法（如 `create|list`）
  - `params`: 业务参数，支持变量插值
  - `authRef`: 适配器凭据引用（如 `adp_123`）
- 输出：`response`（原始响应或提取后的结构）

### aggregator（聚合）
- 作用：合并多路结果（如并行分支）。
- 关键参数：`strategy: concat|merge|score_weighted`、`weights`（可选）
- 输出：`items|merged`（聚合结果）

### condition（条件）
- 作用：基于表达式路由到不同后继。
- 关键参数：`expression`: 如 `len(nodes.ret.items) > 0`
- 输出：无（控制流），根据条件选择 `edges` 的 `to`。

### parallel（并行）
- 作用：并发执行子节点组。
- 关键参数：`branches`: 节点子图列表，`max_concurrency`（默认 4）
- 输出：各分支结果聚合或写入 `$ctx`。

## 边与条件路由

```yaml
edges:
  - from: A
    to: B
    condition: "len(nodes.A.items) > 0"
  - from: A
    to: C
    condition: "len(nodes.A.items) == 0"
```

- 条件表达式使用受限运行时（无副作用），可访问只读上下文。

## 运行与事件流

- 启动：`POST /workflows/{id}/run`，返回 `run_id` 与 `stream_url`。
- 事件流（WebSocket）：`wss://.../workflows/runs/{run_id}/stream`
- 事件类型示例：
  - `node_started`、`node_finished`、`node_error`
  - `log`（结构化日志）、`metric`（指标快照）
  - `output_delta`（流式增量）

事件消息结构：
```json
{
  "type": "node_finished",
  "data": { "node_id": "rsn", "elapsed_ms": 850 },
  "run_id": "run_456",
  "ts": "2024-01-01T00:00:01Z"
}
```

## JSON Schema（摘要）

> 完整 Schema 建议放置于 `schemas/workflow.schema.json`，此处给出关键片段：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["name", "version", "nodes", "edges"],
  "properties": {
    "name": { "type": "string" },
    "version": { "type": "string" },
    "inputs": { "type": "object" },
    "outputs": { "type": "object" },
    "settings": { "type": "object" },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type"],
        "properties": {
          "id": { "type": "string" },
          "type": { "type": "string" },
          "params": { "type": "object" }
        }
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["from", "to"],
        "properties": {
          "from": { "type": "string" },
          "to": { "type": "string" },
          "condition": { "type": "string" }
        }
      }
    }
  }
}
```

## 安全与合规

- 机密管理：`authRef` 引用存储于 Adapters，DSL 不直接包含明文秘钥。
- 沙箱策略：表达式与模板在受限环境执行；外部调用必须明确白名单。
- 审计：运行产生 `trace_id|request_id`，事件与日志写入 Observability。

## 版本化与演进

- `version` 字段用于 DSL 语义版本；破坏性变更需升级大版本并提供迁移指南。
- 建议在 CI 中对 DSL 进行 Schema 校验与集成测试（最小工作流可运行）。

## 示例：并行检索与聚合

```yaml
name: 并行检索-聚合-回答
version: "1"
inputs:
  question: { type: string, required: true }
nodes:
  - id: ret_sem
    type: retriever
    params: { engine: semantic, top_k: 5, query_from: "$inputs.question" }
  - id: ret_kw
    type: retriever
    params: { engine: keyword, top_k: 5, query_from: "$inputs.question" }
  - id: agg
    type: aggregator
    params: { strategy: concat }
  - id: rsn
    type: reasoner
    params:
      model: gpt-4
      prompt: |
        综合以下检索结果：{{nodes.agg.items}}
  - id: exe
    type: executor
edges:
  - { from: ret_sem, to: agg }
  - { from: ret_kw, to: agg }
  - { from: agg, to: rsn }
  - { from: rsn, to: exe }
```

## 结语

以上规范为初版，后续将结合 MCP 设计与前端画布形态迭代完善（节点库、DSL 片段复用、可视化导入导出、运行回放与对比等）。