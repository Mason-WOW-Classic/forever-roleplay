"""Lua 5.1 tests for passive non-player target history; no real game or API."""
import unittest
from pathlib import Path

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    LuaRuntime = None

ADDON = Path(__file__).resolve().parent.parent / 'addon' / 'ForeverRP'


@unittest.skipIf(LuaRuntime is None, 'Optional developer dependency: lupa with Lua 5.1')
class RecentTargetTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.rp = self.lua.table()
        self.lua.execute('''
            currentZone = '西部荒野'
            targetExists = true; targetPlayer = false; targetName = '迪菲亚矿工'
            function GetRealZoneText() return currentZone end
            function UnitExists(unit) assert(unit == 'target'); return targetExists end
            function UnitIsPlayer(unit) assert(unit == 'target'); return targetPlayer end
            function UnitName(unit) assert(unit == 'target'); return targetName end
            tracker = {events={}, scripts={}}
            function CreateFrame() return tracker end
            function tracker:RegisterEvent(event) self.events[event] = true end
            function tracker:SetScript(event, fn) self.scripts[event] = fn end
            local forbidden = function() error('Must not access combat logs, GUIDs or targeting actions') end
            UnitGUID = forbidden; TargetUnit = forbidden; ClearTarget = forbidden
            CombatLogGetCurrentEventInfo = forbidden
            C_CombatLog = setmetatable({}, {__index=forbidden})
        ''')
        for name in ('Core.lua', 'RecentTargets.lua', 'Context.lua'):
            self.lua.execute((ADDON/name).read_text(encoding='utf-8'), 'ForeverRP', self.rp)
        self.rp.StartTargetTracking()

    def names(self): return list(self.rp.GetRecentTargets().values())

    def select(self, name='迪菲亚矿工', player=False, exists=True):
        g = self.lua.globals()
        g.targetName, g.targetPlayer, g.targetExists = name, player, exists
        g.tracker.scripts.OnEvent(g.tracker, 'PLAYER_TARGET_CHANGED')

    def test_records_only_explicit_target_change_and_returns_copy(self):
        self.assertEqual(self.names(), [])
        self.select()
        self.assertEqual(self.names(), ['迪菲亚矿工'])
        copy = self.rp.GetRecentTargets()
        copy[1] = 'modified'
        self.assertEqual(self.names(), ['迪菲亚矿工'])
        self.assertTrue(self.lua.globals().tracker.events.PLAYER_TARGET_CHANGED)
        self.assertIsNone(self.lua.globals().tracker.events.COMBAT_LOG_EVENT_UNFILTERED)

    def test_duplicate_name_moves_to_front_without_consuming_capacity(self):
        self.select('迪菲亚矿工'); self.select('迪菲亚监工'); self.select('迪菲亚矿工')
        self.assertEqual(self.names(), ['迪菲亚矿工', '迪菲亚监工'])
        self.select('迪菲亚矿工')
        self.assertEqual(len(self.names()), 2)

    def test_ten_distinct_names_evict_least_recent(self):
        for i in range(12): self.select(f'NPC{i}')
        self.assertEqual(self.names(), [f'NPC{i}' for i in range(11, 1, -1)])
        self.select('NPC2'); self.select('new')
        self.assertEqual(self.names()[:2], ['new', 'NPC2'])
        self.assertNotIn('NPC3', self.names())

    def test_players_missing_targets_and_unknown_identity_are_skipped(self):
        self.select()
        self.select('Player1', player=True)
        self.select('no target', exists=False)
        self.select('unknown', player=None)
        self.assertEqual(self.names(), ['迪菲亚矿工'])

    def test_restricted_values_and_api_errors_are_skipped(self):
        self.lua.execute("function issecretvalue(v) return v == 'SECRET' end")
        self.select('SECRET')
        self.select('unknown', player='SECRET')
        self.lua.execute("function UnitName() error('restricted') end")
        self.select()
        self.assertEqual(self.names(), [])

    def test_names_reject_controls_markup_oversize_and_keep_chinese(self):
        for name in ('bad|Kname', 'bad\nname', '', '  ', '中'*67): self.select(name)
        self.assertEqual(self.names(), [])
        self.select('  龙侠  ')
        self.assertEqual(self.names(), ['龙侠'])

    def test_friendly_nonplayers_are_scene_hints_too(self):
        self.lua.execute("function UnitCanAttack() error('Must not infer hostility') end")
        self.select('商人'); self.select('训练师'); self.select('宠物')
        self.assertEqual(self.names(), ['宠物', '训练师', '商人'])

    def test_main_zone_and_world_loading_clear_history(self):
        self.select()
        self.lua.globals().currentZone = '艾尔文森林'
        self.rp.HandleTargetHistoryEvent('ZONE_CHANGED')
        self.assertEqual(self.names(), [])
        self.select()
        self.rp.HandleTargetHistoryEvent('PLAYER_ENTERING_WORLD')
        self.assertEqual(self.names(), [])

    def test_room_change_keeps_history_new_area_clears(self):
        self.select()
        self.lua.execute("function GetSubZoneText() return '月溪镇' end")
        self.rp.HandleTargetHistoryEvent('ZONE_CHANGED_INDOORS')
        self.assertEqual(self.names(), ['迪菲亚矿工'])
        self.rp.HandleTargetHistoryEvent('ZONE_CHANGED_NEW_AREA')
        self.assertEqual(self.names(), [])

    def test_snapshot_catches_missed_zone_event(self):
        self.select()
        self.lua.globals().currentZone = '死亡矿井'
        self.assertNotIn('迪菲亚矿工', self.rp.RecentTargetContext())
        self.assertEqual(self.names(), [])

    def test_merge_removes_old_managed_target_and_kill_lines(self):
        self.select(); self.select('迪菲亚监工'); self.select()
        old = '手动场景\n' + self.rp.TARGET_CONTEXT_PREFIX + '旧目标\n近期击杀的非玩家目标（本人/队伍，仅作场景背景）：旧怪物'
        merged = self.rp.MergeRecentTargetContext(old)
        self.assertIn('手动场景', merged)
        self.assertEqual(merged.count('迪菲亚矿工'), 1)
        self.assertNotIn('旧目标', merged)
        self.assertNotIn('旧怪物', merged)
        self.assertNotIn('击杀', merged)

    def test_missing_api_disables_safely(self):
        self.lua.execute('UnitIsPlayer = nil')
        self.rp.HandleTargetHistoryEvent('PLAYER_LOGIN')
        self.select()
        self.assertEqual(self.names(), [])
        self.assertIn('不可用', self.rp.TargetTrackingStatus())

    def test_registration_rejection_disables_safely(self):
        self.lua.execute('''
            function tracker:RegisterEvent(event)
                if event == 'PLAYER_TARGET_CHANGED' then error('Not allowed') end
            end
        ''')
        self.rp.HandleTargetHistoryEvent('PLAYER_LOGIN')
        self.select()
        self.assertEqual(self.names(), [])
        self.assertIn('无法注册', self.rp.TargetTrackingStatus())


if __name__ == '__main__': unittest.main()
