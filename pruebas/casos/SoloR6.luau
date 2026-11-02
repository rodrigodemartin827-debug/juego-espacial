--[[
	Garantía de que el proyecto es solo R6: falla si en `src/` o en las herramientas de Blender aparece el nombre de
	alguna pieza de R15 (UpperTorso, RightHand, LeftLowerLeg...) o se pide un rig R15.

	Los nombres de las piezas de R6 son: HumanoidRootPart, Torso, Head, "Right Arm", "Left Arm", "Right Leg" y
	"Left Leg". Si esta prueba falla, cambia la referencia por la pieza R6 equivalente (el brazo entero en lugar de
	UpperArm/LowerArm/Hand, el torso entero en lugar de UpperTorso/LowerTorso...).
]]

local fs = require("@lune/fs")

-- Las 15 piezas de un personaje R15 que no existen en R6 (HumanoidRootPart y Head sí existen en R6).
local PIEZAS_R15 = {
	"UpperTorso",
	"LowerTorso",
	"RightUpperArm",
	"RightLowerArm",
	"RightHand",
	"LeftUpperArm",
	"LeftLowerArm",
	"LeftHand",
	"RightUpperLeg",
	"RightLowerLeg",
	"RightFoot",
	"LeftUpperLeg",
	"LeftLowerLeg",
	"LeftFoot",
}

-- Otras formas de pedir R15: el enumerado de Roblox y el nombre del rig como texto.
local OTRAS_PISTAS = {
	{ patron = "HumanoidRigType%.R15", descripcion = "Enum.HumanoidRigType.R15" },
	{ patron = '"R15"', descripcion = 'el texto "R15"' },
	{ patron = "'R15'", descripcion = "el texto 'R15'" },
	{ patron = "Rig Builder.-R15", descripcion = "instrucciones de Rig Builder en R15" },
}

-- Carpetas y extensiones que se revisan.
local REVISAR = {
	{ carpeta = "src", extension = ".luau" },
	{ carpeta = "animaciones/herramientas", extension = ".py" },
}

local function archivos(carpeta: string, extension: string, resultado: { string }): { string }
	for _, nombre in fs.readDir(carpeta) do
		local ruta = `{carpeta}/{nombre}`
		if fs.isDir(ruta) then
			archivos(ruta, extension, resultado)
		elseif string.sub(nombre, -#extension) == extension then
			table.insert(resultado, ruta)
		end
	end
	return resultado
end

-- Devuelve las coincidencias de `patron` en el texto, con su número de línea.
local function buscar(texto: string, patron: string): { number }
	local lineas = {}
	local numero = 0
	for linea in string.gmatch(texto .. "\n", "([^\n]*)\n") do
		numero += 1
		if string.find(linea, patron) then
			table.insert(lineas, numero)
		end
	end
	return lineas
end

local function infracciones(): { string }
	local encontradas = {}
	for _, regla in REVISAR do
		for _, ruta in archivos(regla.carpeta, regla.extension, {}) do
			local texto = fs.readFile(ruta)
			for _, pieza in PIEZAS_R15 do
				-- Palabra completa: el límite (%f) evita confundir nombres que solo contienen el texto.
				for _, linea in buscar(texto, `%f[%w_]{pieza}%f[^%w_]`) do
					table.insert(encontradas, `{ruta}:{linea}: pieza de R15 '{pieza}'`)
				end
			end
			for _, pista in OTRAS_PISTAS do
				for _, linea in buscar(texto, pista.patron) do
					table.insert(encontradas, `{ruta}:{linea}: {pista.descripcion}`)
				end
			end
		end
	end
	return encontradas
end

return function(Marco)
	Marco.grupo("Solo R6: ninguna pieza de R15 en el código", function()
		Marco.prueba("ni en src/ ni en las herramientas de Blender aparece una pieza de R15", function()
			local encontradas = infracciones()
			Marco.igual(
				#encontradas,
				0,
				`hay referencias a R15 (usa las piezas R6: Torso, Head, "Right Arm", "Left Arm", "Right Leg", "Left Leg"):\n{table.concat(
					encontradas,
					"\n"
				)}`
			)
		end)

		Marco.prueba("las rutas revisadas existen y tienen archivos (la prueba no puede quedarse vacía)", function()
			for _, regla in REVISAR do
				local lista = archivos(regla.carpeta, regla.extension, {})
				Marco.verdadero(#lista >= 5, `{regla.carpeta}: solo {#lista} archivo(s) {regla.extension}`)
			end
		end)

		Marco.prueba("el detector reconoce de verdad las piezas de R15 (contra falsos negativos)", function()
			for _, pieza in PIEZAS_R15 do
				local texto = `local mano = personaje:FindFirstChild("{pieza}")`
				Marco.igual(#buscar(texto, `%f[%w_]{pieza}%f[^%w_]`), 1, `no detecta '{pieza}'`)
			end
			-- Las piezas de R6 y los nombres parecidos no cuentan.
			for _, valido in { "Torso", "Right Arm", "Left Leg", "Head", "HumanoidRootPart", "UpperTorsoVFX_" } do
				local sospechoso = false
				for _, pieza in PIEZAS_R15 do
					if #buscar(valido, `%f[%w_]{pieza}%f[^%w_]`) > 0 then
						sospechoso = true
					end
				end
				Marco.falso(sospechoso, `'{valido}' no es una pieza de R15`)
			end
		end)
	end)
end
