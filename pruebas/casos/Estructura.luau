--[[
	Estructura del proyecto: que Rojo (aquí, su simulación) monte las carpetas donde toca y que todos
	los archivos .luau del proyecto sean sintácticamente correctos.
]]

local fs = require("@lune/fs")
local luau = require("@lune/luau")

local Entorno = require("../infraestructura/Entorno")

-- Lista todos los archivos .luau que hay bajo `directorio`.
local function archivosLuau(directorio: string, resultado: { string }): { string }
	for _, nombre in fs.readDir(directorio) do
		local ruta = `{directorio}/{nombre}`
		if fs.isDir(ruta) then
			archivosLuau(ruta, resultado)
		elseif string.sub(nombre, -5) == ".luau" then
			table.insert(resultado, ruta)
		end
	end
	return resultado
end

return function(Marco)
	Marco.grupo("Estructura del proyecto", function()
		Marco.prueba("las carpetas se montan en los servicios que indica default.project.json", function()
			local entorno = Entorno.nuevo()
			local buscar = entorno.servidor.buscar

			Marco.igual(buscar("ReplicatedStorage.Shared").ClassName, "Folder")
			Marco.igual(buscar("ServerScriptService.Server").ClassName, "Script")
			Marco.igual(buscar("StarterPlayer.StarterPlayerScripts.Client").ClassName, "LocalScript")
		end)

		Marco.prueba("los archivos se convierten en ModuleScripts con el nombre del archivo", function()
			local entorno = Entorno.nuevo()
			local buscar = entorno.servidor.buscar

			Marco.igual(buscar("ReplicatedStorage.Shared.Red.Validador").ClassName, "ModuleScript")
			Marco.igual(buscar("ServerScriptService.Server.Servicios.ServicioRed").ClassName, "ModuleScript")
			Marco.igual(buscar("StarterPlayer.StarterPlayerScripts.Client.Servicios.ServicioRed").ClassName, "ModuleScript")
		end)

		Marco.prueba("todos los archivos .luau compilan con el compilador de Luau", function()
			local archivos = {}
			for _, raiz in { "src", "pruebas" } do
				archivosLuau(raiz, archivos)
			end
			Marco.verdadero(#archivos > 0, "no se encontró ningún archivo")

			local errores = {}
			for _, ruta in archivos do
				local ok, err = pcall(luau.compile, fs.readFile(ruta))
				if not ok then
					table.insert(errores, `{ruta}: {string.match(tostring(err), "^[^\n]+")}`)
				end
			end
			Marco.igual(#errores, 0, table.concat(errores, "\n"))
		end)
	end)
end
