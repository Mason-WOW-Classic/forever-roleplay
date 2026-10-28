# 发挥风格规则及测试 — 2026-10-28

> v0.3 新增独立背景；可将一句 Biden 场景铺垫和迪菲亚驱逐比喻组成同一个短包袱。背景优先级、最新测试和使用方法见 [背景功能](CONTEXT.md)。下方 18 次数据为新增背景前的轮次。

生效于 companion/core.py 的系统提示词。仍默认正常模式，手动勾选才发挥；模型仍为 gpt-6.1-sol / ultrafast / low。请求协议和插件 UI 无变化。

## 语气与信息保真

允许夸张、自信、傲慢、愤慨、大写，以及 tremendous、beautiful、disaster、folks、believe me 等口头禅。发挥模式可以更浮夸，正常模式保持简洁但也允许轻微自信和 tremendous。

语气不能增加游戏事实或承诺：“A tremendous group in the making”可以；原文没说过时，不加“我熟悉所有首领”“我来指挥”“我带飞”“保证通关”。不虚构玩家无能、偷懒、抢功，不强制每句自嘲。原文确实说过熟悉副本、可以带路，就保留；原文说没打过，也保留。

每条最多选一个相关梗；菜单可自由扩展，没有轮换或命中配额。中性招募、感谢等没有合适的梗时，只做 RP 改写。保持游戏信息在前，不扩成政治演说。正常模式不插入这些包袱。

## 梗菜单

所有素材服从 [话题边界](TOPIC-BOUNDARIES.md)。不使用非法移民/执法机构、现实种族、宗教、性取向、堕胎或 MAGA 等支持者符号。保留 deport 与墙的虚构游戏比喻；国家笑话只针对国家/政府等，不针对人民或玩家的现实身份。

| 素材 | 适用范围 | 使用细节 |
|---|---|---|
| Joe Biden / Kamala Harris / 民主党 | 对地点、服务、排队、掉落、道路等任何已有不满 | Trump 式夸张甩锅；结合具体不满，不将中性消息改成抱怨。不要求结尾反过来自嘲。 |
| Epstein | 神秘人物、消失的盗贼、秘密地点、私人小岛，包括巨魔小岛 | 岛屿、保密、宾客名单的轻微暗示或成人双关；不露骨，不性化未成年人，不编造具体受害者、名单或现实人物犯罪指控。 |
| Trump 币 | 昂贵、涨价、跌价、市场剧烈波动 | 涨跌方向必须与原文一致；仅仅“贵”不能变成真实涨价。用明显漫画式比喻，不补市场数据。 |
| Trump 大厦 / Trump 集团 | 城市、建筑、路桥、标识、重建、豪华装修 | 品牌、镀金、奢华、巨型招牌；不新增游戏建设项目或收费。 |
| Build a wall | 堵路、城门、据点防守 | 作为比喻，不新增战术命令、目的地或移民话题。 |
| Fake News | 传闻、不可靠地图、矛盾消息 | 夸张怀疑，保留原本的不确定性；不反转已确认信息，不凭空说其他玩家撒谎。 |
| 高尔夫 / 官僚主义 | 干等、绕路、繁琐手续 | 嘲讽拖延或低效，不暗示玩家挂机、偷懒或离队；不写玩家赶去参加政治集会。 |
| 中国 / 俄罗斯 / 墨西哥 | 国家、政府、贸易、价格、基建 | 可以开涮，不嘲讽人民、族群、肤色、口音或队友出身，不加入现实非法移民或执法叙事。 |

## 18 次真实 API 测试

12 条英文发挥、4 条中文发挥、2 条正常对照。全部实际返回 gpt-6.1-sol / ultrafast，全部通过格式、手动模式、长度和基础语言检查，没有自动重试。

| 分组 | 接受 / 调用 | 中位耗时 | 最大耗时 |
|---|---:|---:|---:|
| 英文发挥 | 12 / 12 | 1.769 秒 | 5.736 秒 |
| 中文发挥 | 4 / 4 | 1.808 秒 | 2.358 秒 |
| 英文正常 | 2 / 2 | 1.383 秒 | 1.384 秒 |
| 合计 | 18 / 18 | 1.694 秒 | 5.736 秒 |

耗时包括 HTTP 网络与完整解析，脚本并发 2；不是剪贴板端到端时间或服务 SLA。新增提示词约 1,500 输入 token，本轮多条响应命中缓存。样本与前轮不同，不能把耗时差异归因为提示词长度。

人工审阅：

- LFM 返回 `Maraudon! Need two more: one TANK, one HEALER. A tremendous group in the making, folks!`，保留需求，允许夸张，没有新增领导力或技术承诺。
- 新手返回 `I've never run Maraudon, folks. Looking for a group willing to take a newcomer. That would be TREMENDOUS!`，保留没打过。
- 明确“熟悉玛拉顿、可以带路”的草稿保留两点和 1 坦 1 奶，没有因为防止能力虚构而删掉原有能力。
- 西部荒野：`Westfall is a TOTAL DISASTER, folks. Broken-down, absolutely disgraceful. Looks like Joe Biden was running the place!`
- 中文小岛：`赞达拉巨魔这个小岛看着神神秘秘的，朋友们！这保密派头，简直是艾泼斯坦私人岛屿级别的！`
- 神秘 NPC：`This NPC keeps appearing and disappearing, folks. VERY mysterious. More secrecy than an Epstein island guest list!`
- 下跌材料：`This material's price is CRASHING, folks. Tremendous speed—straight out of the Trump coin playbook!`，没有翻转成涨价。
- 堵路城门用“恰好建在不该建的地方的墙”，没有加入另一个战术指令。
- 商人坐骑传闻保留“不确定”，再接 FAKE NEWS；没有改成确认不卖。
- 正常模式的西部荒野和拍卖行对照都没有插入政治梗。

局限：岛屿英文样本没有选 Epstein，选择了“棕榈树都像保密文件”的轻笑话；桥梁抱怨选 Biden 而非 Trump 大厦。这符合可选菜单，不应为了命中名字而重复生成。Biden 样本与提示词示例相近，不能证明泛化；Harris、民主党、高尔夫等选项本轮没有被模型选中，也没有单独强制测试。全部检查通过不保证所有语义与笑话质量，仍由玩家粘贴后审阅。

原始记录：[英文发挥](openai-live-meme-menu-english.json)、[中文发挥](openai-live-meme-menu-chinese.json)、[正常对照](openai-live-meme-menu-normal.json)。包含输入、输出、模型、实际档位、usage、耗时和提示词 SHA256。仅固定合成草稿，不包含密钥或私人聊天。
