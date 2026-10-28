"""Optional Lua 5.1 checks with mocked WoW APIs; never starts a game client."""
import unittest
from pathlib import Path

from companion.core import DraftRequest, parse_request

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    LuaRuntime = None

ADDON = Path(__file__).resolve().parent.parent / 'addon' / 'ForeverRP'


@unittest.skipIf(LuaRuntime is None, 'Optional developer dependency: lupa with Lua 5.1')
class AddonTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.rp = self.lua.table()
        for name in ('Core.lua', 'RecentTargets.lua', 'Context.lua'):
            self.lua.execute((ADDON / name).read_text(encoding='utf-8'), 'ForeverRP', self.rp)

    def test_lua_to_python_wire_with_quotes_newlines_and_unicode(self):
        source = '开怪，收拾迪菲亚 "hi" \\ 路线'
        context = '地点：死亡矿井\n队友：Player1 - 牧师\nWOWRP/3'
        self.assertEqual(parse_request(self.rp.Request(source, True, context)),
                         DraftRequest(source, 'expressive', context))
        self.assertEqual(parse_request(self.rp.Request(source, False, context)).context, '')

    def test_chinese_utf8_bytes_are_not_control_or_whitespace(self):
        self.assertEqual(self.rp.Trim('  龙侠  '), '龙侠')
        self.assertEqual(self.rp.CheckResult('先杀奶！'), '先杀奶！')
        self.assertEqual(parse_request(self.rp.Request('龙侠', True, '地点：龙侠')).text, '龙侠')
        self.assertIsInstance(self.rp.CheckResult('bad\nline'), tuple)

    def test_party_snapshot_only_contains_available_public_fields(self):
        self.lua.execute('''
            function GetRealZoneText() return '死亡矿井' end
            function GetZoneText() return '死亡矿井' end
            function GetSubZoneText() return '铁甲湾' end
            function UnitExists() return false end
            function UnitIsUnit() return false end
            function UnitName(unit) if unit == 'party1' then return 'Player1' end end
            function UnitClass() return '牧师', 'PRIEST' end
        ''')
        snapshot = self.rp.CaptureContext()
        self.assertEqual(snapshot.count('死亡矿井'), 1)
        self.assertIn('队友：Player1 - 牧师', snapshot)
        self.assertIn('铁甲湾', snapshot)
        self.assertNotIn('治疗', snapshot)

    def test_raid_omits_self_and_restricted_names(self):
        self.lua.execute('''
            function UnitExists(unit) return unit == 'raid1' end
            function UnitIsUnit(unit) return unit == 'raid1' end
            function UnitName(unit)
                if unit == 'raid1' then return 'Self' end
                if unit == 'raid2' then return 'SECRET_NAME' end
                if unit == 'raid3' then return 'Player3' end
            end
            function UnitClass() return '盗贼' end
            function issecretvalue(v) return v == 'SECRET_NAME' end
        ''')
        snapshot = self.rp.CaptureContext()
        self.assertNotIn('Self', snapshot)
        self.assertNotIn('SECRET_NAME', snapshot)
        self.assertIn('Player3 - 盗贼', snapshot)

    def test_unavailable_apis_do_not_invent_values(self):
        self.lua.execute('function GetRealZoneText() error("restricted") end')
        self.assertEqual(self.rp.CaptureContext(), '')

    def test_large_roster_budget_and_partial_notice(self):
        self.lua.execute('''
            function UnitExists() return true end
            function UnitIsUnit() return false end
            function UnitName(unit) return string.rep('名字', 50) .. unit end
            function UnitClass() return '牧师' end
        ''')
        snapshot = self.rp.CaptureContext()
        self.assertLessEqual(len(snapshot.encode('utf-8')), 4000)
        self.assertIn('仅列出部分队友', snapshot)

    def test_ui_context_is_opt_in_and_changes_invalidate_preview(self):
        self.lua.execute('''
            widgets = {}; UIParent = {}; UISpecialFrames = {}; SlashCmdList = {}
            local methods = {}
            function methods:SetScript(event, fn) self.scripts[event] = fn end
            function methods:SetText(value)
                self.text = value
                if self.scripts.OnTextChanged then self.scripts.OnTextChanged(self) end
            end
            function methods:GetText() return self.text or '' end
            function methods:SetChecked(value) self.checked = value end
            function methods:GetChecked() return self.checked end
            function methods:IsShown() return self.shown end
            function methods:Show() self.shown = true end
            function methods:Hide() self.shown = false end
            function methods:SetFocus() focused = self end
            local newWidget
            function methods:CreateFontString() return newWidget('FontString') end
            newWidget = function(kind)
                local widget = {kind=kind, scripts={}}
                setmetatable(widget, {__index=function(_, key)
                    return methods[key] or function() end
                end})
                widgets[#widgets+1] = widget
                return widget
            end
            function CreateFrame(kind)
                local widget = newWidget(kind)
                widget.TitleText = newWidget('FontString')
                return widget
            end
            function SendChatMessage() error('Must never send') end
            ChatFrameUtil = {OpenChat=function(text) openedChat = text end}
            function findButton(text)
                for _, w in ipairs(widgets) do
                    if w.kind == 'Button' and w.text == text then return w end
                end
            end
            function click(button) button.scripts.OnClick(button) end
        ''')
        self.lua.execute((ADDON / 'UI.lua').read_text(encoding='utf-8'), 'ForeverRP', self.rp)
        globals = self.lua.globals()
        widgets = list(globals.widgets.values())
        source, context, request, result = [w for w in widgets if w.kind == 'EditBox']
        checkbox = next(w for w in widgets if w.kind == 'CheckButton')
        reads = []
        self.rp.CaptureContext = lambda: reads.append(True) or '地点：西部荒野'
        globals.click(globals.findButton('读取背景'))
        self.assertEqual(reads, [])
        checkbox.SetChecked(checkbox, True)
        globals.click(checkbox)
        globals.click(globals.findButton('读取背景'))
        self.assertEqual(len(reads), 1)
        source.SetText(source, '缺1奶')
        globals.click(globals.findButton('准备复制'))
        self.assertEqual(parse_request(request.GetText(request)).context, '地点：西部荒野')
        result.SetText(result, 'Need 1 healer!')
        self.assertIsNone(globals.openedChat)
        context.SetText(context, '地点：死亡矿井')
        self.assertEqual(request.GetText(request), '')
        self.assertEqual(result.GetText(result), '')
        globals.click(globals.findButton('放入聊天框（不发送）'))
        self.assertIsNone(globals.openedChat)
        context.SetText(context, '手动情境：等队友\n' + self.rp.TARGET_CONTEXT_PREFIX + '旧目标')
        self.rp.HandleTargetHistoryEvent('ZONE_CHANGED_NEW_AREA')
        self.assertEqual(context.GetText(context), '手动情境：等队友')
        self.lua.execute('''
            function GetRealZoneText() return '西部荒野' end
            function UnitExists(unit) return unit == 'target' end
            function UnitIsPlayer() return false end
            function UnitName() return selectedName end
            selectedName = '迪菲亚矿工'
        ''')
        self.rp.HandleTargetHistoryEvent('PLAYER_LOGIN')
        self.rp.HandleTargetHistoryEvent('PLAYER_TARGET_CHANGED')
        globals.click(globals.findButton('读取背景'))
        self.lua.globals().selectedName = '迪菲亚监工'
        self.rp.HandleTargetHistoryEvent('PLAYER_TARGET_CHANGED')
        globals.click(globals.findButton('准备复制'))
        prepared = parse_request(request.GetText(request))
        self.assertIn('迪菲亚监工；迪菲亚矿工', prepared.context)
        self.assertNotIn('击杀', prepared.context)
        self.rp.HandleTargetHistoryEvent('ZONE_CHANGED_NEW_AREA')
        self.assertEqual(context.GetText(context), '')
        self.assertEqual(request.GetText(request), '')


if __name__ == '__main__': unittest.main()
