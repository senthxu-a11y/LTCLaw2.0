# P1-00 Project Bundle 与路径收口

来源：总规划书 Phase 1、4.1、4.2、20 技术雷区 12。

## 目标

把项目数据、Map、Release、RAG、Agent、Audit 等数据统一收口到 project bundle 下，同时保留 legacy path 兼容。

## Checklist

- [ ] 定义 `<project-key>` 生成规则。
- [ ] 定义 project bundle 根目录解析规则。
- [ ] 定义 `project.json`。
- [ ] 定义 `source_config.yaml`。
- [ ] 定义 `sources/docs.yaml`。
- [ ] 定义 `sources/tables.yaml`。
- [ ] 定义 `sources/scripts.yaml`。
- [ ] 定义 `indexes/raw/` 目录结构。
- [ ] 定义 `indexes/canonical/` 目录结构。
- [ ] 定义 `maps/candidate/` 目录结构。
- [ ] 定义 `maps/formal/` 目录结构。
- [ ] 定义 `maps/diffs/` 目录结构。
- [ ] 定义 `releases/` 目录结构。
- [ ] 定义 `rag/` 目录结构。
- [ ] 定义 `runtime/` 目录结构。
- [ ] 定义 `agents/<agent-id>/` 目录结构。
- [ ] 定义 `agents/<agent-id>/audit/workbench_writeback.jsonl`。
- [ ] 定义后续 `admin/` MCP 工具池目录占位。
- [ ] 梳理现有 `paths.py` 与新 project bundle 的映射关系。
- [ ] 标记 legacy path，避免一次性破坏旧数据。

## 输出物

- [ ] Project Bundle 路径规范。
- [ ] Source 配置规范。
- [ ] 路径迁移策略。
- [ ] Legacy path 兼容策略。

## 验收标准

- [ ] Project-level 正式产物不依赖 session-level 私有状态。
- [ ] Session / Agent 只保存偏好、草案、日志和 UI 状态。
- [ ] 新写入路径进入 project bundle。
- [ ] 旧路径仍可兼容读取或给出明确迁移提示。

## 禁止范围

- [ ] 不直接把现有 `paths.py` 全部改掉。
- [ ] 不自动迁移用户数据而不保留回退方案。
- [ ] 不改变业务逻辑，只做路径规范 slice。

