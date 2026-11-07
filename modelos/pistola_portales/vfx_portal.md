# VFX del disparo y del portal: guía para montarlo en Studio

Qué hay que montar, fase por fase, para las dos pistolas: la **normal** (de chatarra, verde, inestable) y la **VIP**
(morado y cian, perfecta). Aquí están los números (partículas, colores, tamaños, tiempos, sonidos); las mallas, las
texturas y las animaciones ya están hechas en el repositorio.

> **Nada de esto se ha probado en Studio** (esta sesión no tiene Studio). Las hojas de contactos son renders de Blender
> con las mismas mallas y las mismas curvas que se describen aquí (el resplandor es un bloom hecho a mano, que en Studio
> hace `BloomEffect`). Lo que hay que comprobar al montarlo está en el último apartado.

Los dos diseños son originales: ninguno copia el portal de Rick y Morty ni el de Portal. El de la chatarra es un óvalo con
el anillo roto en tramos que no casan, un borde de espinas desiguales y un remolino de cuatro brazos; el VIP es un óvalo
exacto con aro interior, marcas ordenadas y una espiral limpia de tres brazos.

## 0. Qué hay y dónde

| Qué | Dónde |
| --- | --- |
| Mallas del portal (anillo, borde, fondo, remolino, onda) | `vfx/chatarra/Portal_Chatarra.fbx`, `vfx/vip/Portal_VIP.fbx` (+ `.json` con centros, tamaños y anclajes) |
| Proyectil y fogonazo | `vfx/chatarra/Disparo_Chatarra.fbx`, `vfx/vip/Disparo_VIP.fbx` |
| Texturas de partículas, Beams, remolinos y flipbooks (todas ≤ 512) | `vfx/texturas/` |
| Animaciones de apuntar y disparar (R6) | `animaciones/pistola/*.rbxmx` (y los `.fbx`) |
| Curvas de las piezas de la pistola (rueda, depósito, anillos, núcleo) | `animaciones/pistola/datos/piezas_*.json` |
| Las curvas del portal en el tiempo (las de este documento, en código) | `animaciones/pistola/herramientas/portal_fases.py` |
| Hojas de contactos | `vfx/hoja_portal_4.png` (portal), `animaciones/pistola/hoja_disparo_4.png` y `hoja_apuntar_4.png` |

Todo está en **studs**, con **Scale Unit = Stud** al importar (ver el README de la carpeta de modelos), y con el mismo
`GIRO_IMPORTACION` que las pistolas: el importador mete las mallas giradas 180° sobre el eje vertical. Cada FBX lleva
Empty que en Studio se convierten en `Attachment`: en las mallas del portal, `Centro` y `Borde_1`…`Borde_8` (cada 45° en
el borde del óvalo); en el disparo, `Origen`; en las pistolas, `Boca`, `Agarre`, `Chispas_Bobina_1..3` (normal) y `Nucleo` (VIP).

### Texturas

| Archivo | Tamaño | Qué es | Para |
| --- | --- | --- | --- |
| `particula_brillo.png` | 128 | Mancha de luz redonda | Estela, luz suelta |
| `particula_chispa.png` | 128 | Trazo con la punta afilada | Chispas (`Orientation = VelocityParallel`) |
| `particula_estrella.png` | 256 | Estrella de 4 puntas y 4 pequeñas | Fogonazo y destello |
| `particula_onda.png` | 256 | Anillo fino | Onda expansiva si no se usa la malla |
| `particula_humo.png` | 128 | Nube suave | Resto de gas en la boca de la chatarra |
| `beam_energia.png` | 512 × 64 | Estela con pulsos | Trail del proyectil |
| `beam_rayo.png` | 512 × 64 | Rayo irregular | Arcos de la chatarra (`Beam`) |
| `flipbook_remolino_chatarra.png` | 512 | 4 × 4 fotogramas de 128: remolino que se deforma | Capa de partícula del portal normal |
| `flipbook_remolino_vip.png` | 512 | 4 × 4: espiral que gira exacta | Capa de partícula del portal VIP |
| `portal_remolino_chatarra.png`, `portal_remolino_vip.png` | 512 | Remolino con color y alfa | Malla `*_Remolino` |
| `portal_fondo_chatarra.png`, `portal_fondo_vip.png` | 512 | Fondo oscuro con alfa | Malla `*_Fondo` |
| `anillo_banda_chatarra.png`, `anillo_banda_vip.png` | 512 × 64 | Bandas que se repiten por el aro | Malla `*_Anillo` (opcional) |

Las de **partícula y Beam son blancas**: el color lo pone `Color` del emisor, así que sirven a las dos pistolas. Los
flipbooks son la forma del remolino también en blanco (se tiñen igual). Los de las mallas llevan su color.

## 1. Colores y reglas comunes

| | Normal (chatarra) | VIP |
| --- | --- | --- |
| Color principal (anillo, proyectil) | `#7DFF3A` lima ácido (el del combustible) | `#A64BFF` morado |
| Color secundario | `#B6FF4A` (borde), `#C8FF8A` (destello) | `#3FF0FF` cian (aro interior, marcas, aros del proyectil) |
| Chispas | `#E6FF7A` → `#7DFF3A` | `#FFFFFF` → `#3FF0FF` |
| Destello / fogonazo | `#C8FF8A` | `#E8FBFF` |
| Luz | `#7DFF3A` | `#A64BFF` |

- Las mallas que brillan: `Material = Neon`, sin sombra (`CastShadow = false`), `CanCollide = false`, `CanQuery = false`,
  `CanTouch = false`, `Anchored = true` si no se mueven con una Tool.
- Los que brillan casi blancos (destello, estrella, brillo): `LightEmission = 1` y `LightInfluence = 0`.
- Con `Lighting` → un `BloomEffect` (`Intensity 0.6`, `Size 24`, `Threshold 0.9`): el neón y el destello lo necesitan para
  verse como en las hojas.
- Todo se crea **a partir de objetos ya hechos** (clonar una plantilla y devolverla a un pool al acabar): no se crean
  `ParticleEmitter` nuevos en cada disparo.
- La chatarra es **irregular de verdad**: tiempos y ángulos con `Random` (se indica «±» en cada sitio). La VIP no usa
  aleatoriedad: siempre sale igual.

### Marcadores de la animación

Cada animación de disparo lleva tres `KeyframeMarker` (en el `.rbxmx`):

| Marcador | Fotograma / tiempo | Cuándo usarlo |
| --- | --- | --- |
| `Carga` | 0 (0 s) | Sonido de carga, vibración de la pistola, luz del núcleo/depósito subiendo |
| `Disparo` | 9 (0,15 s) | **Fogonazo, proyectil, retroceso de cámara, sonido de disparo, chispas de la bobina, flash del núcleo** |
| `RetrocesoMax` | 12 (0,20 s) | Temblor de cámara, hitstop del cliente, el depósito toca fondo |

```lua
pista:GetMarkerReachedSignal("Disparo"):Connect(function()
	Efectos.disparar(pistola) -- fogonazo + proyectil (el servidor valida y lanza el proyectil de verdad)
end)
```

## 2. Las piezas de la pistola al disparar

Datos en `animaciones/pistola/datos/piezas_chatarra.json` y `piezas_vip.json`: una fila por fotograma a 60 fps
(`"f"`), con el disparo y el bucle de apuntar. Se leen con `pista.TimePosition * 60`. Las piezas móviles llevan un `Weld`
llamado **`Giro`** con el atributo `C0Base` (lo pone `montar_*.luau`). El eje de giro es siempre **el Z local** del pivote
del Weld, y para el depósito (que sube y baja) también Z local = arriba del mundo:

```lua
weld.C0 = weld:GetAttribute("C0Base") * CFrame.Angles(0, 0, math.rad(grados))    -- girar (rueda, anillos)
weld.C0 = weld:GetAttribute("C0Base") * CFrame.new(0, 0, salto)                  -- subir (depósito)
```

### Normal: la rueda gira, salta el depósito y salen chispas de la bobina

| Pieza | Qué hace | Datos |
| --- | --- | --- |
| `Chatarra_Rueda` | Coge velocidad al cargar (hasta 140°), da 560° más al soltar frenando (`sale`, 26 fotogramas) | `rueda` (grados acumulados) |
| `Chatarra_DepositoMarco` (+ `Deposito` y `Combustible`, soldados a él) | Vibra ±0,008 studs a 22 Hz al cargar; al soltar salta **0,075 studs** y rebota amortiguándose (`0,075·e^(-t/8)·|sin(πt/10)|`, t en fotogramas) | `deposito` (studs) |
| Chispas de la bobina | Chisporroteo flojo en los fotogramas 3, 6 y 8; **ráfaga grande** de 9 a 11 | `chispas` (0,35 = flojo, 1 = ráfaga) |

Chispas de la bobina, en los `Attachment` `Chispas_Bobina_1`, `_2` y `_3` (uno de cada, el mismo emisor):

| Propiedad | Ráfaga (marcador `Disparo`) | Chisporroteo (al cargar) |
| --- | --- | --- |
| Texture | `particula_chispa.png` | igual |
| Emit | **8 por punto** (24 en total) | 2 por punto en los fotogramas 3, 6 y 8 |
| Speed | 6–16 | 3–8 |
| SpreadAngle | (80, 80) | (60, 60) |
| Lifetime | 0,25–0,5 s | 0,15–0,3 s |
| Size | 0,25 → 0 | 0,15 → 0 |
| Acceleration | (0, -30, 0) | (0, -20, 0) |
| Orientation | VelocityParallel | igual |
| Color | `#E6FF7A` → `#7DFF3A` | `#7DFF3A` |
| LightEmission | 1 | 1 |

### VIP: los anillos giran mucho más rápido y el núcleo da un fogonazo

| Pieza | Qué hace | Datos |
| --- | --- | --- |
| `VIP_Anillo1`, `2`, `3` (los aros de luz van soldados a su anillo) | En reposo giran a **60 / −90 / 120 °/s** (el del medio al revés); al cargar suben a ×3 y **al soltar a ×15** (900 / −1350 / 1800 °/s), y se calman con `e^(-t/14)` fotogramas | `anillos` (grados acumulados de cada uno) |
| `VIP_Nucleo` | Crece hasta ×1,35 al cargar; al soltar **×2,45 y blanco**, y vuelve con `e^(-t/5)` fotogramas | `nucleo_escala` (`Size` × factor), `nucleo_blanco` (`Color:Lerp(blanco, k)`) |
| Luz del núcleo | `PointLight` en el `Attachment` `Nucleo`: brillo 1,2 → 3 al cargar, 9 al soltar y vuelve a 1,2 en 0,25 s; Range 10; Color `#C46BFF` | — |

Al apuntar (bucle de 2 s) los anillos siguen girando a su velocidad de reposo, y el núcleo late ±3 % una vez cada 2 s.

## 3. Las cuatro fases

Los tiempos de cada fase empiezan a cero al empezar esa fase.

### Fase 1: DISPARO (`Disparo` hasta que el proyectil llega)

Fogonazo en la `Boca` y un proyectil de energía que vuela hasta donde se apunta, a **70 studs/s**.

| Elemento | Tipo | Normal (chatarra) | VIP |
| --- | --- | --- | --- |
| Fogonazo (malla) | `MeshPart` `Fogonazo_*`, Neon, en `Boca` mirando al cañón | Color `#C8FF8A`. Dura **0,05 s**: tamaño ×1 → ×0,75 → ×0,4 en 3 fotogramas y `Transparency` 0 → 1. **Gira un ángulo al azar (0–360°) alrededor del cañón** en cada disparo | Color `#E8FBFF`. Igual de largo pero tamaño ×0,9 → ×0,7 → ×0,35. Sin giro al azar |
| Estrella | `ParticleEmitter` `Estrella` en `Boca`, `Emit(1)` | `particula_estrella.png`, Lifetime 0,07–0,09, Size 0,5 → **3,2** → 0 (picos en 0,2 de la vida), Rotation 0–360, `LightEmission 1`, Color `#C8FF8A` | Lo mismo con Size 0,5 → **2,4** → 0, Rotation 0, Color `#E8FBFF` |
| Chispas | `ParticleEmitter` `ChispasBoca`, `Emit` | **10**, Speed 18–36, SpreadAngle (35, 35), Lifetime 0,18–0,3, Size 0,5 → 0, Acceleration (0, −30, 0), `particula_chispa.png`, VelocityParallel, Color `#E6FF7A` → `#7DFF3A` | **6**, Speed 22–30, SpreadAngle (18, 18), Lifetime 0,2, Size 0,4 → 0, sin gravedad, Color `#FFFFFF` → `#3FF0FF` |
| Gas | `ParticleEmitter` `Gas` | Solo la chatarra: `particula_humo.png`, `Emit(4)`, Speed 2–5, Lifetime 0,5–0,8, Size 0,6 → 2,2, Transparency 0,5 → 1, Color `#2A6B1A`, `LightEmission 0`, `LightInfluence 1` | — |
| Luz | `PointLight` en `Boca` | Brillo **6 → 0** en 0,12 s, Range 14, Color `#7DFF3A` | Brillo **5 → 0** en 0,1 s, Range 14, Color `#C46BFF` |
| Proyectil | `MeshPart` `Proyectil_Chatarra` / `Proyectil_VIP_Nucleo` + `Proyectil_VIP_Aro` | Neon `#7DFF3A`, ~0,6 studs. **Se tambalea** ±0,15 studs con ruido (Perlin) mientras vuela y parpadea (`Transparency` 0–0,25 al azar a 20 Hz) | Neon `#C46BFF` en el núcleo y `#3FF0FF` en el aro. Va recto. El aro gira a **540 °/s** sobre el eje de vuelo |
| Estela | `Trail` (dos `Attachment` a 0,35 studs entre sí) | `beam_energia.png`, Lifetime 0,25, Width 0,45 → 0, Color `#7DFF3A` → `#1B6B0C`, Transparency 0,1 → 1, `LightEmission 1`, TextureMode Stretch | Lifetime 0,3, Width 0,3 → 0, Color `#A64BFF` → `#3FF0FF`, Transparency 0 → 1, `LightEmission 1` |
| Chispas de la estela | `ParticleEmitter` en el proyectil | `Rate 45`, `particula_brillo.png`, Lifetime 0,3, Size 0,3 → 0, Speed 1–3, SpreadAngle (180, 180), Color `#7DFF3A` | — (la VIP no deja basura) |
| Cámara | código | Temblor **0,45 studs, 0,22 s**, 18 Hz, decae con `e^(-t/0,08)` | Temblor **0,28 studs, 0,15 s**, 14 Hz |

El proyectil sale en la dirección en que apuntaba la `Boca` **al soltar** (no en la del retroceso). El servidor decide dónde
cae; el cliente solo dibuja. Si no choca con nada, la altura del portal y su distancia máxima son decisiones del código.

### Fase 2: APERTURA (0,45 s desde el impacto)

El portal se abre **de golpe desde un punto**, con onda expansiva y destello. Se coloca un `Part` ancla (`Transparency 1`,
`CanCollide false`, `Anchored`, tamaño 4,4 × 6,2 × 0,4) en el sitio, mirando hacia donde se pueda pasar; todas las mallas y
emisores cuelgan de él (o de su `Attachment` `Centro`). Todas las mallas del portal están centradas en su propio centro, así
que se ponen todas con el mismo `CFrame` y se escalan cambiando su `Size` (tamaño de la malla × factor).

| Elemento | Normal (chatarra) | VIP |
| --- | --- | --- |
| **Portal** (anillo, borde, fondo, remolino) | Tamaño **0 → 1,14** en 0,30 s con `Back` (Out), y se asienta a 1 en 0,15 s **con un bamboleo** de ±6 % a 9 Hz que se apaga con `e^(-6t)` | **0 → 1,04** en 0,30 s con `Back`, y se queda en 1 sin bamboleo |
| Anillo y borde | El anillo sube de brillo `0,4 + 2t` (sin pasar de 1) | Igual |
| Remolino | `Transparency` 1 → 0 entre 0,04 y 0,26 s (suave), girando ×2,5 más rápido que abierto | Igual |
| **Onda** (malla `*_Onda`) | Tamaño **0,15 → 2,25** en 0,40 s (`Quint` Out); `Transparency` 0,35 → 1 con `(1 − t/0,4)^1,5` | Tamaño **0,15 → 2,0**; igual `Transparency` |
| **Destello** | `ParticleEmitter` en `Centro`, `Emit(1)`: `particula_estrella.png`, **Lifetime 0,3**, Size 0 → **7** (a los 0,06 s) → 0 con caída `e^(-(t−0,06)/0,07)`, Rotation 0–360, `LightEmission 1`, Color `#C8FF8A` | Igual con Size 0 → **6**, Rotation 0, Color `#E8FBFF` |
| **Chispas** | **26** en 8 emisores (`Borde_1..8`, `Emit(3)` en cada uno y 2 más en dos al azar), Speed 8–20 hacia fuera y algo desordenadas (±7°), Lifetime 0,5, `particula_chispa.png`, VelocityParallel, Size 0,28 → 0, Acceleration (0, −18, 0), Color `#E6FF7A` | **16** (2 por emisor), Speed **14** exacto hacia fuera, Lifetime 0,5, Size 0,25 → 0, sin gravedad, Color `#FFFFFF` → `#3FF0FF` |
| Luz | `PointLight` en `Centro`, Brillo **8 → 2,2** en 0,45 s, Range 24 → 16 | Brillo **7 → 2** en 0,45 s, Range 24 → 16 |
| Cámara | Si el portal está a menos de 30 studs: temblor 0,2 studs, 0,15 s | 0,12 studs, 0,12 s |
| Sonido | `Apertura`: golpe grave hueco, chisporroteo eléctrico y un «glup» | `Apertura`: «fum» grave limpio y un acorde que sube |

### Fase 3: ABIERTO (en bucle)

El remolino gira, el borde está vivo y da ganas de entrar. Todo va con `RunService.PreRender` (o `Heartbeat` si es lejos).

| Elemento | Normal (chatarra): inestable | VIP: perfecto y estable |
| --- | --- | --- |
| Giro del remolino (el disco **circular** sobre su eje Z local) | **−110 °/s** más un temblor de 6° a 3,1 Hz y 4° a 7,3 Hz | **−50 °/s** exactos |
| Tamaño del conjunto | `1 + 0,025·sin(2π·11·t) + 0,02·sin(2π·17,3·t + 1)` (respira nervioso) | `1 + 0,004·sin(2π·0,5·t)` |
| Brillo del anillo (`Transparency` = 1 − brillo) | `0,75 + 0,25·\|sin(2π·13·t)·sin(2π·4,7·t)\|` (parpadea) | 1, constante |
| Borde (malla `PortalCh_Borde`) | Tamaño `1 + 0,12·sin(2π·6·t)` y giro ±5° a 2,3 Hz | — (la VIP no tiene borde) |
| Marcas (`PortalVIP_Marcas`) | — | `Transparency` = 1 − `(0,4 + 0,6·(0,5 + 0,5·cos(2πt/1,2))²)`: late a 0,83 Hz |
| Capa de remolino (partícula, opcional) | `ParticleEmitter` en `Centro`: `flipbook_remolino_chatarra.png`, `FlipbookLayout = Grid4x4`, `FlipbookMode = Loop`, `FlipbookFramerate = 16`, `Rate 1`, Lifetime 1, Size 5,4, Speed 0, Transparency 0,5, `LightEmission 1`, Color `#7DFF3A` | Igual con `flipbook_remolino_vip.png`, Size 5,2, Color `#3FF0FF`, `FlipbookFramerate = 12` |
| Chispas del borde | 8 emisores (`Borde_1..8`) con `Rate 1` y `Emit(2)` al azar cada 0,3–0,9 s: Speed 4–11 hacia fuera, Lifetime 0,5, Size 0,22 → 0, Acceleration (0, −18, 0), `particula_chispa.png`, VelocityParallel, Color `#E6FF7A` | 8 emisores con `Rate 3` (24/s): **Speed 3,2 hacia el centro** (el `Attachment` mirando al `Centro`), Lifetime 0,9, Size 0,1 → 0, `particula_chispa.png`, VelocityParallel, Color `#3FF0FF` → `#FFFFFF`, sin gravedad. Quedan en filas ordenadas |
| Arcos | **2 `Beam`** entre dos `Borde_n` al azar: `beam_rayo.png`, TextureMode Wrap, TextureLength 4, TextureSpeed 6, Width 0,18, Segments 8, CurveSize0/1 ±0,8 al azar, Transparency 0,15, `LightEmission 1`. Duran 0,08–0,15 s y se vuelven a sortear cada 0,4–1,2 s | — |
| Luz | `PointLight` `Brightness 2,2` con parpadeo 1,6–2,6 a 13 Hz, Range 16, Color `#7DFF3A` | `Brightness 2`, Range 16, Color `#A64BFF`, fija |
| Sonido (en bucle) | Zumbido con chisporroteo y algún «pop», `Volume 0,6`, `PlaybackSpeed` 1 ± 3 % al azar, `RollOffMaxDistance 60` | Zumbido grave y limpio con un acorde suave, `Volume 0,5`, `PlaybackSpeed 1`, `RollOffMaxDistance 60` |

### Fase 4: CIERRE (0,40 s)

Se encoge y desaparece con un pequeño destello.

| Elemento | Normal (chatarra) | VIP |
| --- | --- | --- |
| **Tamaño del conjunto** | `1 − Back_in(t/0,4)`: primero se hincha un poco (×1,1) y después se hunde hasta 0. **Tartamudea**: si `\|sin(2π·14·t)\| > 0,7` se encoge un `0,25·(t/0,4)` más | Igual sin tartamudeo |
| Giro | `−110·t + 220·(t/0,4)²` grados (acelera) | `−50·t + 360·(t/0,4)²` |
| Remolino | `Transparency` 0 → 1 con `1 − (t/0,4)²` (suave) | Igual |
| Anillo | Brillo −60 % a lo largo de la fase | Igual |
| Onda | `Transparency` 1 (no hay) | Igual |
| **Destello final** | En `t = 0,34 s`: `Emit(1)` `particula_estrella.png`, Size 0 → **3,6** → 0, Lifetime 0,1 | Size 0 → **3**, Lifetime 0,1 |
| Chispas finales | **10**, Speed 8–20 hacia fuera, Lifetime 0,5 (también en `t = 0,34`) | **16** ordenadas, Speed 14 |
| Luz | Brillo → 0 en 0,35 s | igual |
| Sonido | `Cierre`: «succión» entrecortada y un tintineo metálico | `Cierre`: «fium» limpio hacia dentro y una campanita |
| Fin | Desactivar emisores (`Enabled = false`), esperar 0,6 s (la vida más larga) y devolver todo al pool | igual |

## 4. Sonidos que hacen falta

Ninguno está hecho. Los que se necesitan (uno por cada pistola salvo que se diga):

| Id | Cuándo | Normal (chatarra) | VIP |
| --- | --- | --- | --- |
| `Carga` | Marcador `Carga` (dura 0,15 s) | Motor que arranca con traqueteo y subida de tono | Condensador que se carga: silbido limpio que sube |
| `Disparo` | Marcador `Disparo` | Golpe grave + chasquido eléctrico, traqueteo de chapa y siseo de gas (0,5 s) | Estampido grave y limpio + brillo agudo (0,6 s) |
| `Proyectil` | En vuelo (bucle corto) | Zumbido crepitante | Zumbido liso que baja de tono al alejarse |
| `Apertura` | Fase 2 | Ver tabla | Ver tabla |
| `Abierto` | Fase 3 (bucle) | Zumbido con chisporroteo y «pop» | Zumbido grave con acorde suave |
| `Cierre` | Fase 4 | Ver tabla | Ver tabla |
| `Rueda` | Con la rueda de la chatarra (marcador `Disparo`) | Carraca que frena | — |

Todos en 3D (`RollOffMode = LinearSquare`, `RollOffMaxDistance 60–80`), `Volume` entre 0,5 y 0,9 y `PlaybackSpeed` ±3 % al azar
en la chatarra.

## 5. Rendimiento en móvil

- **Texturas**: todas ≤ 512 × 512 (las de partículas 128–256; los flipbooks 512 con fotogramas de 128).
- **Mallas**: portal normal 1.852 triángulos (5 piezas), VIP 2.784 (6 piezas); proyectil + fogonazo 442 y 716. Cada una
  muy por debajo del límite de 20.000 triángulos.
- **Partículas vivas a la vez, por portal** (cálculo de las tablas): normal ≈ 8 (chispas) + 1 (flipbook) + 2 `Beam`;
  VIP ≈ 22 (ordenadas) + 1 (flipbook). En la apertura sube un momento a 26 + destello.
- **Presupuesto sugerido**: como mucho **2 portales con todos los efectos** a la vez en pantalla; el resto, solo mallas y luz.
  A más de **80 studs** desactiva los emisores y los `Beam` (se quedan el anillo, el remolino y la luz); a más de 150,
  solo el anillo. `Segments ≤ 8` en los `Beam`.
- `PointLight` sin sombras, **una por portal** (y una más en la boca mientras dura el fogonazo).
- Un solo `BloomEffect` global. No se crean instancias nuevas en cada disparo: **pool**.
- La VIP no se vuelve más pesada por ser más cara: tiene más partículas ordenadas pero menos desorden (menos `Random`).

## 6. Cómo montarlo, en orden

1. Importa `Portal_*.fbx` y `Disparo_*.fbx` (Scale Unit = Stud) y sube las texturas de `vfx/texturas/`.
2. Pon el neón (`Material = Neon`) y los colores de las tablas a cada malla. En los remolinos y los fondos pon la textura
   (ver el último apartado: hay dos formas de hacerlo y hay que probar cuál se ve mejor).
3. Crea las plantillas (`Part` ancla + mallas + `Attachment`s del JSON + emisores + `PointLight`) en
   `ReplicatedStorage/Efectos/PortalChatarra` y `PortalVIP`, y las del disparo.
4. Sube `apuntar_*.rbxmx`, `disparo_*.rbxmx` y `disparo_*_movil.rbxmx` (ver `animaciones/pistola/README.md`).
5. Monta las cuatro fases con `TweenService` y las curvas de `portal_fases.py`. El script de cada fase solo recibe «chatarra»
   o «vip» y lee su tabla.

## 7. Lo que hay que probar en Studio

- [ ] **Remolino y fondo**: dos formas. (A) `MeshPart` con `SurfaceAppearance` (`ColorMap` = el PNG, `AlphaMode = Transparency`)
      y `Material = Neon`; (B) `MeshPart.TextureID` y `Material = Neon`. La región 1 enseñó que con `TextureID` Roblox pinta mal
      el color detrás de las zonas transparentes; mira cuál sale bien con el alfa del remolino. Si ninguna, queda la capa de
      partícula con el flipbook sola.
- [ ] Que el remolino, que es un **círculo**, gire dentro del óvalo sin asomar por el anillo.
- [ ] `Orientation = VelocityPerpendicular` para que la capa flipbook se quede en el plano del portal (con una velocidad
      pequeña a lo largo de la normal). Si no, `FacingCamera` también vale.
- [ ] Que los `KeyframeMarker` llegan: `GetMarkerReachedSignal("Disparo")` al soltar.
- [ ] El **peso** de las poses (`apuntar` solo con el brazo derecho a peso 1; `_movil` con el torso a 0,6) mezclándose con el
      reposo, el andar y el correr de la #17.
- [ ] Que la pistola sale de la boca con la dirección bien (`Boca.WorldCFrame.LookVector`) y que el agarre cae en la mano.
- [ ] Rendimiento con 2 portales y con 10 jugadores disparando: ver el panel de microprofiler en un móvil real.
