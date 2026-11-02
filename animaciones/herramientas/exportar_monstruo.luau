--[[
	Exporta a JSON las animaciones del monstruo TAL CUAL las ve el juego (Personajes/Datos/AnimacionesMonstruo
	horneadas con Animacion/Horneado), para reproducirlas en Blender (andar_monstruo.py): hoja de contactos y FBX.

	Uso (desde la raíz del repositorio, con Lune):
		lune run animaciones/herramientas/exportar_monstruo.luau ruta/salida.json

	Para cada animación y cada cuadro (a Fps) se guarda la rotación de cada pieza RESPECTO A SU PADRE (matriz 3x3
	por filas, en los ejes de Roblox: X derecha, Y arriba, Z atrás) y la traslación del Torso respecto a la
	HumanoidRootPart (studs). Es exactamente lo que el cliente mete en cada Pose, sin pasar por los C0/C1.
	También se guardan las medidas de los pies (pruebas/infraestructura/Pisada) para escribirlas en la hoja.
]]

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local Entorno = require("../../pruebas/infraestructura/Entorno")
local Pisada = require("../../pruebas/infraestructura/Pisada")

local salida = process.args[1]
assert(salida, "uso: lune run animaciones/herramientas/exportar_monstruo.luau salida.json")

local entorno = Entorno.nuevo()
local function cargar(ruta)
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
end
local Datos = cargar("Personajes.Datos.AnimacionesMonstruo")
local Horneado = cargar("Animacion.Horneado")
local Cinematica = cargar("Animacion.CinematicaR6")

local resultado = {}
for _, estado in { "Reposo", "Andar", "Correr", "Saltar", "Caer" } do
	local definicion = Datos.Definiciones[estado]
	local horneada = Horneado.Hornear(definicion)
	local cuadros = {}
	for _, cuadro in horneada.Cuadros do
		local piezas = {}
		for _, pieza in Cinematica.PIEZAS do
			local pose = cuadro.Poses[pieza]
			local r = Cinematica.RotacionDePose(pieza, pose)
			piezas[pieza] = {
				R = { r[1][1], r[1][2], r[1][3], r[2][1], r[2][2], r[2][3], r[3][1], r[3][2], r[3][3] },
				-- Traslación en los ejes del personaje (derecha, arriba, atrás), como la del C0 de la articulación.
				T = { pose[4], pose[5], -pose[6] },
			}
		end
		table.insert(cuadros, { T = cuadro.T, Piezas = piezas })
	end

	local medidas = nil
	if definicion.VelocidadReferencia then
		local analisis = Pisada.Analizar(Horneado, Cinematica, definicion)
		medidas = {
			VelocidadNatural = analisis.VelocidadNatural,
			Patinaje = analisis.Patinaje,
			Aire = analisis.Aire,
		}
	end

	table.insert(resultado, {
		Estado = estado,
		Nombre = Datos.Nombres[estado],
		Duracion = definicion.Duracion,
		Bucle = horneada.Bucle,
		Fps = definicion.Fps or 30,
		VelocidadReferencia = definicion.VelocidadReferencia,
		Medidas = medidas,
		Cuadros = cuadros,
	})
end

fs.writeFile(salida, serde.encode("json", resultado, true))
print(`[ok] {#resultado} animaciones exportadas a {salida}`)
