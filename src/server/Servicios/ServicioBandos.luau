--!strict
--[[
	ServicioBandos: atiende la elección de bando del jugador (Humanos o Monstruos).

	Es el primer consumidor real de los sistemas de red y de datos, y sirve de ejemplo de cómo escribir
	un servicio:
	  - Recibe la petición por ServicioRed.Conectar. Cuando el manejador se ejecuta, el remoto ya ha pasado
	    el límite por segundo y la validación (el bando es "Humanos" o "Monstruos"), pero la lógica de la
	    partida sigue siendo cosa del manejador: ¿tiene ya bando? ¿han cargado sus datos?
	  - Modifica directamente los datos que devuelve ServicioDatos.ObtenerDatos.
	  - Avisa al cliente con ServicioReplicacion y guarda de inmediato, porque elegir bando es una decisión
	    que no debe perderse si el servidor falla.

	Regla actual: el bando se elige una sola vez y no se puede cambiar. Para permitir cambios (con un
	coste, un enfriamiento...) bastaría con modificar la comprobación del manejador.

	Además publica el bando de cada jugador en el atributo Bandos.Atributo de su Player, para que todos los
	clientes lo sepan (lo usa el andar de monstruo). El atributo siempre refleja los datos del servidor: se pone al
	cargar los datos y cada vez que el bando cambia aquí. Cualquier otro código que cambie datos.Bando (el cambio
	de bando de pago, por ejemplo) debe llamar después a ServicioBandos.Publicar.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Bandos = require(ReplicatedStorage.Shared.Juego.Bandos)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioBandos = {}

-- Copia el bando guardado del jugador en el atributo de su Player (nil si sus datos no han cargado).
function ServicioBandos.Publicar(jugador: Player)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	jugador:SetAttribute(Bandos.Atributo, if datos then datos.Bando else nil)
end

-- Asigna el bando al jugador si todavía no tiene (la regla de arriba). Lo usa el remoto y la zona de pruebas.
function ServicioBandos.Elegir(jugador: Player, bando: Bandos.IdBando)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return -- sus datos todavía no han cargado: no hay dónde guardar la elección
	end
	if datos.Bando ~= Bandos.Ninguno then
		return -- ya eligió bando
	end

	datos.Bando = bando
	ServicioBandos.Publicar(jugador)
	ServicioReplicacion.EnviarDatos(jugador)
	ServicioDatos.GuardarAhora(jugador)
end

-- Empieza a atender el remoto ElegirBando y a publicar los bandos. Debe llamarse una sola vez, después de
-- ServicioRed.Iniciar() y antes de ServicioDatos.Iniciar() (para no perderse ningún DatosCargados).
function ServicioBandos.Iniciar()
	ServicioRed.Conectar("ElegirBando", ServicioBandos.Elegir)
	ServicioDatos.DatosCargados:Conectar(ServicioBandos.Publicar)
end

return ServicioBandos
