--!strict
--[[
	Animaciones: animaciones PROVISIONALES para el rig R6 hechas por código (se convierten en una
	KeyframeSequence al jugarse).

	Sirven para que el combate se vea vivo desde el primer día. Para sustituir una por otra hecha en el
	editor de animaciones de Roblox NO hay que tocar código: se pone su ID en Datos/Recursos.Animaciones
	("rbxassetid://123...") y el cliente usa ese en lugar de la de aquí.

	Formato de una animación:
	  Duracion   segundos totales (el último cuadro suele estar en este instante)
	  Prioridad  "Action" (por defecto), "Movement", "Idle" o "Core"
	  Bucle      true para repetirla
	  Cuadros    lista ordenada por tiempo. Cada cuadro:
	               T          segundo en el que se alcanza la pose
	               Poses      { [Parte] = { cabeceo, giro, ladeo [, derecha, arriba, adelante] } }
	               Easing     estilo de interpolación HACIA este cuadro ("Linear", "Cubic", "Elastic", "Bounce",
	                          "Constant"). Por defecto "Linear".
	               Direccion  "Out" (por defecto: llega rápido y frena, bueno para golpes), "In" (arranca despacio,
	                          bueno para la anticipación) o "InOut".
	             Las partes que un cuadro no nombra mantienen su valor anterior. Una parte que SÍ se nombra
	             sustituye por completo a la anterior (si no lleva traslación, vuelve a cero).

	Partes del rig R6 (solo 6 piezas, sin codos ni rodillas): Torso, Head, "Right Arm", "Left Arm",
	"Right Leg" y "Left Leg". Las piernas y los brazos cuelgan del Torso, así que giran con él. HumanoidRootPart
	es la raíz y no se anima. Ojo: los nombres con espacio van entre comillas: ["Right Arm"] = ...

	Los ángulos son en GRADOS, relativos a la pose de reposo, y están pensados desde el punto de vista del
	personaje (mira hacia delante, su derecha es la derecha del personaje), no de los ejes de cada Motor6D:
	  cabeceo  + : el extremo libre de la pieza va hacia DELANTE.
	             Brazo/pierna: 90 = horizontal hacia delante, 180 = recto hacia arriba, negativo = hacia atrás.
	             Torso/cabeza: positivo = se inclina hacia delante (asiente); negativo = hacia atrás.
	  giro     + : gira hacia la IZQUIERDA vista desde arriba (el hombro derecho avanza).
	  ladeo    + : el extremo libre va hacia la DERECHA del personaje. En el brazo derecho es "abrir" el
	             brazo y en el izquierdo es "cruzarlo"; con el brazo ya a 90° de cabeceo, ladeo = giro horizontal.
	  derecha, arriba, adelante: traslación en studs (opcional; sobre todo para el Torso, que lleva el cuerpo).
	Los ángulos se aplican en el orden ladeo → giro → cabeceo.

	La conversión a Motor6D.Transform (cada articulación de R6 tiene su propio eje) está en
	Animaciones.Articulacion; el cliente (VFX/Animador) la usa al construir las KeyframeSequence.
]]

local Animaciones = {}

-- Orientación (rotación de C0) de cada tipo de articulación de R6, como las tres columnas de la matriz:
-- hacia dónde apuntan en el personaje los ejes X, Y y Z de la articulación. Son los valores de fábrica de
-- Roblox para el rig R6 (RootJoint/Neck comparten orientación; el hombro y la cadera cambian con el lado).
local EJES_RAIZ_Y_CUELLO = { X = { -1, 0, 0 }, Y = { 0, 0, 1 }, Z = { 0, 1, 0 } }
local EJES_LADO_DERECHO = { X = { 0, 0, -1 }, Y = { 0, 1, 0 }, Z = { 1, 0, 0 } }
local EJES_LADO_IZQUIERDO = { X = { 0, 0, 1 }, Y = { 0, 1, 0 }, Z = { -1, 0, 0 } }

--[[
	Jerarquía del rig R6: cada parte con las que cuelgan de ella. El cliente la usa para construir el árbol de
	Poses de cada cuadro. `Eje` = orientación de la articulación; `Arriba` = true si el extremo libre de la pieza
	apunta hacia arriba (Torso y cabeza), lo que invierte el signo del cabeceo y el ladeo para que "positivo"
	signifique lo mismo en todas las piezas.
]]
Animaciones.Rig = {
	Nombre = "HumanoidRootPart",
	Hijos = {
		{
			Nombre = "Torso",
			Eje = EJES_RAIZ_Y_CUELLO,
			Arriba = true,
			Hijos = {
				{ Nombre = "Head", Eje = EJES_RAIZ_Y_CUELLO, Arriba = true, Hijos = {} },
				{ Nombre = "Right Arm", Eje = EJES_LADO_DERECHO, Hijos = {} },
				{ Nombre = "Left Arm", Eje = EJES_LADO_IZQUIERDO, Hijos = {} },
				{ Nombre = "Right Leg", Eje = EJES_LADO_DERECHO, Hijos = {} },
				{ Nombre = "Left Leg", Eje = EJES_LADO_IZQUIERDO, Hijos = {} },
			},
		},
	},
}

-- ===== Matemáticas de la conversión (matrices 3x3 por filas, sin depender de CFrame para poder probarlas) =====

local function multiplicar(a: { { number } }, b: { { number } }): { { number } }
	local resultado = {}
	for i = 1, 3 do
		resultado[i] = {}
		for j = 1, 3 do
			resultado[i][j] = a[i][1] * b[1][j] + a[i][2] * b[2][j] + a[i][3] * b[3][j]
		end
	end
	return resultado
end

local function trasponer(m: { { number } }): { { number } }
	return {
		{ m[1][1], m[2][1], m[3][1] },
		{ m[1][2], m[2][2], m[3][2] },
		{ m[1][3], m[2][3], m[3][3] },
	}
end

-- Rotación de Roblox: primero Z, luego Y, luego X (Rx * Ry * Rz), con los ángulos en grados.
local function rotacionXYZ(rx: number, ry: number, rz: number): { { number } }
	local cx, sx = math.cos(math.rad(rx)), math.sin(math.rad(rx))
	local cy, sy = math.cos(math.rad(ry)), math.sin(math.rad(ry))
	local cz, sz = math.cos(math.rad(rz)), math.sin(math.rad(rz))
	local mx = { { 1, 0, 0 }, { 0, cx, -sx }, { 0, sx, cx } }
	local my = { { cy, 0, sy }, { 0, 1, 0 }, { -sy, 0, cy } }
	local mz = { { cz, -sz, 0 }, { sz, cz, 0 }, { 0, 0, 1 } }
	return multiplicar(mx, multiplicar(my, mz))
end

-- Matriz cuyas columnas son los ejes de la articulación.
local function matrizDeEjes(eje: any): { { number } }
	return {
		{ eje.X[1], eje.Y[1], eje.Z[1] },
		{ eje.X[2], eje.Y[2], eje.Z[2] },
		{ eje.X[3], eje.Y[3], eje.Z[3] },
	}
end

--[[
	Convierte una pose (la que se escribe arriba: cabeceo, giro, ladeo [, derecha, arriba, adelante]) en el
	Transform del Motor6D de esa parte. Devuelve:
	  - la matriz de rotación, 9 números por filas (el orden de los argumentos de CFrame.new tras x, y, z),
	  - la traslación { x, y, z }.
	El Transform es C⁻¹ · R · C, donde R es la rotación en el sistema del personaje y C la orientación de la
	articulación (Eje): así el ángulo significa lo mismo en el Torso, la cabeza, los brazos y las piernas.
]]
function Animaciones.Articulacion(nodo: any, pose: { number }): ({ number }, { number })
	local signo = if nodo.Arriba then -1 else 1
	local rotacion = rotacionXYZ(signo * pose[1], pose[2], signo * pose[3])
	local c = matrizDeEjes(nodo.Eje)
	local m = multiplicar(trasponer(c), multiplicar(rotacion, c))

	-- Traslación del personaje (derecha, arriba, adelante) -> ejes del personaje (x derecha, y arriba, z atrás).
	local x, y, z = pose[4] or 0, pose[5] or 0, -(pose[6] or 0)
	local t = {
		c[1][1] * x + c[2][1] * y + c[3][1] * z,
		c[1][2] * x + c[2][2] * y + c[3][2] * z,
		c[1][3] * x + c[2][3] * y + c[3][3] * z,
	}
	return { m[1][1], m[1][2], m[1][3], m[2][1], m[2][2], m[2][3], m[3][1], m[3][2], m[3][3] }, t
end

-- Espejo izquierda-derecha de una animación: intercambia los lados y cambia el signo del giro, el ladeo y el
-- desplazamiento lateral. Sirve para no escribir dos veces los golpes simétricos.
local function espejar(definicion: any): any
	local function nombreEspejo(parte: string): string
		if string.sub(parte, 1, 5) == "Right" then
			return "Left" .. string.sub(parte, 6)
		elseif string.sub(parte, 1, 4) == "Left" then
			return "Right" .. string.sub(parte, 5)
		end
		return parte
	end

	local copia = table.clone(definicion)
	copia.Cuadros = {}
	for indice, cuadro in definicion.Cuadros do
		local nuevo = table.clone(cuadro)
		nuevo.Poses = {}
		for parte, pose in cuadro.Poses do
			local espejo = { pose[1], -pose[2], -pose[3] }
			if pose[4] then
				espejo[4], espejo[5], espejo[6] = -pose[4], pose[5], pose[6]
			end
			nuevo.Poses[nombreEspejo(parte)] = espejo
		end
		copia.Cuadros[indice] = nuevo
	end
	return copia
end

Animaciones.Definiciones = {
	-- Mano derecha adelantada acumulando energía: se echa atrás un instante y luego se adelanta.
	Alzar_Mano = {
		Duracion = 0.3,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 0, 0, 6 },
					["Left Arm"] = { 0, 0, -6 },
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { 0, 0, 4 },
					["Left Leg"] = { 0, 0, -4 },
				},
			},
			{ -- anticipación: el brazo se recoge hacia atrás
				T = 0.08,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { -22, 0, 12 },
					["Left Arm"] = { 10, 0, -14 },
					Torso = { -3, -10, 0 },
				},
			},
			{ -- el brazo sube hacia delante y el cuerpo se afianza
				T = 0.26,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 86, 0, -6 },
					["Left Arm"] = { -18, 0, -30 },
					Torso = { 5, 18, 0 },
					Head = { 0, -14, 0 },
					["Right Leg"] = { -12, 0, 5 },
					["Left Leg"] = { 14, 0, -5 },
				},
			},
		},
	},
	-- Brazo disparado hacia delante: sacudida hacia atrás, disparo que se pasa de largo, retroceso y recogida.
	Disparo_Frente = {
		Duracion = 0.32,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 86, 0, -6 },
					["Left Arm"] = { -18, 0, -30 },
					Torso = { 5, 18, 0 },
					Head = { 0, -14, 0 },
					["Right Leg"] = { -12, 0, 5 },
					["Left Leg"] = { 14, 0, -5 },
				},
			},
			{ -- anticipación: el brazo se encoge un poco antes de disparar
				T = 0.04,
				Easing = "Cubic",
				Poses = { ["Right Arm"] = { 64, 0, -4 }, Torso = { 2, 10, 0 } },
			},
			{ -- disparo: el brazo se pasa de largo y todo el cuerpo se lanza detrás
				T = 0.1,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 106, 0, -3 },
					["Left Arm"] = { -30, 0, -44 },
					Torso = { 9, 28, 0, 0, 0, 0.35 },
					Head = { 0, -24, 0 },
					["Right Leg"] = { -22, 0, 6 },
					["Left Leg"] = { 20, 0, -6 },
				},
			},
			{ -- retroceso
				T = 0.18,
				Easing = "Cubic",
				Poses = { ["Right Arm"] = { 96, 0, -3 }, Torso = { 7, 24, 0, 0, 0, 0.25 } },
			},
			{ -- recuperación
				T = 0.32,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 20, 0, 6 },
					["Left Arm"] = { 0, 0, -8 },
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { 0, 0, 4 },
					["Left Leg"] = { 0, 0, -4 },
				},
			},
		},
	},
	-- Los dos brazos suben al cielo para invocar: se agacha a coger fuerza y estalla hacia arriba.
	Alzar_Cielo = {
		Duracion = 0.7,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 0, 0, 8 },
					["Left Arm"] = { 0, 0, -8 },
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { 0, 0, 4 },
					["Left Leg"] = { 0, 0, -4 },
				},
			},
			{ -- anticipación: se agacha y echa los brazos atrás
				T = 0.2,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { -25, 0, 14 },
					["Left Arm"] = { -25, 0, -14 },
					Torso = { 14, 0, 0, 0, -0.25, 0 },
					Head = { 8, 0, 0 },
					["Right Leg"] = { 10, 0, 18 },
					["Left Leg"] = { 10, 0, -18 },
				},
			},
			{ -- estalla hacia arriba, con el pecho y la cabeza echados atrás
				T = 0.58,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 176, 0, 22 },
					["Left Arm"] = { 176, 0, -22 },
					Torso = { -18, 0, 0, 0, 0.1, 0 },
					Head = { -20, 0, 0 },
					["Right Leg"] = { -6, 0, 10 },
					["Left Leg"] = { -6, 0, -10 },
				},
			},
			{ -- se asienta
				T = 0.7,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 168, 0, 18 },
					["Left Arm"] = { 168, 0, -18 },
					Torso = { -14, 0, 0 },
					Head = { -16, 0, 0 },
				},
			},
		},
	},
	-- Los brazos caen de golpe lanzando el poder: se arquea hacia atrás y se lanza hacia delante.
	Lanzar_Cielo = {
		Duracion = 0.45,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 168, 0, 18 },
					["Left Arm"] = { 168, 0, -18 },
					Torso = { -14, 0, 0 },
					Head = { -16, 0, 0 },
					["Right Leg"] = { -6, 0, 10 },
					["Left Leg"] = { -6, 0, -10 },
				},
			},
			{ -- anticipación: un último arco hacia atrás
				T = 0.07,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 186, 0, 16 },
					["Left Arm"] = { 186, 0, -16 },
					Torso = { -24, 0, 0 },
					Head = { -24, 0, 0 },
				},
			},
			{ -- latigazo hacia delante
				T = 0.17,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 58, 0, 6 },
					["Left Arm"] = { 58, 0, -6 },
					Torso = { 30, 0, 0, 0, -0.2, 0.3 },
					Head = { 18, 0, 0 },
					["Right Leg"] = { -24, 0, 8 },
					["Left Leg"] = { 22, 0, -8 },
				},
			},
			{ -- se pasa un poco y se mantiene un instante
				T = 0.26,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 48, 0, 6 },
					["Left Arm"] = { 48, 0, -6 },
					Torso = { 34, 0, 0, 0, -0.25, 0.35 },
				},
			},
			{
				T = 0.45,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 8, 0, 10 },
					["Left Arm"] = { 8, 0, -10 },
					Torso = { 4, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { -4, 0, 6 },
					["Left Leg"] = { 4, 0, -6 },
				},
			},
		},
	},
	-- Puño al suelo: brazo en alto, se estira atrás y cae con todo el cuerpo en una zancada profunda.
	Golpe_Suelo = {
		Duracion = 0.45,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 150, 0, 8 },
					["Left Arm"] = { 40, 0, -14 },
					Torso = { -10, 0, 0 },
					Head = { -8, 0, 0 },
					["Right Leg"] = { 0, 0, 6 },
					["Left Leg"] = { 0, 0, -6 },
				},
			},
			{ -- anticipación: el puño sube todavía más
				T = 0.1,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 176, 0, 10 },
					Torso = { -18, 0, 0 },
					Head = { -14, 0, 0 },
				},
			},
			{ -- el golpe: torso hundido, una pierna atrás y otra adelante
				T = 0.2,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 38, 0, 4 },
					["Left Arm"] = { 24, 0, -16 },
					Torso = { 40, 10, 0, 0, -0.5, 0.5 },
					Head = { 22, -8, 0 },
					["Right Leg"] = { -32, 0, 16 },
					["Left Leg"] = { 38, 0, -14 },
				},
			},
			{ -- se mantiene aplastado contra el suelo
				T = 0.28,
				Easing = "Cubic",
				Poses = { ["Right Arm"] = { 34, 0, 4 }, Torso = { 42, 10, 0, 0, -0.55, 0.55 } },
			},
			{
				T = 0.45,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 10, 0, 8 },
					["Left Arm"] = { 0, 0, -8 },
					Torso = { 6, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { -6, 0, 5 },
					["Left Leg"] = { 6, 0, -5 },
				},
			},
		},
	},
	-- Los brazos se cierran sobre el pecho comprimiendo energía (gravedad).
	Comprimir = {
		Duracion = 0.4,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 0, 0, 10 },
					["Left Arm"] = { 0, 0, -10 },
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { 0, 0, 4 },
					["Left Leg"] = { 0, 0, -4 },
				},
			},
			{ -- anticipación: los brazos se abren
				T = 0.1,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { -10, 0, 26 },
					["Left Arm"] = { -10, 0, -26 },
					Torso = { -4, 0, 0 },
				},
			},
			{ -- se cierran con fuerza sobre el pecho, encorvado
				T = 0.34,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 82, 0, -42 },
					["Left Arm"] = { 82, 0, 42 },
					Torso = { 16, 0, 0, 0, -0.2, 0 },
					Head = { 12, 0, 0 },
					["Right Leg"] = { -10, 0, 12 },
					["Left Leg"] = { -10, 0, -12 },
				},
			},
			{ -- aprieta un poco más
				T = 0.4,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 86, 0, -48 },
					["Left Arm"] = { 86, 0, 48 },
					Torso = { 18, 0, 0, 0, -0.25, 0 },
				},
			},
		},
	},

	-- ===== Combo (cada golpe es muy rápido) =====
	-- El ladeo del brazo con cabeceo ~90 es el giro horizontal: ladeo = (giro del torso) deja el golpe recto.
	Combo1 = { -- gancho de derecha (impacto en T = 0.12)
		Duracion = 0.3,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 62, 0, -6 },
					["Left Arm"] = { 58, 0, 14 },
					Torso = { 4, 6, 0 },
					Head = { 0, -6, 0 },
					["Right Leg"] = { -14, 0, 6 },
					["Left Leg"] = { 14, 0, -6 },
				},
			},
			{ -- anticipación: el torso gira a la derecha y el brazo se abre bien atrás
				T = 0.05,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 86, 0, 78 },
					["Left Arm"] = { 66, 0, 10 },
					Torso = { 2, -30, 0 },
					Head = { 0, 22, 0 },
				},
			},
			{ -- impacto: el torso gira a la izquierda y el brazo barre por delante
				T = 0.12,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 90, 0, 36 },
					["Left Arm"] = { 44, 0, 24 },
					Torso = { 8, 38, 0, 0, 0, 0.3 },
					Head = { 0, -30, 0 },
					["Right Leg"] = { -24, 0, 8 },
					["Left Leg"] = { 24, 0, -8 },
				},
			},
			{ -- el cuerpo se pasa un poco del golpe
				T = 0.17,
				Easing = "Cubic",
				Poses = { ["Right Arm"] = { 92, 0, 30 }, Torso = { 10, 44, 0, 0, 0, 0.4 } },
			},
			{
				T = 0.3,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 62, 0, -6 },
					["Left Arm"] = { 58, 0, 14 },
					Torso = { 4, 6, 0 },
					Head = { 0, -6, 0 },
					["Right Leg"] = { -14, 0, 6 },
					["Left Leg"] = { 14, 0, -6 },
				},
			},
		},
	},
	Combo3 = { -- patada giratoria con la derecha (impacto en T = 0.16)
		Duracion = 0.4,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 50, 0, -6 },
					["Left Arm"] = { 50, 0, 12 },
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { -6, 0, 5 },
					["Left Leg"] = { 6, 0, -5 },
				},
			},
			{ -- anticipación: el torso gira a la derecha y la pierna se recoge atrás
				T = 0.1,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 30, 0, 40 },
					["Left Arm"] = { 30, 0, -30 },
					Torso = { 3, -34, 0 },
					Head = { 0, 26, 0 },
					["Right Leg"] = { 30, 0, 70 },
					["Left Leg"] = { -4, 0, -4 },
				},
			},
			{ -- patada: la pierna barre en horizontal mientras el cuerpo gira a la izquierda
				T = 0.16,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 20, 0, 70 },
					["Left Arm"] = { 44, 0, -30 },
					Torso = { -8, 52, 0 },
					Head = { 0, -40, 0 },
					["Right Leg"] = { 92, 0, 52 },
					["Left Leg"] = { -12, 0, -6 },
				},
			},
			{ -- mantiene la pierna extendida
				T = 0.24,
				Easing = "Cubic",
				Poses = { Torso = { -10, 56, 0 }, ["Right Leg"] = { 98, 0, 46 } },
			},
			{
				T = 0.4,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 50, 0, -6 },
					["Left Arm"] = { 50, 0, 12 },
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Leg"] = { -6, 0, 5 },
					["Left Leg"] = { 6, 0, -5 },
				},
			},
		},
	},
	--[[
		Remate: puñetazo fuerte a lo anime con la derecha. Sigue las mismas fases y poses clave que la animación de
		Blender (animaciones/herramientas/punetazo_fuerte.py): guardia, anticipación (el cuerpo se agacha y se
		enrosca a la derecha con el puño cargado atrás), tensión, golpe (primero el torso, después el puño),
		impacto exagerado mantenido en T = 0.53 (igual que Tiempos.Carga del Remate) y recuperación (aquí se corta
		en 0.9 s). Las piernas se escriben contando con el giro del torso: R6 las cuelga del Torso, así que giran
		con él y hay que repartir el ángulo entre cabeceo y ladeo para que sigan plantadas hacia delante.
	]]
	Combo4 = {
		Duracion = 0.9,
		Cuadros = {
			{
				T = 0,
				Poses = {
					["Right Arm"] = { 58, 0, -2 },
					["Left Arm"] = { 52, 0, -28 },
					Torso = { 6, -18, 0, 0, -0.15, 0 },
					Head = { 0, 18, 0 },
					["Right Leg"] = { -15, 0, 5 },
					["Left Leg"] = { 17, 0, -6 },
				},
			},
			{ -- máxima anticipación: agachado, torso enroscado a la derecha, puño atrás y mano izquierda apuntando
				T = 0.33,
				Easing = "Cubic",
				Direccion = "InOut",
				Poses = {
					["Right Arm"] = { 30, 0, 75 },
					["Left Arm"] = { 90, 0, -55 },
					Torso = { 10, -55, -4, 0.2, -0.35, -0.6 },
					Head = { -4, 45, 0 },
					["Right Leg"] = { -15, 0, 21 },
					["Left Leg"] = { 10, 0, -15 },
				},
			},
			{ -- tensión: casi quieto
				T = 0.4,
				Easing = "Cubic",
				Direccion = "InOut",
				Poses = { Torso = { 10, -58, -4, 0.2, -0.38, -0.65 }, ["Right Arm"] = { 28, 0, 78 } },
			},
			{ -- el torso arranca antes que el puño, que se queda atrás
				T = 0.47,
				Easing = "Cubic",
				Poses = {
					Torso = { 16, 0, 0, 0, -0.35, 0.2 },
					["Right Arm"] = { 50, 0, 75 },
					["Left Arm"] = { 70, 0, -20 },
					Head = { -10, 0, 0 },
					["Right Leg"] = { -5, 0, 10 },
					["Left Leg"] = { 5, 0, -10 },
				},
			},
			{ -- impacto exagerado: el cuerpo se lanza, el brazo recto y el otro recogido atrás
				T = 0.53,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 92, 0, 55 },
					["Left Arm"] = { -30, 0, -55 },
					Torso = { 30, 55, 5, 0, -0.4, 0.9 },
					Head = { -26, -52, 0 },
					["Right Leg"] = { -26, 0, -37 },
					["Left Leg"] = { 18, 0, 26 },
				},
			},
			{ -- se mantiene (hit stop) y se pasa un poco más
				T = 0.7,
				Easing = "Cubic",
				Poses = { Torso = { 32, 58, 5, 0, -0.45, 1.0 }, ["Right Arm"] = { 94, 0, 58 } },
			},
			{ -- recuperación
				T = 0.9,
				Easing = "Cubic",
				Poses = {
					["Right Arm"] = { 58, 0, -2 },
					["Left Arm"] = { 52, 0, -28 },
					Torso = { 6, -18, 0, 0, -0.15, 0 },
					Head = { 0, 18, 0 },
					["Right Leg"] = { -15, 0, 5 },
					["Left Leg"] = { 17, 0, -6 },
				},
			},
		},
	},

	-- Reacción del que recibe un golpe: el pecho sale despedido hacia atrás, rebota y se recompone.
	Impacto = {
		Duracion = 0.35,
		Cuadros = {
			{
				T = 0,
				Poses = {
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Arm"] = { 0, 0, 6 },
					["Left Arm"] = { 0, 0, -6 },
				},
			},
			{
				T = 0.06,
				Easing = "Cubic",
				Poses = {
					Torso = { -24, 8, 0, 0, 0, -0.35 },
					Head = { -22, 0, 0 },
					["Right Arm"] = { 34, 0, 44 },
					["Left Arm"] = { 34, 0, -44 },
					["Right Leg"] = { 12, 0, 6 },
					["Left Leg"] = { -8, 0, -6 },
				},
			},
			{ -- rebote
				T = 0.14,
				Easing = "Cubic",
				Poses = {
					Torso = { -14, 4, 0, 0, 0, -0.2 },
					Head = { -10, 0, 0 },
					["Right Arm"] = { 20, 0, 30 },
					["Left Arm"] = { 20, 0, -30 },
				},
			},
			{
				T = 0.35,
				Easing = "Cubic",
				Poses = {
					Torso = { 0, 0, 0 },
					Head = { 0, 0, 0 },
					["Right Arm"] = { 0, 0, 6 },
					["Left Arm"] = { 0, 0, -6 },
					["Right Leg"] = { 0, 0, 0 },
					["Left Leg"] = { 0, 0, 0 },
				},
			},
		},
	},
}

Animaciones.Definiciones.Combo2 = espejar(Animaciones.Definiciones.Combo1) -- revés de izquierda

return Animaciones
