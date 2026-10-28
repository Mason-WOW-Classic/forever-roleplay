# v0.4 最近击杀背景 — 2026-10-28

> 已由 v0.5 的 [最近选中目标](RECENT-TARGETS.md) 替代。旧击杀采集代码和测试已移除；本文只记录当时的设计与接口限制。

实现了最多 10 次可确认的本人/队伍 NPC 击杀队列、区域重置、背景合并和模拟测试。**尚不能确认 Forever 正式客户端可自动采集**，也没有声称在已关闭的 beta 做过实机验证。

## 数据来源的限制

核对的 Forever [公开 CombatLog 声明](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/CombatLogDocumentation.lua) 包含过滤、设置、受限查询和事件，没有声明 GetCurrentEventInfo。另一份 [CombatLogSecure 声明](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/CombatLogSecureDocumentation.lua) 将读取方法置于 SecureOnly 环境。这不能证明运行时绝无遗留全局，但也不能根据旧版 WoW 的经验承诺函数可用。

当前适配器只检测客户端实际提供的普通 CombatLogGetCurrentEventInfo，或公开 C_CombatLog.GetCurrentEventInfo，并尝试注册普通击杀事件。二者都不存在、注册失败、接口报错、返回受限数据或明确处于限制状态时，不采集，并在游戏面板读取背景时显示状态。

不制造旧 API 别名，不调用 C_CombatLogInternal / C_CombatLogSecure，不改变游戏限制或战斗日志设置，不读取进程内存，不解析聊天/受保护日志文字，也不把目标血量归零推测为玩家击杀。正式服若仍没有普通可读接口，这项自动采集将保持不可用，地点/队友快照和手填背景仍可使用。

## 队列口径

- 仅处理可读的 PARTY_KILL 载荷，来源归属本人、队伍或团队；这些归属位与 [Forever 枚举](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/CombatLogConstantsDocumentation.lua) 的 1、2、4 一致。不是看到附近任何目标死亡就记录。
- 目标必须是 Creature 类型的 NPC；玩家、宠物、载具和未知 GUID 不记录。载具类 NPC 也会漏掉，优先避免把玩家操控单位混入。
- 内存最多保留最近 10 次，新的放前面、旧的移出。不同怪物同名仍算不同次；同一 NPC 的重复事件不重复入队。
- 仅临时保留这 10 个 NPC 的 GUID 做去重和类型检查，不保存到磁盘，不发送 GUID。提供给 LLM 的只有按名字去重的场景列表，没有伤害、击杀统计或个人战绩。
- 区域变化、重新载入或退出游戏后不保留历史。击杀本身不联网、不调用模型、不发送消息。

示例背景行（合成示例）：

```text
近期击杀的非玩家目标（本人/队伍，仅作场景背景）：迪菲亚监工；迪菲亚矿工
```

这可帮助模型找到“迪菲亚”语境；不能据此声称玩家单杀、熟悉副本、已经清本或下一步一定会打谁。原文的招募、否定、经验、战术与话题边界仍优先。

## 区域与面板

采用主区域/副本边界：ZONE_CHANGED_NEW_AREA 或 PLAYER_ENTERING_WORLD 直接清空；其他区域事件只在主区域名称变化时清空。因此西部荒野到艾尔文森林、进入副本或重新载入世界会清空，同一副本里换房间不会反复清空。源码的 [区域文本 UI](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_FrameXML/Mainline/ZoneText.lua) 使用相应的区域事件。读取背景或处理新击杀时还会核对主区域，以补漏掉的区域事件。

“读取地点/队友”按钮更名为“读取背景”。地点/队友仍是点击时快照；近期击杀在每次准备发挥请求时重新合并，即使上一次读取后又发生了击杀，也不必为名单单独刷新。正常请求不附带这些数据。队列在插件运行时被动维护，包含正常模式期间发生的可确认 NPC 击杀；正常模式不读取/发送队伍和背景快照。

换区时清空队列、旧自动击杀行、已准备请求和粘贴预览；未编辑的整份自动快照也会清除，手动补充的其他文字保留。需重新读取地点和队伍。游戏插件无法撤回外部助手已经发出的旧请求，仍需重新准备、Ctrl+C，并在粘贴后核对。

## 验证与待办

70 项回归通过，包括 18 项 Lua 5.1 模拟检查。新增检查覆盖容量/顺序、同名与重复事件区别、排除玩家/宠物/载具/路人击杀、受限值与 API 错误、限制查询、接口缺失、注册被拒绝、主区域/副本重置、房间保留、漏事件补核对、去重后的背景以及旧背景失效。

测试还发现 Windows Lua 的通用字符类别可能把 UTF-8 中文字节判成控制或空白字符，已在 NPC 名称检查、结果检查和 Trim 中改为明确的 ASCII 范围，新增中文回归验证。

没有为此重复调用真实 LLM。旧版真实模型报告仍是当时提示词的记录，不是本功能的实机采集证明。产品不需要 Lua 测试库，模拟运行时仅在开发用临时目录中。

正式客户端可用后必须核实：普通 getter 是否存在、事件能否注册和实际触发、载荷位置是否匹配、队伍归属/目标类型是否可读、战斗/副本限制、区域事件时机与游戏面板布局。只有这些实机检查通过，才可称自动击杀背景可用。
