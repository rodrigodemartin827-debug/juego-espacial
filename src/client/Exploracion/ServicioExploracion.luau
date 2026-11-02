--!strict
--[[
	ServicioExploracion (cliente): une el escáner de mano, el pico, el inventario y la mesa de crafteo.

	  Q (mantener)   escanear lo que miras: barra de progreso, efectos de escaneo y, al terminar, la ficha
	  R (mantener)   picar el mineral que tienes delante
	  I              abrir o cerrar la bodega (también la pastilla "Bodega" de abajo a la izquierda)
	  Mesa           acércate a una mesa de crafteo y pulsa su aviso (E) para abrir el panel de recetas

	En móvil, Q y R son botones en pantalla. Todo lo que cambia el estado del juego (escanear, picar, fabricar) es una petición
	al servidor, que lo comprueba; aquí solo se pide y se muestra.
]]

local ContextActionService = game:GetService("ContextActionService")

local Avisos = require(script.Parent.Avisos)
local EfectosEscaneo = require(script.Parent.EfectosEscaneo)
local Escaner = require(script.Parent.Escaner)
local Minado = require(script.Parent.Minado)
local PanelCrafteo = require(script.Parent.PanelCrafteo)
local PanelInventario = require(script.Parent.PanelInventario)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

local ServicioExploracion = {}

local iniciado = false

-- Arranca la exploración del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar() y de ServicioDatos.Iniciar().
function ServicioExploracion.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	PanelInventario.Iniciar()
	PanelCrafteo.Iniciar()
	EfectosEscaneo.Iniciar()
	Escaner.Iniciar()
	Minado.Iniciar()

	ServicioRed.Conectar("AvisoExploracion", function(texto: any, tono: any)
		if type(texto) == "string" then
			Avisos.Mostrar(texto, if type(tono) == "string" then tono else "Info")
		end
	end)
	ServicioRed.Conectar("ResultadoCrafteo", function(receta: any, ok: any, mensaje: any)
		if type(receta) == "string" then
			PanelCrafteo.AlRecibirResultado(receta, ok == true, if type(mensaje) == "string" then mensaje else nil)
		end
	end)
	ServicioRed.Conectar("AbrirMesaCrafteo", function()
		PanelCrafteo.Abrir()
	end)

	-- Tecla I para la bodega (sin botón táctil: en móvil se usa la pastilla).
	ContextActionService:BindAction("AbrirBodega", function(_nombre, estado)
		if estado == Enum.UserInputState.Begin then
			PanelInventario.Alternar()
		end
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.I)
end

return ServicioExploracion
