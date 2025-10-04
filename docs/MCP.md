# MCP 设计与子系统划分（完整版本）

本项目以 CAMEL 框架为基底，构建“多代理协作 + Graphic RAG + 提示词可视化”的白盒交互系统。核心思想是将 RAG、知识图谱、提示词工程、服务适配和多代理编排以工具化视角拆解为可插拔的 MCP 子系统，既能独立演化，又能统一编排。

## 总览

- MCP 子系统：Context Engineering、Multimodal RAG、GraphicRAG、Agent Orchestrator、Service Adapter、Observability。
- 设计目标：接口清晰、职责单一、组合灵活、便于演进与替换。
- 协同方式：由 Orchestrator 负责工作流定义与执行，其他 MCP 作为能力提供者。

---

## 1. Context Engineering MCP（上下文工程）

职责：
- 管理提示词模板、变量注入与指令策略（few-shot、CoT、plan→solve）。
- 聚合与维护对话记忆（短期/长期）、用户个性化偏好。

接口：
- `GET /api/prompts/templates`：查询可用模板库（含标签、描述、变量）。
- `POST /api/prompts/render`：将模板与变量渲染为最终提示词。
- `POST /api/prompts/evaluate`：对提示词进行规则性评估（执行度、覆盖度、歧义度）。
- `POST /api/context/profile`：保存/更新用户画像、偏好与会话记忆策略。

示例返回字段：
- Template：`id`, `name`, `description`, `variables`, `categories`。
- Evaluate：`rule_coverage`, `ambiguity_score`, `constraints_ok`, `notes`。

---

## 2. Multimodal RAG MCP（多模态检索）

职责：
- 负责文档/图片/PDF/OCR/网页快照的切片、索引、检索重排与答案生成。
- 支持 `similarity`, `mmr`, `semantic_hybrid` 等策略。

接口：
- `POST /api/documents/upload`（已有）：上传并注册文档资源。
- `POST /api/rag/index`：对文档或资源集合进行索引与分块。
- `POST /api/query`（已有）：执行检索与生成，支持策略/阈值/`top_k`。
- `GET /api/rag/stats`（已有，建议强化）：返回索引规模、embedding cache 命中率、查询延时（p50/p95）等指标。

策略参数示例：
- `strategy`: `similarity | mmr | semantic_hybrid`
- `top_k`, `threshold`, `lambda_mult`, `alpha`

---

## 3. GraphicRAG MCP（图谱增强检索）

职责：
- 实体/关系抽取，知识图谱入库（Neo4j），图检索与边解释，图+文本融合（GraphRAG）。

接口：
- `POST /api/graph/build`：对指定文档/块执行实体与关系抽取并入库 Neo4j。
- `GET /api/graph/nodes|edges`：查询图节点/边（支持筛选与分页）。
- `POST /api/graph/query`：自然语言→Cypher 生成→图检索→相关文本块召回→答案生成。
- `POST /api/graph/explain`：对检索到的边与路径进行解释（证据片段与权重）。

实体/关系示例结构：
- Entity：`{ id, name, type, properties }`
- Relation：`{ id, source, target, relation, evidence }`

---

## 4. Agent Orchestrator MCP（CAMEL 多代理编排）

职责：
- 管理 Planner、PromptEngineer、Retriever、GraphBuilder、Executor、Evaluator 的协作。
- 根据用户上传材料自动生成工作流定义，并执行与追踪状态。

接口：
- `POST /api/agents/workflow/define`：基于材料生成工作流定义（节点/连线/参数）。
- `POST /api/agents/workflow/execute`：按工作流执行，产出结果与引用。
- `GET /api/agents/workflow/status`：查询执行状态、进度与日志。

工作流节点示例：
- `type`: `Retriever | GraphBuilder | PromptEngineer | Executor | Monitor`
- `config`: 模型、阈值、`top_k`、策略、缓存等。

---

## 5. Service Adapter MCP（服务适配）

职责：
- 统一管理第三方服务（LLM、Firecrawl、Neo4j、Ollama/LM Studio）的配置与连通性测试。
- 安全存储 API Key/Endpoint，避免明文落盘（建议加密保存）。

接口：
- `GET /api/services/providers`：列出支持的服务与能力。
- `POST /api/services/credentials`：保存/更新凭据与端点配置。
- `GET /api/services/status|test`：连通性测试与健康检查。

安全建议：
- Windows 环境使用 `cryptography` + 环境变量盐加密存储。
- 禁止在日志与前端页面暴露明文密钥。

---

## 6. Observability MCP（观测与度量）

职责：
- 收集检索链路时延、缓存命中率（embedding cache）、索引规模、图查询耗时、代理对话步数与失败率。

接口：
- `GET /api/rag/stats`：补齐 `embedding_cache_stats`（hits/misses/size）、`query_latency`（p50/p95）、`index_counts`。
- `GET /api/agents/stats`：代理执行步数、失败率、平均响应时间等。
- `GET /api/graph/stats`：节点/边计数、查询耗时分布、热度与社群指标。

实现建议：
- 在 `backend/core/rag/cache.py` 的“更新统计”位置落地缓存读写与命中指标，并回传到 `stats` 路由。
- Prometheus 指标采集 + Grafana 面板展示（可选）。

---

## 参考前端形态（摘要）

- 服务适配页（Settings → Services）：官方链接、API Key 输入、保存与连接测试。
- 提示词实验室（Prompt Lab）：模板库、参数滑块、变量绑定、预览与质量评分。
- 工作流画布（Workflow Canvas）：拖拽节点、连线数据流、节点配置（模型、阈值、`top_k`）。
- 图谱可视化（Graph Viewer）：节点/边检索、路径探索、边解释（证据片段）。

---

## 附：提示词模板（片段）

- Define（Planner）：输出目标、关键模块、数据来源、约束与风险、评估指标、候选工作流节点与连线。
- PromptEngineer：生成模型可执行提示词与变量槽位，提供“规则执行检查清单”。
- Retriever：选择 `keyword/similarity/hybrid/mmr/semantic_hybrid` 并给出参数与依据。
- GraphBuilder：抽取实体/关系/证据片段，输出可入库 JSON。
- Executor：生成最终产出，附数据溯源与质量评估。

---

## 风险与可行性（摘要）

- 中文语义检索：需切换中文友好嵌入并调整分块，影响命中率；风险可控。
- 前端资源报错：影响 UI 完整体验，建议优先修复模块路径或构建配置。
- Neo4j 部署：本地可用，云端需考虑许可与费用。
- 安全与密钥：统一走服务适配页 + 后端加密存储，避免明文。