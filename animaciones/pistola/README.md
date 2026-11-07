# Animaciones de la pistola de portales (R6)

Apuntar en bucle y disparar, para las dos pistolas (`modelos/pistola_portales/`): la **normal** (de chatarra) y la **VIP**.
Mismo formato que las animaciones de movimiento de la #17 (`animaciones/movimiento/`): cada una en `.rbxmx`
(`KeyframeSequence`, para meterla en Studio sin importador), `_solo_huesos.fbx` (importador del Animation Editor), `.fbx`
con el cuerpo de cajas, `.blend`, hoja de contactos y GIF. **60 fps** (el disparo dura 0,67 s y el retroceso llega al
máximo en un solo fotograma: a 30 fps se comería el golpe).

> **Nada se ha probado en Studio** (esta sesión no tiene Studio). Se ha comprobado lo mismo que en la #17: los FBX
> reimportados en Blender coinciden con la animación (0,0000 studs) y los RBXMX se releen y se reproducen con
> `Part1 = Part0 * C0 * Transform * C1:Inverse()` (0,00000 studs).

## Qué hay

| Archivo | Qué es | Dura | Prioridad |
| --- | --- | --- | --- |
| `apuntar_chatarra`, `apuntar_vip` | Apuntar en bucle: **solo mueve el brazo derecho** | 2 s (120 f), `Loop = true` | `Action` |
| `disparo_chatarra`, `disparo_vip` | El disparo entero: carga, retroceso, medio paso atrás y vuelta a apuntar | 0,67 s (40 f) | `Action2` |
| `disparo_chatarra_movil`, `disparo_vip_movil` | El mismo disparo **de cintura para arriba** (solo `.rbxmx` y `_solo_huesos.fbx`) | 0,67 s | `Action2` |
| `datos/piezas_chatarra.json`, `piezas_vip.json` | Curvas de las piezas de la pistola (rueda, depósito, anillos, núcleo) por fotograma | | |
| `hoja_disparo_4.png`, `hoja_apuntar_4.png` | Hojas de contactos: la normal y la VIP, de lado y en 3/4 | | |
| `*.gif` | Los bucles y los disparos moviéndose (lateral + 3/4) | | |
| `rondas/` | Hojas de las rondas de mejora | | |
| `herramientas/` | Los scripts que lo generan | | |

## Cómo se mezcla con reposo, andar y correr

El brazo derecho se anima **en el sistema del torso**, no del mundo, así que se mezcla con cualquier movimiento de debajo.
Los `.rbxmx` llevan **peso por articulación** (`Pose.Weight`): con peso 0 la articulación no es de esta animación y se queda
lo que ponga la de debajo.

| Animación | Torso | Cabeza | Brazo dcho. | Brazo izdo. | Piernas |
| --- | --- | --- | --- | --- | --- |
| `apuntar_*` | 0 | 0 | **1** | 0 | 0 |
| `disparo_*` | 1 | 1 | 1 | 1 | 1 |
| `disparo_*_movil` | **0,6** | 0,8 | 1 | 1 | 0 |

- **Parado**: `apuntar` en bucle mientras se apunta, y al disparar, `disparo_<p>` encima (da el medio paso atrás).
- **Andando o corriendo**: `apuntar` sigue (solo el brazo); al disparar se usa `disparo_<p>_movil`, que no toca las
  piernas y mueve el torso solo un 30 % (las piernas cuelgan del torso y se irían con él). Con el torso a peso 0,6 se mezcla
  con el balanceo del andar.
- Las animaciones de debajo (la #17): `Idle` 0, `Movement` 1; estas: `Action` 2 y `Action2` 3. Entrada y salida con un
  fundido de 0,05–0,1 s (`pista:Play(0.08)` y `pista:Stop(0.1)`).
- `apuntar` empieza y acaba exactamente en la pose en que acaba el disparo, así que el empalme no salta.

## Marcadores (`KeyframeMarker`)

| Marcador | Fotograma | Tiempo |
| --- | --- | --- |
| `Carga` | 0 | 0 s |
| `Disparo` | 9 | 0,15 s (el momento de soltar: fogonazo, proyectil, sonido, temblor de cámara) |
| `RetrocesoMax` | 12 | 0,20 s |

`pista:GetMarkerReachedSignal("Disparo")`. Las fases y los efectos están en `modelos/pistola_portales/vfx_portal.md`.

## El disparo, fotograma a fotograma

| Fotogramas | Fase | Qué pasa |
| --- | --- | --- |
| 0–9 | **Carga (0,15 s)** | El brazo se tensa y la pistola baja (13° la chatarra, 6° la VIP), el torso se inclina hacia delante, el brazo izquierdo se estira como contrapeso. La chatarra **tiembla** (17 y 11 Hz) cada vez más |
| 9 | **Suelta** | Marcador `Disparo` |
| 9–12 | **Retroceso** | El brazo sube **de golpe** (llega al 87 % en un fotograma): 30° la chatarra, 20° la VIP, más lo que sube el torso al echarse atrás. El torso se echa hacia atrás (−17° / −11°), gira (−28° / −8°) y retrocede 0,66 / 0,42 studs. La cabeza salta hacia atrás. El pie trasero se levanta |
| 12–14 | **Hitstop** | Se mantiene el máximo 2 fotogramas (la VIP, 1) |
| 14–38 (32) | **Recuperación** | Vuelve a apuntar, rápido y suave (`sale`). El pie trasero **planta medio paso atrás** (0,62 / 0,40 studs) y vuelve |
| hasta 40 | Quieto | Idéntico al fotograma 0: la pose de apuntar |

Normal (chatarra): más tirón y **menos estable**: el brazo se ladea 24° (la pistola se tuerce), el cuerpo da un bandazo
de 0,14 studs a un lado y todo **se bambolea** (7 Hz, se apaga con `e^(-t/9)`) un momento después. VIP: retroceso fuerte
pero **controlado**: sin ladeo, sin bandazo, sin temblor ni bamboleo y recupera 6 fotogramas antes.

La cámara (temblor) y el hitstop del cliente **no** van en la animación: ver `vfx_portal.md`.

### Apuntar (bucle de 2 s)

Un seno de cada tipo con ciclos enteros (cierra sin salto). **Normal**: respira 1,3° y 0,8°, tiembla 0,55° a 9 ciclos por
bucle, se va 1,6° arriba y abajo y 1,2° de lado. **VIP**: respira 0,35° y nada más.

## Los pies no patinan ni se hunden

Mismo modelo de bota (talón, planta, punta) y mismos pies que el **reposo** de la #17, así que la pose de partida encaja con
él. El pie izquierdo se queda clavado; el derecho da el paso con un levantamiento calculado para que la bota no roce el
suelo. Mediciones (en studs; `generar_pistola.py` falla si se pasan):

| | Hundido (máx.) | Pie izquierdo patina | Pie derecho patina (apoyado) |
| --- | --- | --- | --- |
| Normal | 0,000 | 0,003 | 0,012 |
| VIP | 0,000 | 0,004 | 0,007 |

## Las piezas de la pistola

Todo lo que se mueve en la pistola **ya es una malla suelta** con su punto, para animarlo en Roblox
(`modelos/pistola_portales/README.md` y `vfx_portal.md`): la rueda y el marco del depósito de la normal, los tres anillos y
el núcleo de la VIP. Las curvas por fotograma están en `datos/piezas_*.json` y se leen con `pista.TimePosition * 60`:

- **Normal**: `rueda` (grados), `deposito` (studs hacia arriba), `chispas` (0, 0,35 o 1).
- **VIP**: `anillos` (grados de cada uno), `nucleo_escala` (factor), `nucleo_blanco` (0 a 1).

En las hojas se ven el fogonazo, el proyectil y las chispas de la bobina (rayitas), y el destello del núcleo; en el juego se
sacan de los emisores del `vfx_portal.md`.

## Meterlas en Roblox Studio

Igual que en la #17 (`animaciones/movimiento/README.md`):

1. Rig R6 (Rig Builder → R6 → Block Rig); dentro, un `Model` llamado `AnimSaves`.
2. Arrastra el `.rbxmx` a Studio: aparece la `KeyframeSequence` (ya con `Loop`, la prioridad, los pesos y los marcadores).
   Mételo en `AnimSaves`, ábrelo en el **Animation Editor** (⋮ → Load) y **Publish to Roblox** (a nombre del dueño del juego).
3. Con el ID, la Tool reproduce `apuntar_*` al equiparla y `disparo_*` (o `_movil`) al disparar.
4. Si quieres usar el FBX, ojo: el importador de FBX **no** conserva los pesos ni los marcadores. Para `apuntar` y `_movil`
   usa el `.rbxmx`.

Si algo sale mal:

- **El brazo apunta hacia atrás o a un lado**: la conversión está en `animaciones/movimiento/herramientas/rbxmx.py`
  (`MOTORES`). Es la de la #17 (comprobada con el R6 estándar).
- **La pistola no cae en la mano**: es `Tool.Grip` (lo pone `montar_*.luau`). El brazo termina en el centro de su cara
  inferior y el `Agarre` va ahí (`RightGripAttachment`).
- **El peso no mezcla** (el torso o las piernas se quedan quietos al reproducir `apuntar`): comprueba en el Animation Editor
  que solo `Right Arm` tiene clave y que las demás tienen `Weight 0`.

## Regenerar

Requiere Python 3.13 con `bpy` 5.2 y Pillow (`animaciones/herramientas/requirements.txt`) y los modelos ya generados en
`modelos/pistola_portales/` (la pistola, `vfx/` con el disparo y el portal):

```bash
python animaciones/pistola/herramientas/generar_pistola.py --salida animaciones/pistola --ronda 4 --gif
# solo comprobar y exportar, sin renders:
python animaciones/pistola/herramientas/generar_pistola.py --salida /tmp/prueba --sin-render
```

| Script | Para qué sirve |
| --- | --- |
| `disparo.py` | **Los datos de cada pistola y las poses: aquí se retoca la sensación del disparo** (`ESTILOS`) |
| `rbxmx_pistola.py` | `KeyframeSequence` con pesos y marcadores (y la lectura para comprobarla) |
| `pistola_escena.py` | La escena de las hojas: R6 + pistola en la mano + efectos, y el bloom |
| `generar_pistola.py` | Lo ejecuta todo: comprobaciones, exportación y hojas |
| `portal_fases.py`, `generar_portal.py` | Las curvas del portal en el tiempo y su hoja de contactos (ver `vfx_portal.md`) |

Se reutilizan el rig, la cinemática y la bota de la #17 (`ciclo.py`, `rbxmx.py`): esta rama contiene también esa rama
(`animaciones/movimiento/`), porque estos scripts dependen de ella hasta que se funda.

## Las rondas de mejora

Se hicieron tres rondas rápidas (a menos resolución) y una final (calidad completa, con GIF); las hojas están en `rondas/`.

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | La pistola salía de punta, flotando sobre el hombro: al importar el FBX las mallas llevan una rotación del exportador y los vértices quedan en el marco de Roblox (Y arriba) | Se aplica la transformación a la malla al importar (`pistola_escena._importar_fbx`) |
| 2 | La pistola ya está en la mano. Pero el retroceso levanta el brazo casi en vertical (más de 70°), se sale de cuadro y el máximo se queda demasiado rato (la recuperación empezaba lenta) | Retroceso del brazo 48° → 30° (chatarra) y 34° → 20° (VIP); la recuperación pasa a `sale` (arranca rápido y frena suave); el paso de vuelta, antes; cámara más alta y más lejos |
| 3 | Disparo legible: carga, retroceso, hitstop, paso atrás y vuelta; la normal se tuerce y se bambolea, la VIP se queda limpia. En `_movil` el torso inclinado arrastraba las piernas (cuelgan de él) | El torso en la variante móvil se mueve solo un 30 % y sin desplazamiento (peso 0,6) |
| 4 (final) | Calidad completa con GIF | Etiquetas de fila más anchas |
