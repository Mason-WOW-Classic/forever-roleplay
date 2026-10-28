# Sol Ultrafast 与手动模式评估 — 2026-10-28

> 本文件记录手动模式初轮。随后新增梗菜单并放宽夸张、自信、傲慢的语气，最新规则与 18 次实测见 [发挥风格规则及测试](EXPRESSIVE-STYLE.md)。本文件的输出和耗时保留为原轮次记录。

结论：本机默认改为 **gpt-6.1-sol / ultrafast / low / English**。新策略默认正常，玩家手动勾选发挥；不再自动分类。没有合适的梗就直接改写，不要求逐句自嘲。禁止凭空增加玩家领导力、技术、熟练度、带飞承诺、无能或抢功描述。

## 真实 API 结果

沿用 Astra 对照的 8 个场景：先杀奶、玛拉顿 LFM、盗贼、暴风城、拍卖行、带人数/时间/路线/否定的 LFM、地精过路费、公会致谢。英文正常各一次、发挥各两次；另选四个中文发挥场景，并增加两种模式的新手招募，共 30 次，无重试。接口实际返回的 model 全为 gpt-6.1-sol，service_tier 全为 ultrafast。

| 分组 | 调用 / 接受 | 中位耗时 | 最大耗时 |
|---|---:|---:|---:|
| 英文正常，8 场景 | 8 / 8 | 1.607 秒 | 2.516 秒 |
| 英文发挥，8 场景 × 2 | 16 / 16 | 1.452 秒 | 2.086 秒 |
| 跟随原文中文发挥，4 场景 | 4 / 4 | 1.456 秒 | 1.889 秒 |
| 新手招募，正常 / 发挥 | 2 / 2 | 1.757 秒 | 2.161 秒 |
| 合计 | 30 / 30 | 1.485 秒 | 2.516 秒 |

最快 1.231 秒。耗时为客户端发起 HTTP 到完整解析结束，包括网络；8 场景测试并发 2，新手测试各单次，不包含用户等待、100ms 剪贴板轮询和粘贴时间。模式、字节预算、格式和基础语言检查全部通过；这些不是语义或幽默的自动评分。

历史 Astra 同场景旧提示词中位 1.586 秒；本轮重写了策略且时间不同，不能据此断言 Sol 更快或更强。本轮没有消耗 Astra 调用。Sol 的实际速度与内容足以作为当前默认。

## 人工审阅

正常模式的 8 个输出都直接表达原意，没有时事梗和自嘲。LFM 只写需要两人、一坦一奶；带条件的 LFM 保留 1、1、22:00、紫门与不要满级。

发挥的 LFM、致谢、新手招募没有硬塞笑话，也没有把玩家写成指挥、高手、无能或只抢功的人。新手原文“我没打过玛拉顿，想找愿意带新人的队伍”分别返回：

- 正常：Never run Maraudon before, folks. Looking for a group willing to take a first-timer.
- 发挥：Never run Maraudon before, folks. Looking for a group willing to take a newcomer!

较贴合的发挥输出：

| 场景 | 实际返回 |
|---|---|
| 拍卖行价格 | That AH potion is WAY too expensive, folks. What is this, Trump coin at launch? |
| 暴风城导航 | Finding a trainer in Stormwind is a nightmare, folks. We need DIRECTIONS, not another Trump Tower sign. |
| 盗贼速度 | That rogue moves FAST, folks. Faster than Trump changes the subject when Epstein comes up. |
| 中文拍卖行 | 各位，拍卖行这瓶药也太贵了，贵得离谱！这是药水，还是特朗普币啊？ |
| 中文暴风城 | 暴风城的训练师真难找，各位！要的是指路牌，不是特朗普大厦的招牌！ |

局限：英文盗贼与 LFM 基本复述提示词示例，不能作为泛化能力证明。地精“路该铺金子”和中文盗贼“开超速罚单”比较普通，后者也没有明显 Trump 讽刺。并非每条都好笑，但符合“没合适的梗可以不抖包袱”。本轮未出现支持者式背书；小样本不能保证以后不会出错。Biden 只作为可选素材保留，没有强行加入或专门测试。

## Windows 桌面验证

在真实 Python/Tkinter 窗口、真实 Windows 剪贴板完成两次额外 Sol 调用，不计入上表的 30 次，也没有为 UI 操作记录精确延迟：

1. 重启显示 gpt-6.1-sol / ultrafast，发挥复选框默认未勾选。
2. 默认 LFM → 准备 → Ctrl+C → 显示正常完成、53 字节 → Ctrl+V 得到 `Maraudon! Need two more: one tank, one healer, folks.`。
3. 勾选发挥，确认请求框与粘贴预览清空，状态要求重新准备。
4. 快捷准备拍卖行，协议第三行为 expressive → Ctrl+C → 显示发挥完成、82 字节 → Ctrl+V 得到 `That AH potion is WAY too expensive, folks. What is this, Trump coin at peak hype?`。

新版请求框扩为 4 行以容纳新增模式行；重启确认发挥未勾选，完整请求可见。41 个单元测试通过，涵盖手动模式传递、禁止模型换模式、切换时废弃旧调用、HTTP 与剪贴板流程。发布包完整性和密钥排除扫描通过。

后台没有发送任何游戏聊天。Forever 的 Lua UI、复选框位置、游戏复制/粘贴与频道填入仍未在客户端验证。

## 复现与原始记录

仅合成草稿，未记录用户聊天或密钥。工具不会在普通测试中调用真实 API。以下命令需要显式 --live，会使用单独的 API 用量；不自动重试。

```powershell
python tools/live_eval.py --live --model gpt-6.1-sol --tier ultrafast --mode normal --cases kill_healer,lfm,rogue,stormwind,auction,lfm_conditions,toll,guild --round sol-manual-normal
python tools/live_eval.py --live --model gpt-6.1-sol --tier ultrafast --mode expressive --repeats 2 --cases kill_healer,lfm,rogue,stormwind,auction,lfm_conditions,toll,guild --round sol-manual-expressive
python tools/live_eval.py --live --model gpt-6.1-sol --tier ultrafast --mode expressive --language 跟随原文 --cases kill_healer,auction,stormwind,rogue --round sol-manual-chinese
```

记录：[正常](openai-live-sol-manual-normal.json)、[发挥](openai-live-sol-manual-expressive.json)、[中文](openai-live-sol-manual-chinese.json)、[新手正常](openai-live-sol-novice-normal.json)、[新手发挥](openai-live-sol-novice-expressive.json)。每份含提示词 SHA256、输入、输出、实际模型 / 档位、耗时与 usage。

v0.2 协议为 WOWRP/2 + 人格 + normal/expressive + 原文。模型 Schema 限定为所选模式，客户端再校验一次；不能由 LLM 偷换模式。旧插件须与助手一起更新。
