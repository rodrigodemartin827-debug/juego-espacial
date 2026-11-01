--[[
	Pruebas de AlmacenMemoria: el DataStore falso que ServicioDatos usa en Studio cuando el real no está
	disponible. Debe comportarse como el real en lo que importa: copiar los valores y cancelar con nil.
]]

local Entorno = require("../infraestructura/Entorno")

local function crearAlmacen()
	local AlmacenMemoria = Entorno.nuevo().servidor
		.requerir("ServerScriptService.Server.Servicios.ServicioDatos.AlmacenMemoria")
	return AlmacenMemoria.nuevo()
end

return function(Marco)
	Marco.grupo("AlmacenMemoria", function()
		Marco.prueba("GetAsync devuelve nil para una clave que no existe", function()
			Marco.esNil(crearAlmacen():GetAsync("nada"))
		end)

		Marco.prueba("UpdateAsync crea el valor y la transformación recibe nil la primera vez", function()
			local almacen = crearAlmacen()
			local recibido = "sin llamar"

			local resultado = almacen:UpdateAsync("clave", function(actual)
				recibido = actual
				return { Monedas = 5 }
			end)

			Marco.esNil(recibido)
			Marco.igualProfundo(resultado, { Monedas = 5 })
			Marco.igualProfundo(almacen:GetAsync("clave"), { Monedas = 5 })
		end)

		Marco.prueba("UpdateAsync ve lo guardado antes y puede acumularlo", function()
			local almacen = crearAlmacen()
			almacen:UpdateAsync("clave", function()
				return { Cuenta = 1 }
			end)
			almacen:UpdateAsync("clave", function(actual)
				actual.Cuenta += 1
				return actual
			end)
			Marco.igual(almacen:GetAsync("clave").Cuenta, 2)
		end)

		Marco.prueba("devolver nil cancela la escritura y no cambia lo guardado", function()
			local almacen = crearAlmacen()
			almacen:UpdateAsync("clave", function()
				return { Valor = "original" }
			end)

			local resultado = almacen:UpdateAsync("clave", function(actual)
				actual.Valor = "cambiado"
				return nil
			end)

			Marco.esNil(resultado)
			Marco.igual(almacen:GetAsync("clave").Valor, "original")
		end)

		Marco.prueba("ignora los valores extra que devuelve la transformación (UserIds)", function()
			local almacen = crearAlmacen()
			almacen:UpdateAsync("clave", function()
				return { Valor = 1 }, { 12345 }
			end)
			Marco.igual(almacen:GetAsync("clave").Valor, 1)
		end)

		Marco.prueba("guarda y entrega copias: nunca comparte tablas con quien lo usa", function()
			local almacen = crearAlmacen()
			local original = { Lista = { 1, 2, 3 } }
			almacen:UpdateAsync("clave", function()
				return original
			end)

			original.Lista[1] = 99 -- cambiar lo que se entregó no debe alterar lo guardado
			local leido = almacen:GetAsync("clave")
			Marco.igual(leido.Lista[1], 1)

			leido.Lista[2] = 99 -- ni cambiar lo que se leyó
			Marco.igual(almacen:GetAsync("clave").Lista[2], 2)
		end)
	end)
end
