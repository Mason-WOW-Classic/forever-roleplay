-- No chat events, networking, clipboard API, timers, saved drafts or send calls.
local _, RP = ...
RP.prefix = "WOWRP/3\nReal DonaldTrump\n"

function RP.Trim(text)
    return (text:gsub("^[ \t\r\n\11\12]+", ""):gsub("[ \t\r\n\11\12]+$", ""))
end

local function jsonString(text)
    return '"' .. text:gsub('[%z\1-\31\\"]', function(c)
        if c == '"' then return '\\"' end
        if c == '\\' then return '\\\\' end
        return string.format('\\u%04x', string.byte(c))
    end) .. '"'
end

function RP.Request(text, expressive, context)
    text = RP.Trim(text:gsub("\r\n", "\n"):gsub("\r", "\n"))
    if text == "" then return nil, "请先输入原句。" end
    if #text > 2000 then return nil, "原句超过 2000 字节，请缩短。" end
    context = expressive and RP.Trim(context or "") or ""
    if #context > 4000 then return nil, "背景超过 4000 字节，请缩短。" end
    return RP.prefix .. '{"mode":' .. jsonString(expressive and "expressive" or "normal")
        .. ',"source":' .. jsonString(text) .. ',"context":' .. jsonString(context) .. '}'
end

function RP.CheckResult(text)
    text = RP.Trim(text)
    if text == "" then return nil, "请先粘贴改写结果。" end
    if text:find("WOWRP/", 1, true) then
        return nil, "这还是请求原文。请等待助手完成后再粘贴。"
    end
    if #text > 255 then return nil, "结果超过 255 字节，请缩短；不会自动截断。" end
    if text:find("[%z\1-\31\127]") or text:find("|", 1, true) or text:match("^[/%.]") then
        return nil, "结果包含换行、控制字符、命令或游戏转义标记，请修改。"
    end
    return text
end
