--!strict
--[[
	Poderes: define QUÉ hace cada habilidad (daño, alcance, cooldown, tiempos...). Cómo se VE está en
	Datos/EfectosVFX y cómo se MUEVE el personaje en Datos/Animaciones.

	Este módulo es la fuente de verdad que leen los dos lados:
	  - el SERVIDOR lo usa para decidir (cooldown, energía, alcance, forma del golpe, daño...);
	  - el CLIENTE lo usa para la interfaz (nombre, tecla, cooldown) y para sincronizar los efectos.
	El cliente nunca decide el daño: aunque cambiara estos números en su copia, el servidor usa los suyos.

	Es solo datos (sin tipos de Roblox), así que también se puede cargar en las pruebas.

	Campos de una habilidad:
	  Id, Nombre, Poder ("Rayo" | "Gravedad" | "Cuerpo"), Categoria ("Basico" | "Fuerte" | "Definitiva" | "Combo")
	  Tecla       Nombre de un Enum.KeyCode, o "Click" para el botón principal del ratón.
	  Energia     Coste de energía.
	  Cooldown    Segundos hasta poder repetirla.
	  Rango       Alcance máximo en studs.
	  Forma       Cómo se decide a quién golpea (ver Reglas.EnForma):
	                "Linea"   un haz desde el lanzador hasta el punto de destino, de ancho 2 * Radio;
	                "Area"    una esfera de Radio studs centrada en el punto de destino;
	                "Cono"    delante del lanzador, hasta Rango, dentro de Angulo grados;
	                "Circulo" una esfera de Radio studs centrada en el propio lanzador.
	  Radio, Angulo
	  AlSuelo     Si es true, el punto de destino se coloca a la distancia pedida (golpes de área);
	              si es false, el proyectil recorre siempre todo el Rango en línea recta.
	  Dano        Vida que quita a cada enemigo golpeado.
	  Empuje      { Horizontal, Vertical, Atrae? }  Impulso que recibe el golpeado. Atrae = hacia el destino.
	  Aturdimiento Segundos que el golpeado no puede usar habilidades.
	  Tiempos     { Carga, Viaje, Recuperacion }  segundos:
	                Carga        desde que se pide hasta que sale el poder;
	                Viaje        tiempo de vuelo del proyectil (el golpe llega a Carga + Viaje);
	                Recuperacion pausa extra, tras el golpe, antes de que el lanzador pueda volver a actuar.
	  Inmoviliza  El lanzador no se mueve mientras dura Carga + Viaje + Recuperacion.
	  Invulnerable El lanzador no recibe daño durante ese mismo tiempo.
	  Animaciones { Carga, Lanzamiento }  nombres de Datos/Animaciones (y de Recursos.Animaciones).
	  Efecto      Nombre de la receta de Datos/EfectosVFX.
	  Cinematica  (opcional) nombre de la cinemática de cámara de Datos/Cinematicas.
]]

export type Empuje = { Horizontal: number, Vertical: number, Atrae: boolean? }

export type Habilidad = {
	Id: string,
	Nombre: string,
	Descripcion: string,
	Poder: string,
	Categoria: string,
	Tecla: string,
	Energia: number,
	Cooldown: number,
	Rango: number,
	Forma: string,
	Radio: number,
	Angulo: number?,
	AlSuelo: boolean,
	Dano: number,
	Empuje: Empuje,
	Aturdimiento: number,
	Tiempos: { Carga: number, Viaje: number, Recuperacion: number },
	Inmoviliza: boolean,
	Invulnerable: boolean,
	Animaciones: { Carga: string?, Lanzamiento: string? },
	Efecto: string,
	Cinematica: string?,
	Combo: { Paso: number, Total: number, Ventana: number }?,
}

local Poderes = {}

local habilidades: { [string]: Habilidad } = {
	-- ===================================================================================================
	-- RAYO
	-- ===================================================================================================
	Rayo_Basico = {
		Id = "Rayo_Basico",
		Nombre = "Chispa Voltaica",
		Descripcion = "Lanza un rayo veloz en línea recta.",
		Poder = "Rayo",
		Categoria = "Basico",
		Tecla = "Z",
		Energia = 8,
		Cooldown = 1.2,
		Rango = 70,
		Forma = "Linea",
		Radio = 3.5,
		AlSuelo = false,
		Dano = 14,
		Empuje = { Horizontal = 14, Vertical = 10 },
		Aturdimiento = 0.3,
		Tiempos = { Carga = 0.28, Viaje = 0.1, Recuperacion = 0.15 },
		Inmoviliza = false,
		Invulnerable = false,
		Animaciones = { Carga = "Alzar_Mano", Lanzamiento = "Disparo_Frente" },
		Efecto = "Rayo_Basico",
	},
	Rayo_Fuerte = {
		Id = "Rayo_Fuerte",
		Nombre = "Trueno Divino",
		Descripcion = "Invoca un rayo del cielo que cae sobre la zona señalada.",
		Poder = "Rayo",
		Categoria = "Fuerte",
		Tecla = "X",
		Energia = 25,
		Cooldown = 6,
		Rango = 55,
		Forma = "Area",
		Radio = 14,
		AlSuelo = true,
		Dano = 38,
		Empuje = { Horizontal = 34, Vertical = 30 },
		Aturdimiento = 0.8,
		Tiempos = { Carga = 0.75, Viaje = 0.12, Recuperacion = 0.4 },
		Inmoviliza = true,
		Invulnerable = false,
		Animaciones = { Carga = "Alzar_Cielo", Lanzamiento = "Golpe_Suelo" },
		Efecto = "Rayo_Fuerte",
	},
	Rayo_Definitiva = {
		Id = "Rayo_Definitiva",
		Nombre = "Tormenta Celestial",
		Descripcion = "Desata una tormenta eléctrica devastadora sobre una gran zona.",
		Poder = "Rayo",
		Categoria = "Definitiva",
		Tecla = "C",
		Energia = 80,
		Cooldown = 45,
		Rango = 70,
		Forma = "Area",
		Radio = 30,
		AlSuelo = true,
		Dano = 110,
		Empuje = { Horizontal = 60, Vertical = 55 },
		Aturdimiento = 2,
		Tiempos = { Carga = 2.8, Viaje = 0.25, Recuperacion = 0.9 },
		Inmoviliza = true,
		Invulnerable = true,
		Animaciones = { Carga = "Alzar_Cielo", Lanzamiento = "Lanzar_Cielo" },
		Efecto = "Rayo_Definitiva",
		Cinematica = "Rayo_Definitiva",
	},

	-- ===================================================================================================
	-- GRAVEDAD
	-- ===================================================================================================
	Gravedad_Basico = {
		Id = "Gravedad_Basico",
		Nombre = "Pulso Gravitatorio",
		Descripcion = "Lanza una esfera de gravedad que aplasta lo que toca.",
		Poder = "Gravedad",
		Categoria = "Basico",
		Tecla = "V",
		Energia = 8,
		Cooldown = 1.4,
		Rango = 60,
		Forma = "Linea",
		Radio = 4.5,
		AlSuelo = false,
		Dano = 15,
		Empuje = { Horizontal = 6, Vertical = -8, Atrae = true },
		Aturdimiento = 0.4,
		Tiempos = { Carga = 0.32, Viaje = 0.35, Recuperacion = 0.15 },
		Inmoviliza = false,
		Invulnerable = false,
		Animaciones = { Carga = "Comprimir", Lanzamiento = "Disparo_Frente" },
		Efecto = "Gravedad_Basico",
	},
	Gravedad_Fuerte = {
		Id = "Gravedad_Fuerte",
		Nombre = "Aplastamiento",
		Descripcion = "Multiplica la gravedad en una zona y la hunde contra el suelo.",
		Poder = "Gravedad",
		Categoria = "Fuerte",
		Tecla = "B",
		Energia = 25,
		Cooldown = 7,
		Rango = 50,
		Forma = "Area",
		Radio = 16,
		AlSuelo = true,
		Dano = 40,
		Empuje = { Horizontal = 0, Vertical = -45 },
		Aturdimiento = 1.2,
		Tiempos = { Carga = 0.85, Viaje = 0.1, Recuperacion = 0.5 },
		Inmoviliza = true,
		Invulnerable = false,
		Animaciones = { Carga = "Comprimir", Lanzamiento = "Golpe_Suelo" },
		Efecto = "Gravedad_Fuerte",
	},
	Gravedad_Definitiva = {
		Id = "Gravedad_Definitiva",
		Nombre = "Singularidad",
		Descripcion = "Abre un agujero negro que arrastra a los enemigos y colapsa en una explosión.",
		Poder = "Gravedad",
		Categoria = "Definitiva",
		Tecla = "N",
		Energia = 80,
		Cooldown = 50,
		Rango = 60,
		Forma = "Area",
		Radio = 32,
		AlSuelo = true,
		Dano = 105,
		Empuje = { Horizontal = 40, Vertical = 20, Atrae = true },
		Aturdimiento = 2,
		Tiempos = { Carga = 3.0, Viaje = 0.3, Recuperacion = 0.9 },
		Inmoviliza = true,
		Invulnerable = true,
		Animaciones = { Carga = "Alzar_Cielo", Lanzamiento = "Golpe_Suelo" },
		Efecto = "Gravedad_Definitiva",
		Cinematica = "Gravedad_Definitiva",
	},

	-- ===================================================================================================
	-- COMBO CUERPO A CUERPO (4 golpes). El cliente solo pide "Combo"; el servidor decide qué golpe toca
	-- (ver Servicio de combate) y esos ids internos (Combo1..Combo4) NO se pueden pedir por red.
	-- Cooldown = tiempo mínimo hasta el siguiente golpe. El último deja un cooldown largo.
	-- ===================================================================================================
	Combo1 = {
		Id = "Combo1",
		Nombre = "Golpe 1",
		Descripcion = "Gancho rápido.",
		Poder = "Cuerpo",
		Categoria = "Combo",
		Tecla = "Click",
		Energia = 0,
		Cooldown = 0.36,
		Rango = 7,
		Forma = "Cono",
		Radio = 7,
		Angulo = 110,
		AlSuelo = false,
		Dano = 8,
		Empuje = { Horizontal = 8, Vertical = 4 },
		Aturdimiento = 0.35,
		Tiempos = { Carga = 0.12, Viaje = 0, Recuperacion = 0.08 },
		Inmoviliza = false,
		Invulnerable = false,
		Animaciones = { Carga = "Combo1" },
		Efecto = "Combo1",
		Combo = { Paso = 1, Total = 4, Ventana = 0.7 },
	},
	Combo2 = {
		Id = "Combo2",
		Nombre = "Golpe 2",
		Descripcion = "Revés cruzado.",
		Poder = "Cuerpo",
		Categoria = "Combo",
		Tecla = "Click",
		Energia = 0,
		Cooldown = 0.36,
		Rango = 7,
		Forma = "Cono",
		Radio = 7,
		Angulo = 110,
		AlSuelo = false,
		Dano = 9,
		Empuje = { Horizontal = 9, Vertical = 4 },
		Aturdimiento = 0.35,
		Tiempos = { Carga = 0.12, Viaje = 0, Recuperacion = 0.08 },
		Inmoviliza = false,
		Invulnerable = false,
		Animaciones = { Carga = "Combo2" },
		Efecto = "Combo2",
		Combo = { Paso = 2, Total = 4, Ventana = 0.7 },
	},
	Combo3 = {
		Id = "Combo3",
		Nombre = "Golpe 3",
		Descripcion = "Patada giratoria.",
		Poder = "Cuerpo",
		Categoria = "Combo",
		Tecla = "Click",
		Energia = 0,
		Cooldown = 0.42,
		Rango = 8,
		Forma = "Cono",
		Radio = 8,
		Angulo = 150,
		AlSuelo = false,
		Dano = 11,
		Empuje = { Horizontal = 12, Vertical = 6 },
		Aturdimiento = 0.45,
		Tiempos = { Carga = 0.16, Viaje = 0, Recuperacion = 0.1 },
		Inmoviliza = false,
		Invulnerable = false,
		Animaciones = { Carga = "Combo3" },
		Efecto = "Combo3",
		Combo = { Paso = 3, Total = 4, Ventana = 0.75 },
	},
	Combo4 = {
		Id = "Combo4",
		Nombre = "Remate",
		Descripcion = "Golpe final que lanza al enemigo por los aires.",
		Poder = "Cuerpo",
		Categoria = "Combo",
		Tecla = "Click",
		Energia = 0,
		Cooldown = 1.1,
		Rango = 9,
		Forma = "Cono",
		Radio = 9,
		Angulo = 120,
		AlSuelo = false,
		Dano = 22,
		Empuje = { Horizontal = 46, Vertical = 38 },
		Aturdimiento = 0.9,
		Tiempos = { Carga = 0.24, Viaje = 0, Recuperacion = 0.2 },
		Inmoviliza = false,
		Invulnerable = false,
		Animaciones = { Carga = "Combo4" },
		Efecto = "Combo4",
		Combo = { Paso = 4, Total = 4, Ventana = 0.7 },
	},
}

-- Ids que el cliente puede pedir por red. "Combo" es especial: el servidor elige el golpe.
local solicitables = {
	"Rayo_Basico",
	"Rayo_Fuerte",
	"Rayo_Definitiva",
	"Gravedad_Basico",
	"Gravedad_Fuerte",
	"Gravedad_Definitiva",
	"Combo",
}

-- Orden en que se muestran en la interfaz (cada entrada es un id "solicitable").
local orden = table.clone(solicitables)

-- Congelado en profundidad: nadie modifica por accidente los números del juego.
local function congelar(tabla: any)
	if type(tabla) == "table" and not table.isfrozen(tabla) then
		for _, valor in tabla do
			congelar(valor)
		end
		table.freeze(tabla)
	end
end
congelar(habilidades)
congelar(solicitables)
congelar(orden)

Poderes.Habilidades = habilidades
Poderes.Solicitables = solicitables :: { string }
Poderes.Orden = orden :: { string }

-- Id de la petición de combo y número de golpes del combo.
Poderes.IdCombo = "Combo"
Poderes.GolpesCombo = 4

-- Devuelve la habilidad con ese id, o nil si no existe.
function Poderes.Obtener(id: string): Habilidad?
	return habilidades[id]
end

--[[
	Información de una petición del cliente, tal y como la ve la interfaz:
	para "Combo" devuelve el primer golpe (nombre, tecla y cooldown de referencia).
]]
function Poderes.Presentacion(idSolicitado: string): Habilidad?
	if idSolicitado == Poderes.IdCombo then
		return habilidades.Combo1
	end
	return habilidades[idSolicitado]
end

return Poderes
