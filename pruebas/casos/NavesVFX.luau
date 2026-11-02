--[[
	Pruebas de los DATOS visuales de las naves (Naves/Datos/EfectosNave).

	Igual que con el combate, las recetas son solo datos: un color que no existe o un tipo de capa mal escrito no
	daría error al cargar, sino un efecto que no sale en mitad de una partida. Estas pruebas lo detectan antes.
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
-- Las de siempre más las propias de las naves (Attachments del modelo).
local ANCLAS = {
	Lanzador = true,
	Mano = true,
	Origen = true,
	Objetivo = true,
	Suelo = true,
	Cielo = true,
	Victima = true,
	MotorIzq = true,
	MotorDer = true,
}
local PARA = { Lanzador = true, Golpeados = true, Implicados = true, Todos = true }
local MINIMOS = { Bajo = true, Medio = true, Alto = true }

local function esHex(texto: any): boolean
	return type(texto) == "string" and string.match(texto, "^#%x%x%x%x%x%x$") ~= nil
end

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

local function tiposDe(capas)
	local tipos = {}
	for _, capa in capas do
		tipos[capa.Tipo] = true
	end
	return tipos
end

return function(Marco)
	local Recetas = cargar("Naves.Datos.EfectosNave")
	local Combate = cargar("Combate.Datos.EfectosVFX")
	local Paleta = cargar("Combate.Datos.Paleta")
	local Recursos = cargar("Combate.Datos.Recursos")

	-- Recetas que el código del juego pide por nombre (ver Naves/Efectos).
	local NECESARIAS = {
		"Nave_Laser_Heroes",
		"Nave_Laser_Villanos",
		"Nave_Laser_Neutral",
		"Nave_Impacto_Escudo",
		"Nave_Impacto_Casco",
		"Nave_Impacto_Asteroide",
		"Nave_Choque_Escudo",
		"Nave_Choque_Casco",
		"Nave_Explosion",
		"Nave_Asteroide_Pequeno",
		"Nave_Asteroide_Mediano",
		"Nave_Asteroide_Grande",
		"Nave_Propulsor",
		"Nave_Propulsor_Turbo",
		"Nave_Turbo_Arranque",
		"Nave_Despegue",
	}

	Marco.grupo("Naves VFX: recetas", function()
		Marco.prueba("existen todas las recetas que usa el juego y no chocan con las del combate", function()
			for _, nombre in NECESARIAS do
				Marco.distinto(Recetas[nombre], nil, `falta la receta '{nombre}'`)
			end
			for nombre in Recetas do
				Marco.esNil(Combate[nombre], `'{nombre}' existe también en el combate y taparía a una de las dos`)
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
				Marco.falso(capa.Anclaje == "Victima", `{donde}: 'Victima' solo existe en la fase Golpeado del combate`)
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

		Marco.prueba("los escombros del espacio no tienen gravedad y no buscan el suelo", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				if capa.Tipo == "Escombros" and capa.Libre then
					Marco.igual(capa.Gravedad, 0, `{nombre}/{fase}[{indice}]: los escombros libres no deben caer`)
				end
			end)
		end)
	end)

	Marco.grupo("Naves VFX: calidad de cada efecto", function()
		Marco.prueba("un disparo tiene fogonazo, proyectil, haz, luz y chispas, y cada bando su color", function()
			local colores = {}
			for _, bando in { "Heroes", "Villanos", "Neutral" } do
				local receta = Recetas[`Nave_Laser_{bando}`]
				local tipos = tiposDe(receta.Fases.Lanzamiento)
				for _, requerido in { "Esfera", "Luz", "Onda", "Particulas", "Proyectil", "Haz" } do
					Marco.verdadero(tipos[requerido], `Nave_Laser_{bando}: falta una capa {requerido}`)
				end
				colores[Paleta[receta.Paleta].Principal] = true
			end
			local distintos = 0
			for _ in colores do
				distintos += 1
			end
			Marco.igual(distintos, 3, "los tres bandos deben distinguirse por el color")
		end)

		Marco.prueba("el proyectil dura lo que tarda el disparo en llegar (usa el tiempo de viaje)", function()
			for _, bando in { "Heroes", "Villanos", "Neutral" } do
				for _, capa in Recetas[`Nave_Laser_{bando}`].Fases.Lanzamiento do
					if capa.Tipo == "Proyectil" then
						Marco.igual(capa.Duracion, "Viaje")
					end
				end
			end
		end)

		Marco.prueba("los tres impactos del láser tienen luz, chispas, onda y sonido", function()
			for _, nombre in { "Nave_Impacto_Escudo", "Nave_Impacto_Casco", "Nave_Impacto_Asteroide" } do
				local tipos = tiposDe(Recetas[nombre].Fases.Impacto)
				for _, requerido in { "Esfera", "Luz", "Onda", "Particulas", "Sonido" } do
					Marco.verdadero(tipos[requerido], `{nombre}: falta una capa {requerido}`)
				end
			end
		end)

		Marco.prueba(
			"los choques con un asteroide sacuden, tiñen y desenfocan la pantalla de quien los sufre",
			function()
				for _, nombre in { "Nave_Choque_Escudo", "Nave_Choque_Casco" } do
					local tipos = tiposDe(Recetas[nombre].Fases.Impacto)
					for _, requerido in
						{ "Sacudida", "Tinte", "Desenfoque", "Escombros", "Particulas", "Onda", "Esfera", "Luz" }
					do
						Marco.verdadero(tipos[requerido], `{nombre}: falta una capa {requerido}`)
					end
				end
				Marco.distinto(
					Recetas.Nave_Choque_Escudo.Paleta,
					Recetas.Nave_Choque_Casco.Paleta,
					"el escudo y el casco deben verse distintos"
				)
			end
		)

		Marco.prueba(
			"la explosión de una nave es de calidad máxima: todos los tipos de capa y varias etapas",
			function()
				local impacto = Recetas.Nave_Explosion.Fases.Impacto
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
						"Sonido",
					}
				do
					Marco.verdadero(tipos[requerido], `Nave_Explosion: falta una capa {requerido}`)
				end
				local conRetraso = 0
				for _, capa in impacto do
					if (capa.Retraso or 0) > 0 then
						conRetraso += 1
					end
				end
				Marco.verdadero(conRetraso >= 3, "debe haber explosiones secundarias escalonadas")
				Marco.verdadero(#impacto >= 20, `solo {#impacto} capas`)
				Marco.distinto(Recetas.Nave_Explosion.Fases.Residuo, nil, "debe dejar humo y brasas")
			end
		)

		Marco.prueba("los asteroides estallan con más fuerza cuanto más grandes son", function()
			local function cantidadDeEscombros(nombre)
				local total = 0
				for _, capa in Recetas[nombre].Fases.Impacto do
					if capa.Tipo == "Escombros" then
						total += capa.Cantidad
					end
				end
				return total
			end
			local pequeno = cantidadDeEscombros("Nave_Asteroide_Pequeno")
			local mediano = cantidadDeEscombros("Nave_Asteroide_Mediano")
			local grande = cantidadDeEscombros("Nave_Asteroide_Grande")
			Marco.verdadero(pequeno < mediano and mediano < grande, `{pequeno} / {mediano} / {grande}`)
		end)

		Marco.prueba("los propulsores usan los dos motores, salen hacia atrás y siguen a la nave", function()
			for _, nombre in { "Nave_Propulsor", "Nave_Propulsor_Turbo" } do
				local anclas = {}
				for _, capa in Recetas[nombre].Fases.Lanzamiento do
					if capa.Tipo == "Particulas" and capa.Textura == "Fuego" then
						anclas[capa.Anclaje] = true
						Marco.igual(capa.Direccion, "Atras", `{nombre}: el chorro debe salir hacia atrás`)
						Marco.verdadero(capa.Sigue, `{nombre}: el chorro debe seguir al propulsor`)
						Marco.verdadero(
							capa.Duracion >= 0.25,
							`{nombre}: el pulso es demasiado corto, se verían huecos`
						)
					end
				end
				Marco.verdadero(anclas.MotorIzq and anclas.MotorDer, `{nombre}: faltan propulsores`)
			end
			Marco.distinto(
				Recetas.Nave_Propulsor.Paleta,
				Recetas.Nave_Propulsor_Turbo.Paleta,
				"el turbo debe verse distinto"
			)
		end)

		Marco.prueba("el despegue levanta onda, humo, luz y sacudida", function()
			local tipos = tiposDe(Recetas.Nave_Despegue.Fases.Lanzamiento)
			for _, requerido in { "Onda", "Particulas", "Luz", "Sacudida", "Esfera" } do
				Marco.verdadero(tipos[requerido], `Nave_Despegue: falta una capa {requerido}`)
			end
		end)
	end)
end
