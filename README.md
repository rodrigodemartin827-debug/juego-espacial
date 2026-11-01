# Juego Espacial

Juego de exploración espacial con PvP para Roblox: dos bandos (Héroes y Villanos), naves, poderes, escáner y
crafteo. Proyecto de [Rojo](https://rojo.space) escrito en Luau.

Por ahora el repositorio contiene la **base técnica** sobre la que se construirá el juego:

- la estructura del proyecto (`src/server`, `src/client`, `src/shared`),
- un **sistema de red** con RemoteEvents validados en el servidor y límite de peticiones por segundo,
- un **sistema de datos** con DataStore y **bloqueo de sesión** que guarda bando, nivel, XP, monedas, inventario y
  mejoras de la nave,
- un primer servicio de ejemplo (elegir bando) que usa los dos sistemas, y
- pruebas automáticas que se ejecutan fuera de Studio.

Los poderes, las naves, el escáner y el crafteo todavía no existen: se añadirán como servicios nuevos encima de esta base.

## Puesta en marcha

1. Instala [Rokit](https://github.com/rojo-rbx/rokit) y, desde la carpeta del proyecto, las herramientas que
   fija `rokit.toml` (Rojo, StyLua, Selene y Lune):

   ```bash
   rokit install
   ```

2. Instala el plugin de Rojo en Roblox Studio, abre un lugar vacío y arranca el servidor de Rojo:

   ```bash
   rojo serve
   ```

   Después pulsa **Connect** en el plugin de Studio. También se puede generar un archivo de lugar con
   `rojo build -o JuegoEspacial.rbxl`.

3. Pulsa **Play** en Studio. En la consola deben aparecer `[Servidor] Juego espacial iniciado` y
   `[Cliente] Datos recibidos: ...`.

> **DataStore en Studio.** Mientras el lugar no esté publicado, o no tenga activado *Enable Studio Access to API
> Services* en la configuración del juego, el DataStore real no está disponible. En ese caso el servicio de datos
> avisa por la consola y usa un almacén **en memoria** (los datos se pierden al parar la prueba), así que se puede
> trabajar sin configurar nada. Con el DataStore real, en Studio se usa un almacén aparte (`DatosJugador_Studio`)
> para no mezclar datos de prueba con los de los jugadores.

## Estructura

```
default.project.json         Qué carpeta va a qué servicio de Roblox
rokit.toml                   Versiones de las herramientas
stylua.toml, selene.toml     Formato y análisis estático del código

src/
├── shared/                  → ReplicatedStorage.Shared (servidor y cliente)
│   ├── Datos/Tipos          Tipos de los datos del jugador
│   ├── Juego/Bandos         Héroes, Villanos y "Ninguno"
│   ├── Red/
│   │   ├── Remotos          Lista central de RemoteEvents
│   │   ├── Validador        Validadores de argumentos
│   │   └── LimitadorDeTasa  Cubo de fichas (peticiones por segundo)
│   └── Utilidades/          Senal (eventos) y Tablas (copia profunda)
├── server/                  → ServerScriptService.Server (un Script con sus módulos)
│   ├── init.server.luau     Arranque: inicia los servicios en orden
│   └── Servicios/
│       ├── ServicioRed          Crea los remotos y filtra las peticiones
│       ├── ServicioDatos/       DataStore con bloqueo de sesión
│       │   ├── init             API pública, carga, autoguardado, cierre
│       │   ├── BloqueoSesion    Reglas del bloqueo (funciones puras)
│       │   ├── Esquema          Plantilla, reparación de datos, migraciones
│       │   └── AlmacenMemoria   DataStore falso para Studio
│       ├── ServicioReplicacion  Envía al cliente una copia de sus datos
│       └── ServicioBandos       Ejemplo: elegir bando
└── client/                  → StarterPlayer.StarterPlayerScripts.Client (un LocalScript)
    ├── init.client.luau     Arranque del cliente
    └── Servicios/
        ├── ServicioRed      Envía peticiones y escucha avisos
        └── ServicioDatos    Copia local (solo lectura) de los datos

pruebas/                     Pruebas con Lune (ver más abajo)
```

Convenciones: todo el código de `src/` va en módulos con `--!strict` y comentarios en español; los nombres de módulos,
tipos y funciones públicas son `PascalCase` sin tildes (Luau no admite tildes en identificadores), las variables locales
`camelCase` y las constantes `MAYUSCULAS_CON_GUION_BAJO`. Los puntos de entrada solo arrancan servicios.

## Sistema de red

Toda la comunicación usa **RemoteEvents** (nunca RemoteFunctions: el servidor no debe quedarse esperando la respuesta de
un cliente que puede ser un tramposo). El servidor no se fía de nada de lo que envía el cliente.

`Red/Remotos` es la **única fuente de verdad**: el servidor crea los RemoteEvents a partir de esa lista y el cliente los
busca por su nombre. Cada remoto indica su dirección, su límite y cómo se valida:

```lua
ElegirBando = {
    Direccion = "ClienteAServidor",
    LimitePorSegundo = 1,                                    -- peticiones por segundo y por jugador
    Argumentos = { Validador.Enumeracion(Bandos.Elegibles) }, -- un validador por argumento
},
DatosJugador = { Direccion = "ServidorACliente" },
```

Por cada petición que llega, `ServicioRed` (servidor) hace, en orden:

1. **Límite por segundo**, por jugador y por remoto, con un cubo de fichas: el ritmo sostenido nunca supera
   `LimitePorSegundo`, y `Rafaga` (por defecto igual al límite) fija cuántas peticiones seguidas se toleran de golpe.
2. **Validación** de los argumentos: tipo, rango, longitud, valores NaN/infinitos y número de argumentos (se rechazan los
   de más). Los validadores disponibles son `Numero`, `Entero`, `Cadena`, `Booleano`, `Enumeracion`, `Vector3`,
   `Instancia` y `Opcional`.
3. **Manejador** registrado con `ServicioRed.Conectar`, protegido con `xpcall`: un error en la lógica del juego se
   registra con su traza y no afecta a las demás peticiones.

Lo que no pasa los pasos 1 o 2 se descarta en silencio y cuenta como infracción; con 30 infracciones en 10 segundos se
expulsa al jugador (se ajusta con `MAX_INFRACCIONES` y `VENTANA_INFRACCIONES` en `ServicioRed`). Que los argumentos
tengan buena forma no significa que la acción tenga sentido: eso lo comprueba cada manejador (¿tiene monedas?, ¿está a
tiro?).

El cliente usa los **mismos validadores y límites** antes de enviar. No es una medida de seguridad (un tramposo se la
salta, por eso el servidor lo comprueba todo otra vez), sino de cortesía: un cliente legítimo nunca provoca infracciones.

Para **añadir un remoto**: declararlo en `Red/Remotos`, registrar su manejador en el servidor y usarlo desde el cliente.

```lua
-- servidor
ServicioRed.Conectar("ElegirBando", function(jugador, bando)
    -- aquí `bando` ya es "Heroes" o "Villanos"
end)
ServicioRed.EnviarACliente(jugador, "DatosJugador", datos)

-- cliente
ServicioRed.Enviar("ElegirBando", "Heroes")        -- devuelve false si no pasa la validación o va demasiado deprisa
ServicioRed.Conectar("DatosJugador", function(datos) end)
```

## Sistema de datos

`ServicioDatos` guarda en un DataStore, para cada jugador (clave `Jugador_<UserId>`): **bando, nivel, XP, monedas,
inventario y mejoras de la nave**. Los valores iniciales están en la plantilla de `Servicios/ServicioDatos/Esquema`
(las mejoras de la nave son `Casco`, `Escudo`, `Motor`, `Armas`, `Escaner` y `Carga`, y se pueden cambiar ahí).

### Bloqueo de sesión

Un jugador puede estar en dos servidores a la vez durante unos instantes (al saltar de servidor, al reconectar tras una
caída...). Si ambos cargan y guardan sus datos, el último pisa al otro. Para evitarlo, cada registro lleva un
**bloqueo** que indica qué sesión lo está usando:

- Al entrar, el servidor **toma el bloqueo** con `UpdateAsync` a la vez que lee los datos. Si lo tiene otro servidor,
  espera y reintenta; si sigue ocupado tras unos intentos, expulsa al jugador con un mensaje claro en lugar de dejarle
  jugar con datos que luego no se podrían guardar.
- Mientras juega, sus datos viven en memoria y se **autoguardan cada 60 s**. Cada guardado comprueba que el bloqueo sigue
  siendo suyo y refresca su marca de tiempo. Si otro servidor lo ha tomado, no escribe nada, descarta los cambios sin
  guardar y expulsa al jugador: un servidor nunca puede pisar los datos del que tiene el bloqueo.
- Al salir el jugador, o al cerrarse el servidor (`BindToClose`), hace un **guardado final que libera el bloqueo**. Al
  cerrar, todos los jugadores se guardan a la vez dentro del límite de 30 s de Roblox.
- Si un servidor se cae sin liberar, el bloqueo queda abandonado: pasados **5 minutos** sin refrescarse, cualquier servidor
  puede tomarlo (hasta entonces, el jugador no podrá entrar en otro servidor).

Además: los fallos del DataStore se reintentan con espera creciente; los guardados de un jugador nunca se solapan; los
datos se reparan antes de cada guardado (un `NaN` en las monedas haría fallar todos los guardados); cada registro se asocia
al `UserId` (para poder borrarlo si el jugador lo pide); y un registro corrupto, o guardado con un esquema más nuevo que el
del servidor, no se carga ni se sobrescribe.

Los tiempos se ajustan en `ServicioDatos.Configuracion` (por ejemplo `IntervaloAutoguardado` o `CaducidadBloqueo`).

### Uso desde otros servicios

```lua
ServicioDatos.DatosCargados:Conectar(function(jugador) end)  -- ya hay datos disponibles
local datos = ServicioDatos.ObtenerDatos(jugador)            -- la tabla viva; nil si aún no han cargado
datos.Monedas += 10                                          -- se modifica directamente y se guarda sola
ServicioReplicacion.EnviarDatos(jugador)                     -- avisa al cliente del cambio
ServicioDatos.GuardarAhora(jugador)                          -- guardar ya, tras un cambio importante
```

Modifica los datos solo desde el servidor. El cliente recibe una copia (`ServicioReplicacion`) y la guarda en su
`ServicioDatos`, que es de solo lectura.

### Cambiar el esquema

- **Añadir un campo**: ponerlo en la plantilla de `Esquema` y en `Datos/Tipos`. Los jugadores que ya existen lo reciben con
  su valor inicial la próxima vez que cargan.
- **Renombrar, mover o borrar un campo**: subir `Esquema.VERSION` y añadir la función correspondiente en
  `Esquema.Migraciones`. Se aplican en orden al cargar y los datos se guardan ya con la versión nueva.

Los identificadores que se guardan (`"Heroes"`, `"Villanos"`, los ids de objetos y mejoras) no deben cambiarse una vez
publicado el juego.

## Pruebas

Las pruebas ejecutan los módulos reales de `src/` fuera de Studio con [Lune](https://lune-org.github.io/docs), sobre una
simulación mínima de la API de Roblox (`pruebas/infraestructura`):

```bash
lune run pruebas/ejecutar                   # todas
lune run pruebas/ejecutar BloqueoSesion     # solo las que contengan ese texto en el nombre
```

Cubren la red (validación, límites, expulsión, envío en ambos sentidos), el esquema, el bloqueo de sesión y el servicio de
datos con **varios servidores simulados compitiendo por el mismo DataStore** (traspaso sin perder progreso, servidor caído,
bloqueo perdido, fallos y respuestas perdidas del DataStore, reconexiones rápidas, cierre del servidor...) y la integración
de punta a punta con los scripts de arranque reales.

La simulación es una aproximación: sirve para comprobar la lógica, no sustituye a probar en Studio y en un servidor real.

Calidad del código:

```bash
stylua --check src pruebas       # formato
selene generate-roblox-std       # una sola vez
selene src pruebas               # análisis estático
```

Para tener autocompletado y comprobación de tipos en el editor con [luau-lsp](https://github.com/JohnnyMorganz/luau-lsp),
genera el mapa de fuentes con `rojo sourcemap default.project.json -o sourcemap.json`.
