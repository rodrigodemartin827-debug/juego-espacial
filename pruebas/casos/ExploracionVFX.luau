--[[
	Pruebas de los DATOS visuales de la exploración (Exploracion/Datos/EfectosExploracion): el escáner de mano y la minería.

	Las recetas son solo datos: un color que no existe o un tipo de capa mal escrito no daría error al cargar, sino un
	efecto que no sale en mitad de una partida. Estas pruebas lo detectan antes, y comprueban que el escaneo es de calidad
	máxima (usa todos los tipos de capa que importan, con varias etapas y efectos de pantalla).
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
end

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
local ANCLAS = { Lanzador = true, Mano = true, Origen = true, Objetivo = true, Suelo = true, Cielo = true }
local PARA = { Lanzador = true, Golpeados = true, Implicados = true, Todos = true }
local MINIMOS = { Bajo = true, Medio = true, Alto = true }

local function esHex(texto: any): boolean
	return type(texto) == "string" and string.match(texto, "^#%x%x%x%x%x%x$") ~= nil
end

local function paraCadaCapa(Recetas, f)
	for nombre, receta in Recetas do
		for fase, capas in receta.Fases do
			for indice, capa in capas do
				f(nombre, fase, indice, capa)
			end
		end
	end
end

local function tiposDe(capas)
	local tipos = {}
	for _, capa in capas do
		tipos[capa.Tipo] = true
	end
	return tipos
end

return function(Marco)
	local Recetas = cargar("Exploracion.Datos.EfectosExploracion")
	local Minerales = cargar("Exploracion.Datos.Minerales")
	local Combate = cargar("Combate.Datos.EfectosVFX")
	local Naves = cargar("Naves.Datos.EfectosNave")
	local Paleta = cargar("Combate.Datos.Paleta")
	local Recursos = cargar("Combate.Datos.Recursos")

	Marco.grupo("Exploración VFX: recetas", function()
		Marco.prueba("existen las recetas que usa el cliente y no chocan con las de otros sistemas", function()
			local necesarias = { "Escaner_Carga", "Escaner_Pulso", "Escaner_Completado", "Escaner_Cancelado" }
			for _, id in Minerales.Orden do
				table.insert(necesarias, `Minado_Golpe_{id}`)
				table.insert(necesarias, `Minado_Rotura_{id}`)
			end
			for _, nombre in necesarias do
				Marco.distinto(Recetas[nombre], nil, `falta la receta '{nombre}'`)
			end
			for nombre in Recetas do
				Marco.esNil(Combate[nombre], `'{nombre}' existe también en el combate`)
				Marco.esNil(Naves[nombre], `'{nombre}' existe también en las naves`)
			end
		end)

		Marco.prueba("cada receta usa una paleta que existe y fases conocidas, con capas", function()
			for nombre, receta in Recetas do
				Marco.distinto(Paleta[receta.Paleta], nil, `{nombre}: paleta '{receta.Paleta}' inexistente`)
				local fases = 0
				for fase, capas in receta.Fases do
					fases += 1
					Marco.verdadero(FASES[fase], `{nombre}: fase desconocida '{fase}'`)
					Marco.verdadero(#capas > 0, `{nombre}/{fase}: fase vacía`)
				end
				Marco.verdadero(fases > 0, `{nombre}: sin fases`)
			end
		end)

		Marco.prueba("todas las capas usan tipos, anclas, destinatarios y mínimos conocidos", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
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
					Marco.verdadero(capa.Retraso >= 0 and capa.Retraso < 5, `{donde}: retraso absurdo`)
				end
			end)
		end)

		Marco.prueba("los colores son claves de la paleta o hexadecimales válidos", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local paleta = Paleta[Recetas[nombre].Paleta]
				for _, campo in { "Color", "ColorNucleo", "ColorSuelo" } do
					local valor = capa[campo]
					local lista = if type(valor) == "table" then valor elseif valor ~= nil then { valor } else {}
					for _, color in lista do
						Marco.verdadero(
							paleta[color] ~= nil or esHex(color),
							`{nombre}/{fase}[{indice}]: color '{color}' no está en la paleta ni es hexadecimal`
						)
					end
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
						`{donde}: textura '{capa.Textura}' sin definir`
					)
				end
				if capa.Malla ~= nil then
					Marco.distinto(Recursos.Mallas[capa.Malla], nil, `{donde}: malla '{capa.Malla}' sin definir`)
				end
				if capa.Sonido ~= nil then
					Marco.distinto(Recursos.Sonidos[capa.Sonido], nil, `{donde}: sonido '{capa.Sonido}' sin definir`)
				end
			end)
		end)

		Marco.prueba("las cantidades son razonables (nada que sature un móvil)", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				if capa.Tipo == "Particulas" then
					Marco.verdadero((capa.Cantidad or 0) <= 250, `{donde}: demasiadas partículas por estallido`)
					Marco.verdadero((capa.Tasa or 0) <= 200, `{donde}: demasiadas partículas por segundo`)
				elseif capa.Tipo == "Escombros" then
					Marco.verdadero(capa.Cantidad <= 90, `{donde}: demasiados escombros`)
				elseif capa.Tipo == "Haz" then
					Marco.verdadero(
						(capa.Segmentos or 8) <= 12 and (capa.Ramas or 0) <= 10,
						`{donde}: rayo demasiado cargado`
					)
				end
			end)
		end)

		Marco.prueba("los escombros sueltos no tienen gravedad (no hay suelo que buscar)", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				if capa.Tipo == "Escombros" and capa.Libre then
					Marco.igual(capa.Gravedad, 0, `{nombre}/{fase}[{indice}]: los escombros libres no deben caer`)
				end
			end)
		end)
	end)

	Marco.grupo("Exploración VFX: calidad del escaneo", function()
		Marco.prueba("la carga enciende la mano: esferas, anillos, luz, chispas, partículas y sonido", function()
			local capas = Recetas.Escaner_Carga.Fases.Anticipacion
			local tipos = tiposDe(capas)
			for _, requerido in { "Esfera", "Onda", "Luz", "Particulas", "Sonido", "Tinte", "Zoom" } do
				Marco.verdadero(tipos[requerido], `Escaner_Carga: falta una capa {requerido}`)
			end
			for _, capa in capas do
				if capa.Tipo == "Esfera" then
					Marco.verdadero(capa.Sigue, "las esferas de carga deben seguir a la mano")
				end
			end
		end)

		Marco.prueba("el pulso une la mano con el objetivo: rayo, halo, paquetes de datos y anillos", function()
			local capas = Recetas.Escaner_Pulso.Fases.Lanzamiento
			local tipos = tiposDe(capas)
			for _, requerido in { "Haz", "Proyectil", "Onda", "Esfera", "Luz", "Particulas", "Sonido" } do
				Marco.verdadero(tipos[requerido], `Escaner_Pulso: falta una capa {requerido}`)
			end
			local haces = 0
			for _, capa in capas do
				if capa.Tipo == "Haz" then
					haces += 1
					Marco.igual(capa.Desde, "Mano")
					Marco.igual(capa.Hasta, "Objetivo")
				end
			end
			Marco.verdadero(haces >= 2, "el rayo debe tener núcleo y halo")
		end)

		Marco.prueba("terminar el escaneo es de calidad máxima: todos los tipos de capa y varias etapas", function()
			local impacto = Recetas.Escaner_Completado.Fases.Impacto
			local tipos = tiposDe(impacto)
			for _, requerido in
				{
					"Esfera",
					"Onda",
					"Luz",
					"Particulas",
					"Escombros",
					"Haz",
					"Sacudida",
					"Tinte",
					"Desenfoque",
					"Zoom",
					"Sonido",
				}
			do
				Marco.verdadero(tipos[requerido], `Escaner_Completado: falta una capa {requerido}`)
			end
			local conRetraso, esferas, ondas, arcos = 0, 0, 0, 0
			for _, capa in impacto do
				if (capa.Retraso or 0) > 0 then
					conRetraso += 1
				end
				if capa.Tipo == "Esfera" then
					esferas += 1
				elseif capa.Tipo == "Onda" then
					ondas += 1
				elseif capa.Tipo == "Haz" and capa.Desde == "Objetivo" then
					arcos += 1
				end
			end
			Marco.verdadero(conRetraso >= 5, "las etapas deben estar escalonadas")
			Marco.verdadero(esferas >= 3 and ondas >= 3, "debe haber varias esferas y varios anillos")
			Marco.verdadero(arcos >= 4, "debe haber arcos eléctricos sobre el objetivo")
			Marco.verdadero(#impacto >= 20, `solo {#impacto} capas`)
			Marco.distinto(Recetas.Escaner_Completado.Fases.Residuo, nil, "debe dejar motas de luz")
		end)

		Marco.prueba("los efectos de pantalla son solo para quien escanea", function()
			for _, nombre in { "Escaner_Carga", "Escaner_Completado" } do
				for _, capa in Recetas[nombre].Fases[if nombre == "Escaner_Carga" then "Anticipacion" else "Impacto"] do
					if capa.Tipo == "Tinte" or capa.Tipo == "Desenfoque" or capa.Tipo == "Zoom" then
						Marco.igual(capa.Para, "Lanzador", `{nombre}: la pantalla de los demás no debe cambiar`)
					end
				end
			end
		end)

		Marco.prueba("completar, cancelar y escanear tienen aspecto distinto", function()
			Marco.distinto(Recetas.Escaner_Pulso.Paleta, Recetas.Escaner_Completado.Paleta)
			Marco.distinto(Recetas.Escaner_Pulso.Paleta, Recetas.Escaner_Cancelado.Paleta)
			Marco.distinto(
				Paleta[Recetas.Escaner_Pulso.Paleta].Principal,
				Paleta[Recetas.Escaner_Completado.Paleta].Principal
			)
		end)
	end)

	Marco.grupo("Exploración VFX: calidad de la minería", function()
		Marco.prueba("cada mineral tiene su color y sus dos efectos", function()
			local colores = {}
			for _, id in Minerales.Orden do
				local golpe = Recetas[`Minado_Golpe_{id}`]
				local rotura = Recetas[`Minado_Rotura_{id}`]
				Marco.igual(golpe.Paleta, `Mineral_{id}`)
				Marco.igual(rotura.Paleta, `Mineral_{id}`)
				colores[Paleta[golpe.Paleta].Principal] = true
			end
			local distintos = 0
			for _ in colores do
				distintos += 1
			end
			Marco.igual(distintos, #Minerales.Orden, "cada mineral debe distinguirse por el color")
		end)

		Marco.prueba("un golpe tiene destello, anillo, luz, chispas, esquirlas y sonido", function()
			for _, id in Minerales.Orden do
				local tipos = tiposDe(Recetas[`Minado_Golpe_{id}`].Fases.Impacto)
				for _, requerido in { "Esfera", "Onda", "Luz", "Particulas", "Escombros", "Sonido" } do
					Marco.verdadero(tipos[requerido], `Minado_Golpe_{id}: falta una capa {requerido}`)
				end
			end
		end)

		Marco.prueba("la rotura es más potente que el golpe y deja polvo", function()
			for _, id in Minerales.Orden do
				local golpe = Recetas[`Minado_Golpe_{id}`].Fases.Impacto
				local rotura = Recetas[`Minado_Rotura_{id}`].Fases.Impacto
				Marco.verdadero(#rotura > #golpe, `Minado_Rotura_{id}: debe tener más capas que el golpe`)
				local tipos = tiposDe(rotura)
				for _, requerido in { "Esfera", "Onda", "Luz", "Particulas", "Escombros", "Haz", "Sacudida", "Sonido" } do
					Marco.verdadero(tipos[requerido], `Minado_Rotura_{id}: falta una capa {requerido}`)
				end
				Marco.distinto(Recetas[`Minado_Rotura_{id}`].Fases.Residuo, nil)
			end
		end)
	end)
end
