# ForeverRP v0.5 — 个人自用预览版

ForeverRP is a WoW RP draft rewriter with a Windows clipboard companion. The player explicitly copies a marked draft, reviews the rewritten text, pastes it, and sends it manually. The addon uses ordinary UI APIs for optional scene context. It does not send chat automatically. **Forever client integration is not yet verified.**

For reviewers: [architecture and data flow](docs/ARCHITECTURE.md), [source/package verification](docs/RELEASE-VERIFICATION.md), [acceptance checklist](docs/ACCEPTANCE.md). MIT license; copyright Mason-WOW-Classic. This project has no Blizzard approval or compliance certification.

Real DonaldTrump 讽刺戏仿人格的 WoW 聊天改写工具。**默认正常模式，手动勾选复选框才进入发挥模式**。复制触发后台改写，粘贴后由玩家检查、手动发送。当前没有 Forever 测试服，游戏插件尚未在客户端验证。

## 无游戏也能试

1. 双击 **Start.cmd**。需要带 Tkinter 的 Python 3.10+；本机启动器也支持 Codex 已有的 Python，无需 pip 安装依赖。
2. 干净安装默认使用离线模拟，不联网。在“模型设置”点 **Sol Ultrafast** 可配置已测试的 gpt-6.1-sol / ultrafast / low，默认输出 English；真实调用需用户自己的 API Key。
3. 输入原句；需要抖包袱时勾选“发挥模式”。可在“发挥背景”页填写地点、队友和情境，再切回试用页。默认不勾选，每次启动恢复正常模式。
4. 点“准备复制” → 在已选中的请求框按 **Ctrl+C**。
5. 等状态显示完成 → 点击结果框 **Ctrl+V**，检查内容。助手不主动抢焦点。

可用“先杀奶 / 玛拉顿 LFM / 拍卖行”快捷按钮准备示例。勾选状态保持到本次窗口内再次切换；换草稿不会自动切模式。切换模式会清空已准备请求和粘贴预览，必须重新准备、复制。

窗口最小化后仍监听；“模型设置 → 暂停”停止处理，关闭窗口退出。只开一个助手实例。开发启动：`python -m companion.app`。

## 模型与密钥

把一行 OpenAI API Key 放入本目录 `key.txt`，或者设置 `OPENAI_API_KEY` / `WOW_RP_API_KEY`。密钥不写入设置、聊天日志或发布包。Key 文件仅对精确的官方地址 `https://api.openai.com/v1` 自动读取。

“Sol Ultrafast”预设为 `gpt-6.1-sol / ultrafast / low`；“OpenAI 小模型”预设为 `gpt-5.4-mini / default / none`。Ultrafast 是 API 服务档位，有单独 API 用量和费用，不使用 Codex 聊天订阅额度。

2026-10-28 v0.3 支持发挥背景，最终一轮 **12 次 Sol 真实调用全部通过格式、长度、模式与基础语言检查**，实际档位全部返回 ultrafast。英文发挥中位 **1.68 秒**，中文发挥中位 **1.63 秒**；全部 12 条中位 **1.68 秒**，最大 **6.48 秒**。包含网络和完整响应，不代表 SLA 或剪贴板全流程耗时。见 [背景功能及测试](docs/CONTEXT.md)。

梗菜单见 [风格规则](docs/EXPRESSIVE-STYLE.md)，此前验证见 [Sol 初轮评估](docs/SOL-MANUAL-EVALUATION.md)。历史 [Astra 对照](docs/FLAGSHIP-COMPARISON.md) 使用旧提示词，不能据此断言模型速度或幽默水平优劣。

GPT-6 使用 Responses API、严格 JSON Schema、store=false、low 推理、1024 输出 token 上限；Mini 使用 Chat Completions、none 推理、384 上限。不自动重试、切模型或降档。依据：[Sol 模型文档](https://developers.openai.com/api/docs/models/gpt-6.1-sol)、[Ultrafast 文档](https://developers.openai.com/api/docs/guides/ultrafast-mode)。

也可手动配置其他兼容接口：基础地址通常以 `/v1` 结束，其他提供方需支持非流式 Chat Completions 和 `choices[0].message.content`。本地 Ollama 例如 `http://localhost:11434/v1`，填写已安装的模型名、档位选 default；工具不安装或启动服务。远程必须 HTTPS。切换提供方时注意手动填写的会话 Key 或环境变量。输出可选 English 或“跟随原文”。普通配置保存到 `settings.json`，复选框状态不保存。

## 发挥背景

桌面“发挥背景”页可输入最多 4000 UTF-8 字节的地点、队友名字和职业、当前情境，也可填入虚构的死亡矿井示例。留空也能改写。只有发挥模式会读取和附带；正常模式在准备请求和调用模型时均排除背景。

游戏面板勾选发挥后，可点“读取背景”填入当时的可读区域、子区域和队友名字/职业，随后手动补充。地点与队伍快照需手动刷新。某些客户端只能返回副本名，外部的西部荒野等区域可手动补充。受限或不可读字段跳过，不绕过保护。

v0.5 改为维护**最近选中过的 10 个不同非玩家目标名字**：玩家手动选中目标时读取，跳过玩家及不可读值；同名目标再次选中会移到最前，不占新位置，超过上限移出最久未选中的名字。主区域切换、进出副本或重新载入世界时清空，同一区域内换房间不清空。准备发挥请求时加入最新名单，正常模式不附带。选择目标不会调用模型，记录仅在内存中，不读取 GUID、战斗日志或击杀数据，也不自动选择目标。相关事件和接口已在 Forever 源码声明中核对，实际游戏行为仍待正式客户端验证。详见 [最近目标背景](docs/RECENT-TARGETS.md)。

背景会随手动复制的发挥请求发送给配置的模型，只在本次会话保留，不写设置或聊天日志。背景提供选梗素材，原句决定需求和意图：牧师不自动算治疗，队友会副本不等于玩家会副本，最近选中过的目标不证明当前目标、敌意、战斗、击杀或熟练度，也不代表它们都是敌人。可以在已有战斗宣言里把驱逐迪菲亚到卡利姆多当笑话，不会从中性招募自动编出战斗计划。

## 正常 / 发挥

两种模式都遵守 [话题边界](docs/TOPIC-BOUNDARIES.md)：避开现实非法移民、种族/族群、宗教、性取向、堕胎，以及 MAGA 和其他支持者式口号。deport、build a wall 只作游戏比喻；中国、俄罗斯、墨西哥可用于国家/政府、贸易和基建玩笑，不针对人民、族群或队友身份。游戏职业、虚构种族和技能仍正常表达。明确禁词在本地再次检查，触发时不写回剪贴板；原意本身离不开禁用话题时保留原文、要求调整，不偷偷改成其他意思。

| 玩家选择 | 规则 |
|---|---|
| 正常（默认） | 简洁翻译与 RP 语气，允许 folks、tremendous、大写和轻微自信；不插入政治梗或自嘲。最多 140 UTF-8 字节。 |
| 发挥（勾选） | 允许夸张、自信、傲慢和一个贴合语境的短梗；没有合适的梗就直接表达。最多 255 UTF-8 字节。 |

不再按 LFM、战斗等语义自动切换。两种模式都保留人数、职业需求、地点、时间、路线、否定、经验和不确定性；不凭空增加门槛、收费、指挥职责、实力承诺或玩家无能的描述。“TREMENDOUS group”可以；“我熟悉所有首领、我来带飞”只有原文明确说过才可以。梗菜单覆盖 Biden / Harris / 民主党式甩锅、Epstein 的神秘和岛屿梗、Trump 币涨跌、大厦与城市基建，以及墙、Fake News、高尔夫和官僚主义。一次最多选一个，不要求每句话嘲讽，不展开政治演说。

手动模式初轮真实英文输出举例（最新梗菜单样例见上方规则文档）：

| 原句 / 选择 | 模型返回 |
|---|---|
| 找两个人打玛拉顿，一坦一奶 / 正常 | Maraudon! Need two more: one tank, one healer, folks. |
| 同上 / 发挥 | Maraudon! Need 2 more: 1 TANK, 1 HEALER. Let's get this group together, folks! |
| 拍卖行这瓶药也太贵了 / 发挥 | That AH potion is WAY too expensive, folks. What is this, Trump coin at launch? |
| 我没打过玛拉顿，想找愿意带新人的队伍 / 发挥 | Never run Maraudon before, folks. Looking for a group willing to take a newcomer! |

两种模式都只返回一条物理文本行，不自动拆条。视觉换行随聊天框宽度、字体变化，不能保证最多两行。字节预算尚待正式客户端验证。

本地拒绝模式不符、超长、换行、空结果、命令 / 游戏转义标记，以及明显改变原有阿拉伯数字的输出；不通过截断补救。完整语义、中文数字和翻译仍需玩家检查。

## 正式服上线后

**v0.5 保留 WOWRP/3 背景协议。** 最近目标队列需要新版插件，建议同时更新助手以使用被动场景背景规则。新版助手仍接受 WOWRP/2（没有背景）；WOWRP/1 缺少手动模式，会明确报错要求重新准备。v0.2 及更早助手无法处理新版背景请求。

将 `addon/ForeverRP` 整个文件夹复制到实际 Forever 客户端的 `Interface/AddOns/`，形成 `Interface/AddOns/ForeverRP/ForeverRP_Forever.toc`。当前 TOC 为 beta 的 16001 与 _Forever 后缀，上线后必须核对。

1. 游戏外启动助手，配置模型。
2. 游戏中 `/rp` 或 `/foreverrp` 打开草稿面板。
3. 输入原句，按需勾选“发挥模式”；可点“读取背景”并编辑 → 准备复制时更新最近选中的非玩家目标名单 → **Ctrl+C**。
4. 完成后在插件结果框 **Ctrl+V**，检查内容。
5. 选频道 → “放入聊天框（不发送）” → 在原生聊天框核对后，**自己按回车**。

模式切换或发挥背景修改会使旧请求失效，但游戏插件不能通知后台撤回已经复制的请求；请重新准备并 Ctrl+C，新的复制才会使旧调用失效。不要重新粘贴旧结果。填入操作受客户端限制时，在原生聊天框手动选频道、粘贴。自定义频道和密语也直接用原生聊天框。插件编辑框回车不会发送。

带 WOWRP/3 的是请求，不能发到游戏频道。格式为人格标记加 JSON：

```text
WOWRP/3
Real DonaldTrump
{"mode":"expressive","source":"准备收拾这些家伙","context":"地点：死亡矿井，西部荒野\n敌人：迪菲亚"}
```

正常请求 mode 为 normal，context 为空；每条请求携带自己的模式和背景，后台不使用另一个面板的内容覆盖它。

## 失败处理与验证

每 100ms 检查 Windows 剪贴板序号，仅处理带标记的新复制，无键盘钩子。再次复制任何内容使旧结果失效；写回时在剪贴板锁内同时核对序号和原请求。暂停、配置变更及桌面试用的模式切换也会使待处理结果失效；恢复不重放旧剪贴板。

接口超时、拒绝、截断或输出校验失败时不写回，原句保留。最近结果只在内存中；Windows 写回失败时可从最近结果框手动复制。关闭窗口后，已发出的 HTTP 请求可能仍等待超时，不再写回。

运行 `python -m unittest discover -s tests -v` 检查协议、HTTP 模拟、模式传递、并发失效、暂停和最终比较后写回。本机 HTTP 测试需允许 127.0.0.1 连接。

Windows 桌面已实际验证复制、调用、粘贴；本轮复选框测试见 [评估报告](docs/SOL-MANUAL-EVALUATION.md)。后台通过不等于游戏通过：Forever 加载、输入法、战斗中行为、频道填入、字节上限仍待游戏可用后验收。见 [验收清单](docs/ACCEPTANCE.md)。

## 规则边界

工具不读取或修改游戏内存、不注入、不拦截网络、不模拟游戏输入、不自动发言。插件提供草稿和玩家点击后填入原生聊天框的操作。系统剪贴板方案不等于获得暴雪专项许可，目前没有暴雪对本工具的书面批准。

- [暴雪插件开发政策](https://us.forums.blizzard.com/en/wow/t/ui-add-on-development-policy/24534)
- [暴雪 EULA](https://www.blizzard.com/en-us/legal/simple/bfbbb648-bcc6-4b78-a5c7-e2fe20c135df/blizzard-end-user-license-agreement)
- [Forever 编辑框接口源码镜像](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleEditBoxAPIDocumentation.lua)
- [Forever 聊天框接口源码镜像](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/ChatFrameUtil.lua)
