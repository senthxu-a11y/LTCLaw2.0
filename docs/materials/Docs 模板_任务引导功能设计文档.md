# 任务引导系统功能设计文档

**文档版本**：v2.0
**创建日期**：2026-04-14
**作者**：SystemDesigner
**评审状态**：待主策评审

---

## 1. 功能概述

任务引导系统是HSR项目为新手玩家设计的目标引导系统，通过串联游戏内各个核心玩法系统，帮助玩家逐步了解游戏机制并获得成长奖励。

**核心定位**：
- 完成序章后解锁，在主界面挑战按钮上方显示
- 线性任务流程（100个任务），完成一个解锁下一个
- 点击交互：未完成时跳转目标界面，完成时领取奖励

---

## 2. 设计意图

### 2.1 设计目标

| 目标 | 说明 |
|------|------|
| 降低学习成本 | 通过明确的目标引导，减少新手玩家的迷茫感 |
| 串联核心系统 | 将亡灵密藏、诸神冥殿、爬塔等系统有机串联 |
| 提供成长动力 | 通过阶段性奖励激励玩家持续游戏 |
| 数据埋点支持 | 追踪玩家任务完成情况，优化新手流失率 |

### 2.2 玩家体验预期

- **0-30任务**：熟悉基础操作和核心系统（亡灵密藏、抽奖、装备升级）
- **31-60任务**：深入玩法体验（爬塔、BOSS挑战、遗物系统）
- **61-100任务**：高级玩法探索（混沌形态、献祭、黑市）

---

## 3. 功能流程图

### 3.1 主流程

```
[玩家进入主界面]
    ↓
[检查是否完成序章(2229992)]
    ↓ 是
[检查并激活可解锁任务]
    ↓
[显示当前任务UI]
    ↓
[玩家点击任务]
    ↓
┌─────────────────┐
│ 任务是否完成？   │
│ current>=target │
└─────────────────┘
    ↓ 否              ↓ 是
[JumpViewId跳转]   [发送领奖请求]
    ↓                ↓
[玩家执行操作]      [服务器校验+发放奖励]
    ↓                ↓
[计数触发+1]        [更新状态为已领奖]
    ↓                ↓
[current==target?]  [激活下一个任务]
    ↓ 是             ↓
[标记任务完成]      [显示下一任务/隐藏UI]
    ↓
[等待玩家领奖]
```

### 3.2 任务状态流转

```
[锁定] → [未激活] → [进行中] → [已完成] → [已领奖]
            ↑                              ↓
            └──────── [全部完成消失] ←─────┘
```

| 状态值 | 状态名 | 说明 |
|--------|--------|------|
| 0 | 锁定(Locked) | 前置任务未完成或未满足解锁条件 |
| 1 | 进行中(InProgress) | 已激活，等待玩家完成目标 |
| 2 | 已完成(Completed) | 目标达成，可领取奖励 |
| 3 | 已领奖(Claimed) | 奖励已领取 |

---

## 4. 详细逻辑说明

### 4.1 任务激活逻辑

**激活条件（需同时满足）**：
1. 玩家完成序章（章节ID：2229992）
2. 前置任务已完成（PreTaskId为0或前置任务状态为"已领奖"）
3. 满足解锁章节要求（UnlockChapterId为0或玩家已通关该章节）

**激活时机**：
- 玩家登录时检查
- 完成前置任务时立即激活
- 通关解锁章节时检查激活

**前置依赖检查**：
```
if (PreTaskId == 0) {
    // 无前置任务，直接激活
    ActivateTask(taskId);
} else {
    // 检查前置任务状态
    preTaskStatus = GetTaskStatus(PreTaskId);
    if (preTaskStatus == 3) { // 已领奖
        ActivateTask(taskId);
    }
}
```

### 4.2 任务进度追踪

**计数规则**：
- 任务激活后才开始计数
- 每次操作独立计数，不累加历史记录
- 达到TargetCount后标记为"已完成"
- current_count最大不超过target_count

**各类型计数触发点**：

| 任务类型 | 枚举值 | 计数触发时机 | 事件来源系统 | 特殊参数 |
|----------|--------|--------------|--------------|----------|
| 亡灵密藏开启 | 0 | 开启宝箱时 | TombSystem | - |
| 诸神冥殿抽奖 | 1 | 抽奖完成时 | DrawSystem | 单抽+1，十抽+10 |
| 完成章节 | 2 | 章节结算胜利时 | ChapterSystem | TargetParam=章节ID |
| 装备升级 | 3 | 升级成功时 | EquipSystem | - |
| 携带近战精灵 | 4 | 关卡胜利结算时 | BattleSystem | 检查出战阵容 |
| 携带远程精灵 | 5 | 关卡胜利结算时 | BattleSystem | 检查出战阵容 |
| 遗物升级 | 6 | 升级成功时 | PropertySystem | - |
| 挑战爬塔 | 7 | 爬塔战斗结束时 | TowerSystem | 无论胜负 |
| 挑战金币关 | 8 | 金币关结算时 | GoldLevelSystem | 无论胜负 |
| BOSS挑战 | 9 | BOSS战结束时 | BossSystem | 无论胜负 |
| 黑市购物 | 10 | 购买成功时 | BlackMarketSystem | - |
| 献祭供奉 | 11 | 供奉完成时 | SacrificeSystem | - |
| 升级混沌形态 | 12 | 升级成功时 | ChaosSystem | - |
| 购买体力 | 13 | 购买成功时 | StaminaSystem | - |

**进度更新伪代码**：
```
function UpdateTaskProgress(playerId, taskType, count = 1, param = 0):
    // 1. 查询当前激活的该类型任务
    activeTask = GetActiveTaskByType(playerId, taskType);
    if (activeTask == null) return;
    
    // 2. 检查任务参数是否匹配
    if (activeTask.TargetParam != 0 && activeTask.TargetParam != param):
        return; // 参数不匹配，不计数
    
    // 3. 更新进度
    newCount = min(activeTask.current_count + count, activeTask.target_count);
    activeTask.current_count = newCount;
    
    // 4. 检查是否完成
    if (newCount >= activeTask.target_count):
        activeTask.status = 2; // 已完成
        SendTaskCompleteNotify(playerId, activeTask.task_guide_id);
    
    // 5. 保存并通知客户端
    SaveTaskProgress(playerId, activeTask);
    SendProgressNotify(playerId, activeTask);
```

### 4.3 奖励发放逻辑

**发放时机**：玩家点击"已完成"状态的任务时

**发放流程**：
```
1. 客户端发送 TaskGuideClaimRewardReq
   └─ task_guide_id: 任务ID
   └─ request_id: 幂等请求ID
   
2. 服务器校验
   ├─ 任务存在性检查
   ├─ 任务状态检查（必须为2-已完成）
   ├─ 前置任务检查
   └─ 幂等校验
   
3. 奖励发放
   ├─ 从TaskGuideReward表查询奖励列表
   ├─ 调用Currency系统发放
   ├─ 如背包满则发邮件
   └─ 更新任务状态为3-已领奖
   
4. 激活下一任务
   └─ 检查下一个任务的激活条件
   
5. 返回结果
   ├─ ret_code: 错误码
   ├─ rewards: 实际发放的奖励
   └─ next_task: 下一任务信息（如有）
```

**异常处理**：
| 异常场景 | 处理方案 |
|----------|----------|
| 背包满 | 奖励发送至邮件，提示"背包已满，奖励已邮件发放" |
| 网络异常 | 显示loading，超时(10s)提示"网络异常，请重试" |
| 奖励发放失败 | 任务状态不回滚，奖励重试发放 |
| 并发领奖 | 幂等校验，相同request_id只处理一次 |

### 4.4 边界情况

| 场景 | 处理方案 |
|------|----------|
| 任务进行中退出游戏 | 进度实时存库，下次登录恢复 |
| 任务已完成但未领奖 | 保留完成状态，直到玩家领奖 |
| 同时完成多个任务条件 | 只计数当前激活的任务 |
| 100个任务全部完成 | 任务引导UI从主界面消失 |
| 回滚存档 | 以服务器数据为准 |
| 快速重复点击领奖 | 防重复，锁定500ms |
| 跨服数据同步 | 任务数据跟随玩家账号 |

---

## 5. 数值参数表

### 5.1 TaskGuide.txt 完整字段说明

| 字段名 | 类型 | 枚举/范围 | 必填 | 默认值 | 说明 |
|--------|------|----------|------|--------|------|
| Id | Int | 2700001~2700100 | 是 | - | 任务ID，7位格式，前缀270 |
| Name | String | Language表ID | 是 | - | 任务名称，格式：TaskGuide_Name_{Id} |
| Desc | String | Language表ID | 是 | - | 任务描述，格式：TaskGuide_Desc_{Id} |
| TaskType | Int | 0~13 | 是 | - | 任务类型，参见TaskGuideType枚举 |
| TargetCount | Int | 1~9999 | 是 | - | 目标完成次数 |
| TargetParam | Int | 0~9999999 | 否 | 0 | 任务参数（如章节ID，0表示不限制） |
| JumpViewId | Int | 引用CurrencyJump | 是 | - | 跳转界面ID，引用CurrencyJump表 |
| RewardGroupId | Int | 2710001~2710100 | 是 | - | 奖励组ID，引用TaskGuideReward表 |
| Sort | Int | 1~100 | 是 | - | 任务排序号，线性解锁 |
| IsShowProgress | Bool | true/false | 是 | true | 是否显示进度条 |
| Icon | String | UI资源路径 | 是 | - | 任务图标路径 |
| PreTaskId | Int | 0或2700001~2700099 | 否 | 0 | 前置任务ID，0表示无前置 |
| UnlockChapterId | Int | 0或章节ID | 否 | 0 | 解锁章节ID，0表示无限制 |

### 5.2 TaskGuideReward.txt 完整字段说明

| 字段名 | 类型 | 枚举/范围 | 必填 | 默认值 | 说明 |
|--------|------|----------|------|--------|------|
| Id | Int | 2710001+ | 是 | - | 奖励项ID，需保证组内唯一 |
| GroupId | Int | 2710001~2710100 | 是 | - | 奖励组ID，与TaskGuide.RewardGroupId对应 |
| RewardType | Int | 0~8 | 是 | - | 奖励类型，参见RewardType枚举 |
| RewardId | Int | Currency表ID | 是 | - | 奖励物品ID，引用Currency表 |
| RewardCount | Int | 1~999999 | 是 | - | 奖励数量 |
| Sort | Int | 1~10 | 是 | 1 | 组内排序 |

### 5.3 TaskGuideType 枚举完整定义

```csharp
public enum TaskGuideType
{
    OpenTreasure = 0,           // 亡灵密藏开启次数
    DrawGodPool = 1,            // 诸神冥殿抽奖次数
    CompleteChapter = 2,       // 完成章节（TargetParam=章节ID）
    UpgradeEquipment = 3,       // 装备升级次数
    CarryMeleeFighter = 4,      // 携带近战精灵挑战关卡（胜利）
    CarryRangedFighter = 5,     // 携带远程精灵挑战关卡（胜利）
    UpgradeProperty = 6,        // 遗物升级次数
    ChallengeTower = 7,          // 挑战爬塔次数
    ChallengeGoldLevel = 8,     // 挑战金币关次数
    ChallengeBoss = 9,         // BOSS挑战次数
    BlackMarketBuy = 10,        // 黑市购物次数
    SacrificeWorship = 11,      // 献祭供奉次数
    UpgradeChaosForm = 12,      // 升级混沌形态次数
    BuyStamina = 13,            // 购买体力次数
}
```

### 5.4 TaskGuideRewardType 枚举完整定义

```csharp
public enum TaskGuideRewardType
{
    Gold = 0,                   // 金币 (CurrencyId: 1000001)
    Diamond = 1,                 // 钻石 (CurrencyId: 1000002)
    EquipDrawTicket = 2,        // 装备抽奖券 (CurrencyId: 1000036)
    FighterDrawTicket = 3,      // 精灵抽奖券 (CurrencyId: 1000037)
    PropertyDrawTicket = 4,      // 遗物抽奖券 (CurrencyId: 1000038)
    RandomEquipBlueprint = 5,   // 随机装备图纸 (CurrencyId: 1000040)
    FighterFood = 6,             // 精灵口粮 (CurrencyId: 1000031)
    ChaosFragment = 7,           // 混沌碎片 (CurrencyId: 1000044)
    RefinePotion = 8,            // 精炼药水 (CurrencyId: 1000045)
}
```

### 5.5 JumpViewId 与 CurrencyJump 表映射

| TaskGuide.JumpViewId | CurrencyJump.Id | 跳转目标 | GameFuncType |
|----------------------|-----------------|----------|--------------|
| 3 | 3 | 遗物抽奖界面 | 5 |
| 4 | 4 | 宝箱界面 | 12 |
| 9 | 9 | 装备抽奖界面 | 16 |
| 223 | [需新增] | 装备升级界面 | [需确认] |
| 241 | [需新增] | 诸神冥殿抽奖界面 | [需确认] |
| 251 | 10 | 献祭界面 | 25 |
| 258 | [需新增] | 遗物升级界面 | [需确认] |
| 311 | 11 | 黑市界面 | 17 |
| 312 | [需新增] | 金币关界面 | [需确认] |
| 316 | 27 | 爬塔主界面 | 22 |
| 323 | 26 | BOSS连战主界面 | 24 |
| 234 | 21 | 混沌界面 | 9 |

---

## 6. UI/交互说明

### 6.1 主界面任务引导UI

**位置**：主界面挑战按钮上方，居中显示

**UI构成**：
```
┌─────────────────────────────────────┐
│ [任务图标]  任务名称                  │
│            描述文本（可选）           │
│            进度: 2/3  [■■■□□]        │
└─────────────────────────────────────┘
```

**尺寸规格**：
- 整体宽度：屏幕宽度的60%~80%
- 高度：80~120像素
- 圆角：12像素
- 图标尺寸：48x48像素

**状态样式**：

| 状态 | 背景色 | 边框 | 进度条 | 交互 |
|------|--------|------|--------|------|
| 进行中(1) | #1A1A2E | #3A3A5E | 显示current/target | 点击跳转 |
| 已完成(2) | #2A2A4E | #FFD700(金色) | 满进度+发光 | 点击领奖 |
| 已领奖(3) | 渐隐动画 | - | 消失 | 无 |

**动画效果**：
- 状态切换：200ms ease-out
- 完成闪光：粒子特效 + 金色边框闪烁
- 消失动画：向上飘走 + 淡出

### 6.2 任务详情弹窗

**触发**：长按任务UI（500ms）或点击右侧"?"按钮

**弹窗内容**：
```
┌─────────────────────────────────────┐
│ [X]                                 │
│                                     │
│  任务图标  任务名称                   │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  任务描述：                          │
│  "在亡灵秘藏开启3次宝箱"              │
│                                     │
│  进度：■■■□□ (3/3)                   │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  奖励预览：                          │
│  [金币图标] 1000                     │
│  [装备券图标] x1                     │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  [立即前往] / [领取奖励]              │
│                                     │
└─────────────────────────────────────┘
```

### 6.3 奖励领取特效

**触发时机**：领奖请求成功返回后

**特效流程**：
1. 任务框缩小居中（200ms）
2. 爆炸粒子效果（300ms）
3. 奖励图标依次飞出（100ms间隔）
4. 飘向各自资源栏（500ms）
5. 资源栏数字跳动（200ms）

---

## 7. 联动系统说明

### 7.1 配置表引用关系

```
TaskGuide.txt (270-XXXX)
    ├── 引用 CurrencyJump.txt (JumpViewId) - 界面跳转
    │       └─ 新增JumpViewId需同步更新CurrencyJump表
    └── 引用 TaskGuideReward.txt (RewardGroupId) - 奖励配置

TaskGuideReward.txt (271-XXXX)
    ├── 引用 Currency.txt (RewardId) - 货币奖励
    │       └─ CurrencyId: 1000001~1000045
    ├── 引用 HSRDraw.txt - 抽奖券类(RewardId: 1000036~1000038)
    └── 引用 Equipment.txt - 装备图纸(RewardId: 1000040)
```

### 7.2 系统间事件监听

| 源系统 | 事件名 | 触发参数 | 任务类型 |
|--------|--------|----------|----------|
| TombSystem | OnTreasureOpen | - | OpenTreasure(0) |
| DrawSystem | OnGodPoolDraw | isTenDraw:bool | DrawGodPool(1) |
| ChapterSystem | OnChapterComplete | chapterId:int | CompleteChapter(2) |
| EquipSystem | OnEquipmentUpgrade | equipId:int, level:int | UpgradeEquipment(3) |
| BattleSystem | OnLevelComplete | fighterIds:List, isWin:bool | CarryMeleeFighter(4), CarryRangedFighter(5) |
| PropertySystem | OnPropertyUpgrade | propertyId:int | UpgradeProperty(6) |
| TowerSystem | OnTowerChallenge | floorId:int, isWin:bool | ChallengeTower(7) |
| GoldLevelSystem | OnGoldLevelComplete | isWin:bool | ChallengeGoldLevel(8) |
| BossSystem | OnBossChallenge | bossId:int, isWin:bool | ChallengeBoss(9) |
| BlackMarketSystem | OnBlackMarketBuy | itemId:int | BlackMarketBuy(10) |
| SacrificeSystem | OnSacrificeWorship | offeringType:int | SacrificeWorship(11) |
| ChaosSystem | OnChaosFormUpgrade | formId:int | UpgradeChaosForm(12) |
| StaminaSystem | OnStaminaBuy | count:int | BuyStamina(13) |

### 7.3 与Guide系统的区分

| 维度 | 任务引导系统 | 新手引导系统 |
|------|--------------|--------------|
| 触发时机 | 序章后持续存在 | 仅新手期 |
| 任务数量 | 100个 | ~38个步骤 |
| 线性流程 | 是，前置依赖 | 否，按触发条件 |
| 奖励 | 有，货币/道具 | 有，固定奖励 |
| 表现形式 | 主界面UI入口 | 强制遮罩+手指 |

---

## 8. 开发注意事项

### 8.1 客户端开发注意

| 事项 | 优先级 | 说明 |
|------|--------|------|
| 任务状态缓存 | P0 | 登录时拉取全部状态到本地，减少网络请求 |
| 进度实时更新 | P0 | 收到通知后立即刷新UI，不等待轮询 |
| 领奖防重 | P0 | 按钮锁定500ms，防止重复发送请求 |
| 跳转防抖 | P1 | 跳转时按钮防抖300ms |
| 断线重连 | P1 | 重连后请求最新任务状态 |
| 特效性能 | P2 | 完成特效使用对象池，避免频繁GC |

### 8.2 服务器开发注意

| 事项 | 优先级 | 说明 |
|------|--------|------|
| 并发控制 | P0 | 领奖操作加分布式锁 |
| 幂等设计 | P0 | request_id作为唯一键，相同ID只处理一次 |
| 事务保证 | P0 | 奖励发放与状态更新需在同一事务 |
| 奖励失败处理 | P1 | 奖励发放失败时任务状态不回滚，记录日志 |
| 进度上限 | P1 | current_count不能超过target_count |
| 定时检查 | P2 | 定时任务检查并激活可解锁的任务 |

### 8.3 配置表注意事项

| 事项 | 说明 |
|------|------|
| JumpViewId一致性 | 新增跳转目标时需同步在CurrencyJump表添加记录 |
| CurrencyId有效性 | RewardId必须引用Currency表中存在的ID |
| ID连续性 | TaskGuide.Id和RewardGroupId需保持对应关系 |
| PreTaskId循环检查 | 配置时避免出现循环前置依赖 |

---

## 9. 测试用例

### 9.1 正常流程测试

| 用例ID | 场景描述 | 前置条件 | 操作步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| TC-001 | 任务激活-无前置 | 完成序章 | 进入主界面 | 显示任务1，状态为进行中 |
| TC-002 | 任务激活-有前置 | 任务1已领奖 | 进入主界面 | 任务2自动激活 |
| TC-003 | 任务进度计数 | 任务已激活 | 完成任务目标操作 | 进度+1，显示更新 |
| TC-004 | 任务完成判定 | 进度达到目标 | 最后一次操作 | 状态变为已完成，播放特效 |
| TC-005 | 奖励领取 | 任务已完成 | 点击任务 | 奖励发放，状态变为已领奖 |
| TC-006 | 下一任务激活 | 当前任务已领奖 | 领取奖励后 | 下一任务自动激活显示 |

### 9.2 边界测试

| 用例ID | 场景描述 | 前置条件 | 操作步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| TC-007 | 进度上限 | 当前进度=目标-1 | 触发计数+2 | 进度=max(当前+2, 目标)=目标 |
| TC-008 | 全部完成 | 100个任务全领奖 | 进入主界面 | 任务引导UI不显示 |
| TC-009 | 跨天登录 | 任务进行中 | 跨天登录 | 任务状态保留，继续 |
| TC-010 | 前置未完成 | 任务1未完成 | 登录检查任务2 | 任务2显示为锁定 |
| TC-011 | 快速重复点击 | 任务已完成 | 1秒内点击3次 | 只发送1次领奖请求 |

### 9.3 异常测试

| 用例ID | 场景描述 | 前置条件 | 操作步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| TC-012 | 领奖时断网 | 任务已完成 | 点击领奖后断网 | 显示loading，超时提示重试 |
| TC-013 | 背包满领奖 | 背包满，任务已完成 | 点击领奖 | 奖励发邮件，提示玩家 |
| TC-014 | 非法任务ID | - | 发送不存在的taskId | 服务器返回27001错误 |
| TC-015 | 重复领奖 | 已领奖 | 再次发送领奖请求 | 返回27004错误，状态不变 |
| TC-016 | 未完成领奖 | 任务进行中 | 发送领奖请求 | 返回27003错误 |

---

## 10. 新增配置表需求

### 10.1 需要确认的新增配置表

由于TaskGuide中引用的JumpViewId在CurrencyJump表中存在缺失，需确认以下配置：

| JumpViewId | 跳转目标 | 建议CurrencyJump.Id | 需确认项 |
|-------------|----------|---------------------|----------|
| 223 | 装备升级界面 | 36 | GameFuncType值 |
| 241 | 诸神冥殿抽奖界面 | 41 | GameFuncType值 |
| 258 | 遗物升级界面 | 42 | GameFuncType值 |
| 312 | 金币关界面 | 43 | GameFuncType值 |

**待确认字段**：
- CurrencyJump表新增记录的具体字段值
- GameFuncType枚举中是否需要新增对应类型
- JumpType（跳转类型）的取值

### 10.2 新增配置表草稿（如需新建）

如果CurrencyJump表不支持扩展，建议新建专用跳转表：

**TaskGuideJump.txt（任务引导专用跳转）**

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Id | Int | 是 | 跳转ID |
| JumpName | String | 是 | 跳转名称 |
| JumpType | Int | 是 | 跳转类型 |
| TargetView | String | 是 | 目标界面标识 |
| Params | String | 否 | 跳转参数 |

---

## 11. 文档变更记录

| 版本 | 日期 | 修改内容 | 修改原因 |
|------|------|----------|----------|
| v2.0 | 2026-04-14 | 完善接口字段定义，新增枚举范围说明，补全UI规格，新增测试用例，补录配置表需求 | 主策要求完善接口级设计 |
| v1.0 | 2026-04-14 | 初版文档，完成基础功能设计和程序接口 | 新建 |

---

**文档结束**
