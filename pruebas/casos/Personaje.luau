--[[
	Pruebas del editor de personaje humano: el catálogo (DatosHumanos), las reglas de la apariencia y el guardado en
	el servidor (ServicioApariencia).
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar()
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir("ReplicatedStorage.Shared.Personaje.Apariencia"),
		entorno.servidor.requerir("ReplicatedStorage.Shared.Personaje.DatosHumanos"),
		entorno
end

local PARTES_R6 =
	{ Head = true, Torso = true, ["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true }

return function(Marco)
	Marco.grupo("Personaje: catálogo humano", function()
		Marco.prueba("cada campo tiene opciones con ids únicos, y el aspecto por defecto existe", function()
			local Apariencia, Datos = cargar()
			for _, campo in Apariencia.Campos do
				local vistos = {}
				local opciones = Apariencia.Opciones(campo)
				Marco.verdadero(#opciones >= 4, campo .. ": al menos 4 opciones")
				for _, o in opciones do
					Marco.esNil(vistos[o.Id], campo .. ": id repetido " .. o.Id)
					vistos[o.Id] = true
					Marco.verdadero(type(o.Nombre) == "string" and o.Nombre ~= "", campo .. ": nombre")
				end
				Marco.distinto(Apariencia.Buscar(campo, Datos.Defecto[campo]), nil, campo .. ": defecto")
			end
		end)

		Marco.prueba("todas las piezas van a una parte del R6 y tienen forma, posición, tamaño y color", function()
			local Apariencia = cargar()
			for _, campo in { "Cara", "Pelo", "Ropa", "Complemento" } do
				for _, o in Apariencia.Opciones(campo) do
					for _, p in o.Piezas do
						Marco.verdadero(p.Parte == nil or PARTES_R6[p.Parte], `{o.Id}: parte {p.Parte}`)
						Marco.verdadero(table.find({ "Bloque", "Bola", "Cilindro" }, p.Forma) ~= nil, o.Id .. ": forma")
						Marco.igual(#p.Pos, 3, o.Id .. ": posición")
						Marco.igual(#p.Tam, 3, o.Id .. ": tamaño")
						Marco.verdadero(type(p.Color) == "string", o.Id .. ": color")
					end
				end
			end
		end)

		Marco.prueba("la ropa colorea cada parte con un color conocido", function()
			local Apariencia = cargar()
			for _, r in Apariencia.Opciones("Ropa") do
				for _, parte in { r.Torso, r.Brazos, r.Piernas } do
					Marco.verdadero(table.find({ "Piel", "Principal", "Detalle", "Oscuro" }, parte) ~= nil, r.Id)
				end
			end
		end)
	end)

	Marco.grupo("Personaje: apariencia", function()
		Marco.prueba("Validar completa lo que falta y cambia lo que no existe por el defecto", function()
			local Apariencia, Datos = cargar()
			local a = Apariencia.Validar({ Piel = "Piel9", Pelo = "NoExiste", Ropa = 3 })
			Marco.igual(a.Piel, "Piel9")
			Marco.igual(a.Pelo, Datos.Defecto.Pelo)
			Marco.igual(a.Ropa, Datos.Defecto.Ropa)
			Marco.igual(a.Cara, Datos.Defecto.Cara)
			Marco.igualProfundo(Apariencia.Validar(nil), Datos.Defecto)
		end)

		Marco.prueba("Hecha solo es verdadero con una apariencia guardada", function()
			local Apariencia = cargar()
			Marco.falso(Apariencia.Hecha({}))
			Marco.falso(Apariencia.Hecha(nil))
			Marco.verdadero(Apariencia.Hecha({ Piel = "Piel1" }))
		end)

		Marco.prueba("Aleatoria siempre da una apariencia válida", function()
			local Apariencia = cargar()
			-- Lune no tiene Random: un generador con la misma forma (NextInteger).
			math.randomseed(7)
			local azar = {
				NextInteger = function(_, a, b)
					return math.random(a, b)
				end,
			}
			for _ = 1, 50 do
				local a = Apariencia.Aleatoria(azar)
				Marco.igualProfundo(Apariencia.Validar(a), a)
			end
		end)
	end)
end
