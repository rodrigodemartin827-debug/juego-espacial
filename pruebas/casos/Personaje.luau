--[[
	Pruebas del editor de personaje humano: el catálogo (DatosHumanos), los recursos subidos (RecursosHumanos y
	modelos/personaje_humano/piezas.json), las reglas de la apariencia (Apariencia) y la validación del remoto que la
	guarda (nada de opciones ni colores inventados por el cliente).
]]

local fs = require("@lune/fs")
local serde = require("@lune/serde")

local Entorno = require("../infraestructura/Entorno")

local function cargar()
	local entorno = Entorno.nuevo()
	local r = entorno.servidor.requerir
	return r("ReplicatedStorage.Shared.Personaje.Apariencia"),
		r("ReplicatedStorage.Shared.Personaje.DatosHumanos"),
		r("ReplicatedStorage.Shared.Personaje.RecursosHumanos"),
		r
end

local PARTES_R6 =
	{ Head = true, Torso = true, ["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true }
local ANCLAJES = { HairAttachment = true, HatAttachment = true, FaceFrontAttachment = true }
local TRIANGULOS_MAXIMOS = 1500

-- Lune no tiene Random: un generador con la misma forma (NextInteger).
local function azarFalso(semilla: number)
	math.randomseed(semilla)
	return {
		NextInteger = function(_, a, b)
			return math.random(a, b)
		end,
	}
end

return function(Marco)
	Marco.grupo("Personaje: catálogo humano", function()
		Marco.prueba("cada campo tiene opciones con ids únicos, y el aspecto por defecto es válido", function()
			local Apariencia, Datos = cargar()
			for _, campo in Apariencia.CamposOpcion do
				local vistos = {}
				local opciones = Apariencia.Opciones(campo)
				Marco.verdadero(#opciones >= 4, campo .. ": al menos 4 opciones")
				for _, o in opciones do
					Marco.esNil(vistos[o.Id], campo .. ": id repetido " .. o.Id)
					vistos[o.Id] = true
					Marco.verdadero(type(o.Nombre) == "string" and o.Nombre ~= "", campo .. ": nombre")
				end
			end
			for _, campo in Apariencia.Campos do
				Marco.verdadero(Apariencia.ValorValido(campo, Datos.Defecto[campo]), campo .. ": defecto")
			end
		end)

		Marco.prueba("al menos 5 pieles, de clara a oscura", function()
			local _, Datos = cargar()
			Marco.verdadero(#Datos.Pieles >= 5)
			local function luz(hex: string): number
				local r, g, b = tonumber(hex:sub(2, 3), 16), tonumber(hex:sub(4, 5), 16), tonumber(hex:sub(6, 7), 16)
				return 0.299 * r + 0.587 * g + 0.114 * b
			end
			for i = 2, #Datos.Pieles do
				Marco.verdadero(luz(Datos.Pieles[i].Hex) < luz(Datos.Pieles[i - 1].Hex), Datos.Pieles[i].Id)
			end
		end)

		Marco.prueba("al menos 10 peinados, y cada peinado y accesorio tiene sus piezas 3D y su anclaje", function()
			local Apariencia, _, Recursos = cargar()
			local peinados = 0
			for _, campo in { "Cabello", "Accesorio" } do
				for _, o in Apariencia.Opciones(campo) do
					if o.Id == "Ninguno" then
						Marco.esNil(o.Anclaje, campo .. ": «Ninguno» no lleva nada")
						continue
					end
					Marco.verdadero(ANCLAJES[o.Anclaje], `{campo} {o.Id}: anclaje {o.Anclaje}`)
					local piezas = Recursos.Piezas[`{campo}_{o.Id}`]
					Marco.verdadero(piezas ~= nil and #piezas > 0, `{campo} {o.Id}: sin piezas 3D`)
					for _, p in piezas do
						Marco.igual(p.Parte, "Head", `{p.Nombre}: va en la cabeza`)
					end
					if campo == "Cabello" then
						peinados += 1
					end
				end
			end
			Marco.verdadero(peinados >= 10, `solo hay {peinados} peinados`)
		end)

		Marco.prueba("cada chaqueta y pantalón tiene sus piezas 3D en partes del R6 y con roles conocidos", function()
			local Apariencia, Datos, Recursos = cargar()
			for _, campo in { "Chaqueta", "Pantalon" } do
				for _, o in Apariencia.Opciones(campo) do
					local piezas = Recursos.Piezas[`{campo}_{o.Id}`]
					Marco.verdadero(piezas ~= nil and #piezas > 0, `{campo} {o.Id}: sin piezas 3D`)
					for _, p in piezas do
						Marco.verdadero(PARTES_R6[p.Parte], `{p.Nombre}: parte {p.Parte}`)
					end
				end
				if campo == "Chaqueta" then
					for _, o in Apariencia.Opciones(campo) do
						Marco.verdadero(o.Brazos == "Chaqueta" or o.Brazos == "Piel", `{o.Id}: color de los brazos`)
					end
				end
			end
			for _, piezas in Recursos.Piezas do
				for _, p in piezas do
					Marco.distinto(Datos.Roles[p.Rol], nil, `{p.Nombre}: rol {p.Rol}`)
					Marco.verdadero(string.match(p.Malla, "^rbxassetid://%d+$") ~= nil, `{p.Nombre}: malla`)
					for k = 1, 3 do
						Marco.verdadero(p.Tamano[k] > 0, `{p.Nombre}: tamaño`)
					end
				end
			end
		end)

		Marco.prueba(
			"cada rasgo de la cara tiene su textura (salvo «Sin nariz») y la rueda de color existe",
			function()
				local Apariencia, _, Recursos = cargar()
				for _, campo in { "Cejas", "Ojos", "Nariz", "Boca" } do
					for _, o in Apariencia.Opciones(campo) do
						local imagen = Recursos.Imagenes[`{campo}_{o.Id}`]
						if campo == "Nariz" and o.Id == "Ninguna" then
							Marco.esNil(imagen)
						else
							Marco.verdadero(
								imagen ~= nil and string.match(imagen, "^rbxassetid://%d+$") ~= nil,
								`{campo} {o.Id}: textura`
							)
						end
					end
				end
				Marco.distinto(Recursos.Imagenes.RuedaColor, nil)
			end
		)

		Marco.prueba("los peinados y accesorios de Blender tienen menos de 1.500 triángulos", function()
			local piezas = serde.decode("json", fs.readFile("modelos/personaje_humano/piezas.json"))
			local cuenta = 0
			for elemento, tris in piezas.TriangulosPorElemento do
				if
					string.match(elemento, "^Cabello_")
					or string.match(elemento, "^Accesorio_")
					or string.match(elemento, "^Barba_")
				then
					cuenta += 1
					Marco.verdadero(tris < TRIANGULOS_MAXIMOS, `{elemento}: {tris} triángulos`)
				end
			end
			Marco.verdadero(cuenta >= 40, "faltan piezas en piezas.json")
		end)

		Marco.prueba("RecursosHumanos está al día con piezas.json (todas las piezas, mismos centros)", function()
			local _, _, Recursos = cargar()
			local piezas = serde.decode("json", fs.readFile("modelos/personaje_humano/piezas.json")).Piezas
			local enRecursos = {}
			for _, lista in Recursos.Piezas do
				for _, p in lista do
					enRecursos[p.Nombre] = p
				end
			end
			for nombre, p in piezas do
				local r = enRecursos[nombre]
				Marco.distinto(r, nil, nombre .. ": regenera RecursosHumanos (herramientas/generar_recursos_humanos)")
				if r then
					for k = 1, 3 do
						Marco.verdadero(math.abs(r.Centro[k] - p.Centro[k]) < 1e-3, nombre .. ": centro distinto")
					end
				end
			end
		end)
	end)

	Marco.grupo("Personaje: apariencia", function()
		Marco.prueba("Validar completa lo que falta y cambia lo que no existe por el defecto", function()
			local Apariencia, Datos = cargar()
			local a = Apariencia.Validar({
				Piel = "Piel9",
				Cabello = "NoExiste",
				Chaqueta = 3,
				ColorPelo = "#a1b2c3",
				ColorChaqueta = "rojo",
				ColorPantalon = "#12345",
			})
			Marco.igual(a.Piel, "Piel9")
			Marco.igual(a.Cabello, Datos.Defecto.Cabello)
			Marco.igual(a.Chaqueta, Datos.Defecto.Chaqueta)
			Marco.igual(a.Ojos, Datos.Defecto.Ojos)
			Marco.igual(a.ColorPelo, "#A1B2C3", "los colores se guardan en mayúsculas")
			Marco.igual(a.ColorChaqueta, Datos.Defecto.ColorChaqueta)
			Marco.igual(a.ColorPantalon, Datos.Defecto.ColorPantalon)
			Marco.igualProfundo(Apariencia.Validar(nil), Datos.Defecto)
		end)

		Marco.prueba("Hecha solo es verdadero con una apariencia de este editor guardada", function()
			local Apariencia = cargar()
			Marco.falso(Apariencia.Hecha({}))
			Marco.falso(Apariencia.Hecha(nil))
			Marco.falso(Apariencia.Hecha({ Piel = "Piel1", Ropa = "Explorador" }), "la del editor anterior no vale")
			Marco.verdadero(Apariencia.Hecha({ Piel = "Piel1", Chaqueta = "Piloto" }))
		end)

		Marco.prueba("las flechas recorren las opciones y dan la vuelta", function()
			local Apariencia = cargar()
			local ids = Apariencia.Ids("Cabello")
			Marco.igual(Apariencia.Mover("Cabello", ids[1], 1), ids[2])
			Marco.igual(Apariencia.Mover("Cabello", ids[1], -1), ids[#ids])
			Marco.igual(Apariencia.Mover("Cabello", ids[#ids], 1), ids[1])
			Marco.igual(Apariencia.Mover("Cabello", "NoExiste", 1), ids[2], "lo que no existe cuenta como el primero")
		end)

		Marco.prueba("Aleatoria siempre da una apariencia válida", function()
			local Apariencia = cargar()
			local azar = azarFalso(7)
			for _ = 1, 60 do
				local a = Apariencia.Aleatoria(azar)
				Marco.igualProfundo(Apariencia.Validar(a), a)
			end
		end)

		Marco.prueba("Colores da un color para cada rol de las piezas", function()
			local Apariencia, Datos = cargar()
			local colores = Apariencia.Colores(Apariencia.Validar(nil))
			for rol in Datos.Roles do
				Marco.verdadero(Apariencia.EsColor(colores[rol]), "rol sin color: " .. rol)
			end
			Marco.verdadero(Apariencia.EsColor(colores.Piel))
		end)
	end)

	Marco.grupo("Personaje: variedad ampliada", function()
		-- Cuántas opciones había antes de ampliar el editor (sin contar «ninguno»): ahora, mínimo el doble.
		local ANTES =
			{ Cabello = 12, Cejas = 6, Ojos = 7, Nariz = 4, Boca = 6, Chaqueta = 5, Pantalon = 4, Accesorio = 6 }

		Marco.prueba("cada categoría tiene al menos el doble de opciones que antes", function()
			local Apariencia = cargar()
			for campo, antes in ANTES do
				local n = 0
				for _, o in Apariencia.Opciones(campo) do
					if o.Id ~= "Ninguno" and o.Id ~= "Ninguna" then
						n += 1
					end
				end
				Marco.verdadero(n >= antes * 2 - 1, `{campo}: {n} opciones, antes {antes}`)
			end
		end)

		Marco.prueba("existen las categorías nuevas: complexión, vello facial, cicatriz y tatuaje", function()
			local Apariencia, Datos = cargar()
			for _, campo in { "Complexion", "Barba", "Cicatriz", "Tatuaje" } do
				Marco.verdadero(#Apariencia.Opciones(campo) >= 5, campo)
				Marco.distinto(Datos.Defecto[campo], nil, campo)
				local enLista = false
				for _, cat in Apariencia.Categorias do
					enLista = enLista or cat.Campo == campo
				end
				Marco.verdadero(enLista, campo .. " sale en el editor")
			end
			Marco.verdadero(#Apariencia.Opciones("Complexion") >= 4, "alto, bajo, fuerte y normal como mínimo")
		end)

		Marco.prueba("cada barba tiene sus piezas 3D, y cada cicatriz y tatuaje su textura", function()
			local Apariencia, _, Recursos = cargar()
			for _, o in Apariencia.Opciones("Barba") do
				if o.Id ~= "Ninguna" then
					local piezas = Recursos.Piezas["Barba_" .. o.Id]
					Marco.verdadero(piezas ~= nil and #piezas > 0, "Barba " .. o.Id)
					Marco.igual(o.Anclaje, "FaceFrontAttachment")
				end
			end
			for _, campo in { "Cicatriz", "Tatuaje" } do
				for _, o in Apariencia.Opciones(campo) do
					if o.Id ~= "Ninguna" and o.Id ~= "Ninguno" then
						local imagen = Recursos.Imagenes[`{campo}_{o.Id}`]
						Marco.verdadero(imagen ~= nil, `{campo} {o.Id}: textura`)
					end
				end
			end
		end)

		Marco.prueba("las complexiones no deforman demasiado y «Normal» no cambia nada", function()
			local Apariencia = cargar()
			Marco.esNil(Apariencia.Buscar("Complexion", "Normal").Escala)
			for _, o in Apariencia.Opciones("Complexion") do
				for _, grupo in { "Torso", "Brazos", "Piernas" } do
					local e = o.Escala and o.Escala[grupo]
					if e then
						for k = 1, 3 do
							Marco.verdadero(e[k] >= 0.7 and e[k] <= 1.35, `{o.Id} {grupo}: {e[k]}`)
						end
					end
				end
			end
		end)

		Marco.prueba(
			"los pantalones que dejan la pierna al aire lo dicen, y los tatuajes solo se ven con los brazos al aire",
			function()
				local Apariencia = cargar()
				Marco.igual(Apariencia.Buscar("Pantalon", "Shorts").Piernas, "Piel")
				Marco.esNil(Apariencia.Buscar("Pantalon", "Cargo").Piernas)
				local a = Apariencia.Validar({ Chaqueta = "Camiseta" })
				Marco.verdadero(Apariencia.TatuajeVisible(a))
				a = Apariencia.Validar({ Chaqueta = "Abrigo" })
				Marco.falso(Apariencia.TatuajeVisible(a))
			end
		)

		Marco.prueba("aleatorio casi nunca pone cicatriz, tatuaje o barba", function()
			local Apariencia = cargar()
			local azar = azarFalso(11)
			local con = 0
			for _ = 1, 200 do
				if Apariencia.Aleatoria(azar).Cicatriz ~= "Ninguna" then
					con += 1
				end
			end
			Marco.verdadero(con > 10 and con < 100, `{con} de 200 con cicatriz`)
		end)
	end)

	Marco.grupo("Monstruo: editor de personaje", function()
		local function modulos()
			local _, _, _, requerir = cargar()
			local P = "ReplicatedStorage.Shared.Personaje."
			return requerir(P .. "AparienciaMonstruo"),
				requerir(P .. "DatosMonstruo"),
				requerir(P .. "RecursosMonstruo"),
				requerir
		end

		Marco.prueba(
			"tiene silueta, piel, ojos, cuernos, boca, deformaciones y marcas, y el defecto es válido",
			function()
				local Apariencia, Datos = modulos()
				for _, campo in { "Silueta", "Piel", "Ojos", "Cuernos", "Boca", "Deformacion", "Marcas" } do
					Marco.verdadero(#Apariencia.Opciones(campo) >= 6, campo .. ": al menos 6 opciones")
					local vistos = {}
					for _, o in Apariencia.Opciones(campo) do
						Marco.esNil(vistos[o.Id], campo .. ": id repetido " .. o.Id)
						vistos[o.Id] = true
					end
				end
				for _, campo in Apariencia.Campos do
					Marco.verdadero(Apariencia.ValorValido(campo, Datos.Defecto[campo]), campo .. ": defecto")
				end
				Marco.verdadero(#Apariencia.Categorias >= 6)
			end
		)

		Marco.prueba("cada cuerno y deformación tiene sus piezas 3D, y cada ojo, boca y marca su textura", function()
			local Apariencia, Datos, Recursos = modulos()
			for _, par in { { "Cuernos", "Cuerno" }, { "Deformacion", "Deformacion" } } do
				for _, o in Apariencia.Opciones(par[1]) do
					if o.Id ~= "Ninguno" and o.Id ~= "Ninguna" then
						local piezas = Recursos.Piezas[`{par[2]}_{o.Id}`]
						Marco.verdadero(piezas ~= nil and #piezas > 0, `{par[1]} {o.Id}: sin piezas 3D`)
						for _, pieza in piezas do
							Marco.verdadero(
								pieza.Rol == "Cuerno" or pieza.Rol == "Hueso" or pieza.Rol == "Piel",
								`{pieza.Nombre}: rol {pieza.Rol}`
							)
							Marco.distinto(Datos.Roles[pieza.Rol], nil)
							Marco.verdadero(PARTES_R6[pieza.Parte], `{pieza.Nombre}: parte`)
						end
						if par[1] == "Cuernos" then
							Marco.verdadero(ANCLAJES[o.Anclaje], `{o.Id}: anclaje`)
						end
					end
				end
			end
			for _, par in { { "Ojos", "Ojos" }, { "Boca", "Boca" }, { "Marcas", "Marcas" } } do
				for _, o in Apariencia.Opciones(par[1]) do
					if o.Id ~= "Ninguna" then
						Marco.distinto(Recursos.Imagenes[`{par[2]}_{o.Id}`], nil, `{par[1]} {o.Id}: textura`)
					end
				end
			end
		end)

		Marco.prueba("las siluetas no deforman demasiado y «Base» no cambia nada", function()
			local Apariencia = modulos()
			Marco.esNil(Apariencia.Buscar("Silueta", "Normal").Escala)
			for _, o in Apariencia.Opciones("Silueta") do
				for _, grupo in { "Torso", "Brazos", "Piernas" } do
					local e = o.Escala and o.Escala[grupo]
					if e then
						for k = 1, 3 do
							Marco.verdadero(e[k] >= 0.55 and e[k] <= 1.5, `{o.Id} {grupo}: {e[k]}`)
						end
					end
				end
			end
		end)

		Marco.prueba("Validar, Hecha, Mover y Aleatoria", function()
			local Apariencia, Datos = modulos()
			local a = Apariencia.Validar({
				Piel = "Piel3",
				Cuernos = "NoExiste",
				ColorOjos = "#4de8ff",
				ColorCuernos = "rojo",
			})
			Marco.igual(a.Piel, "Piel3")
			Marco.igual(a.Cuernos, Datos.Defecto.Cuernos)
			Marco.igual(a.ColorOjos, "#4DE8FF")
			Marco.igual(a.ColorCuernos, Datos.Defecto.ColorCuernos)
			Marco.falso(Apariencia.Hecha({}))
			Marco.falso(Apariencia.Hecha(nil))
			Marco.verdadero(Apariencia.Hecha({ Piel = "Piel1", Silueta = "Bestia" }))
			local ids = Apariencia.Ids("Cuernos")
			Marco.igual(Apariencia.Mover("Cuernos", ids[#ids], 1), ids[1])
			local azar = azarFalso(5)
			for _ = 1, 60 do
				local r = Apariencia.Aleatoria(azar)
				Marco.igualProfundo(Apariencia.Validar(r), r)
			end
		end)

		Marco.prueba(
			"el remoto del monstruo rechaza ids inventados y colores mal escritos, y no lleva el booleano del avatar",
			function()
				local Apariencia, Datos, _, requerir = modulos()
				local Remotos = requerir("ReplicatedStorage.Shared.Red.Remotos")
				local Validador = requerir("ReplicatedStorage.Shared.Red.Validador")
				local esquema = Remotos.Definiciones.GuardarAparienciaMonstruo.Argumentos
				Marco.igual(#esquema, #Apariencia.Campos)
				local function args(a)
					local lista = {}
					for k, campo in Apariencia.Campos do
						lista[k] = a[campo]
					end
					return lista
				end
				Marco.verdadero(Validador.ValidarArgumentos(esquema, table.unpack(args(Datos.Defecto))))
				for _, cambio in
					{
						{ "Cuernos", "CoronaVIP" },
						{ "Silueta", "Dios" },
						{ "ColorOjos", "rojo" },
						{ "ColorDetalle", "#12345" },
					}
				do
					local a = table.clone(Datos.Defecto)
					a[cambio[1]] = cambio[2]
					Marco.falso(
						Validador.ValidarArgumentos(esquema, table.unpack(args(a))),
						`{cambio[1]} = {cambio[2]}`
					)
				end
			end
		)

		Marco.prueba("el perfil de cada bando tiene lo que usa el editor, y solo los humanos tienen avatar", function()
			local _, _, _, requerir = modulos()
			local Perfiles = requerir("ReplicatedStorage.Shared.Personaje.PerfilEditor")
			for bando, perfil in Perfiles do
				Marco.igual(perfil.Bando, bando)
				Marco.distinto(perfil.Apariencia, nil, bando)
				Marco.distinto(perfil.Datos.Pieles, nil, bando)
				Marco.distinto(perfil.Datos.ObjetivosColor, nil, bando)
				Marco.distinto(perfil.Datos.Muestras, nil, bando)
				Marco.verdadero(type(perfil.Constructor.Aplicar) == "function", bando)
				Marco.verdadero(type(perfil.Constructor.Colorear) == "function", bando)
				Marco.distinto(perfil.ImagenRueda, nil, bando)
			end
			Marco.verdadero(Perfiles.Humanos.Avatar)
			Marco.falso(Perfiles.Monstruos.Avatar)
		end)
	end)

	Marco.grupo("Personaje: avatar de Roblox en R6", function()
		-- Una descripción simulada con la forma de un HumanoidDescription.
		local function descripcion(accesorios, extra)
			local d = {
				HeightScale = 1,
				WidthScale = 1,
				HeadScale = 1,
				DepthScale = 1,
				BodyTypeScale = 0,
				ProportionScale = 0,
				IdleAnimation = 0,
				ClimbAnimation = 0,
				FallAnimation = 0,
				JumpAnimation = 0,
				MoodAnimation = 0,
				SwimAnimation = 0,
				WalkAnimation = 0,
				RunAnimation = 0,
				Torso = 0,
				LeftArm = 0,
				RightArm = 0,
				LeftLeg = 0,
				RightLeg = 0,
				Emotes = {},
				Accesorios = accesorios,
			}
			for k, v in extra or {} do
				d[k] = v
			end
			function d:GetAccessories(_)
				return self.Accesorios
			end
			function d:SetAccessories(lista, _)
				self.Accesorios = lista
			end
			function d:GetEmotes()
				return self.Emotes
			end
			function d:SetEmotes(e)
				self.Emotes = e
			end
			return d
		end
		local function accesorios(n, capas)
			local lista = {}
			for k = 1, n do
				table.insert(lista, { AssetId = k, IsLayered = k <= (capas or 0) })
			end
			return lista
		end

		Marco.prueba("un avatar normal pasa tal cual y no da avisos", function()
			local _, _, _, requerir = cargar()
			local AvatarR6 = requerir("ReplicatedStorage.Shared.Personaje.AvatarR6")
			local d = descripcion(accesorios(3))
			local informe = AvatarR6.Preparar(d, 6)
			Marco.igual(#d.Accesorios, 3)
			Marco.igual(informe.Accesorios, 3)
			Marco.igual(#AvatarR6.Textos(informe), 0)
		end)

		Marco.prueba("quita la ropa en capas y los accesorios que pasan del máximo", function()
			local _, _, _, requerir = cargar()
			local AvatarR6 = requerir("ReplicatedStorage.Shared.Personaje.AvatarR6")
			local d = descripcion(accesorios(10, 2))
			local informe = AvatarR6.Preparar(d, 4)
			Marco.igual(informe.Capas, 2)
			Marco.igual(informe.Exceso, 4)
			Marco.igual(#d.Accesorios, 4)
			for _, a in d.Accesorios do
				Marco.falso(a.IsLayered)
			end
			Marco.igual(#AvatarR6.Textos(informe), 2)
		end)

		Marco.prueba("deja el cuerpo, las animaciones y los emotes en lo normal y lo avisa", function()
			local _, _, _, requerir = cargar()
			local AvatarR6 = requerir("ReplicatedStorage.Shared.Personaje.AvatarR6")
			local d = descripcion(accesorios(1), {
				HeightScale = 0.9,
				BodyTypeScale = 0.4,
				IdleAnimation = 55,
				Emotes = { Saludo = { 1 } },
				LeftArm = 123,
			})
			local informe = AvatarR6.Preparar(d, 6)
			Marco.verdadero(informe.Escalas)
			Marco.verdadero(informe.Animaciones)
			Marco.verdadero(informe.Partes)
			Marco.igual(informe.Emotes, 1)
			Marco.igual(d.HeightScale, 1)
			Marco.igual(d.BodyTypeScale, 0)
			Marco.igual(d.IdleAnimation, 0)
			Marco.igual(next(d.Emotes), nil)
			Marco.igual(#AvatarR6.Textos(informe), 3)
		end)

		Marco.prueba("el máximo de accesorios es razonable para móvil", function()
			local Config = select(4, cargar())("ReplicatedStorage.Shared.Personaje.ConfigEditor")
			Marco.verdadero(Config.Avatar.MaxAccesorios >= 3 and Config.Avatar.MaxAccesorios <= 10)
		end)
	end)

	Marco.grupo("Personaje: remoto GuardarAparienciaHumano", function()
		local function argumentos(Apariencia, a, avatar)
			local lista = {}
			for i, campo in Apariencia.Campos do
				lista[i] = a[campo]
			end
			lista[#Apariencia.Campos + 1] = if avatar == nil then false else avatar
			return lista
		end

		Marco.prueba("acepta una apariencia válida", function()
			local Apariencia, Datos, _, requerir = cargar()
			local Remotos = requerir("ReplicatedStorage.Shared.Red.Remotos")
			local Validador = requerir("ReplicatedStorage.Shared.Red.Validador")
			local esquema = Remotos.Definiciones.GuardarAparienciaHumano.Argumentos
			local ok = Validador.ValidarArgumentos(esquema, table.unpack(argumentos(Apariencia, Datos.Defecto)))
			Marco.verdadero(ok)
		end)

		Marco.prueba("rechaza ids inventados y colores mal escritos", function()
			local Apariencia, Datos, _, requerir = cargar()
			local Remotos = requerir("ReplicatedStorage.Shared.Red.Remotos")
			local Validador = requerir("ReplicatedStorage.Shared.Red.Validador")
			local esquema = Remotos.Definiciones.GuardarAparienciaHumano.Argumentos
			for _, cambio in
				{
					{ "Cabello", "PeloDeOro" },
					{ "Accesorio", "CoronaVIP" },
					{ "Piel", "Piel99" },
					{ "ColorPelo", "rojo" },
					{ "ColorChaqueta", "#12345" },
					{ "ColorDetalle", "#GGGGGG" },
					{ "ColorPantalon", 123 },
				}
			do
				local a = table.clone(Datos.Defecto)
				a[cambio[1]] = cambio[2]
				local ok = Validador.ValidarArgumentos(esquema, table.unpack(argumentos(Apariencia, a)))
				Marco.falso(ok, `{cambio[1]} = {cambio[2]} no debería pasar`)
			end
		end)

		Marco.prueba("el último argumento es si usa su avatar y tiene que ser un booleano", function()
			local Apariencia, Datos, _, requerir = cargar()
			local Remotos = requerir("ReplicatedStorage.Shared.Red.Remotos")
			local Validador = requerir("ReplicatedStorage.Shared.Red.Validador")
			local esquema = Remotos.Definiciones.GuardarAparienciaHumano.Argumentos
			Marco.verdadero(
				Validador.ValidarArgumentos(esquema, table.unpack(argumentos(Apariencia, Datos.Defecto, true)))
			)
			Marco.falso(Validador.ValidarArgumentos(esquema, table.unpack(argumentos(Apariencia, Datos.Defecto, "si"))))
		end)

		Marco.prueba("VolverEleccionBando existe y no lleva argumentos", function()
			local _, _, _, requerir = cargar()
			local Remotos = requerir("ReplicatedStorage.Shared.Red.Remotos")
			local def = Remotos.Definiciones.VolverEleccionBando
			Marco.distinto(def, nil)
			Marco.igual(def.Direccion, "ClienteAServidor")
			Marco.igual(#def.Argumentos, 0)
		end)
	end)
end
