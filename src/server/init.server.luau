--!strict
--[[
	Punto de entrada del servidor.

	Rojo sincroniza esta carpeta como `ServerScriptService.Server`: este archivo (init.server.luau)
	se convierte en un Script y el resto de módulos de la carpeta quedan como hijos suyos.

	Aquí solo se arrancan los servicios; la lógica vive en los módulos de `Servicios/`.
]]

print("[Servidor] Juego espacial iniciado")
