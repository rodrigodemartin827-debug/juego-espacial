--!strict
--[[
	Notificacion: avisos cortos que entran por la derecha ("Equipado: Espada de Plasma", "Compra realizada"...).

	  [▌icono  Título            ]   barra izquierda del color del aviso
	  [▌       texto secundario  ]

	Se apilan (el más nuevo arriba), duran Theme.Tiempos.DuracionToast y se reutilizan los marcos (pool) para no crear
	y destruir instancias en cada aviso. En partida van bajo el minimapa; con un menú abierto, arriba a la derecha.
	El ajuste "Notificaciones" las desactiva.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local Notificacion = {}

local MAXIMO = 4 -- avisos a la vez
local ANCHO = 216

export type Aviso = {
	Titulo: string,
	Texto: string?,
	Color: Color3?,
	Icono: string?, -- icono de una tinta
	Arte: string?, -- o arte a color
}

local contenedor: Frame? = nil
local activadas = true
local orden = 0

function Notificacion.Iniciar(raiz: Frame)
	local marco = P.Marco(raiz, {
		Nombre = "Notificaciones",
		Tamano = UDim2.fromOffset(ANCHO, 300),
		Posicion = UDim2.new(1, -14, 0, 190),
		Ancla = Vector2.new(1, 0),
		Z = 90,
	})
	P.Lista(marco, Enum.FillDirection.Vertical, 6, Enum.HorizontalAlignment.Right)
	contenedor = marco
end

-- Coloca los avisos según haya un menú abierto o no.
function Notificacion.ModoMenu(menu: boolean)
	local marco = contenedor
	if marco then
		UITweens.Tween(
			marco,
			Theme.Tweens.Normal,
			{ Position = if menu then UDim2.new(1, -24, 0, 56) else UDim2.new(1, -14, 0, 190) }
		)
	end
end

function Notificacion.Activar(valor: boolean)
	activadas = valor
end

function Notificacion.Mostrar(aviso: Aviso)
	local marco = contenedor
	if marco == nil or not activadas then
		return
	end
	-- Si hay demasiados, el más antiguo se va ya.
	local actuales = {}
	for _, hijo in marco:GetChildren() do
		if hijo:IsA("CanvasGroup") then
			table.insert(actuales, hijo)
		end
	end
	table.sort(actuales, function(a, b)
		return a.LayoutOrder > b.LayoutOrder
	end)
	for i = MAXIMO, #actuales do
		actuales[i]:Destroy()
	end

	orden -= 1
	local color = aviso.Color or C.Acento
	local toast = P.Grupo(marco, {
		Nombre = "Aviso",
		Tamano = UDim2.fromOffset(ANCHO, 38),
		Color = C.FondoProfundo,
		Transparencia = 0.06,
		Orden = orden,
		Z = 91,
	})
	P.Esquinas(toast, UDim.new(0, 7))
	P.Borde(toast, color, 0.55)
	P.Marco(toast, { Nombre = "Barra", Tamano = UDim2.new(0, 3, 1, 0), Color = color, Z = 92 })
	if aviso.Arte then
		IconBuilder.Arte(toast, aviso.Arte, {
			Tamano = 22,
			Posicion = UDim2.new(0, 10, 0.5, 0),
			Ancla = Vector2.new(0, 0.5),
			Z = 92,
			ColorRespaldo = color,
		})
	else
		IconBuilder.Icono(
			toast,
			aviso.Icono or "ui_check",
			{ Tamano = 16, Color = color, Posicion = UDim2.new(0, 12, 0.5, 0), Ancla = Vector2.new(0, 0.5), Z = 92 }
		)
	end
	P.Texto(toast, {
		Texto = aviso.Titulo,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.fromOffset(40, if aviso.Texto then 7 else 13),
		Z = 92,
	})
	if aviso.Texto then
		P.Texto(toast, {
			Texto = aviso.Texto,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.TextoSecundario,
			Transparencia = Theme.Alpha.TextoSecundario,
			Caja = UDim2.new(1, -48, 0, 12),
			Posicion = UDim2.fromOffset(40, 20),
			Z = 92,
		}).TextTruncate =
			Enum.TextTruncate.AtEnd
	end

	-- Entra deslizándose desde la derecha y se va con un fundido.
	toast.GroupTransparency = 1
	local escala = UITweens.EscalaDe(toast)
	escala.Scale = 0.9
	UITweens.Tween(toast, Theme.Tweens.Toast, { GroupTransparency = 0 })
	UITweens.Tween(escala, Theme.Tweens.Rebote, { Scale = 1 })
	task.delay(Theme.Tiempos.DuracionToast, function()
		if toast.Parent then
			local salida = UITweens.Tween(toast, Theme.Tweens.Toast, { GroupTransparency = 1 })
			salida.Completed:Once(function()
				toast:Destroy()
			end)
		end
	end)
end

return Notificacion
