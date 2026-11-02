# Modelos 3D

Modelos del juego generados con scripts de Python en Blender sin pantalla (`bpy`) y exportados a `.fbx` para el
importador 3D de Roblox Studio. No hay nada hecho a mano en Blender: todo sale de `herramientas/` y se puede regenerar.

| Carpeta | Qué hay | Triángulos |
| --- | --- | --- |
| `nave_humana/` | Nave humana inicial «Alba»: casco con textura, cabina de cristal y piezas de neón | ~2.400 (límite: 5.000) |
| `monstruo/` | Monstruo base R6 «El Hueco»: 6 piezas R6 + ojos, con textura de color y de normales | ~6.900 |
| `rocas_minerales/` | 4 rocas y 3 minerales brillantes, con textura de color y de normales | 360–700 cada uno |

Cada carpeta tiene la hoja de contactos final (`hoja_contactos_5.png`, 7–8 vistas + la malla) y en `rondas/` las
hojas de las rondas anteriores, para ver cómo ha ido mejorando.

Medidas: los modelos se escriben en **studs** y se exportan a metros con 1 stud = 0,28 m, que es la conversión del
importador de Roblox, así que llegan a Studio con su tamaño. Todos miran a **-Z** (el «delante» de Roblox).

## Importar en Studio (lo común)

1. **Avatar → Import 3D** (o *File → Import 3D*) y elige el `.fbx`.
2. En la ventana del importador revisa la vista previa. Ajustes:
   - **File General → Scale Unit**: déjalo en *Meter* (es como está guardado el FBX). Si el modelo sale 3,57 veces
     más grande o más pequeño, es que se ha leído en studs: cambia la unidad.
   - **Anchored**: actívalo para rocas y minerales (son escenario). Para la nave y el monstruo, desactívalo.
   - **Import only as model**: activado.
3. **Import**. Cada malla del FBX se convierte en una `MeshPart` con el mismo nombre.
4. **Texturas.** El FBX lleva las texturas incrustadas y el importador suele crear la `SurfaceAppearance` sola. Si
   no la crea (o sale gris), créala a mano dentro de cada `MeshPart`:
   - `ColorMap` → `texturas/<pieza>_color.png`
   - `NormalMap` → `texturas/<pieza>_normal.png` (las que lo tienen)
   - Se suben con *Asset Manager → Bulk Import* y se pega el ID en cada propiedad.
5. Las piezas que brillan (`*_Neon`, `*_Cristales`, `Ojos`) no llevan textura: ponles **Material = Neon** y el color
   que se indica abajo.

Si el modelo sale girado 180° (mirando a +Z), el importador ha interpretado otro eje: gíralo 180° en Y o cambia
`axis_forward` en `herramientas/comun.py` (`exportar_fbx`) y vuelve a generar.

## Nave humana inicial (`nave_humana/Nave_Humana.fbx`)

Caza ligero de ciencia ficción limpia: blanco, gris azulado y franjas naranjas, con las dos toberas bien visibles.
Mide 13 × 16 × 3,7 studs (ancho × largo × alto), parecido a la nave que construye el código (`ServicioNaves/Modelo`).

| Pieza | Qué es | En Studio |
| --- | --- | --- |
| `Nave_Casco` | Fuselaje, alas, cañones, góndolas, toberas, derivas | `SurfaceAppearance` con `Nave_Casco_color.png` (colores + oclusión ambiental horneados) |
| `Nave_Cristal` | Cabina | Material **Glass**, color `#16324F`, Transparency 0,3 |
| `Nave_Neon` | Núcleos de las toberas, franjas y luces | Material **Neon**, color del bando (humanos `#4DF0FF`) |

**Anclajes.** `anclajes.json` da la posición (studs, relativa al centro de `Nave_Casco`) de los Attachments que usa
el juego: `Ejes`, `Piloto`, `CanonIzq/Der` (bocas de los cañones) y `MotorIzq/Der` (salida de las toberas). Crea un
`Attachment` con ese nombre dentro de `Nave_Casco` y pon su `Position`. Con eso el motor de efectos encuentra las
anclas igual que en la nave de código.

Para que el juego use este modelo en lugar del de código habría que cambiar `ServicioNaves/Modelo` para que clone
el modelo (soldando las piezas a `Nave_Casco` como hace ahora). Eso es un cambio de código que **no** está en esta
rama: primero hay que probar el modelo en Studio.

## Monstruo base R6 (`monstruo/`)

«El Hueco»: criatura original (no copia ningún personaje conocido) de cuerpo consumido y encorvado, con brazos que
le llegan a las rodillas y dedos larguísimos acabados en garra, piernas flacas con la rodilla hacia delante, una
cresta de vértebras en la espalda y una cabeza alargada partida por una **boca vertical** llena de dientes, con
tres ojos hundidos y desiguales que brillan en rojo. Los brazos son asimétricos (el derecho más largo y con cuatro
dedos, el izquierdo con tres y un bulto). Mide 6,6 studs de alto.

| Archivo | Para qué |
| --- | --- |
| `Monstruo_R6.fbx` | **El que se importa en Studio**: 7 mallas sueltas (`Head`, `Torso`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg`, `Ojos`) |
| `montar_r6.luau` | Script para la barra de comandos que lo convierte en un personaje R6 |
| `articulaciones.json` | Pivotes de cada articulación y centro de cada pieza (los usa el script) |
| `Monstruo_R6_esqueleto.fbx` | Las mismas mallas atadas a un esqueleto R6 (7 huesos con los nombres de R6): para animarlo en Blender |

Es **R6**: cada pieza es rígida y se mueve con su `Motor6D`, sin huesos ni deformación. Pasos:

1. Importa `Monstruo_R6.fbx` (Anchored desactivado) y pon las texturas de `texturas/` en cada pieza (paso 4 de arriba;
   `RightArm_color.png` es para `Right Arm`, etc.).
2. Selecciona el modelo importado, abre **View → Command Bar**, pega el contenido de `montar_r6.luau` y pulsa Enter.
   El script crea `HumanoidRootPart`, el `Humanoid` (RigType R6), los 6 `Motor6D` de R6 con su pivote en las
   articulaciones de este cuerpo, suelda los ojos a la cabeza (material Neon, rojo `#FF2B2B`) y sube `HipHeight`
   porque las piernas miden 2,75 studs y no 2.
3. Los `Motor6D` tienen la **misma orientación que en un R6 estándar**, así que las animaciones R6 (las de Roblox, la
   de `animaciones/` y la futura forma de andar terrorífica) giran cada pieza sobre el eje correcto. Los pivotes no
   están en el mismo sitio que en un R6 normal (el cuello está adelantado, los hombros más altos): las animaciones se
   verán con estas proporciones.
4. Para usarlo como personaje de un jugador, mete el modelo en `StarterPlayer` con el nombre `StarterCharacter`, o
   clónalo desde el servidor al elegir el bando Monstruos.

**Lo que hay que comprobar en Studio** (no se ha podido probar aquí: esta sesión no tiene Studio):
- Que `HipHeight = 0,75` deja los pies en el suelo con el R6. Si flota o se hunde, ajusta `HipHeight` a mano.
- Que la colisión del `Torso` (que es más grande que la caja de 2 × 2 × 1) no lo atasque en puertas: si pasa, pon
  `CollisionFidelity = Box` o un `Torso` invisible del tamaño estándar.

## Rocas y minerales (`rocas_minerales/`)

| Archivo | Qué es | Tamaño (studs) |
| --- | --- | --- |
| `Roca_Canto.fbx` | Canto rodado gris | 6 × 5 × 3 |
| `Roca_Aguja.fbx` | Aguja de basalto | 2,4 × 2,3 × 6 |
| `Roca_Losa.fbx` | Losa de arenisca en capas | 8 × 5 × 2 |
| `Roca_Grupo.fbx` | Grupo de piedras con musgo | 7 × 5 × 2,5 |
| `Mineral_Cristal.fbx` | Cristal cian (el `Cristal` de `Datos/Minerales`) | 4,4 × 3,8 × 5,4 |
| `Mineral_Ambar.fbx` | Ámbar solar, corona de cristales dorados | 4 × 4 × 3 |
| `Mineral_Vacio.fbx` | Esquirla del vacío, violeta | 5 × 3 × 4,8 |

Las rocas tienen la base plana y en z = 0: se pueden hundir un poco en el terreno. Su color es neutro para poder
teñirlas por planeta con `SurfaceAppearance.Color`.

Cada mineral son dos piezas: `<Mineral>_Base` (roca con textura) y `<Mineral>_Cristales` (sin textura). En Studio:
- `_Cristales`: **Material Neon** y el color del mineral (cian `#4FD8FF`, ámbar `#FFB23A`, violeta `#B54DFF`).
  Para que ilumine alrededor, añade una `PointLight` del mismo color (Brightness 1–2, Range 10–14). Con muchos
  minerales a la vista, deja la luz solo en los cercanos (rendimiento en móvil).
- Para que sean picables hay que etiquetarlos `Mineral` y darles el atributo `MineralTipo` (ver
  `src/shared/Exploracion/Datos/Minerales.luau`). `Cristal` ya existe; **Ámbar** y **Vacío** son modelos nuevos sin
  datos en el juego: el violeta encaja como el recurso exclusivo del planeta de los monstruos, pero eso lo decide
  Rodrigo.

## Regenerar

Requiere Python 3.13 y las bibliotecas de `herramientas/requirements.txt` (el mismo `bpy` que usa `animaciones/`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/herramientas/requirements.txt
.venv/bin/python modelos/herramientas/nave_humana.py --salida modelos/nave_humana --ronda 5
.venv/bin/python modelos/herramientas/monstruo.py --salida modelos/monstruo --ronda 5
.venv/bin/python modelos/herramientas/rocas_minerales.py --salida modelos/rocas_minerales --ronda 5
```

Con `--rapido` las texturas y los renders salen a baja resolución (para probar cambios en segundos).
Los renders tardan: con 4 núcleos, unos 3 minutos la nave, 4 el monstruo y 8 las rocas.

| Script | Para qué |
| --- | --- |
| `comun.py` | Escena, materiales, horneado de texturas, estudio de fotos, hoja de contactos y exportación FBX |
| `nave_humana.py` | La nave, por secciones (lofts). **Las medidas y los colores están arriba del todo** |
| `monstruo.py` | El monstruo: metabolas para torso y cabeza, Skin para brazos y piernas, cara tallada, pintado |
| `rocas_minerales.py` | Rocas (poliedro recortado + ruido) y minerales (base + prismas). Una tabla de datos por pieza |
| `plantilla_montar_r6.luau` | Plantilla del script de Studio; `monstruo.py` la rellena con los números del modelo |
| `guardar_ronda.py` | Guarda una hoja de contactos en `rondas/` en JPG |

## Las rondas de mejora

En cada ronda: renderizar la hoja de contactos, mirarla con ojo crítico, anotar lo que falla y corregir el script.
Las rondas 2–3 de las rocas y 2–3 del monstruo se renderizaron en modo rápido (a menos resolución). La columna
«Lo que se cambió» de cada fila es lo que se corrigió para llegar a esa hoja.

### Nave

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Se lee como nave y las toberas se ven, pero las alas son finas y bajas, los cañones son palos sueltos que sobresalen mucho, no hay color de acento y toda la panza es oscura | — |
| 2 | Mejor, pero la franja naranja no se ve (la tapa el lomo) y el casco es una superficie blanca sin cortes | Alas más gruesas y altas (4 secciones), cañones en vaina más cortos, quilla oscura solo en el centro, puntas de las derivas en naranja, radomo oscuro |
| 3 | Más detalle, pero el morro sigue sin acento y el estudio dejaba una línea de luz en el suelo | Flaps en gris, tomas de aire laterales, aleta ventral, antena, más lados en fuselaje y góndolas |
| 4 | Banda naranja en el morro, luz limpia. Los núcleos de las toberas salen blancos de tan brillantes | Anillos extra en el fuselaje para la banda del morro; estudio con focos difusos |
| 5 (final) | — | Neón menos intenso para que se lea el cian del bando |

### Monstruo

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Huecos entre cabeza, torso y piernas; costillas como neumáticos apilados; ojos que sobresalen de la cara; brazos como tubos | — |
| 2 | Ya no hay huecos, ojos en sus cuencas, costillas en diagonal. Pero sigue pareciendo un maniquí: extremidades gruesas iguales y torso de caja | Piezas que solapan, costillas solo en los costados, joroba, cuello adelantado, ojos colocados con un rayo contra la cara, brazos con codo y muñeca huesudos que cuelgan hacia delante |
| 3 | Extremidades flacas y nudosas, pero el torso y la cabeza del Skin salen cuadrados y con pliegues | Torso y cabeza con metabolas (costillar, vientre chupado, joroba, omóplatos, vértebras, pómulos, arco de las cejas) |
| 4 | Silueta consumida y encorvada que da mal rollo. Fallan detalles: los ojos quedaban fuera de la cara estrecha, la boca era demasiado ancha, el cuello de la cabeza se veía muy largo y las costillas cruzaban el pecho como vendas | Ojos y boca a la medida de la cara nueva |
| 5 (final) | — | Cuello más corto, costillas solo en los costados y más sutiles, dientes que no salen de la boca |

### Rocas y minerales

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Formas buenas, pero las grietas forman un dibujo de caparazón de tortuga; los cristales salen blancos quemados; la losa no tiene capas | — |
| 2 | Sin caparazón y con estratos, pero las rocas quedan lisas como jabón y los cristales siguen pálidos | Grietas sueltas sobre coordenadas deformadas, chorretones verticales, estratos con escalones, menos emisión |
| 3 | Estratos solo en las paredes, cristales con color. Rocas oscuras (la aguja casi negra) | Desconchones con ruido *ridged* (aristas vivas), estratos solo en las paredes |
| 4 | Primera a resolución completa: las rocas ya tienen relieve y aristas. Las grietas se pintan como garabatos negros encima de la losa y del canto | Paletas más claras, base del cristal cian en gris, menos emisión y estudio más luminoso |
| 5 (final) | Las grietas quedan en el relieve; queda alguna línea oscura, pero ya no se lee como dibujo | Grietas más finas y casi sin pintar (solo relieve y oclusión) |
