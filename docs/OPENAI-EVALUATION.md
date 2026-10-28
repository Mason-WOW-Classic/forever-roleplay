> 历史记录：本文件针对 v0.1 自动模式与旧提示词。当前 v0.2 为手动模式、默认 Sol Ultrafast，见 [最新报告](SOL-MANUAL-EVALUATION.md)。下方输出和耗时保留作为当时记录。

# OpenAI 真实模型评估 — 2026-10-28

这是先前的小模型评估；后续已加入并实测 GPT-6 Astra Ultrafast，本机当前选择旗舰，最新结果见 [旗舰对照](FLAGSHIP-COMPARISON.md)。

使用用户提供的 key.txt 调用 OpenAI 官方 API。请求模型为 `gpt-5.4-mini`，返回版本为 `gpt-5.4-mini-2026-03-17`；无推理模式、严格 JSON Schema、单次输出上限 384 token。只发送固定的合成 WoW 草稿，不发送真实聊天历史。

## 结论

英文可以开始个人试用：即时指令简洁，招募信息基本完整，发挥模式能够生成自嘲、抢功劳和 TRUMP 品牌讽刺。幽默强度不稳定，部分句子仍是普通自夸/吐槽而非鲜明的 Trump 讽刺。

中文能保留核心信息并使用中文，但仍有完整英文句子混入，以及简短指令额外夸张、发挥模式只吹嘘而没有反讽的情况。“包含中文”检查只能挡住全英文，不能证明语言自然或讽刺合格。当前默认继续使用 English。

## 最后一次完整评估（当前提示词）

| 指标 | English | 跟随原文：中文 |
|---|---:|---:|
| 合成请求数 | 15 | 8 |
| 本地格式/长度/数字校验通过 | 15 | 8 |
| 模式与预设期望一致 | 15 | 8 |
| 基础语言检查通过 | 15 | 8 |
| 中位响应时间 | 1.194 秒 | 1.200 秒 |
| 最慢响应 | 1.655 秒 | 1.372 秒 |

延迟为本次实际调用的客户端测量，包含网络；测试并发为 2。不是服务 SLA。上述自动指标不包含幽默、完整语义或事实保真的评分。

## 实际返回样例（未人工改写）

| 原文 | 模式 | 实际输出 |
|---|---|---|
| 不要打羊 | 简短 | Do NOT hit the sheep, folks! |
| 现在立刻回防铁匠铺，别追人，守住旗子，奶妈留后面 | 简短 | Back to the blacksmith NOW! No chase, hold the flag, healers stay back, folks! |
| 找两个人打玛拉顿，一坦一奶 | 发挥 | Maraudon! Need 1 TANK, 1 HEALER. TREMENDOUS plan—so simple even I can claim credit for it. |
| 暴风城真的难找训练师 | 发挥 | Stormwind trainers are impossible to find, folks. Truly TREMENDOUS city planning—I’d rebuild it with TRUMP signs and still get lost. |
| 拍卖行这瓶药也太贵了 | 发挥 | That Auction House potion is OUTRAGEOUS. Slap TRUMP on the bottle and suddenly it’s a luxury item, folks. |
| LFM 玛拉顿，缺1坦1奶，22:00开，只打紫门，不要满级 | 发挥 | LFM Maraudon, need 1 TANK, 1 HEALER, 22:00 start, ONLY purple side, no max-level players. TREMENDOUS plan—I'll take credit, somebody else can tank. |
| 暴风城真的难找训练师（中文） | 发挥 | 暴风城找训练师？太难了，folks。连我都能把路标做成金的，结果还是找不到，TREMENDOUS管理失误。 |

一些不够好的实际结果也必须保留：

- 地精过路费：`That goblin toll is RIDICULOUSLY expensive. Total deal, folks — I always get taxed by the BEST little crooks.` 主要在骂地精，讽刺 Trump 的指向弱。
- 中文 LFM：`玛拉顿来2人，一坦一奶。I only recruit the BEST, folks, then I take all the credit.` 信息准确但混入整句英文，不算自然的中文输出。
- 中文先杀奶：`先杀奶！我来指挥，当然是TREMENDOUS地准！` 仍有不必要的扩写。
- 中文复杂 LFM：保留了人数/时间/门和满级限制，但追加了“我这指挥，TREMENDOUS…BEST people 来”，没有明显自我拆台，容易像支持者式吹捧。

这是小样本人工审阅意见，不是自动幽默评分。部分场景与提示词示例相同，存在复述；地精、空尸体、公会致谢等场景用于观察泛化。

## 测试中实际发现并修复

1. 英文 `That rogue can run so fast.` 被本地 `run` 关键词强制判成简短。改为只对句首命令式 Run 施加限制，保留模型对闲聊的判断。
2. 复杂 LFM 被数字检查拒绝。提示词要求保留显式数字、22:00 格式，不额外加入等级数字或 LF2M 等缩写。最后一轮该案例中英文均通过；不代表所有数字场景都已覆盖。
3. 部分输出只有 Trump 口气，没有讽刺。增加自夸后自我拆台、品牌溢价和抢功劳等指导，同时禁止 LFM 中凭空加入收费或服务要求。
4. 跟随原文模式最初全部输出英文。现明确发送 Chinese 语言要求并拒绝全英文回复，但中英混杂仍需后续改善。

首轮的基准脚本还遇到 Windows 控制台编码错误：5 个请求已派发，仅保留 1 个结果。脚本已改为 UTF-8；后续报告均完整保存。不能把缺失结果计为通过或用于精确费用计算。

## 可复查数据与复现

- [第一轮 15 条](openai-live-first-pass.json)
- [第一次调优后 30 条重复测试](openai-live-tuned.json)
- [上一版英文结果](openai-live-final-english.json)
- [上一版中文问题记录](openai-live-final-chinese.json)
- [当前提示词英文 15 条](openai-live-verified-english.json)
- [当前提示词中文 8 条](openai-live-verified-chinese.json)

每份报告包含原文、原始输出、模式、耗时、token 使用和提示词 SHA-256；不含密钥。`ok` 仅表示程序校验接受，不能理解成语义或幽默都合格。

显式复现命令：`python tools/live_eval.py --live --round my-eval`。会真实调用 API 并计费，默认 15 个固定草稿，每轮最多 40 次请求，无自动重试；不传 `--live` 不会调用。不要在输出目录放置密钥。

官方接口依据：[GPT-5.4 Mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)、[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat)。

## 真实 API 桌面流程

重启最新版助手，使用保存的 OpenAI 地址、模型、English 和真实模式；Key 自动从 key.txt 读取，输入框中未展示密钥。

- LFM：准备请求 → Ctrl+C → OpenAI 返回发挥模式、135 UTF-8 字节 → Ctrl+V 粘贴成功。实际结果：`Maraudon! Need 2 people, 1 tank, 1 healer. I’ll provide the VERY BEST leadership while everybody else does the actual winning, folks.`
- 即时指令：准备“先杀奶” → Ctrl+C → OpenAI 返回简短模式、18 字节 → Ctrl+V 粘贴成功。实际结果：`Kill healer first!`

第一次复制时曾出现剪贴板暂时不可用提示，后续自动读取重试成功，未阻止本次调用。没有模拟或发送任何游戏聊天。这两次桌面调用不计入上面的 23 条脚本结果。
