# Modelos 3D

Modelos del juego generados con scripts de Python en Blender sin pantalla (`bpy`) y exportados a `.fbx` para el
importador 3D de Roblox Studio. No hay nada hecho a mano en Blender: todo sale de `herramientas/` y se puede regenerar.

| Carpeta | Qué hay | Triángulos |
| --- | --- | --- |
| `nave_humana/` | Nave humana inicial «Alba»: casco con textura, cabina de cristal y piezas de neón | ~2.400 (límite: 5.000) |
| `monstruo/` | Monstruo base R6 «El Hueco»: 6 piezas R6 + ojos, con textura de color y de normales | ~6.900 |
| `rocas_minerales/` | 4 rocas y 3 minerales brillantes, con textura de color y de normales | 360–700 cada uno |
| `ciudad_humana/` | Tienda con persiana animable, edificio residencial, torre de oficinas y farola | 960–6.250 |
| `hangar/` | Hangar humano con la forja de la primera nave | ~15.600 |
| `planeta_monstruos/` | 3 árboles muertos, 2 rocas oscuras con grietas brillantes y el «Arco de costillas» | 680–4.000 |
| `cristal_abisal/` | El recurso exclusivo de los monstruos: cristal oscuro con brillo morado | ~1.300 |
| `criaturas/` | Brincador lanudo (pacífico, humanos) y Acechador del abismo (agresivo, monstruos), por piezas | 2.900 y 3.700 |
| `pistola_portales/` | Pistola de portales normal (de chatarra) y VIP, como Tool (después de la v1). Ver su README | 3.900 cada una |

`hoja_contactos_todo.png` junta todos los modelos en una sola hoja.

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

## Ciudad humana (`ciudad_humana/`)

Ciencia ficción limpia y luminosa, con los colores de la nave: hormigón claro, paneles blancos, gris azulado y
acentos naranja y cian. Cada modelo es un cuerpo con textura (colores + suciedad + oclusión horneadas) y aparte
`_Cristal` (Glass, color `#1E3A55`, Transparency 0,3) y `_Neon` (Neon: cian `#4DF0FF` o cálido `#FFD08A`).

| Archivo | Qué es | Tamaño (studs) |
| --- | --- | --- |
| `Tienda.fbx` | Tienda de una planta con toldo a rayas, mostrador y estantes con productos detrás de la persiana | 19 × 17 × 13,6 |
| `Edificio_Residencial.fbx` | 4 plantas de viviendas sobre un bajo comercial, balcones con jardinera | 24 × 21 × 52 |
| `Edificio_Torre.fbx` | Torre de oficinas escalonada de muro cortina, con helipuerto | 23 × 27 × 70 |
| `Farola.fbx` | Farola de brazo curvo con difusor cálido | 1,8 × 6 × 13 |

**La persiana** (`Tienda_Persiana`) es una pieza aparte para las **persianas de bando**: cuando un monstruo entra
en la ciudad, se bajan. `Tienda.json` da su centro cuando está cerrada y su alto. Para abrirla, la forma más sencilla
es encogerla hacia arriba (las lamas se comprimen como si se enrollara en el cajón):

```lua
-- Abrir: alto 6 -> 0,3, subiendo el centro la mitad de lo que encoge. Cerrar: al revés.
local alto, abierta = 6, 0.3
TweenService:Create(persiana, TweenInfo.new(0.8, Enum.EasingStyle.Quad), {
	Size = Vector3.new(persiana.Size.X, abierta, persiana.Size.Z),
	CFrame = cerrada * CFrame.new(0, (alto - abierta) / 2, 0),
}):Play()
```

La hoja final tiene una vista con la persiana subida. `Tienda_Cartel` es el letrero: ponle un `SurfaceGui` en
la cara delantera (-Z) con el nombre de la tienda. `Tienda.json` y `Farola.json` dan también dónde va la luz
(`LuzToldo`, `Luz`: una SpotLight hacia abajo).

## Hangar (`hangar/`)

El mismo planteamiento que el hangar que construye el código (`src/server/Servicios/Hangar.luau`): planta de
46 × 46 studs, tres muros, frente abierto y **sin techo** (la nave despega hacia arriba). Tiene pilares y ventanales,
puente grúa, pasarela con escalera, depósitos, banco de trabajo y, al fondo, **la forja**: un anillo de fabricación
con un núcleo de energía, dos brazos robóticos y la consola. `Hangar.json` da los anclajes (`Plataforma`,
`Consola`, `Forja`, `PuntasBrazos`, `Gancho`) para colocar la nave, el ProximityPrompt y los efectos de la forja.
Mallas: `Hangar` (textura), `Hangar_Cristal`, `Hangar_Neon` y `Hangar_Cartel` (SurfaceGui con «HANGAR»).

Son ~15.600 triángulos (el cuerpo, 14.300: por debajo del límite de 20.000 por malla de Roblox). Es el edificio más
importante de la v1 y se ve de cerca, por eso tiene más detalle; si en móvil pesa, el atrezo (cajas, bidones,
banco) es lo primero que se puede quitar.

## Planeta de los monstruos (`planeta_monstruos/`)

| Archivo | Qué es | Tamaño (studs) |
| --- | --- | --- |
| `Arbol_Retorcido.fbx` | Árbol alto con el tronco en espiral, ramas como dedos y **dos ojos que brillan en el tronco** | 10 × 10 × 24 |
| `Arbol_Colgante.fbx` | Árbol encorvado con las ramas que caen como brazos | 9 × 9 × 12 |
| `Arbol_Tocon.fbx` | Tronco partido en astillas, con raíces como garras | 12 × 10 × 11,5 |
| `RocaOscura_Partida.fbx` | Peñasco partido en trozos con un núcleo morado que brilla por las grietas | 7,3 × 6,4 × 4 |
| `RocaOscura_Aguja.fbx` | Aguja partida en vertical con el mismo núcleo | 3,5 × 2,2 × 7,4 |
| `Arco_Costillas.fbx` | Estructura siniestra: costillas de piedra que forman un túnel, columna con púas y un altar con runas y un ojo | 18,5 × 26,5 × 16,5 |

Todo lo que brilla va aparte (`_Neon`, `_Nucleo`): material **Neon**, morado `#B54DFF`. Las setas de los árboles y
los núcleos de las rocas quedan muy bien con una `PointLight` morada (Brightness 1, Range 10) en las que estén cerca
del jugador. El núcleo de las rocas es la propia roca encogida, así que solo se ve por las grietas.

## Cristal abisal (`cristal_abisal/`)

El recurso exclusivo del planeta de los monstruos (CLAUDE.md, lista de la v1): cristales negros como la obsidiana
con un corazón morado que asoma por las puntas, sobre una roca oscura con grietas brillantes, y siete esquirlas que
flotan alrededor.

| Pieza | En Studio |
| --- | --- |
| `Cristal_Abisal_Base` | Textura de color y normales (SurfaceAppearance) |
| `Cristal_Abisal_Cristales` | Material **Glass**, color `#2A1838`, Transparency 0,35: deja ver el corazón |
| `Cristal_Abisal_Brillo` | Neon `#B54DFF` (corazón de cada cristal y grietas de la roca) |
| `Cristal_Abisal_Esquirlas` | Neon `#B54DFF`. Pieza aparte para hacerla girar alrededor de `CentroEsquirlas` (en el cliente) |

`Cristal_Abisal.json` da el centro de las esquirlas y dónde poner la luz. El juego todavía no tiene este recurso en
`Datos/Minerales` ni en `Datos/Objetos`: sus valores (vida, botín, precio) son una decisión de diseño. Con esto, la
`Mineral_Vacio` de `rocas_minerales/` queda como mineral violeta normal (o se puede quitar).

## Criaturas (`criaturas/`)

| Criatura | Especie (escáner) | Piezas |
| --- | --- | --- |
| **Brincador lanudo**: bola de lana crema con franjas cian, orejas caídas, ojos grandes y cola de pompón. Pacífico, del planeta humano | `Criatura_BrincadorLanudo` (Común) | Cuerpo, OrejaIzq/Der, Pata1–4, Cola, Ojos |
| **Acechador del abismo**: seis patas de araña, caparazón negro violáceo con bandas y púas de hueso, mandíbulas en gancho y cuatro ojos morados. Agresivo, del planeta de los monstruos | `Criatura_AcechadorAbismo` (Poco común) | Cuerpo, Pata1–6, MandibulaIzq/Der, Ojos |

Las dos especies están dadas de alta en `src/shared/Exploracion/Datos/Especies.luau` (ficha, rareza, recompensa).

Para montarlas: importa el `.fbx`, pon las texturas, selecciona el modelo y pega en la barra de comandos
`montar_brincador.luau` o `montar_acechador.luau`. El script une cada pieza al cuerpo con un `Motor6D` (con su
pivote en la articulación y nombres como `Pata1` u `OrejaIzq`, para animarlas con el Animation Editor), suelda los
ojos, añade `AnimationController` + `Animator`, y les pone la etiqueta **`Escaneable`** y el atributo
**`EspecieId`**: con eso el escáner ya las reconoce. Los ojos del brincador son SmoothPlastic negro con Reflectance
(el brillo de la mirada); los del acechador, Neon morado.

## Regenerar

Requiere Python 3.13 y las bibliotecas de `herramientas/requirements.txt` (el mismo `bpy` que usa `animaciones/`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/herramientas/requirements.txt
.venv/bin/python modelos/herramientas/nave_humana.py --salida modelos/nave_humana --ronda 5
.venv/bin/python modelos/herramientas/monstruo.py --salida modelos/monstruo --ronda 5
.venv/bin/python modelos/herramientas/rocas_minerales.py --salida modelos/rocas_minerales --ronda 5
.venv/bin/python modelos/herramientas/ciudad_humana.py --salida modelos/ciudad_humana --ronda 5
.venv/bin/python modelos/herramientas/hangar.py --salida modelos/hangar --ronda 5
.venv/bin/python modelos/herramientas/planeta_monstruos.py --salida modelos/planeta_monstruos --ronda 5
.venv/bin/python modelos/herramientas/cristal_abisal.py --salida modelos/cristal_abisal --ronda 5
.venv/bin/python modelos/herramientas/criaturas.py --salida modelos/criaturas --ronda 5
.venv/bin/python modelos/herramientas/pistola_portales.py --salida modelos/pistola_portales --ronda 5
.venv/bin/python modelos/herramientas/hoja_conjunto.py modelos/hoja_contactos_todo.png
```

Los scripts de lotes aceptan `--solo Archivo1,Archivo2` para regenerar solo algunos modelos.

Con `--rapido` las texturas y los renders salen a baja resolución (para probar cambios en segundos).
Los renders tardan: con 4 núcleos, unos 3 minutos la nave, 4 el monstruo y 8 las rocas.

| Script | Para qué |
| --- | --- |
| `comun.py` | Escena, materiales, horneado de texturas, estudio de fotos, hoja de contactos y exportación FBX |
| `nave_humana.py` | La nave, por secciones (lofts). **Las medidas y los colores están arriba del todo** |
| `monstruo.py` | El monstruo: metabolas para torso y cabeza, Skin para brazos y piernas, cara tallada, pintado |
| `rocas_minerales.py` | Rocas (poliedro recortado + ruido) y minerales (base + prismas). Una tabla de datos por pieza |
| `plantilla_montar_r6.luau` | Plantilla del script de Studio; `monstruo.py` la rellena con los números del modelo |
| `kit.py` | Piezas de superficie dura (cajas, cilindros, lofts, prismas), materiales con suciedad, bisel, horneado y el «lote» (construir, exportar, renderizar y montar la hoja de varios modelos) |
| `ciudad_humana.py`, `hangar.py` | Edificios con `kit.py`. Medidas y paleta arriba de cada script |
| `planeta_monstruos.py` | Árboles (esqueleto de ramas + metabolas), rocas partidas y el arco de costillas |
| `cristal_abisal.py` | El recurso exclusivo de los monstruos |
| `criaturas.py` | Las dos criaturas por piezas; rellena `plantilla_montar_criatura.luau` con los pivotes |
| `pistola_portales.py` | Las dos pistolas de portales en studs, con atlas compartido por pistola; rellena `plantilla_montar_pistola.luau` |
| `hoja_conjunto.py` | Hoja con todos los modelos (recorta la vista 3/4 de cada hoja final) |
| `verificar_fbx.py` | Reimporta un FBX y muestra mallas, triángulos, tamaño, UV, texturas y huesos |
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

### Ciudad humana

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Se leen bien tienda, toldo, persiana y farola, pero los edificios grandes salen a oscuras (las luces del estudio estaban a la escala de la nave), la suciedad hace manchas de camuflaje y la persiana es casi negra | — |
| 2 | Bien iluminados. Los muros laterales de la tienda son paños lisos y los balcones del residencial apenas se ven | Luces del estudio que se alejan y ganan potencia con el tamaño del modelo, suciedad más fina y suave, persiana más clara, menos ventanas encendidas |
| 3 | Más vida, pero la banda de color no salía en el muro izquierdo de la tienda (fallo de coordenadas) y la torre no tiene ningún color propio | Banda cian y bajante en la tienda, balcones más profundos con jardinera, aletas cian en la fachada, dos ventanas laterales por planta |
| 4 | Primera a calidad completa: todo se lee. Las ventanas encendidas son paños planos enteros | Banda bien colocada, esquinas naranjas en el basamento de la torre |
| 5 (final) | — | Ventanas encendidas a medias (cortina) y una vista con la persiana subida para comprobar que se abre |

### Hangar

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Planta, muros, grúa y forja en su sitio, pero la plataforma era un disco blanco entero (las tapas del anillo de neón lo rellenaban) | — |
| 2 | Plataforma bien. El interior está vacío y desde fuera es una caja | Anillo de neón como cinta sin tapas, pasarela con barandilla y escalera en el muro del fondo |
| 3 | Por fuera ya se reconoce. La forja no tenía punto de interés | Franja naranja exterior, tiras de luz en los pilares, núcleo de energía en el anillo de la forja y conductos |
| 4 | Funciona a calidad completa. La entrada queda desnuda | — |
| 5 (final) | — | Bolardos a franjas con luz en la entrada |

### Planeta de los monstruos

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Al árbol retorcido le faltaba el tronco (el modificador Skin falla con muchas ramas en un nodo), las raíces eran pétalos gordos, todo salía negro y el núcleo de la aguja era más grande que la roca | — |
| 2 | Árboles completos y rocas con grietas que brillan bien. Siguen negros; la aguja tenía un trozo suelto flotando y el tocón era un cono | Metabolas en cápsula en lugar de Skin, raíces finas que acaban en punta, núcleo = la propia roca encogida, paletas más claras |
| 3 | Rocas y arco bien. Los árboles, todavía negros | Tocón partido en astillas, árbol colgante más caído, aguja sin trozo suelto, costillas más gruesas |
| 4 | Corteza visible por fin (el ruido de vetas no estaba normalizado y casi todo era «grieta»; además las ramas finas se perdían al hornear) | Vetas normalizadas por percentiles, más alcance del rayo al hornear, árboles con 2.200 triángulos |
| 5 (final) | — | Dos ojos rasgados que brillan en el tronco del árbol retorcido (colocados con un rayo contra la corteza) y las setas por debajo |

### Cristal abisal

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Obsidiana opaca: solo brillan las puntas y parece carbón | — |
| 2 | Con la obsidiana translúcida se ve el corazón morado: ya se lee. Demasiado violeta claro y la base es pequeña | Obsidiana translúcida (Glass en Studio) |
| 3 | Mejor asentado | Obsidiana más oscura, base más grande, cristalitos medio enterrados alrededor |
| 4 | Bien a calidad completa. Las grietas brillantes de la base quedaban enterradas en la roca | — |
| 5 (final) | — | Grietas que siguen la superficie de la roca (rayos hacia abajo) y corazón más grueso y brillante |

### Criaturas

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Las dos se leen. El brincador parece un conejo de plastilina con las orejas rosas de punta; el acechador es negro y las mandíbulas no se ven | — |
| 2 | Orejas caídas, más tierno. El acechador sigue oscuro | Orejas de belier, lana menos abultada, cabeza del acechador levantada, mandíbulas grandes, púas más altas |
| 3 | Brincador con cabeza y ojos grandes | Cabeza y ojos más grandes, mechones más suaves, caparazón más claro |
| 4 | El acechador tiene por fin un dibujo reconocible. Sus púas parecían dedos y el brincador seguía con bultos | Bandas violetas en el abdomen |
| 5 (final) | Queda algo de relieve de plastilina en el brincador (la lana con metabolas) | Púas en dos tramos (afiladas), cuerpo del brincador suavizado y lana más fina |
