--!strict
--[[
	ServicioNaves: las naves con el SERVIDOR como autoridad.

	El piloto vuela con su propio cliente (el control es inmediato, sin esperar al servidor) pero el servidor no
	se fía de él. Lo que hace este servicio:

	  DESPEGAR      un jugador con sus datos cargados sube a la nave de una plataforma (ver Despegar). Las
	                estadísticas salen de SUS mejoras guardadas (Naves/Estadisticas), no de lo que diga el cliente.
	  VIDA Y ESCUDO el estado de cada nave (Naves/Reglas) vive aquí; el escudo absorbe primero y se recarga solo,
	                calculado "perezosamente" (sin bucles ni temporizadores por nave).
	  ARMAS         el cliente solo pide disparar y dice hacia dónde apunta; la cadencia, el cono de puntería, el
	                cañón, la trayectoria y el daño los decide el servidor (ServicioNaves/Armas).
	  MINERÍA       un láser que da en una veta de mineral de un asteroide la pica (ServicioMinado): el botín va al
	                inventario del piloto, limitado por la mejora Carga.
	  CHOQUES       cada fotograma se comprueba si la nave toca un asteroide (ServicioNaves/Choques): el daño
	                depende de la velocidad que lleva MEDIDA por el servidor y del tamaño de la roca.
	  VIGILANCIA    cada 0,2 s se comprueba que la nave no va más deprisa de lo que permite su motor, ni se sale
	                del mundo. Si se salta los límites varias veces seguidas, se la devuelve a su última posición buena.
	  TURBO         el servidor lleva el depósito de energía y el límite de velocidad con o sin turbo.

	Los clientes reciben los avisos para los efectos (NaveDisparo, NaveImpacto, NaveChoque, NaveDestruida...);
	el piloto, además, su estado (EstadoNave) para el panel de mandos.

	Una nave destruida o abandonada se retira entera: el modelo se destruye y el piloto vuelve a la plataforma.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.Shared
local CombateReglas = require(Shared.Combate.Reglas)
local Config = require(Shared.Naves.Config)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Reglas = require(Shared.Naves.Reglas)
local ServicioAsteroides = require(script.Parent.ServicioAsteroides)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioMinado = require(script.Parent.ServicioMinado)
local ServicioRed = require(script.Parent.ServicioRed)
local Armas = require(script.Armas)
local Choques = require(script.Choques)
local Modelo = require(script.Modelo)
local Piloto = require(script.Piloto)

--[[
	Un lugar desde el que despegar. `Marco` es la posición y orientación de la nave posada (mira hacia donde
	despegará). Mientras haya una nave suya en el aire, `Ocupada` vale true y se avisa con `AlCambiar`.
]]
export type Plataforma = {
	Marco: CFrame,
	Ocupada: boolean,
	AlCambiar: ((ocupada: boolean) -> ())?,
}

type Nave = {
	Jugador: Player,
	Modelo: Model,
	Raiz: BasePart,
	Plataforma: Plataforma,
	Bando: string,
	Stats: Estadisticas.Estadisticas,
	Estado: Reglas.Estado,
	Turbo: Reglas.Turbo,
	Guardado: Piloto.Guardado,
	Conexiones: { RBXScriptConnection },
	Activa: boolean, -- false en cuanto se retira
	Lista: boolean, -- los motores ya han arrancado: el piloto puede volar y disparar

	UltimoDisparo: number?,
	CanonAlterno: number,
	UltimoDanoRecibido: number?,

	-- Vigilancia del movimiento.
	PosValida: Vector3,
	TiempoValido: number,
	Avisos: number,
	Correccion: number, -- sube cada vez que se la devuelve a su sitio (el cliente reinicia su velocidad)

	-- Choques.
	PosPrevia: Vector3,
	VelocidadReciente: number, -- la mayor velocidad de los últimos instantes (la que llevaba al chocar)
	UltimoChoque: { [Model]: number },
	UltimoDanoChoque: number,

	ProximoEstado: number,
}

local ServicioNaves = {}

local iniciado = false
local naves: { [Player]: Nave } = {}
local navePorModelo: { [Model]: Nave } = setmetatable({}, { __mode = "k" }) :: any
local proximoDespegue: { [Player]: number } = {}
local bucle: RBXScriptConnection? = nil

-- Cada cuántos segundos se reenvía el estado al piloto aunque no haya pasado nada (mantiene sincronizado el escudo).
local INTERVALO_ESTADO = 0.5
-- Entre dos choques con el MISMO asteroide hay que esperar esto (el rebote tarda un poco en sacarla de la roca).
local ENFRIAMIENTO_MISMO_ASTEROIDE = 0.3

-- ===== Utilidades =====

local function destinoAterrizaje(nave: Nave): CFrame
	-- Junto a la plataforma, un poco a un lado, para no aparecer dentro de la nave de exhibición.
	return nave.Plataforma.Marco * CFrame.new(10, 3.5, 4)
end

-- Estado completo de la nave para el panel del piloto. Las duraciones van relativas (el reloj del cliente es otro).
local function instantanea(nave: Nave, ahora: number): { [string]: any }
	local stats = nave.Stats
	local estado = nave.Estado
	return {
		Activa = true,
		Lista = nave.Lista,
		Modelo = nave.Modelo,
		Bando = nave.Bando,
		Vida = estado.Vida,
		VidaMax = stats.VidaMax,
		Escudo = Reglas.EscudoActual(estado, stats, ahora),
		EscudoMax = stats.EscudoMax,
		RegenEscudo = stats.RegenEscudo,
		EsperaEscudo = math.max(0, estado.DesdeEscudo + stats.RetrasoEscudo - ahora),
		Inmune = math.max(0, estado.InmuneHasta - ahora),
		Turbo = Reglas.EnergiaTurbo(nave.Turbo, stats, ahora),
		TurboMax = stats.EnergiaTurbo,
		TurboActivo = Reglas.TurboActivo(nave.Turbo, stats, ahora),
		TurboConsumo = Config.TurboConsumo,
		TurboRegeneracion = Config.TurboRegeneracion,
		VelocidadMax = stats.VelocidadMax,
		Aceleracion = stats.Aceleracion,
		TurboMult = stats.TurboMult,
		Dano = stats.Dano,
		Cadencia = stats.Cadencia,
		Alcance = stats.Alcance,
		RadioEscaner = stats.RadioEscaner,
		Capacidad = stats.Capacidad,
		Niveles = stats.Niveles,
		Correccion = nave.Correccion,
	}
end

local function enviarEstado(nave: Nave, aviso: string?)
	local datos = instantanea(nave, os.clock())
	datos.Aviso = aviso
	ServicioRed.EnviarACliente(nave.Jugador, "EstadoNave", datos)
	nave.ProximoEstado = os.clock() + INTERVALO_ESTADO
end

local function hayNaves(): boolean
	return next(naves) ~= nil
end

-- ===== Retirar una nave =====

--[[
	Quita la nave del juego: baja al piloto (a `destino`, si se indica), destruye el modelo y libera la plataforma.
	Avisa al piloto de que ya no vuela (con `resumen` si se indica, p. ej. que ha sido destruida). Los efectos
	para el resto de jugadores los decide quien la llama.
]]
local function retirar(nave: Nave, destino: CFrame?, resumen: { [string]: any }?)
	if not nave.Activa then
		return
	end
	nave.Activa = false
	naves[nave.Jugador] = nil
	navePorModelo[nave.Modelo] = nil
	for _, conexion in nave.Conexiones do
		conexion:Disconnect()
	end
	Piloto.Bajar(nave.Guardado, destino)
	nave.Modelo:Destroy()
	ServicioRed.EnviarACliente(nave.Jugador, "EstadoNave", resumen or { Activa = false })

	nave.Plataforma.Ocupada = false
	local avisar = nave.Plataforma.AlCambiar
	if avisar then
		task.spawn(avisar, false)
	end

	if not hayNaves() and bucle then
		bucle:Disconnect()
		bucle = nil
	end
end

local function destruir(nave: Nave, causa: string)
	if not nave.Activa then
		return
	end
	local jugador = nave.Jugador
	ServicioRed.EnviarATodos("NaveDestruida", nave.Raiz.Position, nave.Bando)
	proximoDespegue[jugador] = os.clock() + Config.SegundosRenacer
	retirar(nave, destinoAterrizaje(nave), { Activa = false, Destruida = true, Causa = causa })
end

-- ===== Daño =====

--[[
	Aplica daño a una nave (escudo primero, luego casco). Si la destruye, la retira. Devuelve el resultado de
	Naves/Reglas.AplicarDano.
]]
local function danar(nave: Nave, dano: number, causa: string): Reglas.ResultadoDano
	local ahora = os.clock()
	local resultado = Reglas.AplicarDano(nave.Estado, nave.Stats, dano, ahora)
	if resultado.Aplicado then
		nave.UltimoDanoRecibido = ahora
		if resultado.Destruida then
			destruir(nave, causa)
		else
			enviarEstado(nave)
		end
	end
	return resultado
end

-- ===== Disparar =====

-- Lo que pasa cuando el proyectil llega a su destino.
local function aplicarImpacto(nave: Nave, punto: Vector3, direccion: Vector3, golpe: BasePart)
	if golpe.Parent == nil then
		return -- lo que se golpeó ya no está
	end
	-- Una veta de mineral: el láser la pica y el botín va a la bodega del piloto (si no cabe nada, el disparo sigue su curso).
	if ServicioMinado.PicarDesdeNave(nave.Jugador, golpe, nave.Stats.Dano) then
		ServicioRed.EnviarATodos("NaveImpacto", nave.Modelo, punto, direccion, "Asteroide")
		return
	end

	local asteroide = Choques.AsteroideDe(golpe)

	-- Un asteroide.
	if asteroide then
		ServicioAsteroides.Danar(asteroide, nave.Stats.Dano * Config.DanoAsteroideFactor)
		ServicioRed.EnviarATodos("NaveImpacto", nave.Modelo, punto, direccion, "Asteroide")
		return
	end

	-- Otra nave: solo hace daño a las enemigas (los del mismo bando no se hacen daño, como en tierra).
	local contenedor = golpe:FindFirstAncestorWhichIsA("Model")
	local objetivo = if contenedor then navePorModelo[contenedor] else nil
	if objetivo then
		if objetivo == nave or not objetivo.Activa or not CombateReglas.SonEnemigos(nave.Bando, objetivo.Bando) then
			return
		end
		local resultado = danar(objetivo, nave.Stats.Dano, "Nave")
		local tipo = if resultado.Aplicado and resultado.DanoCasco > 0 then "Casco" else "Escudo"
		ServicioRed.EnviarATodos("NaveImpacto", nave.Modelo, punto, direccion, tipo)
		return
	end

	-- El escenario.
	ServicioRed.EnviarATodos("NaveImpacto", nave.Modelo, punto, direccion, "Estructura")
end

local function disparar(jugador: Player, direccion: Vector3)
	local nave = naves[jugador]
	if nave == nil or not nave.Lista then
		return
	end
	local resultado = Armas.Resolver(nave, direccion, os.clock())
	if resultado == nil then
		return -- todavía no toca por la cadencia
	end

	ServicioRed.EnviarATodos(
		"NaveDisparo",
		nave.Modelo,
		resultado.Origen,
		resultado.Punto,
		resultado.Direccion,
		resultado.Viaje,
		nave.Bando
	)
	local golpe = resultado.Golpe
	if golpe then
		task.delay(resultado.Viaje, function()
			if nave.Activa then
				aplicarImpacto(nave, resultado.Punto, resultado.Direccion, golpe)
			end
		end)
	end
end

-- ===== Turbo =====

local function cambiarTurbo(jugador: Player, activar: boolean)
	local nave = naves[jugador]
	if nave == nil or not nave.Lista then
		return
	end
	local ahora = os.clock()
	local antes = Reglas.TurboActivo(nave.Turbo, nave.Stats, ahora)
	Reglas.CambiarTurbo(nave.Turbo, nave.Stats, activar, ahora)
	local despues = Reglas.TurboActivo(nave.Turbo, nave.Stats, ahora)
	if antes ~= despues then
		-- Los clientes miran este atributo para el efecto de los propulsores y el arranque del turbo.
		nave.Modelo:SetAttribute("Turbo", despues)
	end
	enviarEstado(nave)
end

-- ===== Aterrizar =====

local function aterrizar(jugador: Player)
	local nave = naves[jugador]
	if nave == nil or not nave.Lista then
		return
	end
	if not Reglas.PuedeAterrizar(nave.UltimoDanoRecibido, os.clock()) then
		enviarEstado(nave, "No puedes aterrizar en pleno combate")
		return
	end
	retirar(nave, destinoAterrizaje(nave))
end

-- ===== Choques y vigilancia (cada fotograma) =====

local function revisarChoque(nave: Nave, ahora: number, dt: number)
	local posicion = nave.Raiz.Position
	local previa = nave.PosPrevia
	nave.PosPrevia = posicion

	-- Velocidad medida por el servidor. Se conserva la mayor de los últimos instantes: cuando se detecta el choque,
	-- el cliente del piloto puede haber rebotado ya y la velocidad actual ser mucho menor que la del impacto.
	local velocidad = if dt > 0 then (posicion - previa).Magnitude / dt else 0
	nave.VelocidadReciente = math.max(velocidad, nave.VelocidadReciente * math.exp(-4 * dt))

	local golpe = Choques.Buscar(previa, posicion, Config.RadioNave, ServicioAsteroides.Raiz())
	if golpe == nil then
		return
	end
	local ultimo = nave.UltimoChoque[golpe.Modelo]
	if ultimo and ahora - ultimo < ENFRIAMIENTO_MISMO_ASTEROIDE then
		return
	end
	nave.UltimoChoque[golpe.Modelo] = ahora

	local tamano = golpe.Modelo:GetAttribute("Tamano")
	local dano = 0
	if ahora - nave.UltimoDanoChoque >= Config.EnfriamientoChoque then
		dano = Reglas.DanoChoque(nave.VelocidadReciente, if type(tamano) == "number" then tamano else 12)
		if dano > 0 then
			nave.UltimoDanoChoque = ahora
		end
	end

	-- El aviso va ANTES de aplicar el daño: si el golpe destruye la nave, el modelo desaparece a continuación.
	local escudoAguanta = Reglas.EscudoActual(nave.Estado, nave.Stats, ahora) >= dano or ahora < nave.Estado.InmuneHasta
	ServicioRed.EnviarATodos(
		"NaveChoque",
		nave.Modelo,
		golpe.Punto,
		golpe.Normal,
		escudoAguanta,
		dano / Config.DanoChoqueMaximo
	)
	if dano > 0 then
		danar(nave, dano, "Asteroide")
	end
end

-- Devuelve la nave a su última posición buena (el cliente ha ido más deprisa de lo posible o se ha salido del mundo).
local function corregir(nave: Nave)
	nave.Avisos = 0
	nave.Correccion += 1
	local raiz = nave.Raiz
	-- Mientras el cliente es su dueño, él manda sobre la posición: se le quita un momento para poder moverla.
	pcall(function()
		raiz:SetNetworkOwner(nil)
	end)
	nave.Modelo:PivotTo(CFrame.new(nave.PosValida) * (raiz.CFrame - raiz.CFrame.Position))
	raiz.AssemblyLinearVelocity = Vector3.zero
	raiz.AssemblyAngularVelocity = Vector3.zero
	nave.TiempoValido = os.clock()
	nave.PosPrevia = nave.PosValida
	enviarEstado(nave)
	task.delay(0.2, function()
		if nave.Activa then
			pcall(function()
				raiz:SetNetworkOwner(nave.Jugador)
			end)
		end
	end)
end

local function vigilar(nave: Nave, ahora: number)
	local transcurrido = ahora - nave.TiempoValido
	if transcurrido < Config.IntervaloVigilancia then
		return
	end
	local posicion = nave.Raiz.Position
	local tope = Reglas.VelocidadTope(nave.Stats, Reglas.TurboActivo(nave.Turbo, nave.Stats, ahora))
	local distancia = (posicion - nave.PosValida).Magnitude

	if
		Reglas.MovimientoValido(distancia, transcurrido, tope)
		and Reglas.DentroDelMundo({ X = posicion.X, Y = posicion.Y, Z = posicion.Z })
	then
		nave.Avisos = 0
		nave.PosValida = posicion
		nave.TiempoValido = ahora
	else
		-- No se actualiza TiempoValido: el margen sigue creciendo con el tiempo, así que un tirón de lag legítimo
		-- acaba aceptándose, pero un teletransporte (fuera de cualquier margen) nunca.
		nave.Avisos += 1
		if nave.Avisos >= Config.AvisosParaCorregir then
			corregir(nave)
		end
	end
end

local function paso(dt: number)
	local ahora = os.clock()
	for _, nave in naves do
		if not nave.Lista or not nave.Activa then
			continue
		end
		revisarChoque(nave, ahora, dt)
		if not nave.Activa then
			continue -- el choque la ha destruido
		end
		vigilar(nave, ahora)

		-- El turbo se agota solo: se apaga el efecto y se avisa al piloto.
		if nave.Turbo.Activo and not Reglas.TurboActivo(nave.Turbo, nave.Stats, ahora) then
			Reglas.CambiarTurbo(nave.Turbo, nave.Stats, false, ahora)
			nave.Modelo:SetAttribute("Turbo", false)
			enviarEstado(nave)
		elseif ahora >= nave.ProximoEstado then
			enviarEstado(nave)
		end
	end
end

local function asegurarBucle()
	if bucle == nil then
		bucle = RunService.Heartbeat:Connect(paso)
	end
end

-- ===== API =====

-- La nave de un jugador, si está volando.
function ServicioNaves.NaveDe(jugador: Player): Nave?
	return naves[jugador]
end

--[[
	Hace despegar al jugador desde `plataforma`. Devuelve false si no puede: ya está volando, la plataforma está
	ocupada, sus datos no han cargado, su personaje no está listo o tiene que esperar tras ser destruido.
	Las estadísticas de la nave salen de las mejoras guardadas en sus datos.
]]
function ServicioNaves.Despegar(jugador: Player, plataforma: Plataforma): boolean
	-- Si no puede, se le dice por qué (el panel de la nave aún no existe: va como un mensaje suelto).
	local function rechazar(motivo: string): boolean
		ServicioRed.EnviarACliente(jugador, "EstadoNave", { Activa = false, Aviso = motivo })
		return false
	end

	if naves[jugador] ~= nil then
		return false
	end
	if plataforma.Ocupada then
		return rechazar("La plataforma está ocupada")
	end
	local ahora = os.clock()
	local espera = (proximoDespegue[jugador] or 0) - ahora
	if espera > 0 then
		return rechazar(`Tu nave se está reparando ({math.ceil(espera)} s)`)
	end
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local personaje = jugador.Character
	local humanoid = if personaje then personaje:FindFirstChildOfClass("Humanoid") else nil
	if datos == nil then
		return rechazar("Tus datos todavía se están cargando")
	end
	if personaje == nil or humanoid == nil or humanoid.Health <= 0 then
		return false
	end

	local stats = Estadisticas.Calcular(datos.MejorasNave)
	local modelo = Modelo.Crear(datos.Bando, jugador.DisplayName, jugador)
	modelo:PivotTo(plataforma.Marco * CFrame.new(0, Modelo.ALTURA_POSADA, 0))
	modelo:SetAttribute(Config.AtributoPiloto, jugador.UserId)
	modelo:SetAttribute("Turbo", false)
	modelo.Parent = workspace
	CollectionService:AddTag(modelo, Config.EtiquetaNave)

	local guardado = Piloto.Subir(personaje, modelo)
	local raiz = modelo.PrimaryPart
	if guardado == nil or raiz == nil then
		modelo:Destroy()
		return false
	end

	local nave: Nave = {
		Jugador = jugador,
		Modelo = modelo,
		Raiz = raiz,
		Plataforma = plataforma,
		Bando = datos.Bando,
		Stats = stats,
		Estado = Reglas.NuevoEstado(stats, ahora + Config.SegundosArranque),
		Turbo = { Energia = stats.EnergiaTurbo, Desde = ahora, Activo = false },
		Guardado = guardado,
		Conexiones = {},
		Activa = true,
		Lista = false,
		UltimoDisparo = nil,
		CanonAlterno = 0,
		UltimoDanoRecibido = nil,
		PosValida = raiz.Position,
		TiempoValido = ahora,
		Avisos = 0,
		Correccion = 0,
		PosPrevia = raiz.Position,
		VelocidadReciente = 0,
		UltimoChoque = setmetatable({}, { __mode = "k" }) :: any,
		UltimoDanoChoque = 0,
		ProximoEstado = ahora,
	}
	naves[jugador] = nave
	navePorModelo[modelo] = nave

	plataforma.Ocupada = true
	if plataforma.AlCambiar then
		task.spawn(plataforma.AlCambiar, true)
	end

	-- Si el piloto muere o su personaje desaparece, la nave se retira con él.
	table.insert(
		nave.Conexiones,
		humanoid.Died:Connect(function()
			retirar(nave, nil)
		end)
	)
	table.insert(
		nave.Conexiones,
		jugador.CharacterRemoving:Connect(function()
			retirar(nave, nil)
		end)
	)

	-- Los motores rugen unos instantes antes de soltar la nave. El estado se repite enseguida: el modelo puede no
	-- haberse replicado todavía al cliente del piloto la primera vez.
	enviarEstado(nave)
	task.delay(0.35, function()
		if nave.Activa and not nave.Lista then
			enviarEstado(nave)
		end
	end)
	ServicioRed.EnviarATodos("NaveDespegue", modelo, plataforma.Marco.Position, plataforma.Marco.LookVector)
	task.delay(Config.SegundosArranque, function()
		if not nave.Activa then
			return
		end
		Modelo.Soltar(modelo)
		Modelo.ActivarFuerzas(modelo, true)
		pcall(function()
			raiz:SetNetworkOwner(jugador)
		end)
		local ahoraLista = os.clock()
		nave.Lista = true
		nave.PosValida = raiz.Position
		nave.PosPrevia = raiz.Position
		nave.TiempoValido = ahoraLista
		enviarEstado(nave)
		asegurarBucle()
	end)
	return true
end

-- El jugador deja la nave y vuelve a la plataforma (la misma comprobación de combate que el remoto AterrizarNave).
function ServicioNaves.Aterrizar(jugador: Player)
	aterrizar(jugador)
end

--[[
	Aplica daño a la nave de un jugador desde fuera (una trampa, un evento...). Devuelve false si no vuela.
]]
function ServicioNaves.Danar(jugador: Player, dano: number, causa: string): boolean
	local nave = naves[jugador]
	if nave == nil or not nave.Lista then
		return false
	end
	danar(nave, dano, causa)
	return true
end

--[[
	Recalcula las estadísticas de la nave en vuelo tras cambiar las mejoras del jugador. La vida y el escudo
	conservan su proporción (subir el Casco no cura, pero tampoco deja la barra a medias de golpe).
]]
function ServicioNaves.ActualizarMejoras(jugador: Player)
	local nave = naves[jugador]
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if nave == nil or datos == nil then
		return
	end
	local ahora = os.clock()
	local escudoAntes = Reglas.EscudoActual(nave.Estado, nave.Stats, ahora)
	local proporcionVida = nave.Estado.Vida / nave.Stats.VidaMax
	local proporcionEscudo = escudoAntes / math.max(nave.Stats.EscudoMax, 1)

	nave.Stats = Estadisticas.Calcular(datos.MejorasNave)
	nave.Estado.Vida = nave.Stats.VidaMax * proporcionVida
	nave.Estado.Escudo = nave.Stats.EscudoMax * proporcionEscudo
	nave.Estado.DesdeEscudo = ahora - nave.Stats.RetrasoEscudo -- que la recarga siga sin esperar de nuevo
	nave.Turbo.Energia = math.min(nave.Turbo.Energia, nave.Stats.EnergiaTurbo)
	enviarEstado(nave)
end

--[[
	Empieza a atender las naves. Debe llamarse una sola vez, después de ServicioRed.Iniciar() y de
	ServicioAsteroides.Iniciar().
]]
function ServicioNaves.Iniciar()
	assert(not iniciado, "ServicioNaves.Iniciar() solo debe llamarse una vez")
	iniciado = true

	ServicioRed.Conectar("DispararNave", disparar)
	ServicioRed.Conectar("TurboNave", cambiarTurbo)
	ServicioRed.Conectar("AterrizarNave", aterrizar)
	ServicioRed.Conectar("PedirEstadoNave", function(jugador: Player)
		local nave = naves[jugador]
		if nave then
			enviarEstado(nave)
		else
			ServicioRed.EnviarACliente(jugador, "EstadoNave", { Activa = false })
		end
	end)

	Players.PlayerRemoving:Connect(function(jugador)
		local nave = naves[jugador]
		if nave then
			retirar(nave, nil)
		end
		proximoDespegue[jugador] = nil
	end)
end

return ServicioNaves
