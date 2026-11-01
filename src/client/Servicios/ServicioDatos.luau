--!strict
--[[
	ServicioDatos (cliente): copia local, de solo lectura, de los datos del jugador.

	Los datos de verdad viven en el servidor. Este servicio guarda la última copia que el servidor ha
	enviado y avisa cuando llega una nueva, para que la interfaz (barras de XP, monedas, nave...) se
	actualice. Nunca modifiques esta copia: no cambia nada en el servidor, y la próxima copia que llegue la
	sustituirá. Para pedir un cambio hay que enviar una petición por ServicioRed.

	Uso:
		ServicioDatos.Iniciar()                       -- una sola vez, después de ServicioRed.Iniciar()
		local datos = ServicioDatos.Obtener()         -- nil hasta que llegue la primera copia
		ServicioDatos.Actualizados:Conectar(function(datos) ... end)
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Se espera a que Roblox replique la carpeta compartida antes de requerir módulos de ella.
ReplicatedStorage:WaitForChild("Shared")
local Shared = ReplicatedStorage.Shared
local Senal = require(Shared.Utilidades.Senal)
local Tipos = require(Shared.Datos.Tipos)
local ServicioRed = require(script.Parent.ServicioRed)

local ServicioDatos = {}

-- Se dispara (con la copia nueva de los datos) cada vez que el servidor envía los datos.
ServicioDatos.Actualizados = Senal.nueva()

local datos: Tipos.Datos? = nil

-- Devuelve la última copia de los datos recibida, o nil si todavía no ha llegado ninguna.
function ServicioDatos.Obtener(): Tipos.Datos?
	return datos
end

--[[
	Empieza a recibir los datos del servidor y los pide por si ya los había enviado antes de que el cliente
	estuviera escuchando. Debe llamarse una sola vez, después de ServicioRed.Iniciar().
]]
function ServicioDatos.Iniciar()
	ServicioRed.Conectar("DatosJugador", function(recibidos: Tipos.Datos)
		datos = recibidos
		ServicioDatos.Actualizados:Disparar(recibidos)
	end)
	ServicioRed.Enviar("PedirDatos")
end

return ServicioDatos
