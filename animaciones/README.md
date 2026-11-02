# Animaciones

Animaciones para el rig **R6** de Roblox, creadas con Blender en modo sin pantalla (`bpy`) y exportadas a `.fbx`.
El juego entero es R6 (ver el README principal): no hay animaciones para R15.

| Archivo | Qué es |
| --- | --- |
| `punetazo_fuerte_anime.fbx` | Rig R6 + cuerpo de cajas + animación. Sirve para previsualizar en Blender u otro programa. |
| `punetazo_fuerte_anime_solo_huesos.fbx` | **El que se importa en Studio**: solo los 7 huesos R6 con la animación. |
| `punetazo_fuerte_anime.blend` | Escena de Blender con la animación ya horneada, para retocarla a mano. |
| `punetazo_fuerte_anime_hoja_de_contactos.png` | Hoja final (ronda 3): fotogramas clave desde frente, lateral y 3/4. |
| `rondas/` | Las hojas de contactos de las rondas anteriores (borrador, 1 y 2), a media resolución. |
| `herramientas/` | Los scripts que lo generan todo (ver más abajo). |

## El rig R6

Los huesos llevan los nombres de las piezas de Roblox, porque el importador de animaciones empareja por nombre:

```
HumanoidRootPart
└── Torso
    ├── Head
    ├── Right Arm      (con espacio, tal cual se llama la pieza en Roblox)
    ├── Left Arm
    ├── Right Leg
    └── Left Leg
```

Diferencias con R15 que condicionan la animación:

- **No hay codos, rodillas ni manos**: cada brazo y cada pierna es una pieza rígida. El movimiento sale del giro, la
  inclinación y el desplazamiento del **torso entero**, de la dirección a la que apunta el brazo y de la posición de las piernas.
- **Las piernas cuelgan del `Torso`** (no de la cadera como en R15), así que giran con él. Para que los pies queden
  plantados la animación calcula, en cada fotograma, la **altura del torso** y apunta la pierna de apoyo a su pie.
- Los huesos están en el **pivote de cada Motor6D** de Roblox (cuello, hombros y caderas), no en el centro de las piezas:
  si no coinciden, el movimiento en Studio no sería el de Blender.

## Animación: puñetazo fuerte estilo anime

40 fotogramas a 30 fps (1,33 s). Brazo derecho, sin bucle. Prioridad recomendada: **Action**.

| Fotogramas | Fase |
| --- | --- |
| 0 | Guardia (cuerpo de lado, brazo izquierdo adelantado) |
| 0–10 | **Anticipación**: el torso se enrosca hacia la derecha (unos −70° más que la guardia) y se agacha; el puño se carga detrás y la mano izquierda apunta al blanco |
| 10–12 | Tensión: casi quieto |
| 12–16 | **Golpe**: el torso gira primero (12–14) y el puño llega después (13–16), dibujando un arco. Son 3 fotogramas (0,1 s) de puño en el aire |
| 16–22 | **Impacto exagerado** y mantenido: cuerpo lanzado hacia delante e inclinado, brazo recto, el otro brazo recogido atrás y la pierna trasera estirada de puntillas |
| 22–40 | Recuperación hasta la guardia |

El fotograma del **impacto es el 16** (0,53 s), que es el `Tiempos.Carga` del Remate. Todas las curvas llevan easing
(suave, entrada, salida, "golpe" explosivo y "rebote" con sobrepaso); no hay tramos lineales. Como Roblox no importa
curvas Bézier, el `.fbx` lleva **una clave por fotograma** con el easing ya aplicado.

Mediciones del script: la pierna de apoyo llega al suelo con un error máximo de **0,02 studs** (no patina ni se hunde) y
el puño llega al saco de los renders en el fotograma 16. La pierna trasera es libre: R6 no tiene rodilla, así que en el
impacto queda estirada hacia atrás y no toca el suelo (a propósito: es la "patada atrás" de un golpe a lo anime).

### Las rondas de mejora

El proceso fue: renderizar la hoja de contactos (3 cámaras × 10 fotogramas), mirarla, anotar qué falla y corregirlo en
`punetazo_fuerte.py`. Se hicieron tres rondas sobre el borrador:

| Hoja | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| `rondas/ronda_0_borrador.png` | Con el pie adelantado dando un paso mientras el torso avanza, en el fotograma 14 el cuerpo se hunde hasta el suelo | — (es el punto de partida) |
| `rondas/ronda_1.png` | Secuencia legible, pero el impacto es tímido: el cuerpo apenas se inclina | El pie adelantado queda plantado todo el golpe (las piernas rígidas no admiten otra cosa sin hundir el cuerpo) |
| `rondas/ronda_2.png` | Impacto con más fuerza, pero la pierna trasera tenía un objetivo imposible (1,16 studs de error) y el cuerpo se pasaba de largo | Más inclinación (30°), más enroscado en la anticipación (−90°), brazo izquierdo recogido atrás, el golpe pasa a llevar más avance |
| `punetazo_fuerte_anime_hoja_de_contactos.png` (ronda 3) | Funciona: guardia, enroscado, golpe, impacto y recuperación se leen en las tres cámaras | Pierna trasera con un objetivo alcanzable (de puntillas hacia atrás), menos avance del torso y un pequeño rebote tras el impacto (fotograma 18) |

## Importar en Roblox Studio

1. Abre el lugar y añade un maniquí R6: pestaña **Avatar → Rig Builder → R6 → Block Rig**.
2. Selecciona el rig y abre el **Animation Editor** (pestaña **Avatar → Animation Editor**, o *Plugins*). Pulsa **Create**
   y dale un nombre, p. ej. `PunetazoFuerte`.
3. En el menú **⋮** de la ventana del editor elige **Import → From FBX** (*Import From FBX*) y selecciona
   `punetazo_fuerte_anime_solo_huesos.fbx`. Roblox empareja los huesos con las partes del rig por su nombre
   (`Torso`, `Right Arm`...), por eso no hay que cambiar nada.
4. Dale a ▶ para ver el resultado, deja **Looping** desactivado y en **⋮ → Set Animation Priority** elige **Action**.
5. **⋮ → Save** y después **⋮ → Publish to Roblox**. La animación se publica a nombre del mismo creador (tu usuario o
   el grupo) que es dueño del juego: si no, otros jugadores no podrán reproducirla.
6. Al publicar, Studio te da el **ID** (también sale en la ventana *Output*). Solo necesitas el número.

## Poner el ID: es el **Remate** del combo (`Combo4`)

El combate ya tiene su sitio para los IDs: `src/shared/Combate/Datos/Recursos.luau`, tabla `Recursos.Animaciones`
(ver el README principal, sección del combate). El puñetazo fuerte es la animación del cuarto golpe del combo, así que
su ID se pega en `Combo4`:

```lua
Recursos.Animaciones = {
	...
	Combo4 = "rbxassetid://1234567890", -- el ID que te dio Studio, con el prefijo rbxassetid://
}
```

No hay que tocar nada más: mientras `Combo4` valga `""` se usa la animación provisional hecha por código, y con un ID
el cliente (`VFX/Animador`) carga esa en su lugar, igual que con el resto de animaciones. La provisional (`Combo4` en
`Datos/Animaciones.luau`) sigue las mismas fases y poses que esta.

**Sincronización con el golpe.** El impacto de este puñetazo cae en el fotograma 16 (0,53 s), así que el Remate
(`Combo4` en `Datos/Poderes`) tiene `Tiempos.Carga = 0.53`: el servidor aplica el daño y el cliente lanza el efecto de
impacto justo cuando el puño llega. Si cambias el ritmo de la animación, cambia `Carga` a la vez.

## Si algo sale mal en Studio

No he podido probar la importación en Studio desde este entorno (sin Studio), sino que he comprobado el `.fbx` volviéndolo
a importar en Blender (`herramientas/verificar_fbx.py`). Si al probarlo ves algo raro:

- **El personaje sale mirando hacia atrás o el golpe va en sentido contrario**: en `herramientas/exportar_fbx.py` cambia
  `axis_forward="Z"` por `"-Z"` y vuelve a generar.
- **El torso se desplaza demasiado o muy poco**: el avance del cuerpo se anima en la traslación del hueso `Torso` (en
  studs de Blender: 1 stud = 0,28 m). Se puede suavizar en `TORSO_POS` de `herramientas/punetazo_fuerte.py`.
- **Los brazos o las piernas giran alrededor de un punto raro**: los pivotes de los huesos deben coincidir con los
  Motor6D de tu rig. Los de `rig_r6.py` son los del R6 estándar (Rig Builder); si usas un R6 con las articulaciones
  movidas, ajusta `ARTICULACIONES`.
- **Sale un hueso de más o una pieza suelta**: importa el `solo_huesos`, que no lleva mallas, y no el de rig + cuerpo.

## Regenerar las animaciones

Requiere Python 3.13 (el de `bpy` 5.2) y las bibliotecas de `herramientas/requirements.txt`:

```bash
python3 -m venv .venv && .venv/bin/pip install -r animaciones/herramientas/requirements.txt
```

```bash
.venv/bin/python animaciones/herramientas/generar.py \
  --hoja animaciones/punetazo_fuerte_anime_hoja_de_contactos.png \
  --fbx animaciones/punetazo_fuerte_anime.fbx \
  --fbx-huesos animaciones/punetazo_fuerte_anime_solo_huesos.fbx \
  --blend animaciones/punetazo_fuerte_anime.blend
```

```bash
.venv/bin/python animaciones/herramientas/verificar_fbx.py animaciones/punetazo_fuerte_anime_solo_huesos.fbx
```

| Script | Para qué sirve |
| --- | --- |
| `rig_r6.py` | Crea los 7 huesos R6 (en el pivote de cada Motor6D, orientados con los ejes del mundo) y el cuerpo de cajas |
| `punetazo_fuerte.py` | Las claves y curvas de la animación, la altura del torso, la orientación de brazos y piernas y el horneado. **Aquí se retoca el movimiento** |
| `hoja_contactos.py` | Render con Cycles (CPU) y montaje de la hoja de contactos |
| `exportar_fbx.py` | Exportación FBX con los ajustes para Roblox |
| `verificar_fbx.py` | Reimporta el FBX y comprueba huesos, jerarquía, duración y posiciones |
| `generar.py` | Lo ejecuta todo |

## Andar de los monstruos

Los jugadores del bando **Monstruos** se mueven con animaciones propias: reposo, andar, correr, saltar y caer.
Estilo creepypasta original: encorvado, la cabeza ladeada y **clavada al frente** mientras el cuerpo se sacude, con
tirones secos; los brazos cuelgan como peso muerto, cada uno a su ritmo; al andar cojea arrastrando la pierna
izquierda con la punta rozando el suelo, y corre a zancadas desiguales, muy agachado, con espasmos.

| Archivo | Qué es |
| --- | --- |
| `andar_monstruo/hoja_<estado>.png` | Hoja de contactos: momentos clave desde frente, lateral y 3/4. El personaje avanza a la velocidad de referencia sobre un suelo de casillas de 1 stud: un pie bien plantado se queda en su casilla |
| `andar_monstruo/bucle_<estado>.gif` | La animación en bucle (vista 3/4), para ver el ritmo y los tirones sin Studio |
| `andar_monstruo/monstruo_<estado>_solo_huesos.fbx` | Para importar en el Animation Editor si se quiere subir como asset (opcional, ver abajo) |

**La fuente de verdad es el código**, no Blender: las curvas están en
`src/shared/Personajes/Datos/AnimacionesMonstruo.luau` y el juego las convierte en `KeyframeSequence` al arrancar
(`Animacion/Horneado` → `VFX/Animador`). Las hojas, los GIF y los FBX se generan **a partir de esos mismos datos**, así
que enseñan exactamente lo que se verá en el juego. Al tocar las curvas, regenera las hojas para revisarlas.

### Cómo se mide que los pies no patinen

R6 no tiene rodillas: las piernas son bloques rígidos que cuelgan del `Torso`. Por eso:

- La **altura del cuerpo se calcula en cada cuadro** (`AlturaAutomatica`) para que el pie más bajo toque el suelo: ni
  flota ni se hunde.
- Las piernas, los brazos y la cabeza se escriben **respecto al mundo** (`Mundo = true`): una pierna a 0° está
  vertical aunque el torso vaya inclinado 40°.
- El pie que pisa se mueve con tramos **lineales**, así va hacia atrás a velocidad constante.
- El ladeo del torso sube una cadera y baja la otra (2·sen(ladeo) studs): se usa para que la pierna que avanza no roce.
- `pruebas/infraestructura/Pisada.luau` mide la velocidad natural de los pies con la cinemática R6 y la prueba
  `AndarMonstruo` exige que `VelocidadReferencia` esté a menos de un 10 % de ella. El cliente reproduce la animación a
  `velocidad real / VelocidadReferencia` para que no patinen a ninguna velocidad (dentro de `RitmoMinimo..RitmoMaximo`).

| Animación | Ciclo | Velocidad de referencia | Patinaje medio | En el aire |
| --- | --- | --- | --- | --- |
| Andar | 0,9 s | 4,2 studs/s (pies: 4,26) | 19 % | 0 % |
| Correr | 0,56 s | 13 studs/s (pies: 13,4) | 12 % | 22 % |

A la velocidad normal de un jugador (16 studs/s) el monstruo **corre** (a 1,23×). Anda por debajo de 8 studs/s (joystick
a medias en móvil). En reposo los pies quedan a ≤ 0,1 studs del suelo en todo el ciclo.

### Regenerar

```bash
lune run animaciones/herramientas/exportar_monstruo.luau /tmp/monstruo.json
.venv/bin/python animaciones/herramientas/andar_monstruo.py --json /tmp/monstruo.json \
  --hojas animaciones/andar_monstruo/hoja --gifs animaciones/andar_monstruo/bucle --fbx-dir animaciones/andar_monstruo
.venv/bin/python animaciones/herramientas/verificar_fbx_monstruo.py --json /tmp/monstruo.json --fbx-dir animaciones/andar_monstruo
```

Con `--solo Andar` se genera solo una. Tarda unos 3 minutos en total (Cycles en CPU).

### Subirlas como asset (opcional)

No hace falta: funcionan registradas por código. Pero si se suben, se ahorra el registro y la animación viaja por la
red como cualquier otra. Para cada `monstruo_<estado>_solo_huesos.fbx`: Rig Builder → R6 → Animation Editor →
Import From FBX → **Looping activado** (todas menos Saltar) → prioridad **Movement** → Publish. Pega el ID en
`src/shared/Combate/Datos/Recursos.luau`, en `Monstruo_Reposo`, `Monstruo_Andar`, `Monstruo_Correr`,
`Monstruo_Saltar` o `Monstruo_Caer`.

### Lista de comprobación en Studio

**Poner a un jugador como Monstruo.** Play. En la zona de pruebas, usa el pedestal rojo "Unirse a Monstruos" (solo
funciona si el jugador aún no tiene bando). Para un jugador que ya es Humano, desde la barra de comandos del servidor:

```lua
local S = game.ServerScriptService.Server.Servicios
local j = game.Players:GetPlayers()[1]
require(S.ServicioDatos).ObtenerDatos(j).Bando = "Monstruos"
require(S.ServicioBandos).Publicar(j)
```

Comprueba `j:GetAttribute("Bando") == "Monstruos"` en el servidor y en el cliente. El **Muñeco Monstruo** de la zona de
pruebas también lleva el reposo de monstruo (sirve de referencia quieta).

1. **Quieto**: encorvado y con la cabeza ladeada; a los ~1,6 s la cabeza da un latigazo al otro lado y los hombros se
   encogen; a los ~3,6 s, tres tics de cabeza y una sacudida del brazo izquierdo. Los pies no flotan ni se hunden.
2. **Andar** (joystick a medias, o `Humanoid.WalkSpeed = 6` desde la consola): cojera, la pierna izquierda se
   arrastra rozando el suelo, el cuerpo se desploma hacia ella y la cabeza da un tirón por ciclo. Mira los pies contra
   el suelo: no deben deslizarse de forma llamativa.
3. **Correr** (velocidad normal, 16): muy agachado, zancadas desiguales, espasmo hacia el lado izquierdo, brazo izquierdo
   arrastrado atrás. Ritmo frenético pero los pies sin patinar mucho.
4. **Saltar y caer**: se encoge y se estira con los brazos abiertos atrás; al caer, brazos arriba como una marioneta.
   Al aterrizar vuelve enseguida a andar o correr.
5. **Combate encima**: con el monstruo, lanza el combo (y algún poder) quieto y corriendo: el golpe debe verse entero,
   y al terminar vuelve el andar de monstruo.
6. **Otros casos**: siéntate en un asiento (debe verse la animación normal de sentarse), muere y reaparece (el andar de
   monstruo vuelve solo), cambia el bando a Humanos con el comando de arriba (vuelve el andar normal sin reaparecer).
7. **Dos jugadores** (Test → Clients and Servers → 2 jugadores): uno Monstruo y otro Humano. Desde el cliente del
   Humano, el Monstruo debe verse quieto, andando, corriendo y saltando con sus animaciones, **sin temblores ni mezclas
   con el andar normal**. Y el Humano debe verse normal desde los dos clientes.
8. Consola sin avisos de `[Animador]`. Para depurar, en la consola del cliente:
   `require(game.Players.LocalPlayer.PlayerScripts.Client.Personajes.AndarMonstruo).Seguidos()` lista los personajes
   con el andar de monstruo.

**Qué mirar especialmente** (no se ha podido comprobar sin Studio):

- Que el andar normal no se mezcle con el del monstruo (si se viera "a medias", el Animate usa una prioridad igual o
  mayor que Movement: súbela en `AnimacionesMonstruo`, campo `Prioridad`).
- En dos jugadores, que no haya parpadeos: cada cliente para la copia replicada que le llega del dueño del personaje y
  reproduce la suya. Si se viera doble o con saltos, avísame con una captura.
- Que la dirección del personaje cuadre: en Studio la cabeza va adelantada y las piernas pisan delante del cuerpo
  (como en la vista lateral de las hojas).

## Por qué no se usó un modelo de IA

Se intentó generar la base con un modelo de texto a movimiento y no fue posible en este entorno:

- **HY-Motion 1.0** (Tencent): los pesos están en Hugging Face, pero piden **24–26 GB de VRAM** (no hay GPU), el código
  de inferencia está en GitHub (bloqueado en el entorno) y además necesita Qwen3 y modelos corporales SMPL. Su licencia
  tampoco cubre la UE, el Reino Unido ni Corea del Sur.
- **MoMask** y **MDM**: repositorios en GitHub bloqueados y pesos en Hugging Face con acceso denegado.

Por eso el movimiento está escrito a mano en código (poses clave con easing y cinemática sencilla), no generado por IA.
