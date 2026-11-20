--!strict
--[[
	Primitivas: piezas básicas con las que se construye toda la interfaz (marcos, textos, botones, cajas...).

	Así cada pantalla describe QUÉ pone y DÓNDE, y el estilo común (esquinas, bordes, fuentes, hover) vive en un
	solo sitio. Todos los colores, tamaños de letra y tiempos salen de EspacialTheme.

	Uso:
		local P = require(Componentes.Primitivas)
		local caja = P.Caja(padre, { Tamano = UDim2.fromOffset(300, 200), Posicion = UDim2.fromOffset(12, 12) })
		P.Texto(caja, { Texto = "ESTADÍSTICAS", Tamano = Theme.Texto.Grande, Fuente = Theme.Fuentes.Negrita })
		P.Boton(caja, { Texto = "EDITAR", Estilo = "Borde", AlPulsar = function() end })
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)

local C = Theme.Colores
local A = Theme.Alpha

local P = {}

-- ===== Creación genérica =====

-- Crea una instancia, le pone las propiedades y los hijos. Devuelve `any` para poder asignarlo a su tipo.
function P.Crear(clase: string, propiedades: { [string]: any }?, hijos: { Instance }?): any
	local objeto = Instance.new(clase :: any)
	local padre = nil
	if propiedades then
		for clave, valor in propiedades do
			if clave == "Parent" then
				padre = valor
			else
				(objeto :: any)[clave] = valor
			end
		end
	end
	if hijos then
		for _, hijo in hijos do
			hijo.Parent = objeto
		end
	end
	-- El padre se pone el último: así Roblox no replica ni dibuja el objeto a medio configurar.
	if padre then
		objeto.Parent = padre
	end
	return objeto
end

-- Esquinas redondeadas.
function P.Esquinas(padre: GuiObject, radio: UDim?): UICorner
	return P.Crear("UICorner", { CornerRadius = radio or Theme.Tamanos.BorderRadius, Parent = padre })
end

-- Borde (UIStroke del contorno, no del texto).
function P.Borde(padre: GuiObject, color: Color3?, transparencia: number?, grosor: number?): UIStroke
	return P.Crear("UIStroke", {
		Color = color or C.Acento,
		Transparency = transparencia or A.BordeSutil,
		Thickness = grosor or Theme.Tamanos.Trazo,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
		Parent = padre,
	})
end

-- Degradado (UIGradient). `rotacion` en grados: 90 = de arriba abajo.
function P.Degradado(
	padre: GuiObject,
	colores: ColorSequence,
	rotacion: number?,
	transparencia: NumberSequence?
): UIGradient
	return P.Crear("UIGradient", {
		Color = colores,
		Rotation = rotacion or 0,
		Transparency = transparencia or NumberSequence.new(0),
		Parent = padre,
	})
end

-- Márgenes interiores.
function P.Relleno(padre: GuiObject, arriba: number, derecha: number?, abajo: number?, izquierda: number?): UIPadding
	local d = derecha or arriba
	return P.Crear("UIPadding", {
		PaddingTop = UDim.new(0, arriba),
		PaddingRight = UDim.new(0, d),
		PaddingBottom = UDim.new(0, abajo or arriba),
		PaddingLeft = UDim.new(0, izquierda or d),
		Parent = padre,
	})
end

-- Lista (vertical u horizontal) con separación.
function P.Lista(
	padre: GuiObject,
	direccion: Enum.FillDirection,
	separacion: number,
	alineacionH: Enum.HorizontalAlignment?,
	alineacionV: Enum.VerticalAlignment?
): UIListLayout
	return P.Crear("UIListLayout", {
		FillDirection = direccion,
		Padding = UDim.new(0, separacion),
		HorizontalAlignment = alineacionH or Enum.HorizontalAlignment.Left,
		VerticalAlignment = alineacionV or Enum.VerticalAlignment.Top,
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = padre,
	})
end

-- ===== Marcos =====

export type OpcionesMarco = {
	Nombre: string?,
	Tamano: UDim2?,
	Posicion: UDim2?,
	Ancla: Vector2?,
	Color: Color3?,
	Transparencia: number?,
	Radio: UDim?,
	Z: number?,
	Orden: number?,
	Recortar: boolean?,
}

-- Marco transparente o de color.
function P.Marco(padre: Instance?, o: OpcionesMarco?): Frame
	local op: OpcionesMarco = o or {}
	local marco = P.Crear("Frame", {
		Name = op.Nombre or "Marco",
		Size = op.Tamano or UDim2.fromScale(1, 1),
		Position = op.Posicion or UDim2.new(),
		AnchorPoint = op.Ancla or Vector2.zero,
		BackgroundColor3 = op.Color or C.Fondo1,
		BackgroundTransparency = if op.Transparencia then op.Transparencia elseif op.Color then 0 else 1,
		BorderSizePixel = 0,
		ZIndex = op.Z or 1,
		LayoutOrder = op.Orden or 0,
		ClipsDescendants = op.Recortar == true,
		Parent = padre,
	}) :: Frame
	if op.Radio then
		P.Esquinas(marco, op.Radio)
	end
	return marco
end

-- Grupo con transparencia de grupo (para fundidos). Ojo: dibuja a textura; usarlo solo en ventanas y vistas.
function P.Grupo(padre: Instance?, o: OpcionesMarco?): CanvasGroup
	local op: OpcionesMarco = o or {}
	return P.Crear("CanvasGroup", {
		Name = op.Nombre or "Grupo",
		Size = op.Tamano or UDim2.fromScale(1, 1),
		Position = op.Posicion or UDim2.new(),
		AnchorPoint = op.Ancla or Vector2.zero,
		BackgroundColor3 = op.Color or C.Fondo1,
		BackgroundTransparency = if op.Transparencia then op.Transparencia elseif op.Color then 0 else 1,
		BorderSizePixel = 0,
		ZIndex = op.Z or 1,
		LayoutOrder = op.Orden or 0,
		Parent = padre,
	}) :: CanvasGroup
end

-- Caja de contenido dentro de una ventana: fondo azul marino translúcido, borde cian sutil y esquinas de 8.
function P.Caja(padre: Instance?, o: OpcionesMarco?): Frame
	local op: OpcionesMarco = o or {}
	local caja = P.Marco(padre, {
		Nombre = op.Nombre or "Caja",
		Tamano = op.Tamano,
		Posicion = op.Posicion,
		Ancla = op.Ancla,
		Color = op.Color or C.Fondo1,
		Transparencia = op.Transparencia or A.Caja,
		Z = op.Z,
		Orden = op.Orden,
		Recortar = op.Recortar,
	})
	P.Esquinas(caja, op.Radio or Theme.Tamanos.BorderRadius)
	P.Borde(caja, C.Acento, A.BordeSutil)
	return caja
end

-- ===== Texto =====

-- Separa las letras con espacios finos (U+2009): imita el letter-spacing de los títulos, que Roblox no tiene.
function P.Espaciar(texto: string): string
	local letras = {}
	for _, codigo in utf8.codes(texto) do
		table.insert(letras, utf8.char(codigo))
	end
	return table.concat(letras, "\u{2009}")
end

export type OpcionesTexto = {
	Nombre: string?,
	Texto: string?,
	Tamano: number?, -- tamaño de letra (Theme.Texto)
	Fuente: Font?,
	Color: Color3?,
	Transparencia: number?,
	AlineacionX: Enum.TextXAlignment?,
	AlineacionY: Enum.TextYAlignment?,
	Caja: UDim2?, -- tamaño del TextLabel (por defecto se ajusta al texto)
	Posicion: UDim2?,
	Ancla: Vector2?,
	Z: number?,
	Orden: number?,
	Envolver: boolean?,
	Rico: boolean?, -- RichText
	Contorno: boolean?, -- contorno oscuro para leerse sobre el mundo (HUD)
	Espaciado: boolean?, -- letras separadas (títulos)
}

function P.Texto(padre: Instance?, o: OpcionesTexto): TextLabel
	local texto = o.Texto or ""
	local etiqueta = P.Crear("TextLabel", {
		Name = o.Nombre or "Texto",
		Text = if o.Espaciado then P.Espaciar(texto) else texto,
		TextSize = o.Tamano or Theme.Texto.Cuerpo,
		FontFace = o.Fuente or Theme.Fuentes.Titulo,
		TextColor3 = o.Color or C.TextoPrincipal,
		TextTransparency = o.Transparencia or 0,
		TextXAlignment = o.AlineacionX or Enum.TextXAlignment.Left,
		TextYAlignment = o.AlineacionY or Enum.TextYAlignment.Center,
		TextWrapped = o.Envolver == true,
		RichText = o.Rico == true,
		BackgroundTransparency = 1,
		Size = o.Caja or UDim2.new(),
		AutomaticSize = if o.Caja then Enum.AutomaticSize.None else Enum.AutomaticSize.XY,
		Position = o.Posicion or UDim2.new(),
		AnchorPoint = o.Ancla or Vector2.zero,
		ZIndex = o.Z or 1,
		LayoutOrder = o.Orden or 0,
		Parent = padre,
	}) :: TextLabel
	if o.Contorno then
		P.Crear("UIStroke", {
			Color = C.Negro,
			Transparency = 0.35,
			Thickness = 1,
			ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual,
			Parent = etiqueta,
		})
	end
	return etiqueta
end

-- Texto secundario (gris de 40 %), para etiquetas de sección ("PASIVAS", "MODOS"...).
function P.Etiqueta(padre: Instance?, texto: string, o: OpcionesTexto?): TextLabel
	local op: OpcionesTexto = o or {}
	op.Texto = texto
	op.Tamano = op.Tamano or Theme.Texto.Mini
	op.Fuente = op.Fuente or Theme.Fuentes.Negrita
	op.Color = op.Color or C.TextoSecundario
	op.Transparencia = op.Transparencia or A.TextoSecundario
	op.Espaciado = if op.Espaciado == nil then true else op.Espaciado
	return P.Texto(padre, op)
end

-- ===== Formato de números =====

-- 12450 -> "12.450"; 1247 -> "1.247" (siempre con punto de miles).
function P.Numero(n: number): string
	local entero = math.floor(math.abs(n) + 0.5)
	local s = tostring(entero)
	local conPuntos = string.reverse((string.gsub(string.reverse(s), "(%d%d%d)", "%1.")))
	if string.sub(conPuntos, 1, 1) == "." then
		conPuntos = string.sub(conPuntos, 2)
	end
	return (if n < 0 then "-" else "") .. conPuntos
end

-- 0.9 -> "0,9"; 16 -> "16" (decimales con coma).
function P.Decimal(n: number, decimales: number?): string
	if n == math.floor(n) then
		return P.Numero(n)
	end
	local s = string.format(`%.{decimales or 1}f`, n)
	return (string.gsub(s, "%.", ","))
end

-- 154 -> "02:34".
function P.MinSeg(segundos: number): string
	local s = math.max(0, math.floor(segundos))
	return string.format("%02d:%02d", s // 60, s % 60)
end

-- ===== Botones =====

export type EstiloBoton = "Cian" | "Dorado" | "Verde" | "Rojo" | "Gris" | "Borde"

local ESTILOS: {
	[string]: {
		Fondo: ColorSequence?,
		Color: Color3,
		Transparencia: number,
		Texto: Color3,
		Borde: Color3?,
		BordeT: number?,
	},
} =
	{
		Cian = { Fondo = Theme.Degradados.Cian, Color = C.Blanco, Transparencia = 0, Texto = C.TextoSobreAcento },
		Dorado = { Fondo = Theme.Degradados.Dorado, Color = C.Blanco, Transparencia = 0, Texto = C.TextoSobreDorado },
		Verde = { Fondo = Theme.Degradados.Verde, Color = C.Blanco, Transparencia = 0, Texto = C.TextoSobreExito },
		Rojo = { Color = C.Peligro, Transparencia = 0.86, Texto = C.PeligroClaro, Borde = C.Peligro, BordeT = 0.55 },
		Gris = { Color = C.Blanco, Transparencia = 0.93, Texto = C.TextoPrincipal, Borde = C.Blanco, BordeT = 0.88 },
		Borde = { Color = C.Acento, Transparencia = 0.92, Texto = C.Acento, Borde = C.Acento, BordeT = A.BordeActivo },
	}

export type OpcionesBoton = {
	Nombre: string?,
	Texto: string,
	Estilo: EstiloBoton?,
	Tamano: UDim2?,
	Posicion: UDim2?,
	Ancla: Vector2?,
	TamanoTexto: number?,
	Orden: number?,
	Z: number?,
	AlPulsar: (() -> ())?,
}

-- Botón con estilo, hover (escala 1,05) y esquinas. Devuelve el TextButton.
function P.Boton(padre: Instance?, o: OpcionesBoton): TextButton
	local estilo = ESTILOS[o.Estilo or "Cian"]
	local boton = P.Crear("TextButton", {
		Name = o.Nombre or "Boton",
		Text = P.Espaciar(o.Texto),
		TextSize = o.TamanoTexto or Theme.Texto.Cuerpo,
		FontFace = Theme.Fuentes.Negrita,
		TextColor3 = estilo.Texto,
		AutoButtonColor = false,
		BackgroundColor3 = estilo.Color,
		BackgroundTransparency = estilo.Transparencia,
		BorderSizePixel = 0,
		Size = o.Tamano or UDim2.fromOffset(110, 24),
		Position = o.Posicion or UDim2.new(),
		AnchorPoint = o.Ancla or Vector2.zero,
		LayoutOrder = o.Orden or 0,
		ZIndex = o.Z or 1,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, Theme.Tamanos.RadioBoton)
	if estilo.Fondo then
		P.Degradado(boton, estilo.Fondo, 90)
	end
	if estilo.Borde then
		P.Borde(boton, estilo.Borde, estilo.BordeT, Theme.Tamanos.Trazo)
	end
	UITweens.Hover(boton)
	if o.AlPulsar then
		local alPulsar = o.AlPulsar
		boton.Activated:Connect(function()
			if boton.Active then
				alPulsar()
			end
		end)
	end
	return boton
end

-- Activa o desactiva un botón (desactivado: 35 % de opacidad y no responde).
function P.Habilitar(boton: GuiButton, activo: boolean)
	boton.Active = activo
	boton.AutoButtonColor = false
	local t = if activo then 0 else 0.65
	if boton:IsA("TextButton") then
		boton.TextTransparency = t
	end
	for _, hijo in boton:GetDescendants() do
		if hijo:IsA("ImageLabel") then
			hijo.ImageTransparency = t
		end
	end
end

-- Insignia de tecla ("P", "Z", "1"...): cuadradito oscuro con borde claro.
function P.Tecla(padre: Instance?, tecla: string, o: OpcionesMarco?): TextLabel
	local op: OpcionesMarco = o or {}
	local etiqueta = P.Crear("TextLabel", {
		Name = "Tecla",
		Text = tecla,
		TextSize = Theme.Texto.Pequeno,
		FontFace = Theme.Fuentes.Negrita,
		TextColor3 = C.TextoPrincipal,
		BackgroundColor3 = C.FondoProfundo,
		BackgroundTransparency = 0.15,
		Size = op.Tamano or UDim2.fromOffset(13, 13),
		AutomaticSize = Enum.AutomaticSize.X,
		Position = op.Posicion or UDim2.new(),
		AnchorPoint = op.Ancla or Vector2.zero,
		ZIndex = op.Z or 1,
		Parent = padre,
	}) :: TextLabel
	P.Esquinas(etiqueta, UDim.new(0, 3))
	P.Borde(etiqueta, C.Blanco, 0.78, Theme.Tamanos.Trazo)
	P.Relleno(etiqueta, 0, 3)
	return etiqueta
end

-- Barra de progreso fina (XP, ELO, bodega...). Devuelve el fondo y el relleno.
function P.BarraProgreso(padre: Instance?, o: OpcionesMarco, degradado: ColorSequence?): (Frame, Frame)
	local fondo = P.Marco(padre, {
		Nombre = o.Nombre or "Barra",
		Tamano = o.Tamano,
		Posicion = o.Posicion,
		Ancla = o.Ancla,
		Color = C.Negro,
		Transparencia = 0.55,
		Radio = UDim.new(1, 0),
		Orden = o.Orden,
		Z = o.Z,
	})
	local relleno = P.Marco(fondo, {
		Nombre = "Relleno",
		Tamano = UDim2.fromScale(0, 1),
		Color = C.Blanco,
		Radio = UDim.new(1, 0),
		Z = (o.Z or 1) + 1,
	})
	P.Degradado(relleno, degradado or Theme.Degradados.Escudo, 0)
	return fondo, relleno
end

return P
