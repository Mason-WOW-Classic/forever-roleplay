local _, RP = ...

-- Passive scene hints from the player's explicit target changes. No combat log,
-- GUIDs, automatic targeting, saved variables or external transmission.
RP.TARGET_CONTEXT_PREFIX = "最近选中过的非玩家目标（仅作场景背景）："
local legacyKillPrefix = "近期击杀的非玩家目标（本人/队伍，仅作场景背景）："
local names, zone, tracker, enabled = {}, nil, nil, false
local status = "目标背景采集尚未初始化"

local function readable(fn, ...)
    if type(fn) ~= "function" then return nil end
    local ok, value = pcall(fn, ...)
    if not ok then return nil end
    if type(issecretvalue) == "function" then
        local checked, secret = pcall(issecretvalue, value)
        if not checked or secret ~= false then return nil end
    end
    return value
end

local function zoneName()
    for _, fn in ipairs({GetRealZoneText or false, GetZoneText or false}) do
        local name = readable(fn)
        if type(name) == "string" and name ~= "" then return name end
    end
end

function RP.RefreshTargetZone(force)
    local current = zoneName()
    if force or (current and zone and current ~= zone) or (not current and zone) then
        names = {}
        zone = current
        if RP.OnTargetHistoryReset then RP.OnTargetHistoryReset() end
    elseif current then
        zone = current
    end
    return current ~= nil
end

function RP.GetRecentTargets()
    RP.RefreshTargetZone(false)
    local copy = {}
    for i, name in ipairs(names) do copy[i] = name end
    return copy
end

function RP.RecentTargetContext()
    local current = RP.GetRecentTargets()
    if #current > 0 then return RP.TARGET_CONTEXT_PREFIX .. table.concat(current, "；") end
    return ""
end

function RP.RemoveTargetContext(text)
    local lines = {}
    for line in (text:gsub("\r\n", "\n") .. "\n"):gmatch("(.-)\n") do
        if line:sub(1, #RP.TARGET_CONTEXT_PREFIX) ~= RP.TARGET_CONTEXT_PREFIX
            and line:sub(1, #legacyKillPrefix) ~= legacyKillPrefix then
            lines[#lines + 1] = line
        end
    end
    return table.concat(lines, "\n")
end

function RP.MergeRecentTargetContext(text)
    local manual = RP.Trim(RP.RemoveTargetContext(text))
    local recent = RP.RecentTargetContext()
    if recent == "" then return manual end
    return recent .. (manual ~= "" and ("\n" .. manual) or "")
end

function RP.TargetTrackingStatus() return status end

local function configure()
    enabled = false
    if type(UnitExists) ~= "function" or type(UnitIsPlayer) ~= "function" or type(UnitName) ~= "function" then
        status = "目标背景采集不可用：目标接口缺失，可手动填写"
        return
    end
    local ok, registered = pcall(tracker.RegisterEvent, tracker, "PLAYER_TARGET_CHANGED")
    if not ok or registered == false then
        status = "目标背景采集不可用：无法注册目标变化事件，可手动填写"
        return
    end
    enabled = true
    status = "监听目标变化，最多保留 10 个不同的非玩家名字"
end

local function readTarget()
    if not enabled or not RP.RefreshTargetZone(false) then return end
    if readable(UnitExists, "target") ~= true then return end
    local player = readable(UnitIsPlayer, "target")
    if player ~= false then
        if player == nil then status = "目标身份不可读，已跳过；原列表保留" end
        return
    end
    local name = readable(UnitName, "target")
    if type(name) ~= "string" or #name > 200 or name:find("[%z\1-\31\127|]") then
        status = "目标名字不可读，已跳过；原列表保留"
        return
    end
    name = RP.Trim(name)
    if name == "" then return end
    for i = #names, 1, -1 do
        if names[i] == name then table.remove(names, i) end
    end
    table.insert(names, 1, name)
    if #names > 10 then table.remove(names) end
    status = "已更新最近选中的非玩家目标，最多 10 个不同名字"
end

function RP.HandleTargetHistoryEvent(event)
    if event == "PLAYER_LOGIN" then
        configure()
        RP.RefreshTargetZone(true)
    elseif event == "PLAYER_ENTERING_WORLD" or event == "ZONE_CHANGED_NEW_AREA" then
        RP.RefreshTargetZone(true)
    elseif event == "ZONE_CHANGED" or event == "ZONE_CHANGED_INDOORS" then
        RP.RefreshTargetZone(false)
    elseif event == "PLAYER_TARGET_CHANGED" then
        readTarget()
    end
end

function RP.StartTargetTracking()
    if tracker then return end
    tracker = CreateFrame("Frame")
    for _, event in ipairs({"PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "ZONE_CHANGED_NEW_AREA",
                           "ZONE_CHANGED", "ZONE_CHANGED_INDOORS"}) do
        pcall(tracker.RegisterEvent, tracker, event)
    end
    tracker:SetScript("OnEvent", function(_, event)
        local ok = pcall(RP.HandleTargetHistoryEvent, event)
        if not ok then status = "目标背景暂时不可读，未采集受限数据" end
    end)
    configure()
    RP.RefreshTargetZone(false)
end
