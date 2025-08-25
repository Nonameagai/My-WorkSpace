-- Minimal stubs to run inside Lua and intercept behaviors
local M = {}

-- Collect output when loadstring is called
local captured = {}
function loadstring(s)
	-- Save last loadstring chunk to file and return a dummy function
	local f = io.open("/workspace/last_loadstring.lua", "w")
	if f then f:write(s or ""); f:close() end
	return function() end
end

-- Stub game with HttpGet capturing
local game = {}
function game:HttpGet(url)
	local f = io.open("/workspace/httpget_url.txt", "w")
	if f then f:write(url or ""); f:close() end
	return "" -- return empty string to avoid executing fetched content
end
_G.game = game

-- Provide bit32 if needed
if not bit32 then
	bit32 = require('bit32') or {}
end

-- Execute the obfuscated script in this environment
local f = assert(io.open("/workspace/underground war", "r"))
local src = f:read("*a"); f:close()
local chunk, err = load(src, "=underground_obf")
if not chunk then
	io.stderr:write("load error: ", tostring(err), "\n")
	os.exit(1)
end
local ok, err2 = pcall(chunk)
if not ok then
	io.stderr:write("runtime error: ", tostring(err2), "\n")
end

return M

