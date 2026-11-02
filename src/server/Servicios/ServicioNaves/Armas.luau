--!strict
--[[
	Armas (Naves): resuelve un disparo de nave EN EL SERVIDOR.

	El cliente solo dice hacia dónde apunta (una dirección). Todo lo demás lo decide el servidor:

	  1. CADENCIA     ¿ha pasado el intervalo que permite el nivel de Armas? (Naves/Reglas.PuedeDisparar)
	  2. DIRECCIÓN    se limita a un cono alrededor de la proa de la nave, medida por el servidor
	                  (Naves/Reglas.LimitarCono): no se puede disparar hacia atrás ni hacia un lado.
	  3. ORIGEN       sale de uno de los dos cañones del modelo, alternando; el cliente no elige desde dónde.
	  4. TRAYECTORIA  un raycast del servidor hasta el alcance del arma decide qué se golpea: un asteroide, otra
	                  nave o el escenario. Las propias partes de la nave se ignoran.

	Este módulo NO aplica daño ni avisa a los clientes: devuelve qué ha pasado y ServicioNaves lo ejecuta
	(el daño llega cuando termina el vuelo del proyectil).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Naves.Config)
local Reglas = require(ReplicatedStorage.Shared.Naves.Reglas)

export type Resultado = {
	Origen: Vector3,
	Punto: Vector3, -- dónde acaba el disparo (el impacto, o el alcance máximo)
	Direccion: Vector3,
	Viaje: number, -- segundos que tarda el proyectil en llegar
	Golpe: BasePart?, -- parte golpeada, si hay
	Normal: Vector3?,
}

local Armas = {}

--[[
	Intenta disparar. Devuelve nil si no se puede (todavía no toca por la cadencia). `nave` aporta el modelo, la raíz, las
	estadísticas y los campos UltimoDisparo y CanonAlterno, que esta función actualiza al disparar.
]]
function Armas.Resolver(nave: any, direccionPedida: Vector3, ahora: number): Resultado?
	if not Reglas.PuedeDisparar(nave.UltimoDisparo, ahora, nave.Stats.Cadencia) then
		return nil
	end
	nave.UltimoDisparo = ahora

	local raiz: BasePart = nave.Raiz
	local proa = raiz.CFrame.LookVector
	local limitada = Reglas.LimitarCono(
		{ X = proa.X, Y = proa.Y, Z = proa.Z },
		{ X = direccionPedida.X, Y = direccionPedida.Y, Z = direccionPedida.Z }
	)
	local direccion = Vector3.new(limitada.X, limitada.Y, limitada.Z)

	-- Cañón: alterna izquierdo y derecho.
	nave.CanonAlterno = (nave.CanonAlterno + 1) % 2
	local nombreCanon = if nave.CanonAlterno == 0 then "CanonIzq" else "CanonDer"
	local canon = raiz:FindFirstChild(nombreCanon) :: Attachment?
	local origen = if canon then canon.WorldPosition else raiz.Position + proa * 4

	-- Trayectoria: se ignora la propia nave.
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	parametros.FilterDescendantsInstances = { nave.Modelo }
	local alcance: number = nave.Stats.Alcance
	local choque = workspace:Raycast(origen, direccion * alcance, parametros)

	local punto = if choque then choque.Position else origen + direccion * alcance
	return {
		Origen = origen,
		Punto = punto,
		Direccion = direccion,
		Viaje = (punto - origen).Magnitude / Config.VelocidadProyectil,
		Golpe = if choque then choque.Instance else nil,
		Normal = if choque then choque.Normal else nil,
	}
end

return Armas
