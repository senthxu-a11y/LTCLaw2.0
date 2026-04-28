# 数值工作台 执行文档

> 文档定位：本文档是数值工作台页面的完整执行规范，可直接交给 Coding Agent 开发。
> 与 `game-planner-workbench-plan.md` 的关系：方向文档确定了"数值工作台是独立页面 + Chat Drawer 双入口"的设计，本文档负责具体实现细节。

---

## 背景与设计决策

数值工作台有两个入口，服务不同场景：

| 入口 | 场景 | 空间 |
|------|------|------|
| Chat 右侧 Drawer | 对话中实时查看引用字段，快速决策 | 380px 窄栏 |
| 独立页面 `/game/workbench` | 专注深度调整，多表并列，全公式预览 | 全宽主内容区 |

两个入口共享同一份数据，状态可以互相传递（从 Drawer 点击跳转到独立页面时携带上下文）。

---

## 整体布局

应用是横版三栏布局：

```
┌──────┬─────────────────────────────────────────┬──────────┐
│      │  主内容区                                │          │
│      │  ┌───────────────────────────────────┐  │          │
│      │  │ 多表并列视图（上半区）              │  │          │
│Side  │  │ HeroTable SkillTable BuffTable ... │  │  右侧    │
│bar   │  │                                   │  │  Drawer  │
│      │  ├────── 可拖动分割线 ───────────────┤  │          │
│      │  │ 实时影响预览（下半区）              │  │（数值工作 │
│      │  │ 改动摘要 + 效果 + 计算链路          │  │ 台模式下 │
│      │  │ [生成变更草稿]  [重置]              │  │ 显示 AI  │
│      │  └───────────────────────────────────┘  │ 补全面板）│
└──────┴─────────────────────────────────────────┴──────────┘
```

- **上下分割线可拖动**，默认比例 6:4，最小高度各 20%
- **右侧 Drawer** 在数值工作台模式下内容切换为 AI 补全面板，Drawer 开关状态不变

---

## 目标

完成后可以验证：

- 策划打开 `/game/workbench`，看到多张关联表并列展示
- 修改任意字段后，下方实时预览影响范围和伤害计算链路
- 右侧 Drawer 自动切换为 AI 补全面板
- 点击 [生成变更草稿] → 进入现有审批流程（ApprovalCard）
- 从 Chat Drawer 点击 [在数值工作台中打开] 可携带上下文跳转并高亮目标字段

---

## 涉及文件清单

### 新建文件

```
console/src/pages/Game/
├── NumericWorkbench.tsx                  主页面
├── NumericWorkbench.module.less          样式
└── components/
    ├── TableColumn.tsx                   单张表的列组件
    ├── TableColumn.module.less
    ├── ImpactPreview.tsx                 实时影响预览区
    ├── ImpactPreview.module.less
    ├── DamageChain.tsx                   伤害计算链路可视化
    ├── DamageChain.module.less
    ├── AISuggestionPanel.tsx             右侧Drawer AI补全面板
    └── AISuggestionPanel.module.less
```

### 改动现有文件

| 文件 | 改动内容 | 性质 |
|------|----------|------|
| `console/src/pages/Game/index.ts` | export NumericWorkbench | 纯追加 |
| `console/src/App.tsx`（或路由文件） | 加 `/game/workbench` 路由 | 纯追加 |
| `console/src/layouts/Sidebar.tsx` | game-group 加"数值工作台"导航项 | 纯追加 |
| `console/src/pages/Chat/PlanPanel/index.tsx` | Drawer 内容根据模式条件渲染 | 扩展，原逻辑不动 |

---

## 数据结构定义

### 前端 State

```typescript
// 当前工作台上下文
interface WorkbenchContext {
  title: string                      // 如"剑士伤害调整"
  tables: WorkbenchTable[]           // 并列展示的表列表
  focusField?: {                     // 从Chat跳转时携带的焦点字段
    tableId: string
    fieldKey: string
  }
}

// 单张表
interface WorkbenchTable {
  tableId: string                    // 如"SkillTable"
  tableName: string
  records: WorkbenchRecord[]         // 展示的行，通常1~3行
}

// 单条记录（表中一行）
interface WorkbenchRecord {
  id: number
  fields: WorkbenchField[]
}

// 单个字段
interface WorkbenchField {
  key: string                        // 如"DamageCoeff"
  label: string                      // 显示名
  value: number | string
  editable: boolean
  pendingValue?: number | string     // 用户修改中的值，未提交
  warning?: string                   // 如"影响3个技能"
  highlight?: boolean                // 从Chat跳转时高亮
}

// 实时影响预览
interface ImpactPreview {
  changes: FieldChange[]
  effects: EffectItem[]
  damageChain?: DamageChain
}

interface FieldChange {
  tableId: string
  fieldKey: string
  oldValue: number | string
  newValue: number | string
}

interface EffectItem {
  description: string                // 如"斩击伤害提升17.6%"
  status: 'ok' | 'warning' | 'danger'
  detail?: string                    // 如"对比同类区间[0.9~1.3]"
}

// 伤害计算链路
interface DamageChain {
  formula: string                    // 完整公式字符串
  variables: DamageVariable[]
  resultBefore: number
  resultAfter: number
  deltaPercent: number
}

interface DamageVariable {
  name: string                       // 如"ATK"
  value: number
  sourceTable: string                // 来源表名
  isChanged: boolean                 // 本次改动是否涉及此变量
}

// AI补全建议（右侧Drawer）
interface AISuggestion {
  availableId?: number
  referenceValues: RefValue[]        // 同类参考值列表
  suggestedRange?: [number, number]  // 建议系数区间
  reusableResources: ReusableItem[]  // 可复用现有资源（如Buff）
  pendingConfirms: string[]          // 待策划确认项清单
}

interface RefValue {
  name: string                       // 技能/角色名
  id: number
  value: number
  note?: string
}

interface ReusableItem {
  id: number
  name: string
  type: string                       // 如"Buff"
}
```

### API 接口草案

```
GET  /api/game/workbench/context
     Query: tableIds[], recordIds[]
     Response: WorkbenchContext

POST /api/game/workbench/preview
     Body: { changes: FieldChange[] }
     Response: ImpactPreview

GET  /api/game/workbench/ai-suggest
     Query: intent（策划描述的意图文字）, tableId
     Response: AISuggestion

POST /api/game/change/propose
     Body: { changes: FieldChange[], description: string }
     Response: { proposalId: string }   → 进入现有审批流
```

---

## 页面结构与关键逻辑

### NumericWorkbench.tsx 主结构

```tsx
<div className={styles.workbench}>
  {/* 顶部标题栏 */}
  <div className={styles.header}>
    <Breadcrumb>数值工作台 / {context.title}</Breadcrumb>
    <Button onClick={handleReset}>重置</Button>
    <Button
      type="primary"
      disabled={pendingChanges.length === 0}
      onClick={handlePropose}
    >
      生成变更草稿
    </Button>
  </div>

  {/* 上下可拖动分割区域 */}
  <ResizablePanels
    direction="vertical"
    defaultSizes={[60, 40]}
    minSizes={[20, 20]}
  >
    {/* 上半：多表并列视图 */}
    <div className={styles.tableArea}>
      <div className={styles.tableColumns}>
        {context.tables.map(table => (
          <TableColumn
            key={table.tableId}
            table={table}
            pendingChanges={pendingChanges}
            onFieldChange={handleFieldChange}
          />
        ))}
      </div>
    </div>

    {/* 下半：实时影响预览 */}
    <ImpactPreview
      preview={impactPreview}
      loading={previewLoading}
    />
  </ResizablePanels>
</div>
```

### 可拖动分割线实现

优先复用项目现有的拖动实现。若没有，使用最小实现：

```tsx
// 不引入新依赖，用 useRef + mousemove 实现
// 上下两个div + 中间拖动条（8px高，cursor: row-resize）
// 拖动时动态修改上方div的flex-basis
```

### TableColumn.tsx 单表列组件

```
每列固定宽度：240px
表列超过4张时，外层横向滚动（不压缩列宽）

字段行结构：
├── 字段名（灰色小字，12px）
├── 字段值
│   ├── editable=false：纯文字展示
│   └── editable=true：点击变成 InputNumber
│                      blur 后触发 preview（防抖300ms）
├── pendingValue 存在：旧值 → 新值（橙色标注）
└── warning 存在：⚠️ 图标 + Tooltip 展示详情
```

### ImpactPreview.tsx 实时影响预览

```
触发时机：
  任意可编辑字段 blur 后，防抖 300ms
  调用 POST /api/game/workbench/preview

空状态：
  "修改上方字段后，这里会实时显示影响预览"

有数据时展示：
├── 改动摘要列表（每条一行：表名.字段 旧值→新值）
├── 预期效果列表
│   ├── ok（绿色）：在合理区间内
│   ├── warning（黄色）：偏高/偏低但可接受
│   └── danger（红色）：超出合理范围
├── DamageChain 组件（后端返回时才展示）
└── 操作按钮：[生成变更草稿]（有pendingChanges时亮起）[重置]
```

### DamageChain.tsx 伤害计算链路

```
布局：
├── 公式行：每个变量是一个 Tag
│   ├── 普通变量：灰色背景，标注来源表
│   └── 被改动的变量：橙色背景高亮
├── = 结果行
│   ├── 改动前：xxx
│   └── 改动后：xxx（红色/绿色，+x.x%）
└── 示例：
    ATK(150)  ×  ATKGrowth(1.2)  ×  DamageCoeff(1.0↑)  ×  0.6
    EquipTable   HeroTable         SkillTable【已改】
    = 108  （原 91.8，+17.6%）
```

### AISuggestionPanel.tsx（右侧Drawer内容）

数值工作台模式下 Drawer 内容切换为此组件：

```
├── 可用 ID：XXXX
├── 同类参考值（表格）
│   ├── 名称 | 系数 | 备注
│   └── 点击行可直接填入当前编辑字段
├── 建议区间：[0.5 ~ 0.7]（含推理说明）
├── 可复用资源（列表）
│   └── 点击直接填入 ID 字段
└── 待确认项（Checklist）
    └── 策划逐项勾选后 [生成变更草稿] 才可点击
```

---

## Drawer 内容切换逻辑

在 `PlanPanel/index.tsx` 加条件渲染，**原有逻辑完全不动**：

```tsx
// 改动前：
<PlanPanelContent ... />

// 改动后：
{isWorkbenchMode
  ? <AISuggestionPanel suggestion={aiSuggestion} />
  : <PlanPanelContent ... />      // 原有逻辑，一行不改
}
```

`isWorkbenchMode` 通过路由判断（`location.pathname.startsWith('/game/workbench')`），不引入额外全局状态。

---

## 从 Chat 跳转到数值工作台

Chat Drawer 里的引用字段旁加跳转入口：

```tsx
<span
  className={styles.openInWorkbench}
  onClick={() =>
    navigate(`/game/workbench?tableId=${tableId}&fieldKey=${fieldKey}`)
  }
>
  在数值工作台中打开 ↗
</span>
```

数值工作台初始化时读取 URL query params：

```typescript
// NumericWorkbench.tsx 初始化
const { tableId, fieldKey } = useSearchParams()
// → 自动滚动到对应列
// → 对应字段 highlight=true
// → 300ms 后取消高亮（只做一次引导）
```

---

## 生成变更草稿流程

```
[生成变更草稿] 点击
    ↓
POST /api/game/change/propose
    ↓
返回 proposalId
    ↓
复用现有 ApprovalCard 机制
阻塞型确认卡片出现在 Chat 消息流里
    ↓
策划批准 → 执行写回（现有 change_applier.py）
策划拒绝 → pendingChanges 保留，可继续修改
```

---

## 验收标准

```
□ 打开 /game/workbench，多表并列正常展示
□ 修改字段值 → 300ms后下方预览自动更新
□ 伤害计算链路中被改动的变量橙色高亮
□ 上下分割线可拖动，最小高度限制（20%）生效
□ [重置] 清空所有 pendingValue，预览区恢复空状态
□ [生成变更草稿] 在 pendingChanges 为空时置灰
□ [生成变更草稿] 点击 → ApprovalCard 出现在 Chat 消息流
□ 从 Chat Drawer [在数值工作台中打开] → 跳转并高亮目标字段
□ 右侧 Drawer 在数值工作台路由下显示 AI 补全面板
□ 离开 /game/workbench 路由 → Drawer 恢复原有内容
□ 回归：Chat 对话 / Agent / Approvals 功能正常
```

---

## 开发注意事项

```
1. ResizablePanels 优先复用项目现有实现，不引入新依赖
   若无，使用 useRef + mousemove 最小实现

2. 预览接口防抖 300ms，避免输入过程中频繁请求

3. pendingChanges 存在组件本地 state 里
   用户没点 [生成变更草稿] 前全部是本地状态，不请求写入

4. 多表并列超过4张时外层横向滚动
   每列保持 240px 固定宽，不压缩

5. Drawer 切换内容时只换内部渲染的组件
   不重置 Drawer 的开关状态，不影响 Drawer 动画

6. 数值工作台是全新页面，不改动任何现有 Chat 逻辑
   PlanPanel 里只加一个条件渲染，原分支完全不动

7. AISuggestionPanel 的"同类参考值"点击填入
   只填入当前正在编辑（focus）的字段，无 focus 时 Toast 提示先选中字段
```
