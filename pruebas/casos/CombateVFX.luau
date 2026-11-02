--[[
	Pruebas de los DATOS visuales del combate: recetas de efectos, paleta, recursos, animaciones y cinemáticas.

	Como los efectos se definen solo con datos, un error tipográfico (un color que no existe, una animación mal
	escrita) no daría error al cargar, sino un efecto que no sale en mitad de una partida. Estas pruebas lo
	detectan antes.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.Combate.{ruta}`)
end

-- Tipos de capa que sabe reproducir el cliente (VFX/Gestor).
local TIPOS = {
	Particulas = true,
	Onda = true,
	Esfera = true,
	Luz = true,
	Proyectil = true,
	Corte = true,
	Haz = true,
	Escombros = true,
	Crater = true,
	Tinte = true,
	Desenfoque = true,
	Zoom = true,
	Sacudida = true,
	Hitstop = true,
	Sonido = true,
}
local FASES = { Anticipacion = true, Lanzamiento = true, Impacto = true, Residuo = true, Golpeado = true }
local ANCLAS =
	{ Lanzador = true, Mano = true, Origen = true, Objetivo = true, Suelo = true, Cielo = true, Victima = true }
local PARA = { Lanzador = true, Golpeados = true, Implicados = true, Todos = true }
local MINIMOS = { Bajo = true, Medio = true, Alto = true }
-- Tipos de capa cuyo `Color` es un color o una lista de colores.
local CON_COLOR = {
	Particulas = true,
	Onda = true,
	Esfera = true,
	Luz = true,
	Proyectil = true,
	Corte = true,
	Haz = true,
	Escombros = true,
	Crater = true,
	Tinte = true,
}

-- Recorre todas las capas de todas las recetas: f(nombreReceta, fase, indice, capa).
local function paraCadaCapa(Recetas, f)
	for nombre, receta in Recetas do
		for fase, capas in receta.Fases do
			for indice, capa in capas do
				f(nombre, fase, indice, capa)
			end
		end
	end
end

local function esHex(texto: any): boolean
	return type(texto) == "string" and string.match(texto, "^#%x%x%x%x%x%x$") ~= nil
end

return function(Marco)
	local Recetas = cargar("Datos.EfectosVFX")
	local Paleta = cargar("Datos.Paleta")
	local Recursos = cargar("Datos.Recursos")
	local Animaciones = cargar("Datos.Animaciones")
	local Cinematicas = cargar("Datos.Cinematicas")
	local Poderes = cargar("Datos.Poderes")

	Marco.grupo("Combate VFX: recetas", function()
		Marco.prueba("cada habilidad tiene su receta y su paleta", function()
			for id, hab in Poderes.Habilidades do
				local receta = Recetas[hab.Efecto]
				Marco.distinto(receta, nil, `{id}: falta la receta '{hab.Efecto}'`)
				Marco.distinto(Paleta[receta.Paleta], nil, `{hab.Efecto}: paleta '{receta.Paleta}' inexistente`)
			end
		end)

		Marco.prueba(
			"los poderes tienen las cuatro fases (anticipación, lanzamiento, impacto, residuo) y la de golpeado",
			function()
				for _, id in
					{
						"Rayo_Basico",
						"Rayo_Fuerte",
						"Rayo_Definitiva",
						"Gravedad_Basico",
						"Gravedad_Fuerte",
						"Gravedad_Definitiva",
					}
				do
					local fases = Recetas[Poderes.Habilidades[id].Efecto].Fases
					for fase in FASES do
						Marco.distinto(fases[fase], nil, `{id}: falta la fase {fase}`)
						Marco.verdadero(#fases[fase] > 0, `{id}: la fase {fase} está vacía`)
					end
				end
			end
		)

		Marco.prueba("cada fase combina varias capas distintas (no un solo efecto)", function()
			for _, id in
				{
					"Rayo_Basico",
					"Rayo_Fuerte",
					"Rayo_Definitiva",
					"Gravedad_Basico",
					"Gravedad_Fuerte",
					"Gravedad_Definitiva",
				}
			do
				local fases = Recetas[Poderes.Habilidades[id].Efecto].Fases
				for _, fase in { "Anticipacion", "Lanzamiento", "Impacto" } do
					local tipos, cuantos = {}, 0
					for _, capa in fases[fase] do
						if not tipos[capa.Tipo] then
							tipos[capa.Tipo] = true
							cuantos += 1
						end
					end
					Marco.verdadero(cuantos >= 3, `{id}/{fase}: solo {cuantos} tipos de capa`)
				end
			end
		end)

		Marco.prueba("el impacto de las definitivas incluye pantalla, cráter, escombros, ondas y luces", function()
			for _, id in { "Rayo_Definitiva", "Gravedad_Definitiva" } do
				local tipos = {}
				for _, capa in Recetas[Poderes.Habilidades[id].Efecto].Fases.Impacto do
					tipos[capa.Tipo] = true
				end
				for _, requerido in
					{
						"Sacudida",
						"Tinte",
						"Desenfoque",
						"Zoom",
						"Crater",
						"Escombros",
						"Onda",
						"Esfera",
						"Luz",
						"Haz",
						"Particulas",
					}
				do
					Marco.verdadero(tipos[requerido], `{id}: falta una capa {requerido} en el impacto`)
				end
			end
		end)

		Marco.prueba("todas las capas usan tipos, fases, anclas y destinatarios conocidos", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				Marco.verdadero(FASES[fase], `{donde}: fase desconocida`)
				Marco.verdadero(TIPOS[capa.Tipo], `{donde}: tipo de capa desconocido '{capa.Tipo}'`)
				for _, campo in { "Anclaje", "Desde", "Hasta" } do
					if capa[campo] ~= nil then
						Marco.verdadero(ANCLAS[capa[campo]], `{donde}: ancla desconocida '{capa[campo]}'`)
					end
				end
				if capa.Para ~= nil then
					Marco.verdadero(PARA[capa.Para], `{donde}: destinatario desconocido '{capa.Para}'`)
				end
				if capa.Minimo ~= nil then
					Marco.verdadero(MINIMOS[capa.Minimo], `{donde}: nivel mínimo desconocido '{capa.Minimo}'`)
				end
				if capa.Retraso ~= nil then
					Marco.verdadero(capa.Retraso >= 0 and capa.Retraso < 10, `{donde}: retraso absurdo`)
				end
			end)
		end)

		Marco.prueba("la víctima solo se usa como ancla en la fase Golpeado", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				for _, campo in { "Anclaje", "Desde", "Hasta" } do
					if capa[campo] == "Victima" then
						Marco.igual(fase, "Golpeado", `{nombre}/{fase}[{indice}]: 'Victima' fuera de Golpeado`)
					end
				end
			end)
		end)

		Marco.prueba("los colores son claves de la paleta o hexadecimales válidos", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local colores = {}
				for _, campo in { "Color", "ColorNucleo", "ColorSuelo" } do
					local valor = capa[campo]
					if type(valor) == "table" then
						for _, elemento in valor do
							table.insert(colores, elemento)
						end
					elseif valor ~= nil then
						table.insert(colores, valor)
					end
				end
				local paleta = Paleta[Recetas[nombre].Paleta]
				for _, color in colores do
					Marco.verdadero(
						paleta[color] ~= nil or esHex(color),
						`{nombre}/{fase}[{indice}]: color '{color}' no está en la paleta ni es hexadecimal`
					)
				end
				if
					CON_COLOR[capa.Tipo]
					and capa.Tipo ~= "Tinte"
					and capa.Tipo ~= "Crater"
					and capa.Tipo ~= "Escombros"
				then
					-- Las capas coloreables siempre tienen alguno (las de pantalla y terreno usan el de paleta por defecto).
					Marco.verdadero(#colores > 0 or capa.Tipo == "Proyectil", `{nombre}/{fase}[{indice}]: sin color`)
				end
			end)
		end)

		Marco.prueba("las texturas, mallas y sonidos nombrados existen en Recursos", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				if capa.Textura ~= nil then
					Marco.distinto(
						Recursos.Texturas[capa.Textura],
						nil,
						`{donde}: textura '{capa.Textura}' sin definir en Recursos`
					)
				end
				if capa.Malla ~= nil then
					Marco.distinto(
						Recursos.Mallas[capa.Malla],
						nil,
						`{donde}: malla '{capa.Malla}' sin definir en Recursos`
					)
				end
				if capa.Sonido ~= nil then
					Marco.distinto(
						Recursos.Sonidos[capa.Sonido],
						nil,
						`{donde}: sonido '{capa.Sonido}' sin definir en Recursos`
					)
				end
				if capa.Estela and capa.Estela.Textura then
					Marco.distinto(
						Recursos.Texturas[capa.Estela.Textura],
						nil,
						`{donde}: textura de estela sin definir`
					)
				end
			end)
		end)

		Marco.prueba("las cantidades y tamaños son razonables (nada que sature un móvil)", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				if capa.Tipo == "Particulas" then
					Marco.verdadero((capa.Cantidad or 0) <= 250, `{donde}: demasiadas partículas por estallido`)
					Marco.verdadero((capa.Tasa or 0) <= 200, `{donde}: demasiadas partículas por segundo`)
				elseif capa.Tipo == "Escombros" then
					Marco.verdadero(capa.Cantidad <= 90, `{donde}: demasiados escombros`)
				elseif capa.Tipo == "Haz" then
					Marco.verdadero((capa.Segmentos or 8) <= 12, `{donde}: demasiados segmentos`)
					Marco.verdadero((capa.Ramas or 0) <= 10, `{donde}: demasiadas ramas`)
				elseif capa.Tipo == "Crater" then
					Marco.verdadero(
						(capa.Rocas or 0) <= 30 and (capa.Grietas or 0) <= 24,
						`{donde}: cráter demasiado cargado`
					)
				end
			end)
		end)

		Marco.prueba(
			"las capas de un mismo Grupo de rayo comparten segmentos, desviación y ramas (si no, el zigzag no coincide)",
			function()
				for nombre, receta in Recetas do
					for fase, capas in receta.Fases do
						local grupos = {}
						for indice, capa in capas do
							if capa.Tipo == "Haz" and capa.Grupo then
								local anterior = grupos[capa.Grupo]
								if anterior then
									local donde = `{nombre}/{fase}[{indice}] (grupo {capa.Grupo})`
									Marco.igual(capa.Segmentos, anterior.Segmentos, `{donde}: Segmentos distintos`)
									Marco.igual(capa.Desviacion, anterior.Desviacion, `{donde}: Desviacion distinta`)
									Marco.igual(capa.Ramas, anterior.Ramas, `{donde}: Ramas distintas`)
									Marco.igual(capa.Parpadeos, anterior.Parpadeos, `{donde}: Parpadeos distintos`)
								else
									grupos[capa.Grupo] = capa
								end
							end
						end
					end
				end
			end
		)
	end)

	Marco.grupo("Combate VFX: paleta y recursos", function()
		Marco.prueba("todas las paletas tienen los cuatro colores en hexadecimal", function()
			for nombre, paleta in Paleta do
				for _, clave in { "Nucleo", "Principal", "Secundario", "Oscuro" } do
					Marco.verdadero(esHex(paleta[clave]), `{nombre}.{clave}: no es un hexadecimal #RRGGBB`)
				end
			end
		end)

		Marco.prueba("los IDs de contenido son texto (vacío = usar el predeterminado)", function()
			for _, grupo in { "Texturas", "Mallas", "Animaciones", "Sonidos" } do
				for nombre, id in Recursos[grupo] do
					Marco.igual(type(id), "string", `Recursos.{grupo}.{nombre}`)
				end
			end
			for nombre, id in Recursos.Texturas do
				Marco.verdadero(id ~= "", `Recursos.Texturas.{nombre}: las texturas deben tener un valor por defecto`)
			end
		end)
	end)

	Marco.grupo("Combate VFX: animaciones y cinemáticas", function()
		Marco.prueba("cada animación usada por una habilidad existe y se puede sustituir por un ID", function()
			local usadas = { Impacto = true }
			for _, hab in Poderes.Habilidades do
				for _, nombre in { hab.Animaciones.Carga, hab.Animaciones.Lanzamiento } do
					usadas[nombre] = true
				end
			end
			for nombre in usadas do
				Marco.distinto(Animaciones.Definiciones[nombre], nil, `falta la animación por código '{nombre}'`)
				Marco.distinto(
					Recursos.Animaciones[nombre],
					nil,
					`Recursos.Animaciones no tiene entrada para '{nombre}'`
				)
			end
			-- Y al revés: ninguna entrada de Recursos sobra.
			for nombre in Recursos.Animaciones do
				Marco.distinto(
					Animaciones.Definiciones[nombre],
					nil,
					`Recursos.Animaciones.{nombre} no corresponde a ninguna animación`
				)
			end
		end)

		Marco.prueba("los cuadros están ordenados en el tiempo y solo nombran partes del rig R15", function()
			local partes = {}
			local function recorrer(nodo)
				partes[nodo.Nombre] = true
				for _, hijo in nodo.Hijos do
					recorrer(hijo)
				end
			end
			recorrer(Animaciones.Rig)
			Marco.verdadero(partes.RightUpperArm and partes.LeftFoot and partes.Head, "el rig está incompleto")

			for nombre, anim in Animaciones.Definiciones do
				Marco.verdadero(#anim.Cuadros >= 2, `{nombre}: necesita al menos dos cuadros`)
				local anterior = -1
				for indice, cuadro in anim.Cuadros do
					Marco.verdadero(
						cuadro.T > anterior or (indice == 1 and cuadro.T == 0),
						`{nombre}: cuadro {indice} desordenado`
					)
					anterior = cuadro.T
					for parte, rotacion in cuadro.Poses do
						Marco.verdadero(partes[parte], `{nombre}: la parte '{parte}' no existe en el rig`)
						Marco.verdadero(#rotacion == 3, `{nombre}.{parte}: la rotación necesita 3 ángulos`)
					end
				end
				Marco.igual(anim.Cuadros[1].T, 0, `{nombre}: debe empezar en T = 0`)
				Marco.verdadero(
					anim.Cuadros[#anim.Cuadros].T <= anim.Duracion + 1e-6,
					`{nombre}: el último cuadro pasa de la duración`
				)
			end
		end)

		Marco.prueba("la animación de carga de cada habilidad no dura más que su tiempo de carga + viaje", function()
			for id, hab in Poderes.Habilidades do
				local nombre = hab.Animaciones.Carga
				if nombre and hab.Categoria ~= "Definitiva" then
					local duracion = Animaciones.Definiciones[nombre].Duracion
					Marco.verdadero(
						duracion <= hab.Tiempos.Carga + hab.Tiempos.Viaje + hab.Tiempos.Recuperacion + 0.35,
						`{id}: la animación '{nombre}' dura {duracion}s y se pasa del tiempo de la habilidad`
					)
				end
			end
		end)

		Marco.prueba("las definitivas tienen cinemática con planos que cubren hasta pasado el impacto", function()
			for id, hab in Poderes.Habilidades do
				if hab.Cinematica then
					local cine = Cinematicas[hab.Cinematica]
					Marco.distinto(cine, nil, `{id}: falta la cinemática '{hab.Cinematica}'`)
					local total = 0
					for indice, plano in cine.Planos do
						total += plano.Duracion
						Marco.verdadero(plano.Duracion > 0, `{id}: plano {indice} sin duración`)
						for _, extremo in { plano.Desde, plano.Hasta } do
							Marco.verdadero(
								ANCLAS[extremo.Pos.Ancla],
								`{id}: plano {indice}: ancla de cámara desconocida`
							)
							Marco.verdadero(
								ANCLAS[(extremo.Mirar or { Ancla = "Objetivo" }).Ancla],
								`{id}: plano {indice}: ancla de mirada desconocida`
							)
							Marco.verdadero(
								extremo.FOV == nil or (extremo.FOV >= 20 and extremo.FOV <= 120),
								`{id}: plano {indice}: FOV fuera de rango`
							)
						end
					end
					Marco.verdadero(
						total >= hab.Tiempos.Carga + hab.Tiempos.Viaje + 0.5,
						`{id}: la cinemática ({total}s) termina antes de que se vea el impacto`
					)
					Marco.verdadero(
						total <= hab.Tiempos.Carga + hab.Tiempos.Viaje + hab.Tiempos.Recuperacion + 0.6,
						`{id}: la cinemática ({total}s) dura demasiado más que la habilidad`
					)
				end
			end
		end)
	end)
end
