local _, RP = ...
local frame = CreateFrame("Frame", "ForeverRPFrame", UIParent, "BasicFrameTemplateWithInset")
frame:SetSize(620, 665)
frame:SetPoint("CENTER")
frame:SetMovable(true)
frame:EnableMouse(true)
frame:RegisterForDrag("LeftButton")
frame:SetScript("OnDragStart", frame.StartMoving)
frame:SetScript("OnDragStop", frame.StopMovingOrSizing)
frame:SetClampedToScreen(true)
frame:SetFrameStrata("DIALOG")
frame.TitleText:SetText("ForeverRP — Real DonaldTrump")
frame:Hide()
table.insert(UISpecialFrames, "ForeverRPFrame")

local function label(text, y)
    local fs = frame:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    fs:SetPoint("TOPLEFT", 20, y)
    fs:SetWidth(580)
    fs:SetJustifyH("LEFT")
    fs:SetText(text)
    return fs
end

local function edit(y, height)
    local box = CreateFrame("EditBox", nil, frame, "InputBoxTemplate")
    box:SetPoint("TOPLEFT", 25, y)
    box:SetSize(565, height)
    box:SetMultiLine(true)
    box:SetAutoFocus(false)
    box:SetFontObject(ChatFontNormal)
    box:SetMaxLetters(0)
    box:SetTextInsets(5, 5, 6, 6)
    box:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
    -- Enter never sends: it only clears this draft box's focus.
    box:SetScript("OnEnterPressed", function(self) self:ClearFocus() end)
    return box
end

local function button(text, x, y, width, callback)
    local b = CreateFrame("Button", nil, frame, "UIPanelButtonTemplate")
    b:SetPoint("TOPLEFT", x, y)
    b:SetSize(width, 26)
    b:SetText(text)
    b:SetScript("OnClick", callback)
    return b
end

label("1. 输入原句（不发送）", -42)
local source = edit(-66, 58)
label("背景（仅发挥发送；准备时更新最近目标，可补充地点 / 队友）", -174)
local context = edit(-198, 80)
label("2. 准备后按 Ctrl+C；后台只处理带标记的请求", -302)
local request = edit(-326, 80)
label("3. 听到助手提示后，在下面 Ctrl+V；检查内容", -426)
local result = edit(-450, 64)
local status = label("背景按点击时读取；正常模式不附带。", -596)
status:SetTextColor(0.45, 0.85, 1)

local preparedSource
local preparedMode
local preparedContext
local capturedContext
local expressive = CreateFrame("CheckButton", nil, frame, "UICheckButtonTemplate")
expressive:SetPoint("TOPLEFT", 165, -132)
expressive:SetChecked(false)
local modeLabel = expressive:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
modeLabel:SetPoint("LEFT", expressive, "RIGHT", 3, 0)
modeLabel:SetText("发挥模式（可加梗）")
expressive:SetScript("OnClick", function()
    preparedSource = nil
    request:SetText("")
    result:SetText("")
    status:SetText("模式已切换，请重新准备并 Ctrl+C；不要粘贴旧结果。")
end)
button("准备复制", 20, -132, 130, function()
    if expressive:GetChecked() then
        RP.RefreshTargetZone(false)
        local previous = context:GetText()
        local merged = RP.MergeRecentTargetContext(previous)
        if previous == capturedContext then capturedContext = merged end
        context:SetText(merged)
    end
    local wire, err = RP.Request(source:GetText(), expressive:GetChecked(), context:GetText())
    if not wire then status:SetText(err); return end
    preparedSource = RP.Trim(source:GetText())
    preparedMode = expressive:GetChecked() and true or false
    preparedContext = preparedMode and RP.Trim(context:GetText()) or ""
    result:SetText("")
    request:SetText(wire)
    source:ClearFocus()
    result:ClearFocus()
    context:ClearFocus()
    request:SetFocus()
    request:HighlightText()
    local notice = preparedMode and (" " .. RP.TargetTrackingStatus()) or ""
    status:SetText((preparedMode and "发挥" or "正常") .. "请求已选中。请 Ctrl+C；不要把带 WOWRP/3 的请求发到频道。" .. notice)
end)
button("读取背景", 435, -132, 165, function()
    if not expressive:GetChecked() then
        status:SetText("请先勾选发挥；正常模式不读取或发送背景。")
        return
    end
    local snapshot, err = RP.CaptureContext()
    if not snapshot then status:SetText(err); return end
    preparedSource = nil
    request:SetText("")
    result:SetText("")
    context:SetText(snapshot)
    capturedContext = snapshot
    status:SetText("已填入可读的背景。" .. RP.TargetTrackingStatus())
end)
RP.OnTargetHistoryReset = function()
    preparedSource = nil
    request:SetText("")
    result:SetText("")
    local current = context:GetText()
    context:SetText(current == capturedContext and "" or RP.RemoveTargetContext(current))
    capturedContext = nil
    status:SetText("主区域已切换，最近目标已清空。请重新读取背景、准备并 Ctrl+C。")
end
RP.StartTargetTracking()
context:SetScript("OnTextChanged", function()
    if preparedMode then
        preparedSource = nil
        request:SetText("")
        result:SetText("")
    end
end)

-- Channel is explicit. No inference from current group/last whisper target.
local channels = { {"说", "/s "}, {"队伍", "/p "}, {"团队", "/raid "},
                   {"公会", "/g "}, {"战场/副本", "/i "} }
local channelIndex = 1
local channelButton
channelButton = button("频道：说", 20, -532, 140, function()
    channelIndex = channelIndex % #channels + 1
    channelButton:SetText("频道：" .. channels[channelIndex][1])
end)
button("放入聊天框（不发送）", 175, -532, 220, function()
    if not preparedSource or RP.Trim(source:GetText()) ~= preparedSource
        or preparedMode ~= (expressive:GetChecked() and true or false)
        or (preparedMode and RP.Trim(context:GetText()) ~= preparedContext) then
        status:SetText("原句、模式或背景已变化，请重新准备、复制并等待新结果。")
        return
    end
    local text, err = RP.CheckResult(result:GetText())
    if not text then status:SetText(err); return end
    local openChat = ChatFrameUtil and ChatFrameUtil.OpenChat or ChatFrame_OpenChat
    if not openChat then
        status:SetText("当前客户端聊天接口不可用。请关闭面板，在原生聊天框手动 Ctrl+V。")
        return
    end
    source:ClearFocus()
    request:ClearFocus()
    result:ClearFocus()
    context:ClearFocus()
    local ok = pcall(openChat, channels[channelIndex][2] .. text)
    if ok then
        frame:Hide()
    else
        status:SetText("当前客户端阻止了填入操作。请在原生聊天框手动粘贴。")
    end
end)
label("频道按钮可切换。原生聊天框里核对内容和频道，再按回车发送。", -572)

SLASH_FOREVERRP1 = "/rp"
SLASH_FOREVERRP2 = "/foreverrp"
SlashCmdList.FOREVERRP = function()
    if frame:IsShown() then
        frame:Hide()
    else
        frame:Show()
        source:SetFocus()
    end
end
