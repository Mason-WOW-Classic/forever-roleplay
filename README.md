# ForeverRP v0.5 — Personal Preview

ForeverRP is a WoW RP draft rewriter with a Windows clipboard companion and a satirical **Real DonaldTrump** persona. **Normal mode is the default; Expressive mode is enabled only by manually checking a checkbox.** Copy a marked draft to trigger a rewrite, paste and review the result, then send it yourself. The addon uses ordinary UI APIs for optional scene context and does not send chat automatically. **Forever client integration is not yet verified because no test server is currently available.**

For reviewers: [architecture and data flow](docs/ARCHITECTURE.md), [source/package verification](docs/RELEASE-VERIFICATION.md), [acceptance checklist](docs/ACCEPTANCE.md). MIT license; copyright Mason-WOW-Classic. This project has no Blizzard approval or compliance certification.

The current UI uses Chinese labels. English descriptions below include the original labels where needed. Most supporting evaluation reports are also in Chinese.

## Try it without the game

1. Double-click **Start.cmd**. Requires Windows and Python 3.10+ with Tkinter. The launcher also recognizes an existing Codex Python runtime; no pip dependencies are needed to run the companion.
2. A clean installation starts in offline simulation mode and makes no network calls. Under **Model Settings (模型设置)**, choose **Sol Ultrafast** to configure the tested `gpt-6.1-sol / ultrafast / low` preset, with English output by default. Live calls require your own API key.
3. Enter a draft. Check **Expressive Mode (发挥模式)** when you want a joke. Optionally add location, party members and scene details on the **Expressive Context (发挥背景)** tab, then return to the trial tab. The checkbox is off at startup, so every session starts in Normal mode.
4. Click **Prepare Copy (准备复制)**, then press **Ctrl+C** in the selected request box.
5. Wait for the completed status, click the result box, press **Ctrl+V**, and review the text. The companion does not steal focus.

The shortcut buttons provide examples for “kill the healer first,” Maraudon LFM, and auction-house prices. The mode stays selected within the current session until you change it; changing drafts does not switch modes. Switching modes clears the prepared request and pasted preview, so prepare and copy again.

The companion keeps watching the clipboard while minimized. Use **Model Settings → Pause (暂停)** to stop processing, or close the window to exit. Run only one instance. To launch from source:

```powershell
python -m companion.app
```

## Models and credentials

Put a single-line OpenAI API key in `key.txt` in this directory, or set `OPENAI_API_KEY` / `WOW_RP_API_KEY`. Keys are excluded from settings, chat logs and release bundles. Automatic key-file loading is restricted to the exact official endpoint, `https://api.openai.com/v1`.

The **Sol Ultrafast** preset uses `gpt-6.1-sol / ultrafast / low`. The **OpenAI Small Model (OpenAI 小模型)** preset uses `gpt-5.4-mini / default / none`. Ultrafast is an API service tier with separate API usage and charges; it does not use your Codex chat subscription allowance.

In the final v0.3 context evaluation on October 28, 2026, **all 12 live Sol calls passed format, length, mode and basic language checks**, and every response reported the ultrafast tier. Median Expressive latency was **1.68 seconds in English** and **1.63 seconds in Chinese**. Across all 12 calls, the median was **1.68 seconds** and the maximum was **6.48 seconds**. These measurements include network time and the full response, not the entire clipboard workflow, and are not an SLA. See [context features and testing](docs/CONTEXT.md).

See the [style rules](docs/EXPRESSIVE-STYLE.md) for the joke menu and the [initial Sol evaluation](docs/SOL-MANUAL-EVALUATION.md) for earlier results. The historical [Astra comparison](docs/FLAGSHIP-COMPARISON.md) used older prompts and does not establish which model is faster or funnier.

The GPT-6 path uses the Responses API, strict JSON Schema, `store=false`, low reasoning effort and a 1,024-token output limit. The Mini path uses Chat Completions, no reasoning and a 384-token output limit. There are no automatic retries, model switches or tier fallbacks. References: [Sol model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Ultrafast documentation](https://developers.openai.com/api/docs/guides/ultrafast-mode).

Other compatible providers can be configured manually. Base URLs usually end in `/v1`; other providers must support non-streaming Chat Completions with `choices[0].message.content`. For example, a local Ollama endpoint can use `http://localhost:11434/v1`, an already installed model name, and the default tier. This tool does not install or start the model server. Remote endpoints must use HTTPS. Review manually entered session keys and environment variables when changing providers. Output language can be English or **Match Source (跟随原文)**. Non-secret configuration is saved to `settings.json`; the mode checkbox is not saved.

## Expressive context

The desktop **Expressive Context (发挥背景)** tab accepts up to 4,000 UTF-8 bytes describing location, party character names and classes, and the current scene. A fictional Deadmines example is available. Context is optional. Only Expressive mode reads and attaches it; Normal mode excludes it during both request preparation and the model call.

In the game panel, enable Expressive mode and click **Read Background (读取背景)** to capture available zone, subzone, and party name/class information, then edit it as needed. Location and party snapshots require manual refresh. Some clients may return only the instance name; surrounding areas such as Westfall can be added manually. Restricted or unreadable fields are skipped without bypassing protections.

Version 0.5 maintains the **10 most recently selected distinct non-player target names**. Names are read when the player manually changes targets; players and unreadable values are skipped. Selecting the same name again moves it to the front without consuming another slot. Once the list exceeds ten names, the least recently selected name is removed. Main-zone changes, entering or leaving instances, and world reloads clear the list; moving between rooms in the same zone does not. The latest list is added when preparing an Expressive request and omitted in Normal mode. Selecting a target does not call a model. The list stays in memory, uses no GUIDs, combat logs or kill data, and does not select targets automatically. Relevant events and APIs have been checked against the Forever source declarations; actual in-game behavior still needs client testing. See [recent-target context](docs/RECENT-TARGETS.md).

Context is sent to the configured model with the Expressive request you manually copy. It remains session-only and is not written to settings or chat logs. It supplies material for jokes; the original draft determines requirements and intent. A priest is not automatically a healer, a knowledgeable party member does not make the player experienced, and recently selected targets do not establish the current target, hostility, combat, kills or proficiency. They are not necessarily enemies. A draft already announcing a fight may joke about deporting the Defias to Kalimdor; a neutral recruitment message must not acquire an invented battle plan.

## Normal and Expressive modes

Both modes follow the [topic boundaries](docs/TOPIC-BOUNDARIES.md): avoid real-world illegal immigration, race/ethnicity, religion, sexual orientation, abortion, MAGA and other supporter-style slogans. “Deport” and “build a wall” are allowed only as game metaphors. China, Russia and Mexico may feature in country/government, trade and infrastructure jokes, without targeting people, ethnic groups or party members' identities. Game classes, fictional races and abilities can still be described normally. A local check rejects explicit prohibited markers before clipboard replacement. If the original meaning depends on an excluded topic, the request fails and the original text is preserved for revision; it is not silently changed to a different meaning.

| Player selection | Rules |
|---|---|
| Normal (default) | Concise translation and RP tone. Allows “folks,” “tremendous,” capitalization and mild confidence, without political jokes or self-deprecation. Maximum 140 UTF-8 bytes. |
| Expressive (checked) | Allows exaggeration, confidence, arrogance and one short contextual joke. If no joke fits, say it directly. Maximum 255 UTF-8 bytes. |

The tool no longer switches modes automatically based on LFM, combat or other content. Both modes preserve counts, class requirements, locations, times, routes, negation, experience and uncertainty. They must not invent entry requirements, fees, leadership duties, skill promises or claims that the player is incompetent. “TREMENDOUS group” is fine; “I know every boss and will carry you” requires that claim in the original draft. The joke menu includes Biden / Harris / Democratic Party blame-shifting, Epstein mystery and island references, Trump coin price movements, towers and city infrastructure, walls, Fake News, golf and bureaucracy. Use at most one joke, without forcing satire into every sentence or turning the message into a political speech.

Examples from the initial live manual-mode evaluation are below. The source descriptions are translated into English here; the original evaluation used Chinese drafts. For examples with the later joke menu, see the style document linked above.

| Original meaning / selection | Model response |
|---|---|
| Need two more for Maraudon: one tank, one healer / Normal | Maraudon! Need two more: one tank, one healer, folks. |
| Same draft / Expressive | Maraudon! Need 2 more: 1 TANK, 1 HEALER. Let's get this group together, folks! |
| This auction-house potion is far too expensive / Expressive | That AH potion is WAY too expensive, folks. What is this, Trump coin at launch? |
| I've never run Maraudon; looking for a group willing to take a newcomer / Expressive | Never run Maraudon before, folks. Looking for a group willing to take a newcomer! |

Both modes return one physical line of text and never split it into multiple messages. Visual wrapping depends on chat-box width and font, so a two-line display limit cannot be guaranteed. The byte budgets still need verification in the released client.

Local validation rejects a mismatched mode, excessive length, line breaks, empty results, commands, game escape markup, and obvious changes to explicit Arabic numerals. Invalid output is rejected rather than truncated. Full meaning, Chinese number words and translation accuracy still require player review.

## When the live client is available

**Version 0.5 retains the WOWRP/3 context protocol.** Recent-target collection needs the updated addon; update the companion too so it uses the passive scene-context rules. The new companion still accepts WOWRP/2 without context. WOWRP/1 lacks an explicit manual mode and is rejected with instructions to prepare a new request. Companions from v0.2 or earlier cannot handle the newer context requests.

Copy the entire `addon/ForeverRP` folder into the actual Forever client's `Interface/AddOns/` directory, producing `Interface/AddOns/ForeverRP/ForeverRP_Forever.toc`. The current TOC uses the beta interface version `16001` and `_Forever` suffix; verify these against the released client.

1. Start the companion outside the game and configure the model.
2. In game, run `/rp` or `/foreverrp` to open the draft panel.
3. Enter the original message and optionally enable **Expressive Mode (发挥模式)**. You can click **Read Background (读取背景)** and edit the snapshot. Preparing the request refreshes the recent non-player target list. Press **Ctrl+C** in the prepared request box.
4. When processing finishes, press **Ctrl+V** in the addon's result box and review the text.
5. Select a channel, click **Put in Chat Box — Do Not Send (放入聊天框（不发送）)**, review it in the native chat box, and **press Enter yourself**.

Changing mode or Expressive context invalidates the old prepared request locally, but the addon cannot tell the companion to revoke an already copied request. Prepare and copy a new request: the new clipboard copy invalidates the older call. Do not paste an old result again. If filling the chat box is restricted by the client, select the channel and paste manually in the native chat box. Use the native chat box directly for custom channels and whispers. Enter in the addon's edit boxes does not send chat.

Text beginning with WOWRP/3 is a request, not a message to send to a game channel. Its format is a persona marker followed by JSON. This example uses English source and context:

```text
WOWRP/3
Real DonaldTrump
{"mode":"expressive","source":"Getting ready to deal with these guys","context":"Location: The Deadmines, Westfall\nEnemies: Defias"}
```

Normal requests use `mode: normal` and an empty context. Each request carries its own mode and context; the companion does not overwrite them with the contents of another panel.

## Failure handling and verification

The companion checks the Windows clipboard sequence number every 100 ms and processes only new copies with the request marker. It uses no keyboard hook. Copying anything else invalidates an old result. Before replacing the clipboard, it compares both the sequence number and exact original request while holding the clipboard lock. Pausing, changing configuration, and switching modes in the desktop trial also invalidate pending results. Resuming does not replay old clipboard contents.

Timeouts, refusals, truncated responses and output-validation failures leave the clipboard unchanged, preserving the original request. Recent results stay in memory; if a Windows clipboard write fails, the recent-result box allows manual copying. After the window closes, an already issued HTTP request may still wait for its timeout, but cannot write back.

Run `python -m unittest discover -s tests -v` to check the protocol, fake HTTP transport, mode propagation, concurrent-result invalidation, pausing and final compare-and-replace behavior. Local HTTP tests require connections to `127.0.0.1`. The full 72-test suite includes 20 Lua simulations, which need the optional developer-only Lupa runtime; see [verification instructions](docs/RELEASE-VERIFICATION.md).

Copy, model-call and paste behavior has been tested on the Windows desktop. See the [evaluation report](docs/SOL-MANUAL-EVALUATION.md) for manual-mode testing. Companion tests do not establish game-client compatibility: Forever loading, IME behavior, combat-time behavior, channel insertion and byte limits still need testing when the game is available. See the [acceptance checklist](docs/ACCEPTANCE.md).

## Policy boundaries

The tool does not read or modify game memory, inject code, intercept network traffic, simulate gameplay inputs or send chat automatically. The addon provides a draft and can fill the native chat edit box after an explicit player click. Using the system clipboard does not constitute special permission from Blizzard; this tool has no written Blizzard approval.

- [Blizzard UI Add-On Development Policy](https://us.forums.blizzard.com/en/wow/t/ui-add-on-development-policy/24534)
- [Blizzard EULA](https://www.blizzard.com/en-us/legal/simple/bfbbb648-bcc6-4b78-a5c7-e2fe20c135df/blizzard-end-user-license-agreement)
- [Forever edit-box API source mirror](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SimpleEditBoxAPIDocumentation.lua)
- [Forever chat-box API source mirror](https://raw.githubusercontent.com/Gethe/wow-ui-source/forever/Interface/AddOns/Blizzard_ChatFrameBase/Shared/ChatFrameUtil.lua)
