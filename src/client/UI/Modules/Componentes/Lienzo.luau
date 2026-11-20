--!strict
--[[
	Lienzo: marco raíz de la interfaz, diseñado a 960×540 unidades y escalado para llenar la pantalla.

	Truco: un UIScale de escala s hace que todo mida s veces más. Si el marco raíz mide (ancho/s, alto/s) unidades, tras
	escalarlo mide exactamente la pantalla, y sus hijos se pueden anclar a las esquinas con posiciones en unidades de
	diseño (por ejemplo, la barra lateral siempre a 10 unidades del borde izquierdo).

	  s = clamp(min(ancho / 960, alto / 540), EscalaMinima, EscalaMaxima)

	A 1280×720 s = 1,33; a 1920×1080 s = 2. El preview HTML hace lo mismo (transform: scale) para que se vea igual.
	La ScreenGui debe tener IgnoreGuiInset = true (el lienzo ocupa toda la pantalla; los elementos de arriba ya dejan
	sitio a los botones de Roblox).
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)

local T = Theme.Tamanos

local Lienzo = {}

export type Lienzo = {
	Raiz: Frame,
	Escala: UIScale,
	-- Unidades de diseño por píxel de pantalla (para convertir AbsolutePosition a posiciones del lienzo).
	AUnidades: (pixeles: Vector2) -> Vector2,
}

-- Crea el lienzo dentro de `gui` (o de `padre`, si es un marco a pantalla completa) y lo mantiene escalado.
function Lienzo.Crear(gui: ScreenGui, nombre: string, z: number?): Lienzo
	local raiz = Instance.new("Frame")
	raiz.Name = nombre
	raiz.BackgroundTransparency = 1
	raiz.BorderSizePixel = 0
	raiz.ZIndex = z or 1
	raiz.Size = UDim2.fromOffset(T.AnchoDiseno, T.AltoDiseno)
	local escala = Instance.new("UIScale")
	escala.Parent = raiz
	raiz.Parent = gui

	local function ajustar()
		local tamano = gui.AbsoluteSize
		if tamano.X <= 0 or tamano.Y <= 0 then
			return
		end
		local s =
			math.clamp(math.min(tamano.X / T.AnchoDiseno, tamano.Y / T.AltoDiseno), T.EscalaMinima, T.EscalaMaxima)
		escala.Scale = s
		raiz.Size = UDim2.fromOffset(tamano.X / s, tamano.Y / s)
	end
	gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(ajustar)
	ajustar()

	return {
		Raiz = raiz,
		Escala = escala,
		AUnidades = function(pixeles: Vector2): Vector2
			return (pixeles - raiz.AbsolutePosition) / escala.Scale
		end,
	}
end

--[[
	Escala adicional para una parte del lienzo (el ajuste "Tamaño del HUD"). Devuelve un marco a pantalla completa cuyos
	hijos se ven `k` veces más grandes, sin salirse de la pantalla: el marco mide 1/k y el UIScale lo devuelve a 1.
	Llama a la función devuelta con otro k para cambiarla.
]]
function Lienzo.SubEscala(padre: Frame, nombre: string): (Frame, (k: number) -> ())
	local marco = Instance.new("Frame")
	marco.Name = nombre
	marco.BackgroundTransparency = 1
	marco.BorderSizePixel = 0
	marco.AnchorPoint = Vector2.new(0.5, 0.5)
	marco.Position = UDim2.fromScale(0.5, 0.5)
	marco.Size = UDim2.fromScale(1, 1)
	local escala = Instance.new("UIScale")
	escala.Parent = marco
	marco.Parent = padre
	return marco,
		function(k: number)
			local valor = math.clamp(k, 0.5, 2)
			escala.Scale = valor
			marco.Size = UDim2.fromScale(1 / valor, 1 / valor)
		end
end

return Lienzo
