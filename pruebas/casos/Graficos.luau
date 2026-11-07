--[[
	Pruebas de los gráficos: los datos de los niveles, la recomendación, cuándo sale la pantalla y el guardado del
	nivel en el servidor (remoto ElegirGraficos).
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(ruta), entorno
end

return function(Marco)
	Marco.grupo("Graficos: niveles", function()
		Marco.prueba("los cuatro niveles existen, en orden, y con todos sus datos", function()
			local Config = cargar("ReplicatedStorage.Shared.Graficos.Config")
			Marco.igualProfundo(Config.Orden, { "Baja", "Media", "Alta", "Ultra" })
			for _, nombre in Config.Orden do
				local n = Config.Niveles[nombre]
				Marco.distinto(n, nil, nombre)
				Marco.verdadero(table.find({ "Bajo", "Medio", "Alto" }, n.Calidad) ~= nil, nombre .. ": Calidad")
				Marco.verdadero(n.Densidad > 0 and n.Densidad <= 1, nombre .. ": Densidad")
				Marco.verdadero(n.Distancia > 0 and n.Vegetacion > 0 and n.Arboles > 0, nombre .. ": distancias")
				Marco.verdadero(n.ArbolesLejos > 0 and n.ArbolesLejos <= 1, nombre .. ": ArbolesLejos")
			end
		end)

		Marco.prueba("cada nivel gasta lo mismo o más que el anterior", function()
			local Config = cargar("ReplicatedStorage.Shared.Graficos.Config")
			for i = 2, #Config.Orden do
				local a, b = Config.Niveles[Config.Orden[i - 1]], Config.Niveles[Config.Orden[i]]
				Marco.verdadero(
					b.Distancia >= a.Distancia
						and b.Vegetacion >= a.Vegetacion
						and b.Densidad >= a.Densidad
						and b.Arboles >= a.Arboles
						and b.ArbolesLejos >= a.ArbolesLejos
				)
				Marco.verdadero(#b.Postefectos >= #a.Postefectos)
			end
		end)

		Marco.prueba(
			"recomendación: móvil sencillo Baja, móvil Media, ordenador Alta, ordenador potente Ultra",
			function()
				local Niveles = cargar("ReplicatedStorage.Shared.Graficos.Niveles")
				Marco.igual(Niveles.Recomendado(true, 2), "Baja")
				Marco.igual(Niveles.Recomendado(true, 0), "Media", "automático en móvil")
				Marco.igual(Niveles.Recomendado(true, 7), "Media")
				Marco.igual(Niveles.Recomendado(false, 0), "Alta")
				Marco.igual(Niveles.Recomendado(false, 10), "Ultra")
			end
		)

		Marco.prueba("la pantalla sale si nunca ha elegido, y siempre en Studio con el modo de pruebas", function()
			local Niveles, entorno = cargar("ReplicatedStorage.Shared.Graficos.Niveles")
			local Config = entorno.servidor.requerir("ReplicatedStorage.Shared.Graficos.Config")
			Marco.verdadero(Niveles.HayQueMostrar("", false))
			Marco.falso(Niveles.HayQueMostrar("Media", false))
			Config.MostrarSiempreEnStudio = true
			Marco.verdadero(Niveles.HayQueMostrar("Media", true))
			Config.MostrarSiempreEnStudio = false
			Marco.falso(Niveles.HayQueMostrar("Media", true))
		end)
	end)
end
