--!strict
--[[
	Remotos: lista central de todos los RemoteEvents del juego.

	Es la única fuente de verdad de la red: el servidor crea los RemoteEvents a partir de esta lista
	(ServicioRed.Iniciar), el cliente los busca por su nombre y ambos usan los mismos validadores.
	Para añadir un remoto nuevo basta con declararlo aquí.

	Cada definición tiene:
	  - Direccion: "ClienteAServidor" (el cliente pide algo) o "ServidorACliente" (el servidor avisa).
	  - LimitePorSegundo: (solo ClienteAServidor) peticiones por segundo que se aceptan por jugador.
	    Si se omite, se usa LIMITE_POR_DEFECTO.
	  - Rafaga: (solo ClienteAServidor) peticiones seguidas que se toleran de golpe. Por defecto, igual
	    a LimitePorSegundo. Súbela en acciones que puedan agruparse por la latencia, como disparar.
	  - Argumentos: (obligatorio en ClienteAServidor) lista de validadores, uno por argumento. Si el
	    remoto no recibe argumentos, pon una lista vacía: {}.

	Solo se usan RemoteEvents. No se usan RemoteFunctions: el servidor nunca debe esperar la respuesta
	de un cliente, porque un tramposo puede dejar la llamada colgada para siempre.
]]

local Bandos = require(script.Parent.Parent.Juego.Bandos)
local Poderes = require(script.Parent.Parent.Combate.Datos.Poderes)
local ConfigExploracion = require(script.Parent.Parent.Exploracion.Config)
local Recetas = require(script.Parent.Parent.Exploracion.Datos.Recetas)
local Catalogo = require(script.Parent.Parent.Tiendas.Datos.Catalogo)
local ConfigTiendas = require(script.Parent.Parent.Tiendas.Config)
local Validador = require(script.Parent.Validador)

export type Direccion = "ClienteAServidor" | "ServidorACliente"

export type Definicion = {
	Direccion: Direccion,
	LimitePorSegundo: number?,
	Rafaga: number?,
	Argumentos: { Validador.Validador }?,
}

local Remotos = {}

-- Nombre de la carpeta de ReplicatedStorage donde el servidor crea los RemoteEvents.
Remotos.NOMBRE_CARPETA = "Remotos"

-- Límite por segundo para los remotos ClienteAServidor que no indican uno propio.
Remotos.LIMITE_POR_DEFECTO = 10

local definiciones: { [string]: Definicion } = {
	-- El jugador elige su bando. Solo se acepta una vez (lo comprueba ServicioBandos).
	ElegirBando = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 1,
		Argumentos = { Validador.Enumeracion(Bandos.Elegibles) },
	},

	-- El servidor envía al cliente una copia de sus datos al cargarlos y cuando cambian.
	DatosJugador = {
		Direccion = "ServidorACliente",
	},

	-- El cliente pide una copia de sus datos. Lo hace al arrancar, por si el servidor ya los había
	-- enviado antes de que el cliente estuviera escuchando (los remotos no guardan mensajes).
	PedirDatos = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 2,
		Argumentos = {},
	},

	-- ===== Combate =====

	-- El cliente pide usar una habilidad. Solo dice CUÁL, hacia dónde apunta y a qué distancia: el
	-- servidor decide si puede (cooldown, energía, estado, alcance) y qué golpea. Los argumentos son:
	-- id de la habilidad, dirección (vector unitario) y distancia al punto señalado.
	UsarHabilidad = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 6,
		Rafaga = 4,
		Argumentos = {
			Validador.Enumeracion(Poderes.Solicitables),
			Validador.Vector3(1.5),
			Validador.Numero(0, 400),
		},
	},

	-- El servidor avisa a todos de que una habilidad ha empezado (para animación y efectos de carga).
	HabilidadIniciada = {
		Direccion = "ServidorACliente",
	},

	-- El servidor avisa a todos del impacto: dónde cae y a quién ha golpeado (efectos de impacto).
	HabilidadImpacto = {
		Direccion = "ServidorACliente",
	},

	-- El servidor avisa a todos de que un luchador ha sido interrumpido (aturdido o muerto) mientras lanzaba una
	-- habilidad: los clientes cancelan su animación y los efectos de carga que aún no han terminado.
	HabilidadInterrumpida = {
		Direccion = "ServidorACliente",
	},

	-- Estado propio de combate: energía, cooldowns. Solo se envía al jugador afectado.
	EstadoCombate = {
		Direccion = "ServidorACliente",
	},

	-- El cliente pide su estado de combate (al arrancar, por si el servidor ya lo había enviado).
	PedirEstadoCombate = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 2,
		Argumentos = {},
	},

	-- ===== Naves =====
	-- Despegar no necesita remoto: lo pide el ProximityPrompt de la plataforma del hangar, que vive en el servidor.

	-- El piloto quiere aterrizar (volver al hangar). El servidor decide si puede y lo devuelve a la plataforma.
	AterrizarNave = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 1,
		Argumentos = {},
	},

	-- El piloto dispara. Solo manda hacia dónde apunta: el servidor decide si puede (cadencia), desde qué cañón
	-- sale, a qué puede apuntar (cono delante de la proa), qué golpea y cuánto daño hace.
	DispararNave = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 12,
		Rafaga = 6,
		Argumentos = { Validador.Vector3(1.5) },
	},

	-- El piloto enciende o apaga el turbo. El servidor lleva el depósito de energía y fija el límite de velocidad.
	TurboNave = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 4,
		Rafaga = 3,
		Argumentos = { Validador.Booleano() },
	},

	-- El cliente pide el estado de su nave (al arrancar o al entrar a un servidor con la nave ya en vuelo).
	PedirEstadoNave = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 2,
		Argumentos = {},
	},

	-- Estado de la nave propia: vida, escudo, turbo y estadísticas. Solo se envía al piloto.
	EstadoNave = {
		Direccion = "ServidorACliente",
	},

	-- Una nave acaba de despegar: todos ven el arranque de los motores.
	NaveDespegue = {
		Direccion = "ServidorACliente",
	},

	-- Una nave ha disparado: modelo, desde dónde, hasta dónde llega, hacia dónde mira y cuánto tarda en llegar.
	NaveDisparo = {
		Direccion = "ServidorACliente",
	},

	-- Un disparo ha llegado a su destino: dónde y contra qué ("Escudo", "Casco", "Asteroide").
	NaveImpacto = {
		Direccion = "ServidorACliente",
	},

	-- Una nave ha chocado con un asteroide: dónde, normal de la superficie, si el escudo aguantó y la intensidad.
	NaveChoque = {
		Direccion = "ServidorACliente",
	},

	-- Una nave ha sido destruida: modelo y posición.
	NaveDestruida = {
		Direccion = "ServidorACliente",
	},

	-- Un asteroide ha estallado: dónde y su tamaño.
	AsteroideDestruido = {
		Direccion = "ServidorACliente",
	},

	-- ===== Planetas =====

	-- El servidor lleva al jugador a otra zona (aterrizar, despegar o viajar): fundido a negro y vuelta.
	TransicionPlaneta = {
		Direccion = "ServidorACliente",
	},

	-- ===== Exploración: escáner de mano, minería y crafteo =====

	-- El jugador apunta con el escáner a algo escaneable. Solo dice QUÉ: el servidor comprueba que se pueda analizar,
	-- que esté al alcance de SU escáner (mejora Escáner), que lo vea, y cuánto tarda.
	EscanearObjetivo = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 3,
		Rafaga = 2,
		Argumentos = { Validador.Instancia() },
	},

	-- El jugador suelta el escáner antes de terminar el análisis.
	CancelarEscaneo = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 3,
		Rafaga = 2,
		Argumentos = {},
	},

	-- Un jugador ha empezado a escanear: quién, qué y cuánto dura (efectos de escaneo para todos los cercanos).
	EscaneoIniciado = {
		Direccion = "ServidorACliente",
	},

	-- Un escaneo se ha interrumpido (soltó, se alejó, murió, el objetivo desapareció): quién.
	EscaneoCancelado = {
		Direccion = "ServidorACliente",
	},

	-- Un escaneo ha terminado: quién, qué y dónde (efecto final para todos).
	EscaneoCompletado = {
		Direccion = "ServidorACliente",
	},

	-- La ficha del análisis, solo para quien escaneó: especie, si es nueva, recompensa y veces escaneada.
	FichaEscaner = {
		Direccion = "ServidorACliente",
	},

	-- El jugador pica un mineral con su pico. El servidor comprueba distancia, cadencia y espacio en la bodega.
	PicarMineral = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 5,
		Rafaga = 3,
		Argumentos = { Validador.Instancia() },
	},

	-- Un mineral ha recibido un golpe (de pico o de láser): dónde, tipo y fracción de vida que le queda.
	MineralGolpeado = {
		Direccion = "ServidorACliente",
	},

	-- Un mineral se ha roto: dónde y tipo.
	MineralRoto = {
		Direccion = "ServidorACliente",
	},

	-- Mensaje corto para el jugador ("+4 Hierro", "Bodega llena"): texto y tono ("Bien", "Mal" o "Info").
	AvisoExploracion = {
		Direccion = "ServidorACliente",
	},

	-- El jugador pide fabricar una receta (una vez o varias, si es un objeto). El servidor comprueba que esté junto a
	-- una mesa, que tenga los materiales y las monedas, y que quepa el resultado.
	FabricarReceta = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 3,
		Rafaga = 2,
		Argumentos = {
			Validador.Enumeracion(Recetas.Orden),
			Validador.Opcional(Validador.Entero(1, ConfigExploracion.CantidadMaximaPorPeticion)),
		},
	},

	-- Resultado de un intento de fabricar: receta, si salió bien y el motivo en texto si no.
	ResultadoCrafteo = {
		Direccion = "ServidorACliente",
	},

	-- El jugador ha usado una mesa de crafteo: el cliente abre el panel de recetas.
	AbrirMesaCrafteo = {
		Direccion = "ServidorACliente",
	},

	-- ===== Tiendas del planeta humano =====

	-- El jugador pide comprar un artículo (una vez o varias, si es un material) en una tienda. Solo dice EN QUÉ tienda
	-- (el modelo), QUÉ y cuántos: el servidor comprueba que sea una tienda, que esté junto al mostrador, su bando (a los
	-- Monstruos no se les vende), la persiana, las monedas, el nivel de la mejora y el espacio en la bodega.
	ComprarArticulo = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 4,
		Rafaga = 3,
		Argumentos = {
			Validador.Instancia("Model"),
			Validador.Enumeracion(Catalogo.Orden),
			Validador.Opcional(Validador.Entero(1, ConfigTiendas.CantidadMaximaPorPeticion)),
		},
	},

	-- Resultado de un intento de compra: artículo, si salió bien y el motivo en texto si no.
	ResultadoCompra = {
		Direccion = "ServidorACliente",
	},

	-- El jugador ha usado el mostrador de una tienda y se le puede atender: el cliente abre el panel (con el modelo).
	AbrirTienda = {
		Direccion = "ServidorACliente",
	},
}

-- Se congela la lista (dos niveles) para que ningún script la modifique por accidente.
for _, definicion in definiciones do
	if definicion.Argumentos ~= nil then
		table.freeze(definicion.Argumentos)
	end
	table.freeze(definicion)
end
Remotos.Definiciones = table.freeze(definiciones)

return Remotos
