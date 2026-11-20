--!strict
--[[
	Controles: los mandos de la pantalla de Ajustes.

	  - Deslizador: pista con relleno cian, asa que se arrastra (ratón y táctil) y el valor a la derecha.
	  - Interruptor: pastilla on/off; la bola se desliza (0,2 s).
	  - Desplegable: caja con flecha y lista de opciones que se abre debajo.
	  - Tecla: botón con la tecla actual; al pulsarlo espera a que pulses otra. Puede estar bloqueado.

	Cada uno llama a `AlCambiar(valor)` cuando el jugador lo cambia.
]]

local UserInputService = game:GetService("UserInputService")

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local Controles = {}

-- ===== Deslizador =====

export type OpcionesDeslizador = {
	Min: number,
	Max: number,
	Valor: number,
	Unidad: string?,
	AlCambiar: (valor: number) -> (),
}

function Controles.Deslizador(padre: Instance, o: OpcionesDeslizador): Frame
	local marco = P.Marco(padre, { Nombre = "Deslizador", Tamano = UDim2.fromOffset(214, 16), Z = 5 })
	local zona = P.Crear("TextButton", {
		Name = "Zona",
		Text = "",
		AutoButtonColor = false,
		BackgroundTransparency = 1,
		Size = UDim2.fromOffset(170, 16),
		ZIndex = 5,
		Parent = marco,
	}) :: TextButton
	local pista = P.Marco(zona, {
		Nombre = "Pista",
		Tamano = UDim2.new(1, 0, 0, 4),
		Posicion = UDim2.fromScale(0, 0.5),
		Ancla = Vector2.new(0, 0.5),
		Color = C.Negro,
		Transparencia = 0.5,
		Radio = UDim.new(1, 0),
		Z = 5,
	})
	P.Borde(pista, C.Blanco, 0.92)
	local lleno = P.Marco(
		pista,
		{ Nombre = "Lleno", Tamano = UDim2.fromScale(0, 1), Color = C.Blanco, Radio = UDim.new(1, 0), Z = 6 }
	)
	P.Degradado(lleno, Theme.Degradados.Escudo, 0)
	local asa = P.Marco(zona, {
		Nombre = "Asa",
		Tamano = UDim2.fromOffset(12, 12),
		Posicion = UDim2.fromScale(0, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Color = C.AcentoClaro,
		Radio = UDim.new(1, 0),
		Z = 7,
	})
	P.Borde(asa, C.Acento, 0, Theme.Tamanos.TrazoGrueso)
	local texto = P.Texto(marco, {
		Texto = "",
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		AlineacionX = Enum.TextXAlignment.Right,
		Caja = UDim2.fromOffset(38, 16),
		Posicion = UDim2.fromScale(1, 0),
		Ancla = Vector2.new(1, 0),
		Z = 5,
	})

	local valor = o.Valor
	local function pintar()
		local p = (valor - o.Min) / math.max(o.Max - o.Min, 1)
		lleno.Size = UDim2.fromScale(p, 1)
		asa.Position = UDim2.fromScale(p, 0.5)
		texto.Text = P.Numero(valor) .. (o.Unidad or "")
	end
	pintar()

	local arrastrando = false
	local function mover(x: number)
		local p = math.clamp((x - zona.AbsolutePosition.X) / math.max(zona.AbsoluteSize.X, 1), 0, 1)
		local nuevo = math.floor(o.Min + p * (o.Max - o.Min) + 0.5)
		if nuevo ~= valor then
			valor = nuevo
			pintar()
			o.AlCambiar(valor)
		end
	end
	zona.InputBegan:Connect(function(entrada)
		if
			entrada.UserInputType == Enum.UserInputType.MouseButton1
			or entrada.UserInputType == Enum.UserInputType.Touch
		then
			arrastrando = true
			mover(entrada.Position.X)
			UITweens.Tween(UITweens.EscalaDe(asa), Theme.Tweens.Rapido, { Scale = 1.2 })
		end
	end)
	UserInputService.InputChanged:Connect(function(entrada)
		if
			arrastrando
			and (
				entrada.UserInputType == Enum.UserInputType.MouseMovement
				or entrada.UserInputType == Enum.UserInputType.Touch
			)
		then
			mover(entrada.Position.X)
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada)
		if
			arrastrando
			and (
				entrada.UserInputType == Enum.UserInputType.MouseButton1
				or entrada.UserInputType == Enum.UserInputType.Touch
			)
		then
			arrastrando = false
			UITweens.Tween(UITweens.EscalaDe(asa), Theme.Tweens.Rapido, { Scale = 1 })
		end
	end)
	return marco
end

-- ===== Interruptor =====

function Controles.Interruptor(padre: Instance, valorInicial: boolean, alCambiar: (valor: boolean) -> ()): TextButton
	local boton = P.Crear("TextButton", {
		Name = "Interruptor",
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(34, 18),
		BackgroundColor3 = C.Blanco,
		ZIndex = 5,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, UDim.new(1, 0))
	local borde = P.Borde(boton, C.Blanco, 0.85)
	local bola = P.Marco(boton, {
		Nombre = "Bola",
		Tamano = UDim2.fromOffset(12, 12),
		Posicion = UDim2.fromOffset(3, 3),
		Color = C.Gris,
		Radio = UDim.new(1, 0),
		Z = 6,
	})
	local valor = valorInicial
	local function pintar(animar: boolean)
		local info = if animar then Theme.Tweens.Fundido else TweenInfo.new(0)
		UITweens.Tween(boton, info, {
			BackgroundColor3 = if valor then C.Acento else C.Blanco,
			BackgroundTransparency = if valor then 0.7 else 0.9,
		})
		UITweens.Tween(
			borde,
			info,
			{ Color = if valor then C.Acento else C.Blanco, Transparency = if valor then 0 else 0.85 }
		)
		UITweens.Tween(bola, info, {
			Position = UDim2.fromOffset(if valor then 19 else 3, 3),
			BackgroundColor3 = if valor then C.AcentoClaro else C.Gris,
		})
	end
	pintar(false)
	boton.Activated:Connect(function()
		valor = not valor
		pintar(true)
		alCambiar(valor)
	end)
	return boton
end

-- ===== Desplegable =====

function Controles.Desplegable(
	padre: Instance,
	opciones: { string },
	valorInicial: string,
	alCambiar: (valor: string) -> ()
): Frame
	local marco = P.Marco(padre, { Nombre = "Desplegable", Tamano = UDim2.fromOffset(140, 24), Z = 8 })
	local boton = P.Crear("TextButton", {
		Name = "Actual",
		Text = valorInicial,
		TextSize = Theme.Texto.Cuerpo,
		FontFace = Theme.Fuentes.Titulo,
		TextColor3 = C.TextoPrincipal,
		TextXAlignment = Enum.TextXAlignment.Left,
		AutoButtonColor = false,
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = C.FondoProfundo,
		BackgroundTransparency = 0.25,
		ZIndex = 8,
		Parent = marco,
	}) :: TextButton
	P.Esquinas(boton, Theme.Tamanos.RadioBoton)
	P.Borde(boton, C.Acento, Theme.Alpha.BordeActivo)
	P.Relleno(boton, 0, 22, 0, 10)
	-- Flecha (dos líneas en V hechas con marcos girados).
	local flecha = P.Marco(boton, {
		Nombre = "Flecha",
		Tamano = UDim2.fromOffset(10, 10),
		Posicion = UDim2.new(1, 12, 0.5, 0),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 9,
	})
	P.Marco(flecha, {
		Tamano = UDim2.fromOffset(6, 1.5),
		Posicion = UDim2.fromScale(0.32, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Color = C.Acento,
		Z = 9,
	}).Rotation =
		45
	P.Marco(flecha, {
		Tamano = UDim2.fromOffset(6, 1.5),
		Posicion = UDim2.fromScale(0.68, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Color = C.Acento,
		Z = 9,
	}).Rotation =
		-45

	local lista = P.Grupo(marco, {
		Nombre = "Lista",
		Tamano = UDim2.new(1, 0, 0, #opciones * 22 + 6),
		Posicion = UDim2.new(0, 0, 1, 4),
		Color = C.FondoProfundo,
		Transparencia = 0,
		Z = 20,
	})
	lista.Visible = false
	P.Esquinas(lista, Theme.Tamanos.RadioBoton)
	P.Borde(lista, C.Acento, Theme.Alpha.BordeActivo)
	P.Relleno(lista, 3)
	P.Lista(lista, Enum.FillDirection.Vertical, 0)
	local abierta = false
	local function abrir(valor: boolean)
		abierta = valor
		UITweens.Fundir(lista, valor, Theme.Tweens.Rapido)
		UITweens.Tween(flecha, Theme.Tweens.Rapido, { Rotation = if valor then 180 else 0 })
	end
	for i, opcion in opciones do
		local fila = P.Crear("TextButton", {
			Name = opcion,
			Text = opcion,
			TextSize = Theme.Texto.Pequeno + 0.5,
			FontFace = Theme.Fuentes.Stats,
			TextColor3 = if opcion == valorInicial then C.Acento else C.TextoPrincipal,
			TextXAlignment = Enum.TextXAlignment.Left,
			AutoButtonColor = false,
			BackgroundColor3 = C.Acento,
			BackgroundTransparency = 1,
			Size = UDim2.new(1, 0, 0, 22),
			LayoutOrder = i,
			ZIndex = 21,
			Parent = lista,
		}) :: TextButton
		P.Esquinas(fila, UDim.new(0, 4))
		P.Relleno(fila, 0, 8)
		fila.MouseEnter:Connect(function()
			fila.BackgroundTransparency = 0.88
		end)
		fila.MouseLeave:Connect(function()
			fila.BackgroundTransparency = 1
		end)
		fila.Activated:Connect(function()
			boton.Text = opcion
			for _, otra in lista:GetChildren() do
				if otra:IsA("TextButton") then
					otra.TextColor3 = if otra.Name == opcion then C.Acento else C.TextoPrincipal
				end
			end
			abrir(false)
			alCambiar(opcion)
		end)
	end
	boton.Activated:Connect(function()
		abrir(not abierta)
	end)
	return marco
end

-- ===== Tecla =====

-- Botón de una tecla. Al pulsarlo espera la siguiente tecla del teclado (Escape cancela).
function Controles.Tecla(
	padre: Instance,
	valorInicial: string,
	bloqueado: boolean,
	alCambiar: (tecla: Enum.KeyCode) -> ()
): TextButton
	local boton = P.Crear("TextButton", {
		Name = "Tecla",
		Text = valorInicial,
		TextSize = Theme.Texto.Medio,
		FontFace = Theme.Fuentes.Negrita,
		TextColor3 = if bloqueado then C.Gris else C.TextoPrincipal,
		AutoButtonColor = false,
		Size = UDim2.fromOffset(54, 24),
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundColor3 = C.FondoProfundo,
		BackgroundTransparency = 0.25,
		ZIndex = 5,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, Theme.Tamanos.RadioBoton)
	P.Relleno(boton, 0, 8)
	local borde =
		P.Borde(boton, if bloqueado then C.Gris else C.Acento, if bloqueado then 0.8 else Theme.Alpha.BordeActivo)
	if bloqueado then
		return boton
	end
	UITweens.Hover(boton)
	local esperando: RBXScriptConnection? = nil
	boton.Activated:Connect(function()
		if esperando then
			return
		end
		boton.Text = "PULSA UNA TECLA"
		boton.TextSize = Theme.Texto.Pequeno
		boton.TextColor3 = C.Dorado
		borde.Color = C.Dorado
		esperando = UserInputService.InputBegan:Connect(function(entrada)
			if entrada.UserInputType ~= Enum.UserInputType.Keyboard then
				return
			end
			local conexion = esperando
			if conexion then
				conexion:Disconnect()
			end
			esperando = nil
			boton.TextSize = Theme.Texto.Medio
			boton.TextColor3 = C.TextoPrincipal
			borde.Color = C.Acento
			if entrada.KeyCode == Enum.KeyCode.Escape then
				boton.Text = valorInicial
				return
			end
			valorInicial = entrada.KeyCode.Name
			boton.Text = valorInicial
			alCambiar(entrada.KeyCode)
		end)
	end)
	return boton
end

return Controles
