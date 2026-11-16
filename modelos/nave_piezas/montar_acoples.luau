--!strict
-- Crea los Attachments de acople en las piezas de nave importadas (generado por nave_piezas.py: no editar a mano).
--
-- Uso: importa el .fbx de una o varias piezas, selecciónalas en el Explorer (el Model o sus MeshParts) y pega este
-- script en View → Command Bar. En cada MeshPart que tenga acoples crea un Attachment con el nombre del acople,
-- su Position y Orientation, y los atributos Tipo, Direccion, Brida y Acepta (tipos separados por comas).
--
-- Regla de encaje (la que debe aplicar el hangar):
--   * Una entrada encaja en una salida si el tipo de la salida está en Acepta de la entrada (o alguno es UNIVERSAL)
--     y su brida no es más grande que la de la salida.
--   * pieza.CFrame = salida.WorldCFrame * CFrame.Angles(0, math.pi, 0) * entrada.CFrame:Inverse()
--     (las normales quedan opuestas y los "arriba" coinciden). Con MeshParts el CFrame de la pieza es el de la
--     MeshPart que tiene la entrada; el resto del Model se mueve con ella (PivotTo).

local Selection = game:GetService("Selection")

type Acople = {
	malla: string,
	nombre: string,
	tipo: string,
	direccion: string,
	brida: number,
	pos: Vector3,
	rot: Vector3,
	acepta: { string },
}

local PIEZAS: { [string]: { Acople } } = {
	["casco_explorador_t1"] = {
		{ malla = "casco_explorador_t1", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.14, -0.356, 0.045), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_explorador_t1", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.14, -0.356, 0.045), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_explorador_t1", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.356, 5.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t1", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.354, -2.355), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t1", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.341, 3.245), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t1", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.028, -0.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_explorador_t1", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.091, -3.945), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_explorador_t2"] = {
		{ malla = "casco_explorador_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.14, -0.321, 0.055), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_explorador_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.14, -0.321, 0.055), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_explorador_t2", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.321, 5.355), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t2", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.39, -2.465), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t2", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.377, 3.415), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t2", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.992, -0.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_explorador_t2", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.055, -4.115), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_explorador_t3"] = {
		{ malla = "casco_explorador_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.098, 0.336, 0.065), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_explorador_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.098, 0.336, 0.065), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_explorador_t3", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, 0.336, 5.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t3", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.911, -2.575), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t3", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.013, 3.585), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_explorador_t3", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.321, -0.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_explorador_t3", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.192, -4.285), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_caza_t1"] = {
		{ malla = "casco_caza_t1", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.041, -0.322, 0.685), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_caza_t1", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.041, -0.322, 0.685), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_caza_t1", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.27, 7.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t1", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 0.918, -2.395), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t1", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.235, 5.025), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t1", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.83, 0.545), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_caza_t1", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.708, -4.745), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_caza_t2"] = {
		{ malla = "casco_caza_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.045, -0.27, 0.715), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_caza_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.045, -0.27, 0.715), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_caza_t2", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.218, 7.355), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t2", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 0.901, -2.475), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t2", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.287, 5.21), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t2", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.781, 0.57), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_caza_t2", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.57, -4.895), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_caza_t3"] = {
		{ malla = "casco_caza_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.949, 0.274, 0.745), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_caza_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(1.949, 0.274, 0.745), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_caza_t3", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, 0.326, 7.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t3", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.371, -2.555), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t3", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.844, 5.395), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t3", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.239, 0.595), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_caza_t3", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -0.861, -5.045), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_caza_t4"] = {
		{ malla = "casco_caza_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.099, -0.396, 0.775), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_caza_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.099, -0.396, 0.775), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_caza_t4", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.344, 7.855), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t4", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 0.672, -2.635), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t4", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.2, 5.58), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_caza_t4", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.895, 0.62), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_caza_t4", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.554, -5.195), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_transporte_t1"] = {
		{ malla = "casco_transporte_t1", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.4, -0.905, -2.395), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.4, -0.905, -2.395), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.4, -0.905, 2.725), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.4, -0.905, 2.725), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(1.342, -0.813, 8.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-1.342, -0.813, 8.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.713, -5.595), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_superior_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.757, 0.645), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.698, 6.245), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.378, -4.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.378, 3.845), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_transporte_t1", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.356, -6.945), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_transporte_t2"] = {
		{ malla = "casco_transporte_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.4, -0.905, -2.465), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.4, -0.905, -2.465), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.4, -0.905, 2.815), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.4, -0.905, 2.815), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(1.342, -0.813, 8.355), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-1.342, -0.813, 8.355), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.713, -5.765), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_superior_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.757, 0.67), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.698, 6.445), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.378, -4.28), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.378, 3.97), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_transporte_t2", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.356, -7.145), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_transporte_t3"] = {
		{ malla = "casco_transporte_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.4, 0.125, -2.535), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.4, 0.125, -2.535), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.4, 0.125, 2.905), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.4, 0.125, 2.905), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(1.342, 0.217, 8.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-1.342, 0.217, 8.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.524, -5.935), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_superior_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.787, 0.695), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.727, 6.645), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.348, -4.405), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.348, 4.095), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_transporte_t3", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.177, -7.345), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_bombardero_t2"] = {
		{ malla = "casco_bombardero_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.793, -0.639, -1.595), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.793, -0.639, -1.595), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.94, -0.639, 3.805), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.94, -0.639, 3.805), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(1.4, -0.639, 9.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-1.4, -0.639, 9.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.076, -5.555), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_torreta", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.65, 0.745), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.403, 7.045), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.981, -5.555), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.22, 6.325), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_bombardero_t2", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.158, -7.025), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_bombardero_t3"] = {
		{ malla = "casco_bombardero_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.888, -0.106, -1.675), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.888, -0.106, -1.675), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.04, -0.106, 4.025), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.04, -0.106, 4.025), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(1.44, -0.106, 9.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-1.44, -0.106, 9.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.681, -5.855), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_torreta", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.284, 0.795), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.025, 7.445), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.502, -5.855), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.752, 6.685), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_bombardero_t3", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.674, -7.385), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_fragata_t3"] = {
		{ malla = "casco_fragata_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.583, -0.629, -5.755), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.583, -0.629, -5.755), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.775, -0.629, -0.155), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.775, -0.629, -0.155), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_lateral_izq_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.978, -0.629, 6.005), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_lateral_der_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.978, -0.629, 6.005), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(2.228, 0.046, 14.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-2.227, 0.046, 14.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_motor_3", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -1.844, 14.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.771, -10.235), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_torreta_1", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.443, -4.075), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_torreta_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.576, 9.925), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.672, -5.755), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.876, 5.445), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_fragata_t3", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.279, -12.305), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_fragata_t4"] = {
		{ malla = "casco_fragata_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.677, -1.238, -5.955), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.677, -1.238, -5.955), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.806, -1.238, -0.155), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.806, -1.238, -0.155), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_lateral_izq_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-4.947, -1.238, 6.225), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_lateral_der_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(4.947, -1.238, 6.225), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(2.227, -0.563, 14.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-2.227, -0.563, 14.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_motor_3", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -2.453, 14.605), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 0.767, -10.595), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_torreta_1", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.796, -4.215), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_torreta_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.942, 10.285), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -4.236, -5.955), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -4.45, 5.645), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_fragata_t4", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.618, -12.725), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_crucero_t4"] = {
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-5.248, -1.621, -13.355), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(5.248, -1.621, -13.355), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-6.065, -1.621, -6.755), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(6.065, -1.621, -6.755), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_izq_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-6.265, -1.621, -0.155), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_der_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(6.265, -1.621, -0.155), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_izq_4", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-6.465, -1.621, 6.445), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_der_4", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(6.465, -1.621, 6.445), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_izq_5", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-6.43, -1.621, 13.045), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_lateral_der_5", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(6.43, -1.621, 13.045), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(2.838, -0.589, 22.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-2.838, -0.589, 22.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_motor_3", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(2.838, -2.825, 22.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_motor_4", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-2.838, -2.825, 22.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_motor_5", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -1.621, 22.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.259, -16.875), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_torreta_1", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.249, -8.955), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_torreta_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.382, -2.355), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_torreta_3", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.492, 13.925), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -5.261, -11.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -5.708, 2.045), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_inferior_3", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -5.774, 13.045), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_crucero_t4", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -4.705, -20.345), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_nave_nodriza_t5"] = {
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-11.597, 0, -12.157), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(11.597, 0, -12.157), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_lateral_izq_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-12.486, 0, -0.157), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_lateral_der_2", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(12.486, 0, -0.157), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_lateral_izq_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-12.163, 0, 11.843), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_lateral_der_3", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(12.163, 0, 11.843), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_motor_1", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(2.268, 0, 30.103), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_motor_2", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(-2.268, 0, 30.103), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_motor_3", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, 0, 30.103), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 3.268, -20.557), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_torreta_1", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 5.776, -0.157), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_torreta_2", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 4.923, 16.643), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_inferior_1", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.318, -12.157), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_inferior_2", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -3.701, 11.843), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_nave_nodriza_t5", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.199, -26.947), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_interceptor_t3"] = {
		{ malla = "casco_interceptor_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.65, 0.305, 2.405), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_interceptor_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(1.65, 0.305, 2.405), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_interceptor_t3", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, 0.305, 8.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_interceptor_t3", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.408, -1.435), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_interceptor_t3", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.825, 6.245), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_interceptor_t3", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.152, 2.405), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_interceptor_t3", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -0.89, -4.385), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_stealth_t4"] = {
		{ malla = "casco_stealth_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.643, -0.243, 1.765), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_stealth_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.643, -0.243, 1.765), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_stealth_t4", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.243, 8.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_stealth_t4", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 0.959, -2.395), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_stealth_t4", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.297, 5.605), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_stealth_t4", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.734, 1.445), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_stealth_t4", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.651, -3.745), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_alien_t5"] = {
		{ malla = "casco_alien_t5", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-3.308, -0.126, -1.955), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_alien_t5", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(3.308, -0.126, -1.955), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_alien_t5", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, -0.126, 9.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_alien_t5", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 2.213, -5.195), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_alien_t5", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.481, 6.325), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_alien_t5", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.7, -0.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_alien_t5", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.63, -7.025), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["casco_prototipo_t5"] = {
		{ malla = "casco_prototipo_t5", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(-2.949, 0, -0.155), rot = Vector3.new(0, 90, 0), acepta = {  } },
		{ malla = "casco_prototipo_t5", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "salida", brida = 1.6, pos = Vector3.new(2.949, 0, -0.155), rot = Vector3.new(0, -90, 0), acepta = {  } },
		{ malla = "casco_prototipo_t5", nombre = "acople_motor", tipo = "CASCO_TRASERO", direccion = "salida", brida = 2.4, pos = Vector3.new(0, 0, 8.105), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "casco_prototipo_t5", nombre = "acople_cabina", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.79, -3.995), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_prototipo_t5", nombre = "acople_superior_cola", tipo = "CASCO_SUPERIOR", direccion = "salida", brida = 2, pos = Vector3.new(0, 1.942, 5.605), rot = Vector3.new(90, 180, 0), acepta = {  } },
		{ malla = "casco_prototipo_t5", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -2.265, -0.155), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "casco_prototipo_t5", nombre = "acople_frontal", tipo = "CASCO_FRONTAL", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.73, -5.985), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["ala_corta_t1"] = {
		{ malla = "ala_corta_t1_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(2.153, 0, -0.012), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_corta_t1_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-1.753, -0.521, -0.073), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_corta_t1_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-2.153, 0, -0.012), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_corta_t1_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(1.753, -0.521, -0.073), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_corta_t2"] = {
		{ malla = "ala_corta_t2_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(2.339, 0, -0.107), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_corta_t2_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-1.939, -0.455, 0.263), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_corta_t2_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.039, -0.544, -0.057), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_corta_t2_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-2.339, 0, -0.107), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_corta_t2_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(1.939, -0.455, 0.263), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_corta_t2_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.039, -0.544, -0.057), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_media_t1"] = {
		{ malla = "ala_media_t1_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(3.475, 0, 0.014), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_media_t1_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-3.035, -0.42, -0.184), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t1_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.325, -0.542, -0.253), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t1_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-3.475, 0, 0.014), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_media_t1_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(3.035, -0.42, -0.184), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t1_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.325, -0.542, -0.253), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_media_t2"] = {
		{ malla = "ala_media_t2_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(3.627, -0.175, -0.684), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_media_t2_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-2.883, -0.52, 1.005), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t2_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.477, -0.681, -0.038), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t2_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-3.627, -0.175, -0.684), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_media_t2_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(2.883, -0.52, 1.005), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t2_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.477, -0.681, -0.038), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_media_t3"] = {
		{ malla = "ala_media_t3_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(3.726, 0, -0.604), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_media_t3_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-3.249, -0.266, 1.239), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t3_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.024, -0.439, 0.241), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t3_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-3.726, 0, -0.604), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_media_t3_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(3.249, -0.266, 1.239), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_media_t3_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.024, -0.439, 0.241), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_larga_t2"] = {
		{ malla = "ala_larga_t2_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(5.475, -0.105, -0.445), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_larga_t2_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-4.755, -0.373, 0.676), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t2_izq", nombre = "acople_motor_1", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(1.955, -0.043, 2.127), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "ala_larga_t2_izq", nombre = "acople_motor_2", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.785, 0.076, 2.161), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "ala_larga_t2_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-5.475, -0.105, -0.445), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_larga_t2_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(4.755, -0.373, 0.676), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t2_der", nombre = "acople_motor_1", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.955, -0.043, 2.127), rot = Vector3.new(0, -180, 0), acepta = {  } },
		{ malla = "ala_larga_t2_der", nombre = "acople_motor_2", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(1.785, 0.076, 2.161), rot = Vector3.new(0, -180, 0), acepta = {  } },
	},
	["ala_larga_t3"] = {
		{ malla = "ala_larga_t3_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(5.729, -0.237, -0.717), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_larga_t3_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-4.966, 0.241, 1.641), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t3_izq", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(1.359, -0.161, 2.179), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "ala_larga_t3_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-5.729, -0.237, -0.717), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_larga_t3_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(4.966, 0.241, 1.641), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t3_der", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.359, -0.161, 2.179), rot = Vector3.new(0, -180, 0), acepta = {  } },
	},
	["ala_larga_t4"] = {
		{ malla = "ala_larga_t4_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(5.628, 0.008, -0.843), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_larga_t4_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-4.602, -0.457, 1.922), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t4_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-2.293, -0.512, 1.333), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t4_izq", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(1.008, 0, 1.817), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "ala_larga_t4_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-5.628, 0.008, -0.843), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_larga_t4_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(4.602, -0.457, 1.922), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t4_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(2.293, -0.512, 1.333), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_larga_t4_der", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.008, 0, 1.817), rot = Vector3.new(0, -180, 0), acepta = {  } },
	},
	["ala_delta_t3"] = {
		{ malla = "ala_delta_t3_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(2.804, 0, -0.52), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_delta_t3_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-2.404, -0.53, 2.535), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t3_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.004, -0.601, 0.807), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t3_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-2.804, 0, -0.52), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_delta_t3_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(2.404, -0.53, 2.535), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t3_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.004, -0.601, 0.807), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_delta_t4"] = {
		{ malla = "ala_delta_t4_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(3.79, -0.196, -0.727), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_delta_t4_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-2.906, -0.831, 3.281), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t4_izq", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.674, -0.861, 1.594), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t4_izq", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(1.63, -0.276, 4.613), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "ala_delta_t4_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-3.79, -0.196, -0.727), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_delta_t4_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(2.906, -0.831, 3.281), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t4_der", nombre = "acople_hardpoint_1", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.674, -0.861, 1.594), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_delta_t4_der", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(-1.63, -0.276, 4.613), rot = Vector3.new(0, -180, 0), acepta = {  } },
	},
	["ala_variable_t4"] = {
		{ malla = "ala_variable_t4_izq.001", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(1, 0, -0.151), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_variable_t4_izq_extendida", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-2.93, -0.305, 0.565), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_variable_t4_izq_plegada", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-1.832, -0.305, 2.665), rot = Vector3.new(-90, 52, 0), acepta = {  } },
		{ malla = "ala_variable_t4_der.001", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-1, 0, -0.151), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_variable_t4_der_extendida", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(2.93, -0.305, 0.565), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_variable_t4_der_plegada", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(1.832, -0.305, 2.665), rot = Vector3.new(-90, -52, 0), acepta = {  } },
	},
	["ala_anular_t3"] = {
		{ malla = "ala_anular_t3_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(2.902, 0.243, 0.404), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_anular_t3_izq", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(-0.698, 0.243, 0.744), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "ala_anular_t3_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-0.698, -2.447, 0.004), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_anular_t3_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-2.902, 0.243, 0.404), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_anular_t3_der", nombre = "acople_motor", tipo = "ALA_MOTOR", direccion = "salida", brida = 1.6, pos = Vector3.new(0.698, 0.243, 0.744), rot = Vector3.new(0, -180, 0), acepta = {  } },
		{ malla = "ala_anular_t3_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(0.698, -2.447, 0.004), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_canard_t2"] = {
		{ malla = "ala_canard_t2_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(1.275, 0, -0.002), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_canard_t2_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-1.275, 0, -0.002), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["ala_alien_t5"] = {
		{ malla = "ala_alien_t5_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(4.285, 0, -0.9), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_alien_t5_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-2.629, -0.091, -0.13), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_alien_t5_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-4.285, 0, -0.9), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_alien_t5_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(2.629, -0.091, -0.13), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["ala_energia_t5"] = {
		{ malla = "ala_energia_t5_izq", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(3.855, 0, -0.558), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_energia_t5_izq", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(-3.345, -0.19, 1.442), rot = Vector3.new(-90, 0, 0), acepta = {  } },
		{ malla = "ala_energia_t5_der", nombre = "acople_raiz", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-3.855, 0, -0.558), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "ala_energia_t5_der", nombre = "acople_punta", tipo = "ALA_PUNTA", direccion = "salida", brida = 0.9, pos = Vector3.new(3.345, -0.19, 1.442), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["motor_quimico_t1"] = {
		{ malla = "motor_quimico_t1", nombre = "acople_montaje", tipo = "ALA_MOTOR", direccion = "entrada", brida = 1.6, pos = Vector3.new(0, 0, -1.92), rot = Vector3.new(0, 0, 0), acepta = { "ALA_MOTOR", "CASCO_TRASERO" } },
		{ malla = "motor_quimico_t1", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 1.97), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_quimico_t2"] = {
		{ malla = "motor_quimico_t2", nombre = "acople_montaje", tipo = "ALA_MOTOR", direccion = "entrada", brida = 1.6, pos = Vector3.new(0, 0, -2.17), rot = Vector3.new(0, 0, 0), acepta = { "ALA_MOTOR", "CASCO_TRASERO" } },
		{ malla = "motor_quimico_t2", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 2.22), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_ion_t2"] = {
		{ malla = "motor_ion_t2", nombre = "acople_montaje", tipo = "ALA_MOTOR", direccion = "entrada", brida = 1.6, pos = Vector3.new(0, 0, -1.82), rot = Vector3.new(0, 0, 0), acepta = { "ALA_MOTOR", "CASCO_TRASERO" } },
		{ malla = "motor_ion_t2", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 1.87), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_ion_t3"] = {
		{ malla = "motor_ion_t3", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, 0, -2.28), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_ion_t3", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 2.31), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_plasma_t3"] = {
		{ malla = "motor_plasma_t3", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, 0, -2.829), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_plasma_t3", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 2.861), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_plasma_t4"] = {
		{ malla = "motor_plasma_t4", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, -0.15, -2.754), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_plasma_t4", nombre = "acople_escape_1", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0.85, -0.15, 2.786), rot = Vector3.new(0, 180, 0), acepta = {  } },
		{ malla = "motor_plasma_t4", nombre = "acople_escape_2", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(-0.85, -0.15, 2.786), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_fusion_t4"] = {
		{ malla = "motor_fusion_t4", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, -0.061, -3.329), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_fusion_t4", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, -0.061, 3.361), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_fusion_t5"] = {
		{ malla = "motor_fusion_t5", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, 0, -3.45), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_fusion_t5", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 3.5), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_warp_t5"] = {
		{ malla = "motor_warp_t5.001", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0.195, 0, -3.225), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_warp_t5.001", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0.195, 0, 3.275), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_gravitacional_t5"] = {
		{ malla = "motor_gravitacional_t5.001", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, 0, -1.998), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_gravitacional_t5.001", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 1.922), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_auxiliar_t1"] = {
		{ malla = "motor_auxiliar_t1", nombre = "acople_montaje", tipo = "UNIVERSAL", direccion = "entrada", brida = 0.8, pos = Vector3.new(0, 0, -1.02), rot = Vector3.new(0, 0, 0), acepta = { "ALA_MOTOR", "CASCO_TRASERO", "UNIVERSAL" } },
		{ malla = "motor_auxiliar_t1", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 1.07), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_auxiliar_t3"] = {
		{ malla = "motor_auxiliar_t3", nombre = "acople_montaje", tipo = "UNIVERSAL", direccion = "entrada", brida = 0.8, pos = Vector3.new(0, 0, -1.179), rot = Vector3.new(0, 0, 0), acepta = { "ALA_MOTOR", "CASCO_TRASERO", "UNIVERSAL" } },
		{ malla = "motor_auxiliar_t3", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 1.211), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["motor_retro_t2"] = {
		{ malla = "motor_retro_t2", nombre = "acople_montaje", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.81, 0.425), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL" } },
		{ malla = "motor_retro_t2", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, -0.18, -1.525), rot = Vector3.new(0, 0, 0), acepta = {  } },
	},
	["motor_vtol_t3"] = {
		{ malla = "motor_vtol_t3.001", nombre = "acople_montaje", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.845, 0), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL" } },
		{ malla = "motor_vtol_t3_tobera", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, -0.855, 0), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
	["motor_turbo_t4"] = {
		{ malla = "motor_turbo_t4", nombre = "acople_montaje", tipo = "CASCO_TRASERO", direccion = "entrada", brida = 2.4, pos = Vector3.new(0, 0, -2.745), rot = Vector3.new(0, 0, 0), acepta = { "CASCO_TRASERO" } },
		{ malla = "motor_turbo_t4", nombre = "acople_escape", tipo = "MOTOR_ESCAPE", direccion = "salida", brida = 0, pos = Vector3.new(0, 0, 2.645), rot = Vector3.new(0, 180, 0), acepta = {  } },
	},
	["laser_ligero_t1"] = {
		{ malla = "laser_ligero_t1", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.955, 1.565), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "laser_ligero_t1", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.64, -0.155, 1.565), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_ligero_t1", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.64, -0.155, 1.565), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["laser_ligero_t2"] = {
		{ malla = "laser_ligero_t2", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.955, 1.715), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "laser_ligero_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.64, -0.155, 1.715), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_ligero_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.64, -0.155, 1.715), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["laser_doble_t2"] = {
		{ malla = "laser_doble_t2", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.955, 1.665), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "laser_doble_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.64, -0.155, 1.665), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_doble_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.64, -0.155, 1.665), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["laser_pesado_t3"] = {
		{ malla = "laser_pesado_t3", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.005, 2.015), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "laser_pesado_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.79, -0.155, 2.015), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_pesado_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.79, -0.155, 2.015), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_pesado_t3", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 3.155), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["laser_pesado_t4"] = {
		{ malla = "laser_pesado_t4", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.005, 2.515), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "laser_pesado_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.79, -0.155, 2.515), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_pesado_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.79, -0.155, 2.515), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_pesado_t4", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 3.655), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["laser_gatling_t3"] = {
		{ malla = "laser_gatling_t3.001", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0.174, 1.005, 0.8), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "laser_gatling_t3.001", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.566, -0.155, 0.8), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "laser_gatling_t3.001", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.914, -0.155, 0.8), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["misiles_pod_t1"] = {
		{ malla = "misiles_pod_t1", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.955, 0.5), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "misiles_pod_t1", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.93, -0.155, 0.5), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "misiles_pod_t1", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.93, -0.155, 0.5), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["misiles_pod_t2"] = {
		{ malla = "misiles_pod_t2", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.965, 0.6), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "misiles_pod_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-1.55, -0.145, 0.6), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "misiles_pod_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(1.55, -0.145, 0.6), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["misiles_rack_t3"] = {
		{ malla = "misiles_rack_t3", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.122, 0.8), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "misiles_rack_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-1.63, -0.05, 0.8), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "misiles_rack_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(1.63, -0.05, 0.8), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["torpedo_t3"] = {
		{ malla = "torpedo_t3", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.105, 1.05), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "torpedo_t3", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.74, -0.155, 1.05), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "torpedo_t3", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.74, -0.155, 1.05), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "torpedo_t3", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 2.29), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["torpedo_t4"] = {
		{ malla = "torpedo_t4", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.105, 1.05), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "torpedo_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.74, -0.155, 1.05), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "torpedo_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.74, -0.155, 1.05), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "torpedo_t4", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 2.29), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["canon_balistico_t2"] = {
		{ malla = "canon_balistico_t2", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.955, 3.37), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "canon_balistico_t2", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.69, -0.155, 3.37), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "canon_balistico_t2", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.69, -0.155, 3.37), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "canon_balistico_t2", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 4.61), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["canon_balistico_t4"] = {
		{ malla = "canon_balistico_t4.001", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.105, 4.536), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "canon_balistico_t4.001", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.84, -0.155, 4.536), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "canon_balistico_t4.001", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.84, -0.155, 4.536), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "canon_balistico_t4.001", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 5.776), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["torreta_auto_t3"] = {
		{ malla = "torreta_auto_t3.001", nombre = "acople_base", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -0.295, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["torreta_auto_t4"] = {
		{ malla = "torreta_auto_t4.001", nombre = "acople_base", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -0.295, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["railgun_t4"] = {
		{ malla = "railgun_t4", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.105, 4.6), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "railgun_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.89, -0.155, 4.6), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "railgun_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.89, -0.155, 4.6), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "railgun_t4", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.155, 5.94), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["railgun_t5"] = {
		{ malla = "railgun_t5", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.731, 6.099), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "railgun_t5", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.89, -0.529, 6.099), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "railgun_t5", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.89, -0.529, 6.099), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "railgun_t5", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.529, 7.439), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["canon_plasma_t4"] = {
		{ malla = "canon_plasma_t4", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.06, 1.405), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "canon_plasma_t4", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.84, -0.2, 1.405), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "canon_plasma_t4", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.84, -0.2, 1.405), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "canon_plasma_t4", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.2, 2.545), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["arma_alien_t5"] = {
		{ malla = "arma_alien_t5", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 0.978, 1.979), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "arma_alien_t5", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.74, -0.182, 1.979), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "arma_alien_t5", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.74, -0.182, 1.979), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
	},
	["desintegrador_t5"] = {
		{ malla = "desintegrador_t5", nombre = "acople_colgar", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.06, 1.565), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "UNIVERSAL" } },
		{ malla = "desintegrador_t5", nombre = "acople_lateral_izq", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(-0.84, -0.2, 1.565), rot = Vector3.new(0, 90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "desintegrador_t5", nombre = "acople_lateral_der", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.84, -0.2, 1.565), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL" } },
		{ malla = "desintegrador_t5", nombre = "acople_trasero", tipo = "CASCO_FRONTAL", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, -0.2, 2.805), rot = Vector3.new(0, 180, 0), acepta = { "CASCO_FRONTAL" } },
	},
	["blindaje_extra_t1"] = {
		{ malla = "blindaje_extra_t1", nombre = "acople_montaje", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.305, 0, 0), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL", "UNIVERSAL" } },
	},
	["blindaje_extra_t2"] = {
		{ malla = "blindaje_extra_t2", nombre = "acople_montaje", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.505, 0, 0), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL", "UNIVERSAL" } },
	},
	["blindaje_reactivo_t3"] = {
		{ malla = "blindaje_reactivo_t3", nombre = "acople_montaje", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.422, 0, 0), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL", "UNIVERSAL" } },
	},
	["blindaje_energetico_t4"] = {
		{ malla = "blindaje_energetico_t4", nombre = "acople_montaje", tipo = "CASCO_LATERAL", direccion = "entrada", brida = 1.6, pos = Vector3.new(0.555, 0, 0), rot = Vector3.new(0, -90, 0), acepta = { "CASCO_LATERAL", "UNIVERSAL" } },
	},
	["generador_escudo_t2"] = {
		{ malla = "generador_escudo_t2", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -0.645, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["generador_escudo_t3"] = {
		{ malla = "generador_escudo_t3", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -0.645, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["generador_escudo_t4"] = {
		{ malla = "generador_escudo_t4", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -0.775, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["generador_escudo_t5"] = {
		{ malla = "generador_escudo_t5", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -0.68, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["contramedidas_t2"] = {
		{ malla = "contramedidas_t2", nombre = "acople_montaje", tipo = "UNIVERSAL", direccion = "entrada", brida = 0.8, pos = Vector3.new(0.02, -0.649, 0), rot = Vector3.new(-90, 0, 0), acepta = { "ALA_MOTOR", "ALA_PUNTA", "CASCO_FRONTAL", "CASCO_INFERIOR", "CASCO_LATERAL", "CASCO_SUPERIOR", "CASCO_TRASERO", "UNIVERSAL" } },
	},
	["contramedidas_t4"] = {
		{ malla = "contramedidas_t4", nombre = "acople_montaje", tipo = "UNIVERSAL", direccion = "entrada", brida = 0.8, pos = Vector3.new(0, -1.575, 0.026), rot = Vector3.new(-90, 0, 0), acepta = { "ALA_MOTOR", "ALA_PUNTA", "CASCO_FRONTAL", "CASCO_INFERIOR", "CASCO_LATERAL", "CASCO_SUPERIOR", "CASCO_TRASERO", "UNIVERSAL" } },
	},
	["cabina_abierta_t1"] = {
		{ malla = "cabina_abierta_t1", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.32, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_cerrada_t1"] = {
		{ malla = "cabina_cerrada_t1", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.22, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_caza_t2"] = {
		{ malla = "cabina_caza_t2", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.17, -0.05), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_caza_t3"] = {
		{ malla = "cabina_caza_t3", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.17, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_caza_t4"] = {
		{ malla = "cabina_caza_t4", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.17, 0.152), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_transporte_t2"] = {
		{ malla = "cabina_transporte_t2", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.281, 0.023), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_puente_t3"] = {
		{ malla = "cabina_puente_t3", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -2.07, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_puente_t4"] = {
		{ malla = "cabina_puente_t4", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.685, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_alien_t5"] = {
		{ malla = "cabina_alien_t5", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.27, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["cabina_ia_t5"] = {
		{ malla = "cabina_ia_t5", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.339, 0), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR" } },
	},
	["tren_aterrizaje_fijo_t1"] = {
		{ malla = "tren_aterrizaje_fijo_t1", nombre = "acople_montaje", tipo = "CASCO_INFERIOR", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, 1.078, 0.21), rot = Vector3.new(90, 180, 0), acepta = { "CASCO_INFERIOR" } },
	},
	["tren_aterrizaje_retractil_t2"] = {
		{ malla = "tren_aterrizaje_retractil_t2.001", nombre = "acople_montaje", tipo = "CASCO_INFERIOR", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, 0.295, 0), rot = Vector3.new(90, 180, 0), acepta = { "CASCO_INFERIOR" } },
	},
	["tren_aterrizaje_hover_t3"] = {
		{ malla = "tren_aterrizaje_hover_t3", nombre = "acople_montaje", tipo = "CASCO_INFERIOR", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, 0.546, 0), rot = Vector3.new(90, 180, 0), acepta = { "CASCO_INFERIOR" } },
	},
	["estabilizador_vertical_t1"] = {
		{ malla = "estabilizador_vertical_t1", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.37, -0.363), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["estabilizador_vertical_t3"] = {
		{ malla = "estabilizador_vertical_t3", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.577, -0.48), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["estabilizador_doble_t2"] = {
		{ malla = "estabilizador_doble_t2", nombre = "acople_montaje", tipo = "CASCO_SUPERIOR", direccion = "entrada", brida = 2, pos = Vector3.new(0, -1.049, -0.2), rot = Vector3.new(-90, 0, 0), acepta = { "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["tanque_combustible_t1"] = {
		{ malla = "tanque_combustible_t1", nombre = "acople_montaje", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1, 0), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL" } },
	},
	["tanque_combustible_t3"] = {
		{ malla = "tanque_combustible_t3", nombre = "acople_montaje", tipo = "ALA_PUNTA", direccion = "entrada", brida = 0.9, pos = Vector3.new(0, 1.255, -0.25), rot = Vector3.new(90, 180, 0), acepta = { "ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL" } },
	},
	["radar_t2"] = {
		{ malla = "radar_t2.001", nombre = "acople_montaje", tipo = "UNIVERSAL", direccion = "entrada", brida = 0.8, pos = Vector3.new(0, -0.745, 0), rot = Vector3.new(-90, 0, 0), acepta = { "ALA_PUNTA", "CASCO_FRONTAL", "CASCO_INFERIOR", "CASCO_LATERAL", "CASCO_SUPERIOR", "UNIVERSAL" } },
	},
	["bahia_carga_t3"] = {
		{ malla = "bahia_carga_t3", nombre = "acople_montaje", tipo = "CASCO_INFERIOR", direccion = "entrada", brida = 1.2, pos = Vector3.new(0, 1.515, 0), rot = Vector3.new(90, 180, 0), acepta = { "CASCO_INFERIOR" } },
		{ malla = "bahia_carga_t3", nombre = "acople_inferior", tipo = "CASCO_INFERIOR", direccion = "salida", brida = 1.2, pos = Vector3.new(0, -1.515, 0), rot = Vector3.new(-90, 0, 0), acepta = {  } },
	},
}

-- Índice malla -> lista de acoples
local porMalla: { [string]: { Acople } } = {}
for _, lista in PIEZAS do
	for _, a in lista do
		porMalla[a.malla] = porMalla[a.malla] or {}
		table.insert(porMalla[a.malla], a)
	end
end

local creados = 0
local function montar(parte: Instance)
	if not parte:IsA("MeshPart") then
		return
	end
	local lista = porMalla[parte.Name]
	if not lista then
		return
	end
	for _, a in lista do
		local att = parte:FindFirstChild(a.nombre)
		if not (att and att:IsA("Attachment")) then
			att = Instance.new("Attachment")
			att.Name = a.nombre
			att.Parent = parte
		end
		local at = att :: Attachment
		at.Position = a.pos
		at.Orientation = a.rot
		at:SetAttribute("Tipo", a.tipo)
		at:SetAttribute("Direccion", a.direccion)
		at:SetAttribute("Brida", a.brida)
		at:SetAttribute("Acepta", table.concat(a.acepta, ","))
		creados += 1
	end
end

for _, sel in Selection:Get() do
	montar(sel)
	for _, d in sel:GetDescendants() do
		montar(d)
	end
end
print(string.format("[montar_acoples] %d acoples creados o actualizados", creados))
