# P3-01 管理员面板、版本显示与审计聚合

来源：总规划书 P3、Phase 10、Phase 11。

## 目标

把 Map/RAG/Release 管理员能力集中到本地管理入口，并补齐当前知识版本显示和多个 agent 写回日志聚合查看。

## Checklist

- [x] 在本地 Admin Panel 页面显示当前 project bundle 路径。
- [x] 在本地 Admin Panel 页面显示 source config 路径。
- [x] 在本地 Admin Panel 页面显示当前 Release ID。
- [x] 在本地 Admin Panel 页面显示当前 Map hash。
- [x] 在本地 Admin Panel 页面显示 RAG status。
- [x] 在本地 Admin Panel 页面显示 Formal Map 状态。
- [x] 在本地 Admin Panel 页面显示当前 knowledge version。
- [ ] 不在本切片提供 Rebuild Index 按钮。
- [ ] 不在本切片提供 Candidate Map 生成按钮。
- [x] 提供 Candidate Map Review / Map Diff Review 入口。
- [x] 提供 Save Formal Map 操作入口。
- [x] 提供 Build Release 操作入口。
- [x] 提供 Publish / Set Current 操作入口。
- [ ] 不在本切片提供主动知识一致性检查按钮。
- [x] 提供 agent audit 聚合查看占位入口，并明确无后端读取能力时只做 UI 占位。
- [x] 不向普通策划展示管理员操作。
- [x] 工作台显示当前知识版本由 P3-00 既有实现继承，本切片不重复改动。
- [x] Draft Overlay 明确标记由 P3-00 既有实现继承，本切片不重复改动。
- [x] RAG citation 到工作台建议上下文闭环由 P3-00 既有实现继承，本切片不重复改动。

## 输出物

- [x] Admin Panel 信息架构。
- [x] 管理员操作权限矩阵。
- [x] 管理员操作确认流程边界说明。
- [x] 管理员聚合查看设计边界说明。

## 本次实现

- 管理入口落在现有 Advanced 页面，作为本地 Admin Panel，不新增新路由和新后端工作流。
- 面板只聚合只读状态：project bundle path、source config path、current release id、current map hash、formal map status、RAG status、current knowledge version。
- 写操作仍然跳转到既有页面：Map Editor 负责 Candidate Map Review / Map Diff Review 与 Save Formal Map，Knowledge 页面负责 Build Release 与 Publish / Set Current。
- 前端 capability gate 继承现有语义：有显式 capability 上下文时按 capability 隐藏或禁用；无显式 capability 上下文时不新增额外前端限制。
- audit 聚合只提供信息架构占位，不新增中心化审计服务，也不新增 audit 读取 API。

## 权限矩阵

- Candidate Map Review / Map Diff Review：需要 knowledge.candidate.read、knowledge.candidate.write、knowledge.map.read。
- Save Formal Map：需要 knowledge.map.read、knowledge.map.edit。
- Build Release：需要 knowledge.build。
- Publish / Set Current：需要 knowledge.publish。
- 普通策划或只读角色：不显示 Admin Panel 内的管理员操作入口。

## 确认流程边界

- 本切片不在 Admin Panel 内直接执行写操作，因此不新增新的确认弹窗或二次提交流程。
- 所有写操作继续在原页面执行，并沿用原页面已有的确认与错误处理逻辑。

## 审计聚合边界

- 允许在 Admin Panel 中保留只读 audit 聚合槽位，用于说明未来聚合视图的位置。
- 若后端没有现成 audit 读取能力，则本切片只显示占位说明，不自行扫描文件系统，不新增中心化聚合服务。

## 验收标准

- [x] 管理员操作都受 capability gate 控制。
- [x] Build Release 和 Publish / Set Current 是两个显式操作。
- [x] agent audit 在无现成后端读取 API 时仅保留聚合查看占位，不新增中心化服务。
- [x] 普通策划看不到管理员操作入口。

## 禁止范围

- [ ] 不做中心化审计服务。
- [ ] 不把管理员操作暴露给普通策划。
- [ ] 不让一致性检查自动打扰普通策划。

