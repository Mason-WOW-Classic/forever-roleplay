local _, RP = ...

-- Only public UI APIs, called on the player's click. Restricted values are omitted.
local function readable(fn, ...)
    if type(fn) ~= "function" then return nil end
    local ok, value = pcall(fn, ...)
    if not ok or (issecretvalue and issecretvalue(value)) then return nil end
    return value
end

local function text(fn, ...)
    local value = readable(fn, ...)
    if type(value) == "string" and value ~= "" then return value end
end

function RP.CaptureContext()
    local ok, snapshot = pcall(function()
        local lines, seen = {}, {}
        local function place(value)
            if value and not seen[value] then
                lines[#lines + 1] = "地点：" .. value
                seen[value] = true
            end
        end
        place(text(GetRealZoneText))
        place(text(GetZoneText))
        place(text(GetSubZoneText))
        local recent = RP.RecentTargetContext()
        if recent ~= "" then lines[#lines + 1] = recent end
        local raid = readable(UnitExists, "raid1") == true
        local prefix, limit = raid and "raid" or "party", raid and 40 or 4
        local partial = false
        for i = 1, limit do
            local unit = prefix .. i
            if readable(UnitIsUnit, unit, "player") == false then
                local name = text(UnitName, unit)
                if name then
                    local class = text(UnitClass, unit) or "职业未知"
                    local line = "队友：" .. name .. " - " .. class
                    if #table.concat(lines, "\n") + #line < 3850 then
                        lines[#lines + 1] = line
                    else
                        partial = true
                    end
                end
            end
        end
        if partial then lines[#lines + 1] = "备注：仅列出部分队友，背景长度已达预算。" end
        return table.concat(lines, "\n")
    end)
    if not ok then return nil, "当前客户端无法读取背景，请手动填写。" end
    return snapshot
end
