> 历史记录：本文件针对 v0.1 自动模式与旧提示词。当前 v0.2 为手动模式、默认 Sol Ultrafast，见 [最新报告](SOL-MANUAL-EVALUATION.md)。下方输出和耗时保留作为当时记录。

# 旗舰极速模型对照 — 2026-10-28

目标：比较更强模型是否能改善 Trump 讽刺，而不是仅增加 TREMENDOUS 等口头禅。使用现有 key.txt，只发送固定的合成 WoW 草稿，不涉及真实聊天。

## 配置与结果

按 [当前模型指南](https://developers.openai.com/api/docs/guides/latest-model)，选择最高能力的 `gpt-6-astra`；按 [Ultrafast 文档](https://developers.openai.com/api/docs/guides/ultrafast-mode) 配置 `service_tier: ultrafast`。推理使用该模型支持的最低档 `low`，不是不支持的 `none`。

为使用 Ultrafast，新增 OpenAI Responses HTTP 接口；小模型继续用 Chat Completions。两者使用相同的提示词、JSON 结构、原文、输出语言和本地校验。旗舰每次最多 1024 输出 token（含推理），小模型最多 384。所有旗舰结果实际返回的服务档位均为 `ultrafast`，没有把默认处理伪装成极速。

| 同提示词英文对照 | GPT-5.4 Mini / default | GPT-6 Astra / ultrafast |
|---|---:|---:|
| 选定场景 | 8 | 8 |
| 格式、长度、数字校验通过 | 8 | 8 |
| 模式符合预期 | 8 | 8 |
| 中位完整响应时间 | 1.374 秒 | 1.586 秒 |
| 最慢响应 | 1.506 秒 | 2.390 秒 |

另测 Astra 中文 4 条，全部通过模式、长度和基础语言检查；中位 1.579 秒，最慢 1.769 秒。这 4 条没有同时跑同提示词的小模型中文对照，不能当作严格的中文模型对照实验。

测试使用 HTTP、并发 2，未固定缓存状态，模型顺序也未随机化，因此不是严谨的性能基准。Ultrafast 是该旗舰的最快服务档位，不表示它一定比 Mini 快；本次实际更慢约 0.21 秒。幽默质量由人工看输出判断，不能用校验通过率代表幽默合格率。

## 实际输出

| 场景 | 小模型 | Astra Ultrafast |
|---|---|---|
| 拍卖行药水太贵 | That AH potion price is climbing faster than my Trump coin, folks. Tremendous markup, absolutely terrible deal. | That AH potion is WAY too expensive, folks. Rising faster than my Trump coin! Unlike my promises, though, the potion actually delivers. |
| 盗贼跑得快 | That rogue is moving FAST, folks. Almost as fast as I disappear when the bill shows up. | That rogue runs FAST, folks! I promised a wall to stop him. TREMENDOUS announcement, still no wall. |
| 地精过路费贵 | This goblin toll is RIDICULOUS, folks. I’d call it a tremendous deal, but only if I were the one pocketing it. | That goblin's toll is outrageous, folks. I promised the BEST roads, then spent the whole budget gold-plating the tollbooth. |

中文原始返回（未人工润色）：

- 拍卖行：`拍卖行这瓶药也太贵了，伙计们，涨得比我的特朗普币还猛！不过药水至少真有用，不像我，只会保证效果惊人。`
- 暴风城：`暴风城的训练师真难找，伙计们！我承诺修最棒的路标，结果全写着「特朗普大厦」，连我自己都迷路了。`
- 盗贼：`这个盗贼跑得真快，伙计们！我宣布这是我的指挥成果——虽然我还没找到疾跑键。`
- 简短：`先杀奶，就这么干！`

我的判断：Astra 这一轮更善于把价格/技能/导航等具体游戏情境与空头承诺、金装饰、抢功劳等笑点结合，后半句更常形成反讽。小模型也能生成不错的单句，尤其给出明确 Trump 币示例后；提升并非每条都明显。例子仍可能复述、重复或生硬，不保证每次都有好梗。

用户提供的 Trump 币涨价比较被作为讽刺性夸张加入提示词，不是实际行情陈述，也不查询或编造行情价格。

## 实施

本机设置已切换到 `gpt-6-astra / ultrafast / English`。模型设置新增“旗舰 Ultrafast”与“OpenAI 小模型”两个预设及服务档位下拉框，方便比较或切回。正式游戏仍不可测试。

Ultrafast 费用高于 Standard，参见 [官方价格表](https://developers.openai.com/api/docs/pricing?latest-pricing=ultrafast)。这次只做小规模测试，无自动重试或自动降级。

原始数据：[Mini 8 条](openai-live-mini-compare.json)、[Astra 8 条](openai-live-astra-compare.json)、[Astra 中文 4 条](openai-live-astra-chinese.json)、[最初 Astra 完整 15 条](openai-live-astra-ultrafast-probe.json)。

测试脚本首轮的 --cases 筛选未接到真正的任务列表，原定 3 条实际派发 15 条；全部完成并保存了结果，没有把它记为 3 条。已修复为实际按选定场景发送，并新增不联网的请求数回归测试，后续 8/8/4 条实际数量均吻合。
