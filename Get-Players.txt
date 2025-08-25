local G = {}
local Players = game:GetService("Players")
local plr = Players.LocalPlayer

function G:getPlayers(txt)
    -- Remove trailing spaces
    txt = txt:gsub("%s+$", "") -- This line removes trailing spaces from the string

    local tl = txt:lower()
    local found = {}
    local allPlayers = Players:GetPlayers()  -- Retrieve all players once

    if tl == "me" then
        table.insert(found, plr)
    elseif tl == "random" then
        if #allPlayers > 0 then
            table.insert(found, allPlayers[math.random(1, #allPlayers)])
        end
    elseif tl == "others" then
        for _, v in pairs(allPlayers) do
            if v ~= plr then
                table.insert(found, v)
            end
        end
    elseif tl == "all" then
        found = allPlayers  -- Directly use the retrieved list
    elseif tl == "enemies" then
        for _, v in pairs(allPlayers) do
            if v ~= plr and v.Team and v.Team ~= plr.Team then
                table.insert(found, v)
            end
        end
    elseif tl == "team" then
        for _, v in pairs(allPlayers) do
            if v.Team and v.Team == plr.Team then
                table.insert(found, v)
            end
        end
    else
        for _, v in pairs(allPlayers) do
            if v.Name:lower():match(tl) or v.DisplayName:lower():match(tl) then
                table.insert(found, v)
            end
        end
    end

    return found
end

return G
