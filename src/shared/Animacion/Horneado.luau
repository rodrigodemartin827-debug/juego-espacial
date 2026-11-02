--!strict
--[[
	Horneado: convierte una animación escrita como CURVAS POR PIEZA (claves con easing, como en el editor de
	curvas de un programa de animación) en la lista de cuadros que entiende el cliente (VFX/Animador), con un
	cuadro cada 1/Fps segundos, todas las piezas en cada cuadro e interpolación lineal entre ellos.

	¿Por qué hornear en lugar de dejar el easing al motor?
	  - Lo que se ve en el juego es exactamente lo que calcula este módulo, que es lo mismo que comprueban las
	    pruebas (pies en el suelo, que no patinen, bucles que cierran) y lo que se exporta a Blender para la hoja
	    de contactos. No depende de cómo interpola Roblox cada estilo de easing de las Pose.
	  - Permite cosas que una KeyframeSequence no sabe hacer sola:
	      * cada pieza tiene sus propias claves y su propio desfase (brazos y cabeza a destiempo del cuerpo),
	      * piezas escritas "respecto al mundo" (Mundo = true): la cabeza que se queda clavada mirando mientras el
	        cuerpo se sacude, o los brazos que cuelgan por su peso aunque el torso se incline,
	      * la altura del torso calculada en cada cuadro para que el pie más bajo toque el suelo (AlturaAutomatica):
	        el cuerpo ni flota ni se hunde aunque las piernas (rígidas en R6) se abran.

	FORMATO DE UNA ANIMACIÓN (ver Personajes/Datos/AnimacionesMonstruo para ejemplos):
	  Duracion           segundos de un ciclo.
	  Bucle              true para repetirla. En un bucle cada canal debe acabar en T = Duracion con la misma pose
	                     con la que empieza (así el ciclo cierra sin saltos).
	  Prioridad          "Core", "Idle", "Movement" o "Action".
	  Fps                cuadros por segundo del horneado (por defecto 30).
	  AlturaAutomatica   true: la traslación "arriba" del Torso pasa a ser la altura SOBRE EL SUELO del pie más bajo
	                     (0 = pisando). Si no, es la traslación normal del Torso.
	  Easing, Direccion  valores por defecto de las claves que no los indican ("Sine" e "InOut" si se omiten).
	  Canales            { [pieza] = canal } con las seis piezas del R6: Torso, Head, "Right Arm", "Left Arm",
	                     "Right Leg" y "Left Leg". Cada canal:
	                       Claves   lista ordenada por T. Cada clave: { T = segundos, Pose = { cabeceo, giro, ladeo
	                                [, derecha, arriba, adelante] }, Easing = ..., Direccion = ... }
	                                El easing de una clave es el del tramo que LLEGA a ella desde la anterior.
	                       Mundo    true: los ángulos son respecto al personaje erguido, no respecto al Torso.
	                       Desfase  segundos que se adelanta este canal respecto al resto (solo en bucles).
	  Los ángulos y las traslaciones significan lo mismo que en Combate/Datos/Animaciones.

	ESTILOS DE EASING: "Linear", "Constant" (se queda quieto y salta de golpe al llegar a la clave: tirones),
	"Sine", "Quad", "Cubic", "Back" (se pasa de largo y vuelve), "Elastic" y "Bounce".
	DIRECCIONES: "In" (arranca despacio), "Out" (llega frenando) e "InOut".
]]

local Cinematica = require(script.Parent.CinematicaR6)

export type Clave = { T: number, Pose: { number }, Easing: string?, Direccion: string? }
export type Canal = { Claves: { Clave }, Mundo: boolean?, Desfase: number? }
export type Definicion = {
	Duracion: number,
	Bucle: boolean?,
	Prioridad: string?,
	Fps: number?,
	AlturaAutomatica: boolean?,
	Easing: string?,
	Direccion: string?,
	Canales: { [string]: Canal },
	[string]: any, -- otros datos que el horneado no usa (VelocidadReferencia...)
}
-- Formato de Combate/Datos/Animaciones (el que construye VFX/Animador).
export type Cuadro = { T: number, Poses: { [string]: { number } }, Easing: string? }
export type Horneada = { Duracion: number, Bucle: boolean, Prioridad: string, Cuadros: { Cuadro } }

local Horneado = {}

local FPS_POR_DEFECTO = 30
local PRECISION = 1e-6

-- ===== Easing =====

local PI = math.pi

-- Curvas "de entrada" (In): t de 0 a 1 -> avance de 0 a 1. Out e InOut se obtienen de ellas.
local CURVAS: { [string]: (number) -> number } = {
	Linear = function(t)
		return t
	end,
	Sine = function(t)
		return 1 - math.cos(t * PI / 2)
	end,
	Quad = function(t)
		return t * t
	end,
	Cubic = function(t)
		return t * t * t
	end,
	Back = function(t)
		local s = 1.70158
		return t * t * ((s + 1) * t - s)
	end,
	Elastic = function(t)
		if t <= 0 or t >= 1 then
			return t
		end
		return -(2 ^ (10 * (t - 1))) * math.sin((t - 1.075) * (2 * PI) / 0.3)
	end,
	Bounce = function(t)
		-- Rebote de salida espejado (la curva de entrada de Bounce).
		local u = 1 - t
		local r
		if u < 1 / 2.75 then
			r = 7.5625 * u * u
		elseif u < 2 / 2.75 then
			u -= 1.5 / 2.75
			r = 7.5625 * u * u + 0.75
		elseif u < 2.5 / 2.75 then
			u -= 2.25 / 2.75
			r = 7.5625 * u * u + 0.9375
		else
			u -= 2.625 / 2.75
			r = 7.5625 * u * u + 0.984375
		end
		return 1 - r
	end,
}

Horneado.ESTILOS = { "Linear", "Constant", "Sine", "Quad", "Cubic", "Back", "Elastic", "Bounce" }
Horneado.DIRECCIONES = { "In", "Out", "InOut" }

-- Avance (normalmente de 0 a 1; Back y Elastic se pasan un poco) en el instante t (0..1) de un tramo.
function Horneado.Easing(estilo: string, direccion: string, t: number): number
	if estilo == "Constant" then
		return if t >= 1 then 1 else 0
	end
	local curva = CURVAS[estilo]
	assert(curva, `estilo de easing desconocido: {estilo}`)
	if direccion == "In" then
		return curva(t)
	elseif direccion == "Out" then
		return 1 - curva(1 - t)
	elseif direccion == "InOut" then
		if t < 0.5 then
			return curva(2 * t) / 2
		end
		return 1 - curva(2 - 2 * t) / 2
	end
	error(`dirección de easing desconocida: {direccion}`)
end

-- ===== Evaluación de las curvas =====

-- Valor de un canal en el instante t (segundos del ciclo, ya con el desfase aplicado).
local function evaluarClaves(definicion: Definicion, claves: { Clave }, t: number): { number }
	local primera, ultima = claves[1], claves[#claves]
	local function copiar(pose: { number }): { number }
		return { pose[1], pose[2], pose[3], pose[4] or 0, pose[5] or 0, pose[6] or 0 }
	end
	if t <= primera.T then
		return copiar(primera.Pose)
	end
	if t >= ultima.T then
		return copiar(ultima.Pose)
	end
	for indice = 2, #claves do
		local b = claves[indice]
		if t <= b.T then
			local a = claves[indice - 1]
			local avance = (t - a.T) / (b.T - a.T)
			local e = Horneado.Easing(
				b.Easing or definicion.Easing or "Sine",
				b.Direccion or definicion.Direccion or "InOut",
				avance
			)
			local pa, pb = copiar(a.Pose), copiar(b.Pose)
			local resultado = {}
			for componente = 1, 6 do
				resultado[componente] = pa[componente] + (pb[componente] - pa[componente]) * e
			end
			return resultado
		end
	end
	return copiar(ultima.Pose)
end

--[[
	Poses "tal cual están escritas" de todas las piezas en el instante t (con el desfase de cada canal), sin
	convertir las piezas Mundo ni calcular la altura. Devuelve { [pieza] = { 6 números } }.
]]
function Horneado.Evaluar(definicion: Definicion, t: number): { [string]: { number } }
	local poses = {}
	for pieza, canal in definicion.Canales do
		local instante = t
		if definicion.Bucle and canal.Desfase and canal.Desfase ~= 0 then
			instante = (t + canal.Desfase) % definicion.Duracion
		end
		poses[pieza] = evaluarClaves(definicion, canal.Claves, instante)
	end
	return poses
end

--[[
	Poses FINALES de todas las piezas en el instante t: las que se meten en la animación. Las piezas Mundo se pasan
	a relativas al Torso y, con AlturaAutomatica, se calcula la altura del Torso para que el pie más bajo quede a la
	altura pedida sobre el suelo.
]]
function Horneado.PoseEn(definicion: Definicion, t: number): { [string]: { number } }
	local poses = Horneado.Evaluar(definicion, t)

	local torso = poses.Torso
	local rotacionTorso = Cinematica.RotacionDePose("Torso", torso)
	for pieza, canal in definicion.Canales do
		if canal.Mundo and pieza ~= "Torso" then
			local pose = poses[pieza]
			local mundo = Cinematica.RotacionDePose(pieza, pose)
			local relativa = Cinematica.Multiplicar(Cinematica.Trasponer(rotacionTorso), mundo)
			local angulos = Cinematica.PoseDeRotacion(pieza, relativa)
			poses[pieza] = { angulos[1], angulos[2], angulos[3], pose[4], pose[5], pose[6] }
		end
	end

	if definicion.AlturaAutomatica then
		-- Subir o bajar el Torso desplaza todo el cuerpo por igual: basta medir con la altura a cero y corregir.
		local sobreSuelo = torso[5]
		torso[5] = 0
		local piezas = Cinematica.Piezas(poses)
		local pie = math.min(Cinematica.AlturaPie(piezas["Right Leg"]), Cinematica.AlturaPie(piezas["Left Leg"]))
		torso[5] = Cinematica.ALTURA_SUELO - pie + sobreSuelo
	end
	return poses
end

-- ===== Horneado =====

-- Número de cuadros del horneado (sin contar el del instante 0).
function Horneado.NumeroCuadros(definicion: Definicion): number
	return math.max(1, math.round(definicion.Duracion * (definicion.Fps or FPS_POR_DEFECTO)))
end

-- Convierte la definición en el formato de Combate/Datos/Animaciones, con un cuadro lineal cada 1/Fps s.
function Horneado.Hornear(definicion: Definicion): Horneada
	local problemas = Horneado.Validar(definicion)
	assert(#problemas == 0, `animación mal formada:\n{table.concat(problemas, "\n")}`)

	local n = Horneado.NumeroCuadros(definicion)
	local cuadros = {}
	for indice = 0, n do
		local t = definicion.Duracion * indice / n
		table.insert(cuadros, { T = t, Poses = Horneado.PoseEn(definicion, t), Easing = "Linear" })
	end
	return {
		Duracion = definicion.Duracion,
		Bucle = definicion.Bucle == true,
		Prioridad = definicion.Prioridad or "Movement",
		Cuadros = cuadros,
	}
end

-- ===== Validación =====

local function esNumero(valor: any): boolean
	return type(valor) == "number" and valor == valor and valor ~= math.huge and valor ~= -math.huge
end

local PRIORIDADES = { Core = true, Idle = true, Movement = true, Action = true }

--[[
	Revisa que la definición esté bien formada. Devuelve la lista de problemas (vacía si está bien): piezas que no
	son de R6 o que faltan, claves desordenadas, tiempos fuera del ciclo, bucles que no cierran, easing desconocidos,
	poses con un número de valores incorrecto o ángulos desorbitados.
]]
function Horneado.Validar(definicion: Definicion): { string }
	local problemas = {}
	local function problema(texto: string)
		table.insert(problemas, texto)
	end

	if not esNumero(definicion.Duracion) or definicion.Duracion <= 0 then
		problema("Duracion debe ser un número positivo")
		return problemas
	end
	if definicion.Prioridad ~= nil and not PRIORIDADES[definicion.Prioridad] then
		problema(`Prioridad desconocida: {definicion.Prioridad}`)
	end
	if definicion.Fps ~= nil and (not esNumero(definicion.Fps) or definicion.Fps < 10 or definicion.Fps > 60) then
		problema("Fps debe estar entre 10 y 60")
	end

	for _, pieza in Cinematica.PIEZAS do
		if definicion.Canales[pieza] == nil then
			problema(`falta el canal de '{pieza}'`)
		end
	end

	for pieza, canal in definicion.Canales do
		if Cinematica.ARTICULACIONES[pieza] == nil then
			problema(`'{pieza}' no es una pieza animable de R6`)
			continue
		end
		if canal.Mundo and pieza == "Torso" then
			problema("el Torso ya es relativo al personaje: no lleva Mundo")
		end
		if canal.Desfase ~= nil and (not esNumero(canal.Desfase) or not definicion.Bucle) then
			problema(`{pieza}: Desfase solo vale en bucles y debe ser un número`)
		end
		local claves = canal.Claves
		if type(claves) ~= "table" or #claves == 0 then
			problema(`{pieza}: sin claves`)
			continue
		end
		local anterior = -math.huge
		for indice, clave in claves do
			local donde = `{pieza}[{indice}]`
			if not esNumero(clave.T) then
				problema(`{donde}: T no es un número`)
				continue
			end
			if clave.T <= anterior then
				problema(`{donde}: T = {clave.T} no es mayor que la clave anterior ({anterior})`)
			end
			anterior = clave.T
			if clave.T < -PRECISION or clave.T > definicion.Duracion + PRECISION then
				problema(`{donde}: T = {clave.T} está fuera de la animación (0..{definicion.Duracion})`)
			end
			local pose = clave.Pose
			if type(pose) ~= "table" or (#pose ~= 3 and #pose ~= 6) then
				problema(`{donde}: la pose debe tener 3 ángulos o 3 ángulos y 3 traslaciones`)
				continue
			end
			for componente, valor in pose do
				if not esNumero(valor) then
					problema(`{donde}: el valor {componente} de la pose no es un número`)
				elseif componente <= 3 and math.abs(valor) > 180 then
					problema(`{donde}: ángulo de {valor}° fuera de -180..180`)
				elseif componente > 3 and math.abs(valor) > 3 then
					problema(`{donde}: traslación de {valor} studs (más de 3 es casi seguro un error)`)
				end
			end
			if clave.Easing ~= nil and table.find(Horneado.ESTILOS, clave.Easing) == nil then
				problema(`{donde}: easing desconocido '{clave.Easing}'`)
			end
			if clave.Direccion ~= nil and table.find(Horneado.DIRECCIONES, clave.Direccion) == nil then
				problema(`{donde}: dirección desconocida '{clave.Direccion}'`)
			end
		end

		if math.abs(claves[1].T) > PRECISION then
			problema(`{pieza}: la primera clave debe estar en T = 0`)
		end
		if definicion.Bucle then
			local primera, ultima = claves[1], claves[#claves]
			if math.abs(ultima.T - definicion.Duracion) > PRECISION then
				problema(`{pieza}: en un bucle la última clave debe estar en T = Duracion ({definicion.Duracion})`)
			end
			for componente = 1, 6 do
				local a = primera.Pose[componente] or 0
				local b = ultima.Pose[componente] or 0
				if math.abs(a - b) > PRECISION then
					problema(`{pieza}: el bucle no cierra (la última pose no es igual que la primera)`)
					break
				end
			end
		end
	end
	return problemas
end

return Horneado
