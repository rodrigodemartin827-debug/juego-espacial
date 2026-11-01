--!strict
--[[
	Animaciones: animaciones PROVISIONALES hechas por código (se convierten en KeyframeSequence al jugarse).

	Sirven para que el combate se vea vivo desde el primer día. Para sustituir una por otra hecha en el
	editor de animaciones de Roblox NO hay que tocar código: se pone su ID en Datos/Recursos.Animaciones
	("rbxassetid://123...") y el cliente usa ese en lugar de la de aquí.

	Formato de una animación:
	  Duracion   segundos totales (el último cuadro suele estar en este instante)
	  Prioridad  "Action" (por defecto), "Movement", "Idle" o "Core"
	  Bucle      true para repetirla
	  Cuadros    lista ordenada por tiempo. Cada cuadro:
	               T       segundo en el que se alcanza la pose
	               Poses   { [Parte] = { rotX, rotY, rotZ } } en GRADOS, relativas a la pose de reposo
	               Easing  estilo de interpolación HACIA este cuadro ("Linear", "Cubic", "Elastic", "Bounce", "Constant")
	             Las partes que un cuadro no nombra mantienen su valor anterior.

	Partes (rig R15): HumanoidRootPart, LowerTorso, UpperTorso, Head,
	  RightUpperArm, RightLowerArm, RightHand, LeftUpperArm, LeftLowerArm, LeftHand,
	  RightUpperLeg, RightLowerLeg, RightFoot, LeftUpperLeg, LeftLowerLeg, LeftFoot.

	Guía rápida de rotaciones: los brazos cuelgan hacia abajo.
	  RightUpperArm X = +90   brazo extendido hacia DELANTE        X = +180  brazo hacia ARRIBA
	  RightUpperArm Z = +90   brazo extendido hacia la DERECHA     LeftUpperArm Z = -90  hacia la izquierda
	  UpperTorso Y            gira el torso (positivo = hacia la izquierda)
	  X negativo en un antebrazo o espinilla lo dobla hacia atrás; positivo, hacia delante.
]]

local Animaciones = {}

Animaciones.Definiciones = {
	-- Mano derecha adelantada acumulando energía.
	Alzar_Mano = {
		Duracion = 0.3,
		Cuadros = {
			{ T = 0, Poses = { RightUpperArm = { 0, 0, 10 }, UpperTorso = { 0, 0, 0 }, LowerTorso = { 0, 0, 0 } } },
			{
				T = 0.26,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 80, -10, 20 },
					RightLowerArm = { 50, 0, 0 },
					LeftUpperArm = { 20, 0, -25 },
					UpperTorso = { -4, 18, 0 },
					LowerTorso = { 0, 8, 0 },
					RightUpperLeg = { -8, 0, 0 },
					LeftUpperLeg = { 10, 0, 0 },
				},
			},
		},
	},
	-- Brazo disparado hacia delante.
	Disparo_Frente = {
		Duracion = 0.32,
		Cuadros = {
			{
				T = 0,
				Poses = { RightUpperArm = { 80, -10, 20 }, RightLowerArm = { 50, 0, 0 }, UpperTorso = { -4, 18, 0 } },
			},
			{
				T = 0.07,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 92, 0, 6 },
					RightLowerArm = { 0, 0, 0 },
					LeftUpperArm = { 25, 0, -35 },
					UpperTorso = { 6, -12, 0 },
					LowerTorso = { 0, -6, 0 },
					RightUpperLeg = { -14, 0, 0 },
					LeftUpperLeg = { 14, 0, 0 },
				},
			},
			{
				T = 0.32,
				Easing = "Quad",
				Poses = {
					RightUpperArm = { 85, 0, 8 },
					RightLowerArm = { 5, 0, 0 },
					UpperTorso = { 2, -6, 0 },
				},
			},
		},
	},
	-- Los dos brazos suben al cielo para invocar.
	Alzar_Cielo = {
		Duracion = 0.7,
		Cuadros = {
			{ T = 0, Poses = { RightUpperArm = { 0, 0, 8 }, LeftUpperArm = { 0, 0, -8 } } },
			{
				T = 0.6,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 170, 0, 20 },
					LeftUpperArm = { 170, 0, -20 },
					RightLowerArm = { 15, 0, 0 },
					LeftLowerArm = { 15, 0, 0 },
					UpperTorso = { -16, 0, 0 },
					Head = { -14, 0, 0 },
					RightUpperLeg = { -6, 0, 6 },
					LeftUpperLeg = { -6, 0, -6 },
				},
			},
			{ T = 0.7, Poses = { UpperTorso = { -18, 0, 0 } } },
		},
	},
	-- Los brazos caen de golpe lanzando el poder al suelo / al objetivo.
	Lanzar_Cielo = {
		Duracion = 0.45,
		Cuadros = {
			{
				T = 0,
				Poses = { RightUpperArm = { 170, 0, 20 }, LeftUpperArm = { 170, 0, -20 }, UpperTorso = { -16, 0, 0 } },
			},
			{
				T = 0.12,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 70, 0, 10 },
					LeftUpperArm = { 70, 0, -10 },
					UpperTorso = { 24, 0, 0 },
					Head = { 12, 0, 0 },
					RightUpperLeg = { -25, 0, 0 },
					LeftUpperLeg = { 20, 0, 0 },
				},
			},
			{
				T = 0.45,
				Easing = "Quad",
				Poses = { RightUpperArm = { 60, 0, 10 }, LeftUpperArm = { 60, 0, -10 }, UpperTorso = { 14, 0, 0 } },
			},
		},
	},
	-- Puño al suelo / palmada hacia abajo.
	Golpe_Suelo = {
		Duracion = 0.45,
		Cuadros = {
			{ T = 0, Poses = { RightUpperArm = { 170, 0, 10 }, UpperTorso = { -10, 0, 0 } } },
			{
				T = 0.14,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 40, 0, 6 },
					RightLowerArm = { 20, 0, 0 },
					LeftUpperArm = { 40, 0, -10 },
					UpperTorso = { 38, 0, 0 },
					Head = { 8, 0, 0 },
					LowerTorso = { 12, 0, 0 },
					RightUpperLeg = { -40, 0, 0 },
					RightLowerLeg = { 60, 0, 0 },
					LeftUpperLeg = { 22, 0, 0 },
				},
			},
			{ T = 0.45, Easing = "Quad", Poses = { UpperTorso = { 30, 0, 0 } } },
		},
	},
	-- Los brazos se cierran sobre el pecho comprimiendo energía (gravedad).
	Comprimir = {
		Duracion = 0.4,
		Cuadros = {
			{ T = 0, Poses = { RightUpperArm = { 0, 0, 10 }, LeftUpperArm = { 0, 0, -10 } } },
			{
				T = 0.36,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 60, 0, -10 },
					LeftUpperArm = { 60, 0, 10 },
					RightLowerArm = { 80, 0, 0 },
					LeftLowerArm = { 80, 0, 0 },
					UpperTorso = { 14, 0, 0 },
					LowerTorso = { 6, 0, 0 },
					Head = { 10, 0, 0 },
					RightUpperLeg = { -20, 0, 0 },
					RightLowerLeg = { 30, 0, 0 },
					LeftUpperLeg = { -20, 0, 0 },
					LeftLowerLeg = { 30, 0, 0 },
				},
			},
		},
	},

	-- ===== Combo (cada golpe es muy rápido) =====
	Combo1 = { -- gancho de derecha
		Duracion = 0.3,
		Cuadros = {
			{
				T = 0,
				Poses = { RightUpperArm = { 30, 0, 10 }, UpperTorso = { 0, 30, 0 }, RightLowerArm = { 70, 0, 0 } },
			},
			{
				T = 0.1,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 95, 0, 0 },
					RightLowerArm = { 0, 0, 0 },
					UpperTorso = { 4, -34, 0 },
					LowerTorso = { 0, -14, 0 },
					RightUpperLeg = { 18, 0, 0 },
					LeftUpperLeg = { -18, 0, 0 },
				},
			},
			{ T = 0.3, Easing = "Quad", Poses = { RightUpperArm = { 40, 0, 6 }, UpperTorso = { 0, -6, 0 } } },
		},
	},
	Combo2 = { -- revés de izquierda
		Duracion = 0.3,
		Cuadros = {
			{
				T = 0,
				Poses = { LeftUpperArm = { 30, 0, -10 }, UpperTorso = { 0, -30, 0 }, LeftLowerArm = { 70, 0, 0 } },
			},
			{
				T = 0.1,
				Easing = "Cubic",
				Poses = {
					LeftUpperArm = { 95, 0, 0 },
					LeftLowerArm = { 0, 0, 0 },
					UpperTorso = { 4, 34, 0 },
					LowerTorso = { 0, 14, 0 },
					RightUpperLeg = { -18, 0, 0 },
					LeftUpperLeg = { 18, 0, 0 },
				},
			},
			{ T = 0.3, Easing = "Quad", Poses = { LeftUpperArm = { 40, 0, -6 }, UpperTorso = { 0, 6, 0 } } },
		},
	},
	Combo3 = { -- patada giratoria
		Duracion = 0.4,
		Cuadros = {
			{ T = 0, Poses = { UpperTorso = { 0, 40, 0 }, LowerTorso = { 0, 20, 0 }, RightUpperLeg = { 0, 0, 0 } } },
			{
				T = 0.16,
				Easing = "Cubic",
				Poses = {
					UpperTorso = { -10, -60, 0 },
					LowerTorso = { 0, -40, 0 },
					RightUpperLeg = { 100, 0, 8 },
					RightLowerLeg = { 5, 0, 0 },
					LeftUpperLeg = { -10, 0, 0 },
					LeftLowerLeg = { 20, 0, 0 },
					RightUpperArm = { 20, 0, 60 },
					LeftUpperArm = { 20, 0, -60 },
				},
			},
			{
				T = 0.4,
				Easing = "Quad",
				Poses = { RightUpperLeg = { 20, 0, 0 }, UpperTorso = { 0, -10, 0 }, LowerTorso = { 0, -6, 0 } },
			},
		},
	},
	Combo4 = { -- remate: salto con puñetazo doble
		Duracion = 0.55,
		Cuadros = {
			{
				T = 0,
				Poses = { RightUpperArm = { 160, 0, 10 }, LeftUpperArm = { 160, 0, -10 }, UpperTorso = { -14, 0, 0 } },
			},
			{
				T = 0.2,
				Easing = "Cubic",
				Poses = {
					RightUpperArm = { 80, 0, 6 },
					LeftUpperArm = { 80, 0, -6 },
					UpperTorso = { 34, 0, 0 },
					Head = { 10, 0, 0 },
					RightUpperLeg = { -35, 0, 0 },
					RightLowerLeg = { 50, 0, 0 },
					LeftUpperLeg = { 25, 0, 0 },
				},
			},
			{
				T = 0.55,
				Easing = "Quad",
				Poses = { RightUpperArm = { 60, 0, 6 }, LeftUpperArm = { 60, 0, -6 }, UpperTorso = { 20, 0, 0 } },
			},
		},
	},

	-- Reacción del que recibe un golpe: retrocede un instante.
	Impacto = {
		Duracion = 0.35,
		Cuadros = {
			{ T = 0, Poses = { UpperTorso = { 0, 0, 0 }, Head = { 0, 0, 0 } } },
			{
				T = 0.08,
				Easing = "Cubic",
				Poses = {
					UpperTorso = { -22, 6, 0 },
					Head = { -16, 0, 0 },
					RightUpperArm = { 20, 0, 30 },
					LeftUpperArm = { 20, 0, -30 },
				},
			},
			{ T = 0.35, Easing = "Quad", Poses = { UpperTorso = { 0, 0, 0 }, Head = { 0, 0, 0 } } },
		},
	},
}

-- Jerarquía del rig R15: cada parte con las partes que cuelgan de ella. El cliente la usa para construir
-- el árbol de Poses de cada cuadro.
Animaciones.Rig = {
	Nombre = "HumanoidRootPart",
	Hijos = {
		{
			Nombre = "LowerTorso",
			Hijos = {
				{
					Nombre = "UpperTorso",
					Hijos = {
						{ Nombre = "Head", Hijos = {} },
						{
							Nombre = "RightUpperArm",
							Hijos = { { Nombre = "RightLowerArm", Hijos = { { Nombre = "RightHand", Hijos = {} } } } },
						},
						{
							Nombre = "LeftUpperArm",
							Hijos = { { Nombre = "LeftLowerArm", Hijos = { { Nombre = "LeftHand", Hijos = {} } } } },
						},
					},
				},
				{
					Nombre = "RightUpperLeg",
					Hijos = { { Nombre = "RightLowerLeg", Hijos = { { Nombre = "RightFoot", Hijos = {} } } } },
				},
				{
					Nombre = "LeftUpperLeg",
					Hijos = { { Nombre = "LeftLowerLeg", Hijos = { { Nombre = "LeftFoot", Hijos = {} } } } },
				},
			},
		},
	},
}

return Animaciones
