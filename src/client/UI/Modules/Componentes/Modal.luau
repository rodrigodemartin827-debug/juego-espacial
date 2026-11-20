--!strict
--[[
	Modal: ventana de confirmación ("¿Comprar Espada de Plasma por 5.000 monedas?", "¿Dejar el clan?",
	"¿Restaurar valores?"...). Oscurece el resto y aparece con escala 0,95 → 1.

	  Modal.Confirmar({ Titulo = "¿CONFIRMAR COMPRA?", Texto = "...", Arte = "item_espada_plasma",
	                    TextoSi = "COMPRAR", EstiloSi = "Cian", AlSi = function() ... end })
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local Modal = {}

export type Opciones = {
	Titulo: string,
	Texto: string, -- admite RichText (<b>...</b>)
	Icono: string?,
	Arte: string?,
	Color: Color3?,
	TextoSi: string?, -- nil = sin botón de aceptar
	EstiloSi: P.EstiloBoton?,
	TextoNo: string?,
	AlSi: (() -> ())?,
	-- Contenido extra bajo el texto (por ejemplo, los paquetes de gemas). Recibe el marco donde dibujarlo.
	Extra: ((marco: Frame, cerrar: () -> ()) -> ())?,
}

local velo: TextButton? = nil
local caja: CanvasGroup? = nil
local abierto = false

function Modal.Iniciar(raiz: Frame)
	local fondo = P.Crear("TextButton", {
		Name = "Modal",
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = C.FondoNegro,
		BackgroundTransparency = 1,
		ZIndex = 80,
		Visible = false,
		Parent = raiz,
	}) :: TextButton
	-- Clic fuera de la caja = cancelar.
	fondo.Activated:Connect(function()
		Modal.Cerrar()
	end)
	local g = P.Grupo(fondo, {
		Nombre = "Caja",
		Tamano = UDim2.fromOffset(310, 0),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Color = C.Blanco,
		Transparencia = 0,
		Z = 81,
	})
	g.AutomaticSize = Enum.AutomaticSize.Y
	P.Degradado(g, ColorSequence.new(C.Fondo2, C.Fondo3), 35)
	P.Esquinas(g, Theme.Tamanos.RadioVentana)
	P.Borde(g, C.Acento, Theme.Alpha.BordeActivo)
	P.Relleno(g, 18)
	P.Lista(g, Enum.FillDirection.Vertical, 8, Enum.HorizontalAlignment.Center)
	-- La caja se come los clics para que no lleguen al velo (que cierra el modal).
	g.Active = true
	velo = fondo
	caja = g
end

local function limpiar(g: CanvasGroup)
	for _, hijo in g:GetChildren() do
		if
			not (
				hijo:IsA("UIPadding")
				or hijo:IsA("UIListLayout")
				or hijo:IsA("UICorner")
				or hijo:IsA("UIStroke")
				or hijo:IsA("UIGradient")
			)
		then
			hijo:Destroy()
		end
	end
end

function Modal.Cerrar()
	local fondo, g = velo, caja
	if fondo == nil or g == nil or not abierto then
		return
	end
	abierto = false
	UITweens.Tween(fondo, Theme.Tweens.Rapido, { BackgroundTransparency = 1 })
	local t = UITweens.Tween(g, Theme.Tweens.Rapido, { GroupTransparency = 1 })
	t.Completed:Once(function(estado)
		if estado == Enum.PlaybackState.Completed and not abierto then
			fondo.Visible = false
		end
	end)
end

function Modal.EstaAbierto(): boolean
	return abierto
end

function Modal.Confirmar(o: Opciones)
	local fondo, g = velo, caja
	if fondo == nil or g == nil then
		return
	end
	limpiar(g)
	local color = o.Color or C.Dorado
	if o.Arte then
		IconBuilder.Arte(g, o.Arte, { Tamano = 48, Orden = 1, Z = 82, ColorRespaldo = color })
	else
		IconBuilder.Icono(g, o.Icono or "ui_alerta", { Tamano = 44, Color = color, Orden = 1, Z = 82 })
	end
	P.Texto(g, {
		Texto = o.Titulo,
		Tamano = Theme.Texto.Titulo,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Orden = 2,
		Z = 82,
	})
	local texto = P.Texto(g, {
		Texto = o.Texto,
		Rico = true,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Medio,
		Color = C.TextoPrincipal,
		Transparencia = Theme.Alpha.TextoMedio,
		AlineacionX = Enum.TextXAlignment.Center,
		Caja = UDim2.new(1, 0, 0, 0),
		Envolver = true,
		Orden = 3,
		Z = 82,
	})
	texto.AutomaticSize = Enum.AutomaticSize.Y
	if o.Extra then
		local extra = P.Marco(g, { Nombre = "Extra", Tamano = UDim2.new(1, 0, 0, 0), Orden = 4, Z = 82 })
		extra.AutomaticSize = Enum.AutomaticSize.Y
		o.Extra(extra, Modal.Cerrar)
	end
	local botones = P.Marco(g, { Nombre = "Botones", Tamano = UDim2.new(1, 0, 0, 28), Orden = 5, Z = 82 })
	P.Lista(botones, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	if o.TextoNo ~= "" then
		P.Boton(botones, {
			Texto = o.TextoNo or "CANCELAR",
			Estilo = "Gris",
			Tamano = UDim2.fromOffset(104, 28),
			Orden = 1,
			Z = 83,
			AlPulsar = Modal.Cerrar,
		})
	end
	if o.TextoSi then
		local alSi = o.AlSi
		P.Boton(botones, {
			Texto = o.TextoSi,
			Estilo = o.EstiloSi or "Cian",
			Tamano = UDim2.fromOffset(104, 28),
			Orden = 2,
			Z = 83,
			AlPulsar = function()
				Modal.Cerrar()
				if alSi then
					alSi()
				end
			end,
		})
	end

	abierto = true
	fondo.Visible = true
	UITweens.Tween(fondo, Theme.Tweens.Rapido, { BackgroundTransparency = Theme.Alpha.Velo })
	UITweens.Aparecer(g)
end

return Modal
