--!strict
--[[
	GENERADO por herramientas/generar_recursos_humanos.luau monstruo: no lo edites a mano.

	Recursos subidos del monstruo (cuernos y deformaciones):
	  · Piezas[elemento]: las piezas 3D de cada elemento (modelos/personaje_monstruo).
	    Malla: la malla subida. Parte: la parte del R6 a la que va. Rol: de qué color se pinta (ver DatosHumanos.Roles).
	    Centro: dónde va su centro respecto al centro de la parte (studs). Tamano: su tamaño en studs (las mallas
	    llegan de Roblox a otra escala: se les pone este tamaño al crearlas).
	  · Imagenes[nombre]: las texturas de la cara (Decals) y la rueda de color del editor.
]]

export type Pieza = {
	Nombre: string,
	Malla: string,
	Parte: string,
	Rol: string,
	Centro: { number },
	Tamano: { number },
}

local Recursos = {}

Recursos.Piezas = {
	Cuerno_Astas = {
		{
			Nombre = "Cuerno_Astas__Cabeza__Cuerno",
			Malla = "rbxassetid://133214672138127",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 1.1926, 0.1136 },
			Tamano = { 1.7637, 1.3399, 0.2868 },
		},
	},
	Cuerno_Carnero = {
		{
			Nombre = "Cuerno_Carnero__Cabeza__Cuerno",
			Malla = "rbxassetid://101652781449936",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 0.4559, 0.2675 },
			Tamano = { 1.6006, 1.0935, 1.2158 },
		},
	},
	Cuerno_Corona = {
		{
			Nombre = "Cuerno_Corona__Cabeza__Cuerno",
			Malla = "rbxassetid://108105902946027",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 0.8895, 0 },
			Tamano = { 1.3396, 0.7791, 1.3395 },
		},
	},
	Cuerno_Curvos = {
		{
			Nombre = "Cuerno_Curvos__Cabeza__Cuerno",
			Malla = "rbxassetid://112802561179568",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 1.0993, -0.0429 },
			Tamano = { 1.4344, 1.2608, 0.3141 },
		},
	},
	Cuerno_Diablillo = {
		{
			Nombre = "Cuerno_Diablillo__Cabeza__Cuerno",
			Malla = "rbxassetid://90177978980693",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 0.7153, -0.1 },
			Tamano = { 1.1067, 0.4362, 0.2556 },
		},
	},
	Cuerno_Rectos = {
		{
			Nombre = "Cuerno_Rectos__Cabeza__Cuerno",
			Malla = "rbxassetid://106462240820654",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 1.0898, 0.0084 },
			Tamano = { 1.3794, 1.1526, 0.3228 },
		},
	},
	Cuerno_Retorcidos = {
		{
			Nombre = "Cuerno_Retorcidos__Cabeza__Cuerno",
			Malla = "rbxassetid://79567305636578",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0.0165, 1.2563, 0.1749 },
			Tamano = { 1.3049, 1.6028, 0.7678 },
		},
	},
	Cuerno_Unicornio = {
		{
			Nombre = "Cuerno_Unicornio__Cabeza__Cuerno",
			Malla = "rbxassetid://70464482460802",
			Parte = "Head",
			Rol = "Cuerno",
			Centro = { 0, 1.0553, -0.7096 },
			Tamano = { 0.3, 1.2552, 0.782 },
		},
	},
	Deformacion_BrazoHinchado = {
		{
			Nombre = "Deformacion_BrazoHinchado__BrazoD__Hueso",
			Malla = "rbxassetid://137868810658084",
			Parte = "Right Arm",
			Rol = "Hueso",
			Centro = { 0.5, 0.35, -0.6 },
			Tamano = { 0.2663, 0.2663, 0.2 },
		},
		{
			Nombre = "Deformacion_BrazoHinchado__BrazoD__Piel",
			Malla = "rbxassetid://129716335304634",
			Parte = "Right Arm",
			Rol = "Piel",
			Centro = { 0.15, 0, 0 },
			Tamano = { 1.8524, 2.5, 1.9 },
		},
	},
	Deformacion_Costillas = {
		{
			Nombre = "Deformacion_Costillas__Torso__Hueso",
			Malla = "rbxassetid://81357542841982",
			Parte = "Torso",
			Rol = "Hueso",
			Centro = { 0, 0.0486, -0.3456 },
			Tamano = { 2.112, 1.9027, 0.6172 },
		},
	},
	Deformacion_Espinas = {
		{
			Nombre = "Deformacion_Espinas__Torso__Hueso",
			Malla = "rbxassetid://72524742060432",
			Parte = "Torso",
			Rol = "Hueso",
			Centro = { 0, -0.033, 0.8226 },
			Tamano = { 0.2425, 2.0056, 0.7131 },
		},
	},
	Deformacion_Garras = {
		{
			Nombre = "Deformacion_Garras__BrazoD__Hueso",
			Malla = "rbxassetid://115442246050193",
			Parte = "Right Arm",
			Rol = "Hueso",
			Centro = { 0.0137, -1.4625, -0.1358 },
			Tamano = { 0.9059, 0.9525, 0.31 },
		},
		{
			Nombre = "Deformacion_Garras__BrazoI__Hueso",
			Malla = "rbxassetid://100822808303698",
			Parte = "Left Arm",
			Rol = "Hueso",
			Centro = { 0.0137, -1.4625, -0.1358 },
			Tamano = { 0.9059, 0.9525, 0.31 },
		},
	},
	Deformacion_Hombros = {
		{
			Nombre = "Deformacion_Hombros__BrazoD__Hueso",
			Malla = "rbxassetid://138797420462576",
			Parte = "Right Arm",
			Rol = "Hueso",
			Centro = { 0.4305, 1.0539, 0 },
			Tamano = { 0.5098, 0.9339, 1.5422 },
		},
		{
			Nombre = "Deformacion_Hombros__BrazoI__Hueso",
			Malla = "rbxassetid://77975468468460",
			Parte = "Left Arm",
			Rol = "Hueso",
			Centro = { -0.4305, 1.0539, 0 },
			Tamano = { 0.5098, 0.9339, 1.5422 },
		},
	},
	Deformacion_Joroba = {
		{
			Nombre = "Deformacion_Joroba__Torso__Piel",
			Malla = "rbxassetid://116441433522629",
			Parte = "Torso",
			Rol = "Piel",
			Centro = { 0, 0.6, 0.75 },
			Tamano = { 2.0162, 1.6742, 1.4 },
		},
	},
	Deformacion_Placas = {
		{
			Nombre = "Deformacion_Placas__BrazoD__Hueso",
			Malla = "rbxassetid://107940306543176",
			Parte = "Right Arm",
			Rol = "Hueso",
			Centro = { 0, -0.35, 0 },
			Tamano = { 0.75, 0.9, 1.12 },
		},
		{
			Nombre = "Deformacion_Placas__BrazoI__Hueso",
			Malla = "rbxassetid://115164896220365",
			Parte = "Left Arm",
			Rol = "Hueso",
			Centro = { 0, -0.35, 0 },
			Tamano = { 0.75, 0.9, 1.12 },
		},
		{
			Nombre = "Deformacion_Placas__PiernaD__Hueso",
			Malla = "rbxassetid://76860333725415",
			Parte = "Right Leg",
			Rol = "Hueso",
			Centro = { 0, -0.0625, -0.56 },
			Tamano = { 0.9, 1.725, 0.16 },
		},
		{
			Nombre = "Deformacion_Placas__PiernaI__Hueso",
			Malla = "rbxassetid://93345383828014",
			Parte = "Left Leg",
			Rol = "Hueso",
			Centro = { 0, -0.0625, -0.56 },
			Tamano = { 0.9, 1.725, 0.16 },
		},
		{
			Nombre = "Deformacion_Placas__Torso__Hueso",
			Malla = "rbxassetid://92678292429799",
			Parte = "Torso",
			Rol = "Hueso",
			Centro = { 0, 0.3, -0.56 },
			Tamano = { 1.6, 1, 0.14 },
		},
	},
	Deformacion_Vertebras = {
		{
			Nombre = "Deformacion_Vertebras__Torso__Hueso",
			Malla = "rbxassetid://72461176512056",
			Parte = "Torso",
			Rol = "Hueso",
			Centro = { 0, 0.15, 0.53 },
			Tamano = { 0.3234, 2.2283, 0.34 },
		},
	},
} :: { [string]: { Pieza } }

Recursos.Imagenes = {
	Boca_Abierta = "rbxassetid://131632654334111",
	Boca_Cerrada = "rbxassetid://73073006664321",
	Boca_Colmillos = "rbxassetid://95077820262535",
	Boca_Cosida = "rbxassetid://71107135211485",
	Boca_SonrisaRota = "rbxassetid://103535099502576",
	Boca_Vertical = "rbxassetid://103658100523025",
	Marcas_Costuras = "rbxassetid://117579281394827",
	Marcas_Espiral = "rbxassetid://104579742274084",
	Marcas_Grietas = "rbxassetid://106638476827055",
	Marcas_Ojos = "rbxassetid://82440694789467",
	Marcas_Runas = "rbxassetid://86812583011992",
	Marcas_Venas = "rbxassetid://137055646341382",
	Ojos_Cuatro = "rbxassetid://95813495881379",
	Ojos_Cuencas = "rbxassetid://99699336865974",
	Ojos_Dos = "rbxassetid://122983730698814",
	Ojos_Grandes = "rbxassetid://79669507345040",
	Ojos_Multiples = "rbxassetid://106249192665999",
	Ojos_Rendija = "rbxassetid://118413871132983",
	Ojos_Tres = "rbxassetid://104248395643368",
	Ojos_Uno = "rbxassetid://133465276508685",
} :: { [string]: string }

return Recursos
