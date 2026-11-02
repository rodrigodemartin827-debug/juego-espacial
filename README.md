# Juego Espacial

Juego de exploración espacial con PvP para Roblox: dos bandos (Héroes y Villanos), naves, poderes, escáner y
crafteo. Proyecto de [Rojo](https://rojo.space) escrito en Luau.

Por ahora el repositorio contiene la **base técnica** sobre la que se construirá el juego:

- la estructura del proyecto (`src/server`, `src/client`, `src/shared`),
- un **sistema de red** con RemoteEvents validados en el servidor y límite de peticiones por segundo,
- un **sistema de datos** con DataStore y **bloqueo de sesión** que guarda bando, nivel, XP, monedas, inventario y
  mejoras de la nave,
- un primer servicio de ejemplo (elegir bando) que usa los dos sistemas,
- el **sistema de combate** (servidor autoritativo, poderes Rayo y Gravedad, combo, VFX por fases, interfaz y una zona de
  pruebas; ver [Combate](#combate)), y
- pruebas automáticas que se ejecutan fuera de Studio.

Las naves, el escáner y el crafteo todavía no existen: se añadirán como servicios nuevos encima de esta base.

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

## Avatar R6

**El juego es solo R6**: todos los personajes usan las 6 piezas clásicas (`Torso`, `Head`, `Right Arm`, `Left Arm`,
`Right Leg`, `Left Leg`, más `HumanoidRootPart`). Las animaciones del combate, las anclas de los efectos (el puño es la punta
del `Right Arm`), los muñecos de entrenamiento y las animaciones de Blender están hechos para ese rig. R6 no tiene codos,
rodillas ni manos, así que cada brazo y cada pierna se anima como una pieza rígida.

### Dónde se pone R6

El tipo de avatar es un ajuste **del juego en la web de Roblox**, no una propiedad de `StarterPlayer`, así que Rojo no
puede fijarlo desde `default.project.json`. Ponlo una vez a mano:

1. En Roblox Studio, abre el lugar y ve a **Home → Game Settings** (o en [create.roblox.com](https://create.roblox.com):
   **Creations →** tu experiencia **→ Configure**).
2. Entra en la pestaña **Avatar**.
3. En **Avatar Type** elige **R6** (no *R15* ni *Player Choice*) y guarda con **Save**.
4. Publica el lugar (**File → Publish to Roblox**). En Studio, para probarlo, vuelve a abrir el lugar o pulsa **Play** de nuevo.

### Red de seguridad por código

Si ese ajuste se olvida (o el lugar no está publicado), `ServicioPersonaje` lo corrige al instante: cuando aparece un
personaje que no es R6, crea otro **R6 con el mismo aspecto** (`Humanoid:GetAppliedDescription`), lo coloca en la misma
posición, le copia los scripts del personaje (`Animate` y los de `StarterCharacterScripts`) y se lo asigna al jugador. Además avisa por
consola (`[ServicioPersonaje] ... no es R6`) para que te acuerdes de poner el ajuste de arriba. Con el ajuste bien puesto
no hace nada.

Limitaciones: la sustitución se ve como un parpadeo del personaje al aparecer, y no he podido probarla en Studio (las
pruebas automáticas la cubren con personajes simulados). Si usas un script `Animate` propio, asegúrate de que soporta R6.
Ni el `Animator` del combate (`VFX/Animador`) ni las animaciones importadas funcionan en R15: el animador avisa y las ignora.

La prueba `pruebas/casos/SoloR6` **falla si aparece cualquier pieza de R15** (`UpperTorso`, `RightHand`, `LeftLowerLeg`...) en
`src/` o en los scripts de Blender, para que no se cuele por error.

## Estructura

```
default.project.json         Qué carpeta va a qué servicio de Roblox
rokit.toml                   Versiones de las herramientas
stylua.toml, selene.toml     Formato y análisis estático del código

src/
├── shared/                  → ReplicatedStorage.Shared (servidor y cliente)
│   ├── Datos/Tipos          Tipos de los datos del jugador
│   ├── Juego/Bandos         Héroes, Villanos y "Ninguno"
│   ├── Combate/             Datos y reglas del combate (ver más abajo)
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
│       ├── ServicioPersonaje    Garantiza que todos los personajes son R6
│       ├── ServicioBandos       Ejemplo: elegir bando
│       ├── ServicioCombate      Combate: cooldown, energía, alcance, daño (autoritativo)
│       └── ZonaPruebas          Plataforma con muñecos de entrenamiento
└── client/                  → StarterPlayer.StarterPlayerScripts.Client (un LocalScript)
    ├── init.client.luau     Arranque del cliente
    ├── Servicios/
    │   ├── ServicioRed      Envía peticiones y escucha avisos
    │   └── ServicioDatos    Copia local (solo lectura) de los datos
    ├── Combate/             Entrada, interfaz (vida, energía, cooldowns), números de daño
    └── VFX/                 Motor de efectos visuales (ver Combate)

pruebas/                     Pruebas con Lune (ver más abajo)
animaciones/                 Animaciones de combate (.fbx para R6) y los scripts de Blender que las generan
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

## Combate

El cliente **pide** usar una habilidad; el **servidor decide**. Los del mismo bando no se hacen daño (un jugador sin bando
puede dañar y ser dañado por cualquiera).

### Cómo se decide (servidor)

`UsarHabilidad(id, dirección, distancia)` pasa por `Combate/Arbitro`, que comprueba en orden:

1. **Estado**: vivo, sin aturdimiento y sin otra habilidad en marcha.
2. **Cooldown** de esa habilidad.
3. **Energía** (se regenera sola con el tiempo, sin bucles).
4. **Distancia**: el punto señalado debe estar dentro del alcance (se recorta al rango real).

Si todo es válido, cobra la energía, arranca el cooldown y avisa a todos (`HabilidadIniciada`). Pasado el tiempo de carga y
de viaje, el servidor calcula **él mismo** a quién alcanza (forma del golpe, alcance medido otra vez desde donde está ahora el
lanzador, bando, invulnerabilidad), aplica el daño y avisa del impacto (`HabilidadImpacto`). El cliente no dice a quién
golpea ni cuánto daño hace. Quien recibe un golpe queda aturdido (esto interrumpe lo que estuviera lanzando: el servidor cancela su golpe y avisa
con `HabilidadInterrumpida` para que los clientes paren su animación y sus efectos de carga) y su propio
cliente aplica el empuje.

Las reglas son funciones puras (`Combate/Reglas`, `Combate/Arbitro`) y tienen pruebas propias.

### Qué se puede jugar

| Poder | Básico | Fuerte | Definitiva (con cinemática) |
| --- | --- | --- | --- |
| **Rayo** (`Z` `X` `C`) | Chispa Voltaica: rayo veloz en línea | Trueno Divino: rayo del cielo sobre una zona | Tormenta Celestial |
| **Gravedad** (`V` `B` `N`) | Pulso Gravitatorio: esfera que aplasta | Aplastamiento: zona hundida contra el suelo | Singularidad: agujero negro que arrastra y colapsa |
| **Cuerpo a cuerpo** (clic) | Combo de 4 golpes: gancho, revés, patada giratoria y remate | | |

En móvil, los mismos botones aparecen en la esquina inferior derecha y se apunta hacia el enemigo más cercano delante de la
cámara. Hay barra de vida y de energía, y cada botón muestra su cooldown y se apaga si falta energía.

### Zona de pruebas

Al arrancar el servidor se crea (`ZonaPruebas`) una plataforma con tres muñecos de entrenamiento: uno de los **Héroes**,
uno de los **Villanos** y uno **sin bando**; renacen solos. Dos pedestales (`ProximityPrompt`) permiten elegir bando sin
interfaz: si eliges Héroes, el muñeco Héroe ya no recibe tu daño. El bando se elige una sola vez (regla de `ServicioBandos`).

### Efectos visuales (VFX)

Cada habilidad tiene una receta en `Combate/Datos/EfectosVFX` con cinco **fases**, y cada fase combina varias **capas**:

| Fase | Cuándo | Ejemplos de capas |
| --- | --- | --- |
| Anticipación | al aceptar la habilidad | aura, esferas que crecen, partículas que convergen, luz, aviso en el suelo |
| Lanzamiento | acaba la carga | proyectil con estela, rayos, onda de salida |
| Impacto | lo confirma el servidor | explosión, ondas, escombros, cráter temporal, cámara (sacudida, FOV, desenfoque, destello) |
| Residuo | tras el impacto | brasas, humo, arcos eléctricos, luz que se apaga |
| Golpeado | por cada enemigo alcanzado | destello, chispas, pantalla del golpeado, reacción |

Tipos de capa: `Particulas`, `Onda`, `Esfera`, `Luz`, `Proyectil`, `Corte`, `Haz` (rayos con zigzag y ramas),
`Escombros`, `Crater`, `Tinte`, `Desenfoque`, `Zoom`, `Sacudida`, `Hitstop` y `Sonido`. Cada módulo de `client/VFX/Capas`
documenta sus campos.

**Móvil y rendimiento**: los objetos se reutilizan (`VFX/Pool`, con precalentado), un único bucle mueve todo lo animado
(`VFX/Actores`) y `VFX/Calidad` mide los fotogramas por segundo para bajar (o subir) entre Bajo, Medio y Alto, escalando
partículas, escombros, luces y segmentos de rayo. En móvil se empieza en Medio. Las capas con `Minimo = "Alto"` se omiten
en dispositivos lentos y los efectos lejanos no se dibujan.

### Cambiar cosas sin tocar código

Todo está en `src/shared/Combate/Datos/`:

| Quiero cambiar... | Archivo |
| --- | --- |
| **IDs de texturas, mallas, animaciones y sonidos** | `Recursos` (cadena vacía = valor por defecto) |
| Colores de un poder | `Paleta` |
| Daño, cooldown, energía, alcance, tiempos, teclas | `Poderes` |
| Tamaños, cantidades y tiempos de los efectos | `EfectosVFX` |
| Movimientos de cámara de las definitivas | `Cinematicas` |
| Las animaciones provisionales | `Animaciones` |

**Sustituir una animación**: las animaciones provisionales están hechas por código (`Animaciones`) y se convierten en una
`KeyframeSequence` al jugarse. Cada cuadro da, para cada pieza R6, tres ángulos en grados desde el punto de vista del
personaje (`cabeceo`, `giro`, `ladeo`) y opcionalmente una traslación en studs; `Animaciones.Articulacion` los convierte al eje
de cada `Motor6D` (en R6 cada articulación tiene el suyo). Todas tienen anticipación, impacto exagerado y recuperación. Para usar una hecha en el editor de Roblox, pega su ID en `Recursos.Animaciones`
(por ejemplo `Combo1 = "rbxassetid://123456"`); desde ese momento se usa esa, sin más cambios. Las animaciones están hechas para
el rig **R6** (ver *Avatar R6*). Con `Recursos.Mallas` ocurre lo mismo (el mesh debe medir 1 stud) y con las texturas de `Recursos.Texturas`.

Limitaciones conocidas: no he podido probarlo dentro de Roblox Studio (las pruebas automáticas cubren reglas y datos, no el
aspecto), así que los números de los efectos (tamaños, tiempos) son un primer ajuste.

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
de punta a punta con los scripts de arranque reales. Para el combate comprueban el árbitro (cooldown, energía, alcance,
estado, combo, fuego amistoso), la geometría de los golpes, la conversión de las poses a los ejes de los `Motor6D` de R6, el
servicio que fuerza el personaje R6 y que los datos visuales sean coherentes (colores, texturas y
animaciones que existen, límites de partículas para móvil, cinemáticas que cubren el impacto).

La simulación es una aproximación: sirve para comprobar la lógica, no sustituye a probar en Studio y en un servidor real.

Calidad del código:

```bash
stylua --check src pruebas       # formato
selene generate-roblox-std       # una sola vez
selene src pruebas               # análisis estático
```

Para tener autocompletado y comprobación de tipos en el editor con [luau-lsp](https://github.com/JohnnyMorganz/luau-lsp),
genera el mapa de fuentes con `rojo sourcemap default.project.json -o sourcemap.json`.
