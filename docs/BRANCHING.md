# 分支策略（Open-Shrimp）

本文档定义仓库分支模型与提交流程，适用于 Open-Shrimp 的 `shrimp-agent-v2` 项目。

## 分支角色

- `main`
  - 作为主分支，承载稳定、可发布的代码；保留已验证能力与完整文档。
- `develop`
  - 集成分支，用于跨服务联调、接口对齐与前后端联测。
- `feature/*`
  - 功能分支（短周期），从 `develop` 切出用于增量开发：
    - 例如：`feature/mcp-rag`、`feature/mcp-graph`、`feature/mcp-prompt`、`feature/mcp-adapter`。
- `release/<version>`
  - 发布分支，配合 Tag（如 `v2.1.0`）用于冻结版本、回滚与环境对齐。
- `env/*`（可选）
  - 环境分支：如 `env/staging`、`env/prod`，用于隔离环境相关配置或资源清单；更稳妥的做法是使用配置仓 + 覆盖文件。

## 流程（GitFlow 精简变体）

1. 从 `develop` 切出 `feature/*` 开发分支。
2. 在 `feature/*` 分支完成开发/联测 → 提交 PR 回 `develop`。
3. `develop` 集成验证通过后，合并进入 `main`。
4. 如需发布：从 `develop` 切出 `release/<version>`，完成冻结与回归→ 合并到 `main`，并创建 Tag（例如：`v2.1.0`）。

## 提交与 PR 规范

- 提交信息建议使用前缀：`feat:`、`fix:`、`docs:`、`refactor:`、`test:`、`chore:`。
- PR 需包含：变更说明、影响范围、测试/验证要点、相关 Issue/需求链接。
- 代码合并策略建议：
  - `main`：仅允许通过 PR 合并，启用分支保护（评审、CI 通过、禁止直接 push）。
  - `develop`：允许通过 PR 合并，CI 必须通过；必要时允许维护者 rebase/squash。

## CI 与环境建议（后续可启用）

- 触发规则：对 `main`、`develop`、`release/*`、`feature/*` 的 PR/Push 运行。
- 发布流程：`release/<version>` 合并到 `main` 后创建 Tag，并生成发布说明。

## 默认分支

- GitHub 仓库默认分支请设置为 `main`（仓库 Settings → Branches → Default branch）。

## 分支保护建议（GitHub Settings → Branches → Branch protection rules）

建议对 `main`、`develop` 启用如下保护规则：

- 必须通过 Pull Request 合并，禁止直接 push（Allow force pushes: off）。
- 需要评审通过：至少 1–2 位 Reviewers（Dismiss stale approvals: on）。
- 必须通过状态检查（Require status checks to pass）：
  - Backend CI（Python/pytest）
  - Frontend CI（Node/build/test）
- 合并前分支需与目标分支保持最新（Require branches to be up to date before merging）。
- 合并策略：建议启用 `Squash merge`（线性历史，可选 `Require linear history`）。
- 可选：Require signed commits、限制可推送用户/团队（Restrict who can push to matching branches）。

## 配置步骤（快速参考）

1. 在仓库 Settings → Branches 将 Default branch 设置为 `main`。
2. 新建两条 Branch protection rules：分别匹配 `main` 与 `develop`。
3. 在 Rules 中启用：PR 评审、Require status checks（选择 Backend CI、Frontend CI）、Require branches to be up to date、限制合并策略和直推。
4. 保存后，所有 PR 必须通过 CI 与评审方可合并。