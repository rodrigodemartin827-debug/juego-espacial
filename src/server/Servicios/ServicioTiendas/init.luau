--!strict
--[[
	ServicioTiendas: las tiendas del planeta humano, validadas en el servidor.

	COMPRAR. El cliente solo pide `ComprarArticulo(tienda, idArticulo, cantidad)`. El servidor, en este orden:
	  1. comprueba que `tienda` sea una tienda registrada, que el jugador tenga datos, esté vivo, a pie y JUNTO AL
	     MOSTRADOR (Config.AlcanceTienda);
	  2. calcula con las reglas compartidas (Tiendas/Compras.Planificar) si se puede: bando (a los Monstruos no se les
	     vende), persiana (con la persiana bajada la tienda está cerrada), que la tienda venda ese artículo, monedas,
	     nivel máximo de la mejora y espacio en la bodega;
	  3. si se puede, cobra y entrega en el MISMO instante, sin esperas entre medias (Compras.Aplicar), así que no se
	     puede comprar dos veces con las mismas monedas mandando dos peticiones a la vez;
	  4. responde al cliente, le reenvía sus datos, recalcula la nave si subió una mejora y guarda.

	PERSIANA. Cada Config.IntervaloVigilancia segundos mira a qué distancia está el monstruo más cercano de cada tienda y
	actualiza su estado con Tiendas/Persiana.Evaluar (baja si se acerca uno; sube cuando se van). El estado se publica en
	el atributo Config.AtributoPersiana del modelo: los clientes lo animan (con sonido) y el servidor lo usa para no vender.
	Mientras está bajada, el ProximityPrompt del mostrador se desactiva.

	`CrearTienda` construye un local completo (ver Modelo). Los modelos que se monten a mano en un mapa también valen si
	llevan la etiqueta Config.EtiquetaTienda, el atributo Config.AtributoTiendaId y la misma estructura de piezas.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Catalogo = require(Shared.Tiendas.Datos.Catalogo)
local Compras = require(Shared.Tiendas.Compras)
local Config = require(Shared.Tiendas.Config)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Persiana = require(Shared.Tiendas.Persiana)
local Modelo = require(script.Modelo)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioNaves = require(script.Parent.ServicioNaves)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

type Registro = {
	Id: string,
	Modelo: Model,
	Mostrador: BasePart,
	Prompt: ProximityPrompt,
	Estado: Persiana.Estado,
}

local ServicioTiendas = {}

local tiendas: { [Model]: Registro } = {}
local iniciado = false

-- ===== Utilidades =====

-- Raíz del personaje vivo del jugador, o nil.
local function raizViva(personaje: Model?): BasePart?
	if personaje == nil then
		return nil
	end
	local humanoid = personaje:FindFirstChildOfClass("Humanoid")
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	if humanoid == nil or humanoid.Health <= 0 or raiz == nil or not raiz:IsA("BasePart") then
		return nil
	end
	return raiz
end

-- ¿Es el jugador de un bando al que no se vende (los Monstruos)? Sin datos cargados, no se le puede vender igualmente.
local function esVetado(jugador: Player): boolean
	local datos = ServicioDatos.ObtenerDatos(jugador)
	return datos ~= nil and Compras.EsVetado(datos.Bando)
end

local function aviso(jugador: Player, texto: string, tono: string)
	ServicioRed.EnviarACliente(jugador, "AvisoExploracion", texto, tono)
end

local function responder(jugador: Player, articulo: string, ok: boolean, mensaje: string?)
	ServicioRed.EnviarACliente(jugador, "ResultadoCompra", articulo, ok, mensaje)
end

-- ===== Persiana =====

-- Publica el estado de la persiana: atributo (lo animan los clientes) y ProximityPrompt del mostrador.
local function publicarPersiana(registro: Registro)
	local bajada = registro.Estado.Bajada
	registro.Modelo:SetAttribute(Config.AtributoPersiana, bajada)
	registro.Prompt.Enabled = not bajada
end

-- Una vuelta de vigilancia: posición de los monstruos vivos y estado de cada persiana.
local function vigilar(ahora: number)
	local monstruos: { Vector3 } = {}
	for _, jugador in Players:GetPlayers() do
		if esVetado(jugador) then
			local raiz = raizViva(jugador.Character)
			if raiz then
				table.insert(monstruos, raiz.Position)
			end
		end
	end

	for modelo, registro in tiendas do
		if not modelo:IsDescendantOf(workspace) then
			continue
		end
		local centro = registro.Mostrador.Position
		local distancia = math.huge
		for _, posicion in monstruos do
			distancia = math.min(distancia, (posicion - centro).Magnitude)
		end
		if Persiana.Evaluar(registro.Estado, distancia, ahora) then
			publicarPersiana(registro)
		end
	end
end

-- ===== Abrir el panel y comprar =====

-- Alguien ha usado el mostrador: si se le puede atender, el cliente abre el panel de la tienda.
local function alUsarMostrador(registro: Registro, jugador: Player)
	if ServicioDatos.ObtenerDatos(jugador) == nil then
		return
	end
	if esVetado(jugador) then
		aviso(jugador, Compras.Mensajes.BandoVetado, "Mal")
		return
	end
	if registro.Estado.Bajada and Config.CerradaParaTodosConPersianaBajada then
		aviso(jugador, Compras.Mensajes.PersianaBajada, "Mal")
		return
	end
	ServicioRed.EnviarACliente(jugador, "AbrirTienda", registro.Modelo)
end

-- Petición del cliente.
local function comprar(jugador: Player, tienda: Instance, idArticulo: string, cantidad: number?)
	local registro = if tienda:IsA("Model") then tiendas[tienda] else nil
	if registro == nil or not tienda:IsDescendantOf(workspace) then
		return -- no es una tienda: un cliente normal nunca lo manda
	end
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local personaje = jugador.Character
	local raiz = raizViva(personaje)
	if datos == nil or personaje == nil or raiz == nil then
		return
	end
	if personaje:GetAttribute(Config.AtributoPilotando) == true then
		responder(jugador, idArticulo, false, "Aterriza para comprar")
		return
	end
	if (raiz.Position - registro.Mostrador.Position).Magnitude > Config.AlcanceTienda * Config.HolguraAlcance then
		responder(jugador, idArticulo, false, "Estás demasiado lejos del mostrador")
		return
	end

	local capacidad = Estadisticas.Calcular(datos.MejorasNave).Capacidad
	local bajada = registro.Estado.Bajada
	local plan = Compras.Planificar(datos, registro.Id, idArticulo, capacidad, cantidad, bajada)
	if not plan.Ok then
		responder(jugador, idArticulo, false, Compras.Mensajes[plan.Motivo :: string])
		return
	end

	-- Comprobación y cobro seguidos, sin ceder el hilo: nadie puede colarse entre medias.
	if not Compras.Aplicar(datos, plan, capacidad, bajada) then
		responder(jugador, idArticulo, false, "No se pudo comprar, inténtalo de nuevo")
		return
	end

	responder(jugador, idArticulo, true, nil)
	ServicioReplicacion.EnviarDatos(jugador)
	if plan.Mejora then
		ServicioNaves.ActualizarMejoras(jugador) -- por si hay una nave en vuelo; si no, no hace nada
	end
	-- Una compra no debe perderse si el servidor se cae.
	task.spawn(ServicioDatos.GuardarAhora, jugador)
end

-- ===== Registro de tiendas =====

-- Da de alta un modelo de tienda (creado por CrearTienda o montado a mano con la etiqueta). Devuelve false si no vale.
local function registrar(modelo: Instance): boolean
	if not modelo:IsA("Model") or tiendas[modelo] ~= nil then
		return false
	end
	local id = modelo:GetAttribute(Config.AtributoTiendaId)
	local mostrador = modelo:FindFirstChild("Mostrador")
	if type(id) ~= "string" or Catalogo.Tiendas[id] == nil or mostrador == nil or not mostrador:IsA("BasePart") then
		warn(`[Tiendas] {modelo:GetFullName()} no es una tienda válida (falta {Config.AtributoTiendaId} o Mostrador)`)
		return false
	end

	local prompt = mostrador:FindFirstChildOfClass("ProximityPrompt")
	if prompt == nil then
		local nuevo = Instance.new("ProximityPrompt")
		nuevo.ActionText = "Comprar"
		nuevo.ObjectText = Catalogo.Tiendas[id].Nombre
		nuevo.HoldDuration = 0.2
		nuevo.MaxActivationDistance = Config.AlcanceTienda - 3
		nuevo.RequiresLineOfSight = false
		nuevo.Parent = mostrador
		prompt = nuevo
	end

	local registro: Registro = {
		Id = id,
		Modelo = modelo,
		Mostrador = mostrador,
		Prompt = prompt :: ProximityPrompt,
		Estado = Persiana.Nuevo(),
	}
	tiendas[modelo] = registro
	publicarPersiana(registro)
	registro.Prompt.Triggered:Connect(function(jugador: Player)
		alUsarMostrador(registro, jugador)
	end)
	modelo.Destroying:Once(function()
		tiendas[modelo] = nil
	end)
	return true
end

--[[
	Construye una tienda `idTienda` (id de Tiendas/Datos/Catalogo) en `origen` (en el suelo, mirando a la calle), la
	registra y la coloca en `padre`. Devuelve el modelo.
]]
function ServicioTiendas.CrearTienda(padre: Instance, idTienda: string, origen: CFrame): Model
	local modelo = Modelo.Construir(idTienda, origen)
	registrar(modelo)
	CollectionService:AddTag(modelo, Config.EtiquetaTienda)
	modelo.Parent = padre
	return modelo
end

-- Estado actual de la persiana de una tienda (para la zona de pruebas y las comprobaciones en Studio).
function ServicioTiendas.PersianaBajada(modelo: Model): boolean?
	local registro = tiendas[modelo]
	return if registro then registro.Estado.Bajada else nil
end

-- Registra la petición del cliente y empieza a vigilar las persianas. Debe llamarse una vez, después de ServicioRed.Iniciar().
function ServicioTiendas.Iniciar()
	assert(not iniciado, "ServicioTiendas.Iniciar() solo debe llamarse una vez")
	iniciado = true

	ServicioRed.Conectar("ComprarArticulo", comprar)

	-- Tiendas montadas a mano en los mapas.
	for _, modelo in CollectionService:GetTagged(Config.EtiquetaTienda) do
		registrar(modelo)
	end
	CollectionService:GetInstanceAddedSignal(Config.EtiquetaTienda):Connect(registrar)

	task.spawn(function()
		while true do
			-- Protegido: un error en una vuelta no debe dejar las persianas paradas para siempre.
			local ok, motivo = pcall(vigilar, os.clock())
			if not ok then
				warn(`[Tiendas] Error al vigilar las persianas: {motivo}`)
			end
			task.wait(Config.IntervaloVigilancia)
		end
	end)
end

return ServicioTiendas
