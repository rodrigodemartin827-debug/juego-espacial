--!strict
--[[
	ServicioTiendas (cliente): une la animación de las persianas y el panel de compra.

	  Mostrador   acércate a una tienda humana y pulsa su aviso (E) para abrir el panel de compra
	  Persiana    cuando un monstruo se acerca, el servidor la baja: aquí se anima (con sonido) y el panel se cierra

	Todo lo que cambia el estado del juego (comprar) es una petición al servidor, que lo comprueba; aquí solo se pide y se
	muestra.
]]

local PanelTienda = require(script.Parent.PanelTienda)
local Persianas = require(script.Parent.Persianas)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

local ServicioTiendas = {}

local iniciado = false

-- Arranca las tiendas del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar() y de ServicioDatos.Iniciar().
function ServicioTiendas.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	PanelTienda.Iniciar()
	Persianas.Iniciar()

	ServicioRed.Conectar("AbrirTienda", function(modelo: any)
		if typeof(modelo) == "Instance" and modelo:IsA("Model") then
			PanelTienda.Abrir(modelo)
		end
	end)
	ServicioRed.Conectar("ResultadoCompra", function(articulo: any, ok: any, mensaje: any)
		if type(articulo) == "string" then
			PanelTienda.AlRecibirResultado(articulo, ok == true, if type(mensaje) == "string" then mensaje else nil)
		end
	end)
end

return ServicioTiendas
