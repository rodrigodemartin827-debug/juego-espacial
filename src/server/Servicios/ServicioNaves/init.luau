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
	  ENTORNO       cerca del sol la nave se recalienta (Planetas/Calor) y el casco se daña por encima del umbral;
	                el agujero negro la atrae (Planetas/Gravedad) y su horizonte la destruye. La vigilancia cuenta
	                con esa atracción: caer es válido, escapar más deprisa de lo que permite el motor, no.
	  ZONAS         una nave está en el Espacio o en la Superficie de un planeta (Planetas/Espacio). Entrar en la
	                atmósfera de un planeta o subir por encima del techo de su superficie avisa a ServicioPlanetas
	                (ver PonerEntorno), que hace la transición y la coloca con Teletransportar. Cambiar de zona por
	                su cuenta, o meterse dentro de un planeta o del sol, es trampa: se la devuelve a su sitio.
	                En las zonas seguras (alrededor de los planetas de bando y en sus puertos) no hay PvP de naves.

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
local Calor = require(Shared.Planetas.Calor)
local DatosPlanetas = require(Shared.Planetas.Datos)
local Espacio = require(Shared.Planetas.Espacio)
local Gravedad = require(Shared.Planetas.Gravedad)
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

--[[
	Lo que ServicioPlanetas quiere saber de las naves (ver PonerEntorno). Las funciones se llaman en un hilo aparte
	y pueden esperar (fundidos, carga del terreno).
	  AlEntrarEnAtmosfera  la nave ha entrado en la atmósfera de un planeta y puede aterrizar
	  AlSuperarTecho       la nave ha subido por encima del techo de la superficie de un planeta
	  DestinoAterrizaje    dónde se baja el piloto al aterrizar con F (nil = junto a su plataforma, como siempre)
]]
export type Entorno = {
	AlEntrarEnAtmosfera: ((jugador: Player, planeta: string) -> ())?,
	AlSuperarTecho: ((jugador: Player, planeta: string) -> ())?,
	DestinoAterrizaje: ((jugador: Player, posicion: Vector3) -> CFrame?)?,
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

	-- Entorno (planetas, sol y agujero negro).
	Zona: Espacio.Zona, -- dónde está: el espacio o la superficie de un planeta
	EnTransicion: boolean, -- aterrizando o despegando (fundido a negro): no se vigila ni se daña
	Calor: number, -- recalentamiento junto al sol (Planetas/Calor)
	ProximoEntorno: number,
	ProximoAvisoAtmosfera: number,
}

local ServicioNaves = {}

local iniciado = false
local naves: { [Player]: Nave } = {}
local navePorModelo: { [Model]: Nave } = setmetatable({}, { __mode = "k" }) :: any
local proximoDespegue: { [Player]: number } = {}
local bucle: RBXScriptConnection? = nil
local entorno: Entorno = {}

-- Cada cuántos segundos se reenvía el estado al piloto aunque no haya pasado nada (mantiene sincronizado el escudo).
local INTERVALO_ESTADO = 0.5
-- Entre dos choques con el MISMO asteroide hay que esperar esto (el rebote tarda un poco en sacarla de la roca).
local ENFRIAMIENTO_MISMO_ASTEROIDE = 0.3
-- Un cliente que se mete más de esto dentro de un planeta o del sol (el suyo le hace resbalar por fuera) hace trampa.
local MARGEN_CUERPO_SOLIDO = 40

local SOL = DatosPlanetas.Sol
local AGUJERO = DatosPlanetas.AgujeroNegro
local CENTRO_SOL = Vector3.new(SOL.Centro.X, SOL.Centro.Y, SOL.Centro.Z)
local CENTRO_AGUJERO = Vector3.new(AGUJERO.Centro.X, AGUJERO.Centro.Y, AGUJERO.Centro.Z)

-- Los módulos de Planetas trabajan con tablas { X, Y, Z } (son puros); esto convierte un Vector3.
local function aVec(v: Vector3): Espacio.Vec
	return { X = v.X, Y = v.Y, Z = v.Z }
end

-- ===== Utilidades =====

local function destinoAterrizaje(nave: Nave): CFrame
	-- En la superficie de un planeta, ServicioPlanetas decide (junto al puerto de ese planeta).
	local alternativo = entorno.DestinoAterrizaje
	if alternativo and nave.Raiz.Parent ~= nil then
		local destino = alternativo(nave.Jugador, nave.Raiz.Position)
		if destino then
			return destino
		end
	end
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
		-- Entorno: para el panel (calor) y para la física del cliente (zona).
		Calor = nave.Calor,
		CalorMax = SOL.Calor.CalorMax,
		CalorAviso = SOL.Calor.UmbralAviso,
		CalorDano = SOL.Calor.UmbralDano,
		NivelCalor = Calor.Nivel(nave.Calor, SOL.Calor),
		Zona = nave.Zona.Tipo,
		Planeta = nave.Zona.Planeta,
		EnTransicion = nave.EnTransicion,
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
local function danar(nave: Nave, dano: number, causa: string, ignorarEscudo: boolean?): Reglas.ResultadoDano
	local ahora = os.clock()
	local resultado = Reglas.AplicarDano(nave.Estado, nave.Stats, dano, ahora, ignorarEscudo)
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
		-- Zonas seguras: ni se daña a quien está dentro ni se dispara desde dentro. El escudo "para" el disparo.
		if Espacio.EnZonaSegura(aVec(nave.Raiz.Position)) or Espacio.EnZonaSegura(aVec(objetivo.Raiz.Position)) then
			ServicioRed.EnviarATodos("NaveImpacto", nave.Modelo, punto, direccion, "Escudo")
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

	-- Velocidad: la del motor más la atracción del agujero negro (Planetas/Gravedad; fuera de su alcance es la
	-- comprobación de siempre). El tiempo se limita igual que en Naves/Reglas.MovimientoValido.
	local movimientoValido = Gravedad.MovimientoValido(
		aVec(nave.PosValida),
		aVec(posicion),
		math.clamp(transcurrido, 0, Config.DtMaximo),
		tope,
		AGUJERO.Centro,
		AGUJERO.Atraccion,
		Config.HolguraVelocidad,
		Config.MargenPosicion
	)
	-- Zona: sigue donde estaba (el espacio o la misma superficie) y no está metida dentro de un cuerpo sólido.
	local zona = Espacio.ZonaDe(aVec(posicion))
	local zonaValida = zona.Tipo ~= "Fuera" and Espacio.MismaZona(zona, nave.Zona)
	local fueraDeCuerpos = Espacio.CuerpoSolido(aVec(posicion), -MARGEN_CUERPO_SOLIDO) == nil

	if movimientoValido and zonaValida and fueraDeCuerpos then
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

-- ===== Entorno: sol, agujero negro, atmósferas y techo de las superficies =====

local function avisarAtmosfera(nave: Nave, ahora: number, texto: string)
	if ahora >= nave.ProximoAvisoAtmosfera then
		nave.ProximoAvisoAtmosfera = ahora + DatosPlanetas.Transicion.SegundosEntreAvisos
		enviarEstado(nave, texto)
	end
end

-- Pasa el control a ServicioPlanetas (en otro hilo: hará un fundido y moverá la nave con Teletransportar).
local function empezarTransicion(nave: Nave, funcion: (Player, string) -> (), planeta: string)
	nave.EnTransicion = true
	enviarEstado(nave)
	task.spawn(function()
		local ok, err = pcall(funcion :: any, nave.Jugador, planeta)
		if not ok then
			warn(`[ServicioNaves] Falló la transición a {planeta}: {err}`)
		end
		-- Si nadie la ha colocado (fallo o la nave ya no está), se reanuda la vigilancia donde esté.
		if nave.Activa and nave.EnTransicion then
			nave.EnTransicion = false
			nave.PosValida = nave.Raiz.Position
			nave.PosPrevia = nave.Raiz.Position
			nave.TiempoValido = os.clock()
		end
	end)
end

local function revisarEntorno(nave: Nave, ahora: number, dt: number)
	local posicion = nave.Raiz.Position
	local zona = nave.Zona

	if zona.Tipo == "Superficie" then
		local planeta = zona.Planeta :: string
		local alSubir = entorno.AlSuperarTecho
		if alSubir and Espacio.SuperaTecho(planeta, aVec(posicion)) then
			empezarTransicion(nave, alSubir, planeta)
		end
		return
	end

	-- Agujero negro: dentro del horizonte no hay vuelta atrás.
	if (posicion - CENTRO_AGUJERO).Magnitude <= AGUJERO.RadioHorizonte then
		destruir(nave, "AgujeroNegro")
		return
	end

	-- Sol: el calor se acerca al de esta distancia y, por encima del umbral, daña el casco. Tocarlo la funde.
	local distanciaSol = (posicion - CENTRO_SOL).Magnitude
	if distanciaSol <= SOL.Radio then
		destruir(nave, "Sol")
		return
	end
	local antes = Calor.Nivel(nave.Calor, SOL.Calor)
	nave.Calor = Calor.Paso(nave.Calor, distanciaSol, dt, SOL.Calor)
	local danoPorSegundo = Calor.DanoPorSegundo(nave.Calor, SOL.Calor)
	if danoPorSegundo > 0 then
		danar(nave, danoPorSegundo * dt, "Sol", SOL.Calor.IgnoraEscudo)
		if not nave.Activa then
			return
		end
	end
	if Calor.Nivel(nave.Calor, SOL.Calor) ~= antes then
		local aviso = if Calor.Nivel(nave.Calor, SOL.Calor) == "Peligro"
			then "¡Recalentamiento! Aléjate del sol"
			else nil
		enviarEstado(nave, aviso)
	end

	-- Atmósfera de un planeta: se aterriza (si no está en pleno combate).
	local planeta = Espacio.EnAtmosfera(aVec(posicion))
	local alEntrar = entorno.AlEntrarEnAtmosfera
	if planeta and alEntrar then
		if Reglas.PuedeAterrizar(nave.UltimoDanoRecibido, ahora) then
			empezarTransicion(nave, alEntrar, planeta)
		else
			avisarAtmosfera(nave, ahora, "No puedes aterrizar en pleno combate")
		end
	end
end

local function paso(dt: number)
	local ahora = os.clock()
	for _, nave in naves do
		if not nave.Lista or not nave.Activa or nave.EnTransicion then
			continue
		end
		revisarChoque(nave, ahora, dt)
		if not nave.Activa then
			continue -- el choque la ha destruido
		end
		vigilar(nave, ahora)
		if ahora >= nave.ProximoEntorno then
			local intervalo = Config.IntervaloVigilancia
			nave.ProximoEntorno = ahora + intervalo
			revisarEntorno(nave, ahora, intervalo)
			if not nave.Activa or nave.EnTransicion then
				continue
			end
		end

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
	-- Con StreamingEnabled, la nave llega entera a cada cliente o no llega (nunca a medias).
	modelo.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
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
		Zona = Espacio.ZonaDe(aVec(plataforma.Marco.Position)),
		EnTransicion = false,
		Calor = 0,
		ProximoEntorno = ahora,
		ProximoAvisoAtmosfera = 0,
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

--[[
	Coloca la nave de un jugador en `marco` (de un sitio a otro del mapa: la superficie de un planeta o su órbita).
	La vigilancia la acepta allí: se actualizan su zona y su última posición buena, se le quita la velocidad y el
	cliente del piloto se reorienta (como en una corrección). Termina la transición. Devuelve false si no vuela.
]]
function ServicioNaves.Teletransportar(jugador: Player, marco: CFrame): boolean
	local nave = naves[jugador]
	if nave == nil or not nave.Activa then
		return false
	end
	local raiz = nave.Raiz
	pcall(function()
		raiz:SetNetworkOwner(nil)
	end)
	nave.Modelo:PivotTo(marco)
	raiz.AssemblyLinearVelocity = Vector3.zero
	raiz.AssemblyAngularVelocity = Vector3.zero

	local ahora = os.clock()
	nave.Zona = Espacio.ZonaDe(aVec(marco.Position))
	nave.PosValida = marco.Position
	nave.PosPrevia = marco.Position
	nave.TiempoValido = ahora
	nave.VelocidadReciente = 0
	nave.Avisos = 0
	nave.Correccion += 1
	nave.EnTransicion = false
	nave.ProximoEntorno = ahora + 0.5
	enviarEstado(nave)
	-- El cliente del piloto vuelve a mandar en cuanto la nueva posición le ha llegado.
	task.delay(0.25, function()
		if nave.Activa then
			pcall(function()
				raiz:SetNetworkOwner(nave.Jugador)
			end)
		end
	end)
	return true
end

--[[
	Conecta las funciones de ServicioPlanetas (ver el tipo Entorno). Sin ellas las naves vuelan como antes:
	ni se aterriza en los planetas ni se despega de sus superficies.
]]
function ServicioNaves.PonerEntorno(nuevo: Entorno)
	entorno = nuevo
end

-- El entorno conectado ahora (para quien quiera ampliarlo sin perder lo que ya hacía).
function ServicioNaves.ObtenerEntorno(): Entorno
	return entorno
end

-- ¿Está la nave del jugador en mitad de una transición (aterrizando o despegando)?
function ServicioNaves.EnTransicion(jugador: Player): boolean
	local nave = naves[jugador]
	return nave ~= nil and nave.EnTransicion
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
