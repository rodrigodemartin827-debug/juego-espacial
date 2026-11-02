# Juego Espacial

Juego de exploración espacial con PvP para Roblox: dos bandos (Humanos y Monstruos), naves, poderes, escáner y
crafteo. Proyecto de [Rojo](https://rojo.space) escrito en Luau.

Por ahora el repositorio contiene la **base técnica** sobre la que se construirá el juego:

- la estructura del proyecto (`src/server`, `src/client`, `src/shared`),
- un **sistema de red** con RemoteEvents validados en el servidor y límite de peticiones por segundo,
- un **sistema de datos** con DataStore y **bloqueo de sesión** que guarda bando, nivel, XP, monedas, inventario y
  mejoras de la nave,
- un primer servicio de ejemplo (elegir bando) que usa los dos sistemas, con la **pantalla de elección de bando** de la
  primera entrada (planetas, grieta y confirmación con VFX; ver [Elección de bando](#elección-de-bando)),
- el **sistema de combate** (servidor autoritativo, poderes Rayo y Gravedad, combo, VFX por fases, interfaz y una zona de
  pruebas; ver [Combate](#combate)),
- el **sistema de naves** (vuelo en el espacio para PC, móvil y mando, vida y escudo, armas validadas en el servidor,
  campos de asteroides generados por código y mejoras leídas de los datos del jugador; ver [Naves](#naves)),
- la **exploración**: escáner de mano con ficha en pantalla, minerales que se pican a pie y desde la nave, inventario con
  límite según la mejora Carga y crafteo validado en el servidor; ver [Exploración](#exploración), y
- pruebas automáticas que se ejecutan fuera de Studio.

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
│   ├── Juego/Bandos         Humanos, Monstruos y "Ninguno"
│   ├── Eleccion/            Pantalla de elección de bando: datos (escena, textos, efectos) y reglas puras
│   ├── Combate/             Datos y reglas del combate (ver más abajo)
│   ├── Naves/               Datos y reglas puras de las naves (ver Naves)
│   ├── Exploracion/         Escáner, minerales, inventario y crafteo: datos y reglas puras (ver Exploración)
│   ├── Red/
│   │   ├── Remotos          Lista central de RemoteEvents
│   │   ├── Validador        Validadores de argumentos
│   │   └── LimitadorDeTasa  Cubo de fichas (peticiones por segundo)
│   └── Utilidades/          Senal (eventos), Tablas (copia profunda) y Azar (aleatorio con semilla)
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
│       ├── ServicioBandos       Elegir bando (una sola vez) y proteger al jugador mientras elige
│       ├── ServicioCombate      Combate: cooldown, energía, alcance, daño (autoritativo)
│       ├── ServicioNaves/       Naves: despegue, vida y escudo, armas, choques, vigilancia
│       ├── ServicioAsteroides   Campos de asteroides generados por código (con vetas de mineral)
│       ├── ServicioInventario   Inventario del jugador con el límite de su bodega (mejora Carga)
│       ├── ServicioMinado       Minerales: pico a pie y láseres de la nave
│       ├── ServicioEscaner      Escáner de mano: alcance, velocidad, ficha y recompensa
│       ├── ServicioCrafteo      Mesa de crafteo: comprobación y cobro atómicos
│       ├── Hangar               Hangar con plataforma de despegue
│       └── ZonaPruebas          Plataforma con muñecos, hangar, asteroides, minerales, criatura y mesa de crafteo
└── client/                  → StarterPlayer.StarterPlayerScripts.Client (un LocalScript)
    ├── init.client.luau     Arranque del cliente
    ├── Servicios/
    │   ├── ServicioRed      Envía peticiones y escucha avisos
    │   └── ServicioDatos    Copia local (solo lectura) de los datos
    ├── Combate/             Entrada, interfaz (vida, energía, cooldowns), números de daño
    ├── Naves/               Vuelo, cámara, panel de mandos, controles y efectos de las naves
    ├── Exploracion/         Escáner (Q), pico (R), ficha, bodega (I), mesa de crafteo y efectos de escaneo
    ├── Eleccion/            Pantalla de elección de bando: escena 3D, interfaz, bloqueo de controles
    └── VFX/                 Motor de efectos visuales (lo usan el combate y las naves)

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
    -- aquí `bando` ya es "Humanos" o "Monstruos"
end)
ServicioRed.EnviarACliente(jugador, "DatosJugador", datos)

-- cliente
ServicioRed.Enviar("ElegirBando", "Humanos")        -- devuelve false si no pasa la validación o va demasiado deprisa
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

Los identificadores que se guardan (`"Humanos"`, `"Monstruos"`, los ids de objetos y mejoras) no deben cambiarse una vez
publicado el juego. Si hace falta, se hace con una migración: la versión 2 del esquema, por ejemplo, convierte los bandos
antiguos `"Heroes"` y `"Villanos"` en `"Humanos"` y `"Monstruos"`.

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

Al arrancar el servidor se crea (`ZonaPruebas`) una plataforma con tres muñecos de entrenamiento: uno de los **Humanos**,
uno de los **Monstruos** y uno **sin bando**; renacen solos. Dos pedestales (`ProximityPrompt`) permiten elegir bando sin
interfaz: si eliges Humanos, el muñeco Humano ya no recibe tu daño. El bando se elige una sola vez (regla de `ServicioBandos`).
La zona también tiene el hangar y el campo de asteroides de las [Naves](#naves) y un ambiente nocturno con resplandor
(`AMBIENTE_ESPACIAL` en `ZonaPruebas`).

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

## Naves

Una nave se pilota con el cliente del jugador (control inmediato) pero **el servidor es la autoridad** de todo lo que
importa: qué estadísticas tiene, cuándo y hacia dónde puede disparar, a qué daña, cuándo choca y si se mueve de forma
creíble.

### Jugar

En la zona de pruebas hay un **hangar** (a la derecha de los pedestales de bando, en `x = +75, z = +62`) con una nave
posada. Acércate a la consola y usa **Despegar**. El campo de asteroides está al norte (−Z), a unos 300 studs, con una baliza
luminosa en un claro central.

| | Ordenador | Mando | Móvil |
| --- | --- | --- | --- |
| Acelerar / frenar | `W` / `S` | palanca izquierda | joystick (abajo-izquierda) |
| Desplazarse de lado | `A` / `D` | palanca izquierda | joystick |
| Subir / bajar | `Espacio` / `Ctrl` o `C` | `A` / `B` | botones ▲ ▼ |
| Orientar | ratón (se bloquea al centro) | palanca derecha | arrastrar por la mitad derecha |
| Disparar | clic | `R2` | botón DISPARAR |
| Turbo | `Shift` | `L2` | botón TURBO |
| Aterrizar | `F` | `Y` | botón ATERRIZAR |

El panel muestra casco, escudo y turbo, la velocidad, la mira, la bodega, los niveles de mejora y un **radar** (alcance según
el nivel de Escáner; las naves enemigas salen en rojo y las aliadas en verde). Mientras pilotas, el combate a pie queda
pausado: ni el clic ni las teclas lanzan habilidades y el personaje, invisible dentro de la cabina, no puede ser alcanzado
por ellas.

### Las mejoras salen de los datos del jugador

`datos.MejorasNave` (`Casco`, `Escudo`, `Motor`, `Armas`, `Escaner`, `Carga`) se lee **en el servidor al despegar**
(`Naves/Estadisticas.Calcular`, función pura que sanea niveles raros: ausentes, negativos, decimales, `NaN`, por encima del
máximo...). Qué hace cada una, nivel a nivel, está en `Naves/Datos/Mejoras` (`Base + PorNivel × nivel`, nivel máximo 10):

| Mejora | Efecto |
| --- | --- |
| Casco | vida máxima |
| Escudo | capacidad, velocidad de recarga y espera antes de recargar |
| Motor | velocidad máxima, aceleración, potencia y depósito del turbo |
| Armas | daño, cadencia y alcance de los láseres |
| Escáner | alcance del radar de la nave y alcance y velocidad del escáner de mano |
| Carga | capacidad de la bodega: es el límite del inventario (ver [Exploración](#exploración)) |

`ServicioNaves.ActualizarMejoras(jugador)` recalcula las estadísticas de una nave en vuelo cuando cambien las mejoras
(conserva la proporción de vida y escudo).

### Qué decide el servidor

- **Vida y escudo** (`Naves/Reglas`): el escudo absorbe primero y el sobrante pasa al casco; se recarga solo tras unos
  segundos sin daño, calculado "perezosamente" (sin bucles por nave, igual que la energía del combate). Al despegar hay unos
  segundos de inmunidad.
- **Armas** (`ServicioNaves/Armas`): el cliente solo manda la dirección. El servidor comprueba la **cadencia** (la del nivel de
  Armas), **limita la dirección a un cono** alrededor de la proa que él mide (no se dispara hacia atrás), elige el **cañón**
  (alternan) y hace el raycast. El daño llega cuando termina el vuelo del proyectil. Las naves del mismo bando no se hacen daño.
- **Choques con asteroides** (`ServicioNaves/Choques`): cada fotograma, un barrido esférico más una consulta de solape. El
  daño depende de la **velocidad medida por el servidor** y del tamaño de la roca (`Reglas.DanoChoque`). El piloto rebota al
  momento con una predicción local; si no, el servidor se lo ordena.
- **Vigilancia**: cada 0,2 s se comprueba que la nave no vaya más deprisa de lo que permite su motor (con o sin turbo, que
  también gestiona el servidor) ni salga del mundo. Si falla varias veces seguidas se la devuelve a su última posición buena.
  Un tirón de lag legítimo se acepta (el margen crece con el tiempo), un teletransporte no.
- **Remotos** (`Red/Remotos`): `DispararNave`, `TurboNave`, `AterrizarNave` y `PedirEstadoNave`, todos con validación y límite por
  segundo. Las reglas, la física y el generador son funciones puras con pruebas.

### Campos de asteroides

`ServicioAsteroides.CrearCampo({ Semilla, Cantidad, Centro, Radio, Aplanado, TamanoMin, TamanoMax, Separacion, Exclusiones })`
construye un campo por código. El reparto (`Naves/GeneradorAsteroides`) es **determinista por semilla**, con muchos pequeños y
pocos grandes, sin solapes y respetando zonas de exclusión. Cada asteroide es una esfera con fragmentos de roca; tiene vida,
estalla cuando se le dispara y renace pasado un tiempo (si no hay una nave encima).

### Efectos visuales: el mismo motor que el combate

Las naves **no tienen un sistema de efectos propio**: usan el de `client/VFX` con sus mismas capas y fases, a través de
`Gestor.Reproducir(receta, fases, opciones)`. Las recetas están en `Naves/Datos/EfectosNave` (con colores en
`Combate/Datos/Paleta` y sonidos en `Combate/Datos/Recursos`) y se construyen con los mismos atajos (`Combate/Datos/Atajos`):

| Receta | Cuándo |
| --- | --- |
| `Nave_Laser_<Bando>` | cada disparo: fogonazo, proyectil con estela y haz; azul, rojo o verde según el bando |
| `Nave_Impacto_Escudo` / `_Casco` / `_Asteroide` | el láser golpea cada cosa |
| `Nave_Choque_Escudo` / `_Casco` | choque con un asteroide (sacude, tiñe y desenfoca la pantalla del piloto) |
| `Nave_Explosion` | nave destruida: destello, bola de fuego en capas, ondas, chispas, humo, restos, arcos eléctricos y explosiones secundarias escalonadas |
| `Nave_Asteroide_<Tamaño>` | un asteroide estalla, con más fuerza cuanto más grande |
| `Nave_Propulsor` / `_Turbo` / `Nave_Turbo_Arranque` | estela de los propulsores (se repite mientras se acelera) y destello al encender el turbo |
| `Nave_Despegue` | arranque de los motores en el hangar |

Para que el motor sirviera en el espacio se le añadió: dirección 3D en las anclas (`Espacial`), anclas por nombre (los
Attachments `CanonIzq`, `MotorDer`... del modelo), partículas hacia atrás (`Direccion = "Atras"`) y escombros sin suelo
(`Libre = true`). La calidad adaptativa de `VFX/Calidad` se aplica igual: las capas pesadas llevan `Minimo = "Alto"`.

### Modelo 3D

La nave se construye por código (`ServicioNaves/Modelo`): fuselaje, cabina de cristal, alas en flecha con un cañón en cada
punta, dos propulsores y neón del color del bando. No hay assets que subir. Las naves **no colisionan físicamente** con nada
(grupo de colisión propio): los choques los decide el servidor.

### Limitaciones conocidas

- **No he podido probarlo dentro de Roblox Studio** (este entorno no tiene Studio). La lógica pura (estadísticas, reglas,
  física, generador, datos de efectos y cableado de red) está cubierta por pruebas; la parte que usa el motor de Roblox (física
  de la nave, propiedad de red, cámara, interfaz, aspecto de los efectos) se ha revisado con el analizador de tipos de
  `luau-lsp` pero **hay que ajustarla probándola**: sensibilidad, distancias de cámara, tamaños de efectos y la sensación del vuelo.
- La nave de un piloto la simula su cliente: es la forma estándar de que el control sea inmediato, pero implica que el servidor
  no puede impedir cada movimiento, solo detectar y deshacer los imposibles.
- Los sonidos están vacíos (`Recursos.Sonidos`); pega un ID y suenan sin tocar código.

## Exploración

Escáner de mano, minerales, inventario y crafteo. Se apoyan en la red, los datos, las naves y el motor de VFX de arriba, y
siguen la misma regla: **el cliente pide, el servidor decide**.

### Controles

| Tecla | Qué hace |
| --- | --- |
| **Q** (mantener) | escanear lo que miras (mando: L1; móvil: botón *Escanear*) |
| **R** (mantener) | picar el mineral que tienes delante (mando: R1; móvil: botón *Picar*) |
| **I** | abrir o cerrar la bodega (también la pastilla *Bodega* de abajo a la izquierda) |
| **E** en una mesa | abrir el panel de crafteo |
| clic con la nave | los láseres rompen las vetas de mineral de los asteroides |

### Escáner de mano

Apunta a una criatura, una planta o un mineral y mantén Q. El servidor comprueba que sea escaneable (etiqueta `Escaneable` y
atributo `EspecieId`), que esté **al alcance de tu escáner**, que lo veas (raycast) y que sigas cerca mientras dura; y calcula
cuánto tarda con **la velocidad de tu escáner**. La mejora **Escáner** sube `AlcanceEscaner` (40 studs + 9 por nivel) y
`VelocidadEscaner` (×1 + 0,15 por nivel) además del radar de la nave. Al terminar sale la **ficha** (nombre, rareza, datos de la
especie y recompensa); el primer escaneo de cada especie paga la recompensa completa y se anota en `datos.Descubrimientos`,
los siguientes pagan una fracción (`Config.RecompensaRepeticion`).

Los **efectos de escaneo** usan el motor de VFX (`Exploracion/Datos/EfectosExploracion`) con todos los tipos de capa: carga de
energía en la mano, un rayo con núcleo y halo y paquetes de datos que viajan hasta el objetivo, anillos y chispas sobre él, un
contorno pulsante, barridos de luz de abajo arriba, y al terminar un estallido con esferas, anillos, arcos, esquirlas luminosas,
destello, zoom, desenfoque y sacudida (la pantalla solo cambia a quien escanea). Los minerales tienen golpe y rotura con la
paleta de cada uno.

Para que algo sea escaneable desde otro código: `ServicioEscaner.Marcar(instancia, "Criatura_MedusaVacio")`.

### Minerales

Un nodo es un `Model` o `Part` etiquetado `Mineral` con el atributo `MineralTipo` (`ServicioMinado.CrearNodo` construye la roca y
lo registra). Se pica **a pie** (R: el servidor comprueba distancia, cadencia y que quepa el botín) y **desde la nave** (los
láseres que dan en un nodo llaman a `ServicioMinado.PicarDesdeNave`; el botín va al inventario del piloto). Hay nodos en el
suelo (planetas) y, en los campos de asteroides con `ProbabilidadVeta`, vetas pegadas a la roca. Al agotarse el nodo suelta su
botín, se oculta y reaparece a los `Config.SegundosRenacerMineral`. Con la bodega llena no se rompe nada (se avisa y el mineral
queda como estaba).

### Inventario

`datos.Inventario` guarda `{ idObjeto = cantidad }`. Cada objeto ocupa su `Volumen` (`Exploracion/Datos/Objetos`) y la bodega
tiene el espacio de la mejora **Carga** (`Capacidad`: 20 + 10 por nivel). Solo se cambia por `ServicioInventario`
(`Anadir`/`Quitar`), que aplica `Exploracion/Inventario` (funciones puras) y rechaza cantidades inválidas.

### Crafteo

La mesa de crafteo (`ServicioCrafteo.CrearMesa`) abre un panel con las recetas. El cliente solo envía `FabricarReceta(id, cantidad)`;
el servidor comprueba que estés **junto a una mesa**, a pie, y evalúa con `Exploracion/Crafteo.Planificar` (materiales, monedas,
nivel máximo de la mejora y espacio en la bodega); si todo es válido, **cobra y entrega en el mismo instante** (`Aplicar`, sin
esperas entre medias, así no se puede duplicar nada pidiendo dos veces a la vez), reenvía los datos, recalcula la nave si subió
una mejora y guarda.

### Cambiar cosas sin tocar código

Todo está en módulos de datos:

| Quiero... | Edito |
| --- | --- |
| añadir o equilibrar una **receta** (objeto o mejora de la nave) | `Exploracion/Datos/Recetas` |
| añadir un **objeto** (espacio que ocupa, nombre, color) | `Exploracion/Datos/Objetos` |
| añadir un **mineral** (vida, botín, dónde aparece, color) | `Exploracion/Datos/Minerales` (+ un objeto, y su paleta `Mineral_<id>` en `Combate/Datos/Paleta`) |
| añadir una **criatura o planta** escaneable y su ficha | `Exploracion/Datos/Especies` |
| cambiar los **efectos** de escaneo y minería | `Exploracion/Datos/EfectosExploracion` |
| cambiar alcances, cadencias, daño del pico, tiempos | `Exploracion/Config` |
| cambiar lo que da cada nivel de Escáner o de Carga | `Naves/Datos/Mejoras` |

Una receta de mejora cuesta `Base + PorNivel × nivelActual` de cada ingrediente (redondeado hacia arriba). Ejemplo:

```lua
MejoraCasco = {
    Nombre = "Casco reforzado",
    Categoria = "Mejora",
    Ingredientes = { PlacaTitanio = { Base = 1, PorNivel = 1 }, LingoteHierro = { Base = 2, PorNivel = 1 } },
    Monedas = { Base = 40, PorNivel = 20 },
    Resultado = { Mejora = "Casco" },
},
```

Los ids válidos de `FabricarReceta` salen de `Recetas.Orden`, así que una receta nueva no exige tocar la red. Las pruebas
comprueban que toda receta use objetos y mejoras que existen, que cada ingrediente se pueda conseguir y que haya una receta por
cada mejora de la nave.

### Zona de pruebas

`ZonaPruebas` crea, a la izquierda del punto de aparición, un corro de **rocas minables** (hierro, cobre y cristal), una
**medusa del vacío** flotante y dos plantas luminosas **escaneables**, y una **mesa de crafteo**. En el campo de asteroides, un
tercio de las rocas lleva una veta (incluido titanio) que se pica con los láseres de la nave. Para fabricar mejoras hace
falta recolectar y refinar materiales; las monedas se ganan escaneando.

### Limitaciones conocidas

- **No se ha podido probar dentro de Roblox Studio** (el entorno de desarrollo no lo tiene). La lógica pura (inventario, escáner,
  crafteo, catálogos y datos de efectos), el cableado de red y las reglas de seguridad del servidor están cubiertas por
  pruebas; la parte que usa el motor (interfaz, cámara, aspecto de los efectos, sensación de la puntería) **hay que ajustarla
  probándola**: tamaños de la interfaz, distancia de los efectos, tiempos y cantidades de partículas.
- Los sonidos están vacíos (`Recursos.Sonidos`); pega un ID y suenan sin tocar código.
- El pico no tiene animación propia ni herramienta en la mano; los golpes se ven por los efectos del mineral.
- El XP se acumula pero todavía no hay sistema de niveles del jugador (el pico mejora con `datos.Nivel` cuando exista).

## Elección de bando

La **primera vez** que un jugador entra (su bando guardado es `Ninguno`), en lugar del juego ve la pantalla de elección:
cámara fija, sin poder moverse ni girar la cámara y sin la interfaz del juego. A la izquierda, el planeta de los
**Humanos** (océanos, continentes, nubes y su sol) con un explorador; en medio, la **grieta** (una rasgadura animada con
bordes de energía, vacío negro, ramas, motas y chispazos); a la derecha, el planeta de los **Monstruos** (roca negra, venas de
lava, niebla púrpura y un agujero negro por sol) con una silueta de brazos larguísimos que da tirones con la cabeza.

- **Ratón**: al pasar por una mitad, ese lado se resalta (el planeta crece y se ilumina, la cámara gira un poco hacia él,
  la grieta le lanza un rayo y se despliega su panel con sus ventajas). Un clic lo elige.
- **Táctil**: los dos paneles se ven siempre; tocar una mitad la resalta y soltar el dedo sobre ella la elige.
- **Teclado / mando**: ◀ ▶ (o A / D) para resaltar, Intro / Ⓐ para elegir.

Al elegir, el planeta "toma aire" mientras responde el servidor (anticipación); cuando confirma, la escena se congela un
instante y estalla la confirmación (`Eleccion_Confirmar_<Bando>`: destellos, ondas, rayos desde la grieta, destello de
pantalla, temblor y zoom), el otro lado se apaga, la cámara se acerca al planeta elegido y todo se funde a negro para volver
al juego. Quien ya tiene bando no ve nada de esto (solo un fundido de entrada).

**Qué hace el servidor** (`ServicioBandos`): solo acepta `Humanos` o `Monstruos`, solo si el bando guardado es `Ninguno`, y
guarda en el acto. Mientras el jugador elige, su personaje queda **anclado** y con un `ForceField` invisible, y el `Player`
lleva el atributo `EligiendoBando`: el combate no le deja usar habilidades ni le toma como objetivo. Al elegir se quita todo
y se dispara `ServicioBandos.BandoElegido` (jugador, bando); en el cliente, `ServicioEleccion.Terminada` (bando) cuando ya ha
vuelto al juego. Ahí se enganchará el tutorial.

**Cambiar cosas sin tocar código**: `shared/Eleccion/Config` (posiciones y tamaños de los planetas, continentes, nubes, sol,
agujero negro, grieta y figuras R6, cámara y encuadre, tiempos de cada fase), `shared/Eleccion/Datos/Textos` (todo lo que se
lee) y `shared/Eleccion/Datos/EfectosEleccion` (recetas de VFX; colores en `Combate/Datos/Paleta`, sonidos en
`Combate/Datos/Recursos`, de momento vacíos). La escena se monta solo en el cliente que elige, lejos del mapa
(`Config.Camara.Origen`), y el campo de visión se ajusta a la proporción de la pantalla para que los dos planetas quepan
siempre a lo ancho (`Eleccion/Encuadre`).

**Probarla en Studio**: con el almacén en memoria (lugar sin publicar), cada partida empieza sin bando, así que la pantalla
sale siempre. Con DataStore real, hay que borrar el registro `Jugador_<UserId>` del almacén `DatosJugador_Studio`.

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
animaciones que existen, límites de partículas para móvil, cinemáticas que cubren el impacto). Para las naves comprueban
las estadísticas por mejora (incluidos datos corruptos), el escudo y el daño, la cadencia y el cono de disparo, el turbo, la
vigilancia del movimiento, la física del vuelo, el generador de asteroides (determinismo, sin solapes, exclusiones), los datos
de los efectos y que cada remoto de naves esté declarado, bien dirigido, usado por los dos lados y validado. El servidor y el
cliente de las naves usan la API 3D de Roblox, que la simulación no tiene, así que en las pruebas de integración se
sustituyen por módulos vacíos (como ya se hace con `ZonaPruebas`). Para la exploración comprueban los catálogos y las recetas
(todo ingrediente se puede conseguir, hay una receta por mejora), el inventario con límite, la elección del objetivo del
escáner, la recompensa, el crafteo (materiales, monedas, nivel máximo, bodega llena, plan que ya no vale), los datos de los
efectos (calidad máxima del escaneo) y el cableado de red y las reglas de seguridad de los servicios. Para la elección de
bando comprueban cuándo se muestra la pantalla, que solo se pide una vez y que manda el servidor (flujo), que los dos planetas
quepan en cualquier pantalla (encuadre), la forma de la grieta, los textos y las recetas de efectos, y en el servidor la
validación, la protección del personaje mientras elige y que no se pueda elegir dos veces.

La simulación es una aproximación: sirve para comprobar la lógica, no sustituye a probar en Studio y en un servidor real.

Calidad del código:

```bash
stylua --check src pruebas       # formato
selene generate-roblox-std       # una sola vez
selene src pruebas               # análisis estático
```

Para tener autocompletado y comprobación de tipos en el editor con [luau-lsp](https://github.com/JohnnyMorganz/luau-lsp),
genera el mapa de fuentes con `rojo sourcemap default.project.json -o sourcemap.json`.
