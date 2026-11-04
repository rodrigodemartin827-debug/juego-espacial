# Región 1 · Valle del Alba (planeta humano Nueva Tierra)

La región inicial del planeta humano, hecha en Blender **para revisar el diseño con renders**. Es la región más
tranquila: praderas, un río que cruza el valle, bosques suaves, colinas y una colina con vistas al atardecer. Tiene
tres sitios: **Pradoverde** (el pueblo inicial), **Aurora** (la capital) y **Los Molinos**.

> **Todavía no se ha exportado a Roblox ni se ha visto en Studio** (lo pediste así: primero revisar el diseño). Todo
> lo de esta carpeta sale de scripts de Python que usan `bpy` sin pantalla, así que se puede cambiar y regenerar.

![Hoja de contactos](renders/hoja_de_contactos.png)

## Dónde está y cómo se apoya en el planeta de prueba

- Usa la geometría de `modelos/planeta_prueba` (rama `feat/planeta-prueba`, PR #15): una esfera de **radio 2400
  studs** partida como un cubo inflado con reparto de ángulos iguales. La región 1 es la cara **YP** (la normal +Y
  de Roblox, que en Blender es +Z). La cara mide unos **3.770 × 3.770 studs** sobre la esfera.
- El relieve de la región es una **función** (`herramientas/relieve.py`), igual que en el planeta de prueba: cualquier
  malla (la de los renders o la de los trozos para Roblox) pide la altura a la función y sale el mismo terreno.
- **Empalme con el resto del planeta:** en los últimos 420 studs de la cara el valle se funde con el relieve del
  planeta de prueba (copiado tal cual en `herramientas/terreno_base.py`), con derivada nula en el borde: no hay
  costura con las caras vecinas.
- **Decisión que tienes que validar:** en el planeta de prueba la cara YP es casi toda mar (33 % de tierra). Por eso
  el valle está rodeado por una sierra de colinas y, al otro lado de la sierra, el terreno pasa al relieve del
  planeta de prueba, con su costa y su mar. Queda un valle cerrado con mar alrededor, con tierra hacia el oeste
  (por donde sale el camino a la región vecina) y hacia el sur. Cuando se diseñen las otras regiones habrá que
  decidir si se cambia el relieve de base del planeta.

## Contenido

| | Qué hay |
| --- | --- |
| **Terreno** | Praderas onduladas (dos capas de ruido suave), sierra de colinas alrededor del valle con pasos para el río y los caminos, 8 colinas sueltas y la **colina del atardecer** (88 studs). Sin escalones: la mediana de la pendiente en tierra es de 9° |
| **Río** | Nace en una charca entre las colinas del norte, cruza el valle con meandros (de 14 a 48 studs de ancho) y sale al mar por un paso de la sierra en el suroeste. Su nivel baja de 52 a 0 studs. Cauce parabólico y orillas en talud unidas al terreno con un mínimo suave |
| **Pradoverde** (120 × 120) | Al pie de la colina del atardecer. Prado central con pozo, **tablón de misiones** de cara a quien llega por el camino, poste indicador, la **casa del jugador** (puerta y contraventanas azules, jardín vallado con cerezo y banco), la **tienda** del pueblo y 7 casas rústicas con entramado de madera, huertos, pajar, carro y farolas |
| **Aurora** (400 × 400) | Capital en retícula: **plaza mayor** de 88 × 88 con **fuente** de dos tazas, bancos, cerezos, farolas, mercado de puestos y **tablón de misiones**; **ayuntamiento** (portada de columnas, balcón, frontón con reloj, banderas) al norte; **torre del reloj** de 92 studs en la esquina noreste; **6 tiendas** en la plaza (general, armería, materiales, pociones, taller de naves y panadería), cada una con escaparate, toldo y cartel con emblema; calle mayor, avenidas, calles secundarias y ronda; 72 edificios de tejado rojo; portales en las cuatro entradas y jardines arbolados |
| **Los Molinos** (120 × 120) | **3 molinos** de viento (torre encalada, caperuza roja, aspas de celosía mirando al suroeste), era, pozo, tablón de misiones, 4 casas de labor y un granero, pajares, carro; alrededor, **42 parcelas** de trigo, coles, lavanda, calabazas, tierra arada y barbecho, con hileras de cultivo en 3D y espantapájaros |
| **Caminos** | Aurora → **puente** → cruce (con poste indicador) → Pradoverde; cruce → Los Molinos; sendero de Pradoverde al mirador; salidas hacia las regiones del oeste y del sur. Cada camino tiene un perfil suavizado (sin cuestas bruscas ni inclinación lateral) y sube en «lomo de asno» al cruzar el río |
| **Puente** | Puente de piedra de 83 studs y tres ojos, con tajamares, dovelas, pretiles y farolas |
| **Mirador** | Un **balcón natural** (terraza llana) a media ladera de la colina del atardecer, mirando al oeste, con bancos, un árbol grande, murete, farola y poste. Ver «Qué ha enseñado» |
| **Vegetación** | 15.609 árboles (frondosos, pinos, abedules), 2.189 arbustos y 621 rocas instanciados con Geometry Nodes, más 20.837 matas de hierba y flores alrededor de los sitios. Bosques con forma orgánica, con claros, sobre la sierra y en manchas por el valle; sotos a lo largo del río |

## El kit de construcción

![Hoja del kit](renders/kit_hoja_piezas.png)

`kit_valle_del_alba.blend` tiene las 49 piezas ordenadas por categorías (Paredes, Puertas y ventanas, Tejados,
Mobiliario, Campo, Vegetación, Especiales) y 5 edificios de ejemplo montados con ellas. Cada objeto guarda su
categoría, su tamaño en studs y sus triángulos como propiedades.

- **Estilo:** pueblo europeo de cuento, limpio y luminoso. Yeso de colores claros, zócalo y esquinas de sillar,
  tejas rojas por hiladas (cada teja con su tono), contraventanas pintadas, jardineras con flores, farolas de hierro.
  Low-poly con volumen (recercados, alféizares, goterones de las tejas), sin texturas: en Roblox cada material es un
  Color + Material.
- **Medidas** (en `kit.py`, `MEDIDAS`): tramo de pared de 8 studs; pisos de 10 (planta baja de 11); puerta de 4 × 7,4
  (un R6 mide 5); tejado de unos 32°.
- **Convención de las paredes:** ocupan x ∈ [0, 8] a lo largo de la pared, y ∈ [0, 1] hacia dentro (la cara exterior
  mira a −Y) y z ∈ [0, piso]. Así se encadenan en cualquier fachada girándolas 0/90/180/270°.
- **Ranuras de material:** las piezas usan nombres como `PARED`, `TEJA`, `PINTURA`, `PUERTA`, `TOLDO_A`, `PIEDRA`,
  `MARCO`; cada edificio elige una variante (`materiales.py`, `VARIANTES`). Con las mismas piezas salen casas de seis
  colores de yeso, tres tonos de teja, cuatro de contraventana...
- **Montaje** (`edificios.py`): un edificio se pide con módulos de ancho y fondo, pisos, tipo (`casa`, `rustica`,
  `tienda`, `ayuntamiento`) y una semilla, y se monta con las piezas: paredes con puerta, ventana o escaparate,
  zócalo, cornisas, sillares de esquina, tejado por tramos con remates, hastiales y cumbrera, y chimeneas.

## Renders

Todos en `renders/`, a 1920 × 1080 con Cycles. El mar, el resto del planeta y el planeta de los monstruos son de
referencia (colección `Referencia_no_exportar`).

| Archivo | Vista |
| --- | --- |
| `00_planeta_region.png` | La región sobre el planeta, desde 2.300 studs de altura |
| `01_region_aerea.png` | La región entera desde el aire, desde el sur |
| `02_region_cenital.png` | Vista cenital (sirve de mapa) |
| `03_aurora_aerea.png` · `04_aurora_plaza_suelo.png` · `05_aurora_calle_mayor.png` | Aurora desde el aire, la plaza mayor y la calle mayor a la altura de una persona |
| `06_pradoverde_aerea.png` · `07_pradoverde_suelo.png` | Pradoverde desde el aire y desde el camino de llegada |
| `08_molinos_aerea.png` · `09_molinos_suelo.png` | Los Molinos y sus campos, desde el aire y desde el suelo |
| `10_colina_atardecer.png` | **El plano de la cinemática:** desde el mirador, al atardecer, con Pradoverde debajo y el planeta de los monstruos en el cielo |
| `11_colina_desde_el_prado_atardecer.png` | La colina del atardecer vista desde el prado |
| `12_puente_suelo.png` | El puente desde la orilla |
| `13_valle_desde_colina.png` | El valle por la mañana desde el mirador |
| `kit_hoja_piezas.png` · `hoja_de_contactos.png` | Hoja del kit y hoja de contactos |

## Rondas de revisión

Cada ronda se renderizó entera o en parte, se revisó y se corrigió (son 5):

1. **Kit:** salían manchas negras donde había caras coincidentes (sillares de dos cajas solapadas, toldos de doble
   cara): sillares en L de un solo prisma y sin caras duplicadas. Rocas mal formadas. Imagen lavada: exposición y
   contraste nuevos, chorros de la fuente finos y translúcidos.
2. **Región:** el cielo físico de Blender toma +Z del mundo como «arriba», pero en un planeta la vertical cambia
   (18° en la colina): el atardecer salía como un mediodía. Ahora **se gira el planeta entero en cada render** para
   que la vertical del sitio sea +Z. Además: bosques redondos → bosques con forma orgánica, con claros y sobre la
   sierra; menos árboles sueltos «espolvoreados»; molinos a escala 1,5 (no destacaban sobre las casas); puente en
   lomo de asno (salía chato); mar más claro; suelo de la plaza menos blanco.
3. Por debajo del horizonte el cielo físico es negro y en un planeta pequeño se ve (el limbo, los reflejos del mar):
   se rellena con el color del horizonte. Las aspas de los molinos estaban de canto: ahora miran al suroeste. Menos
   rocas en las laderas. Cámaras reencuadradas. Se añade el planeta de los monstruos en el cielo del atardecer.
4. **La colina del atardecer:** desde la cima el propio lomo tapaba el valle (ver abajo). El mirador pasa a ser una
   terraza a media ladera.
5. Cámara del mirador en el borde de la terraza, poste y árbol fuera del primer plano y terraza despejada de hierba.

## Qué ha enseñado (para el diseño del juego)

1. **Con radio 2400, la curvatura manda.** Desde la cima de una colina de 88 studs el horizonte cae 16° y el lomo
   redondeado de la cima tapa todo lo que está más abajo de unos 10°: desde la cima **no se ve el valle**. Por eso el
   mirador es un balcón a media ladera (en la parte cóncava del perfil). Esto vale para cualquier mirador o vista
   lejana del juego: buscar laderas y salientes, no cimas redondas.
2. **Los pueblos «llanos» siguen la esfera.** Aurora mide 400 studs y entre su centro y su borde hay 8 studs de
   flecha; está aplanada a radio constante y cada edificio se apoya en su propia vertical (con gravedad radial,
   correcto). Si la gravedad del juego no fuera radial, habría que hacerlo de otra forma.
3. **Pocos sitios se ven desde otros:** Aurora está a 1.060 studs del mirador y en el render del atardecer solo se
   adivina en el horizonte, a la derecha. Si la cinemática tiene que enseñar la capital, habría que acercarla o
   girar el plano hacia ella.
4. **Entre el horizonte del terreno y el del cielo queda una franja de bruma.** Por la curvatura, desde la ladera el
   suelo se acaba unos 16° por debajo de la horizontal; esa franja es «cielo por debajo del horizonte», que se rellena
   con el color de la bruma. En el juego pasará lo mismo: conviene que la niebla de Roblox (`Atmosphere`) la cubra, o
   poner algo en el horizonte (la sierra, el mar) que la llene.

## Pensando en Roblox (para la exportación, que aún no se ha hecho)

| | Estado / riesgo |
| --- | --- |
| Terreno | En el .blend es **una malla de 2,1 M de triángulos** (cuadros de 3,7 studs) para que los renders tengan detalle. Para Roblox hay que partirla en trozos como el planeta de prueba (cada trozo ≤ 20.000 triángulos): con 8 × 8 trozos por cara salen cuadros de ~7 studs. Lo bueno es que el relieve es una función: se regenera a la resolución que haga falta |
| Textura del terreno | `textura_terreno.png`, 4096 × 4096 (0,9 studs por píxel) para la cara entera. Para Roblox habría que partirla en 16 de 1024 (una por trozo) |
| Edificios | 86 mallas, unos **11.700 triángulos de media** (el ayuntamiento, 20.500). Caben en el límite de 20.000 por malla, pero Aurora suma 0,9 M: habrá que medirlo en móvil y, si hace falta, quitar detalle a las tejas (`MEDIDAS["teja"]`) y a las ventanas o separar el detalle en piezas con LOD |
| Piezas repetidas | Farolas, bancos, árboles, rocas... comparten malla (instancias): en Roblox, un modelo por pieza y copias |
| Interiores | Los edificios son cerrados por dentro (puertas cerradas). Si se puede entrar en la tienda o la casa del jugador, hay que hacer interiores |
| Colisión | Sin probar. Las tejas y las ventanas son detalle visual: en Roblox convendría colisión de caja por edificio |

## Archivos

| Archivo | Qué es |
| --- | --- |
| `region1_valle_del_alba.blend` | La escena entera (56 MB, comprimido). Colecciones: `Region1_Valle_del_Alba` → `Terreno`, `Agua`, `Aurora`, `Pradoverde`, `LosMolinos` (cada uno con `_Edificios` y `_Mobiliario`), `Campos`, `Caminos_Puente_Mirador`, `Vegetacion` (con las fuentes de las instancias, ocultas); y aparte `Referencia_no_exportar` (resto del planeta y mar) |
| `kit_valle_del_alba.blend` | El kit: todas las piezas y los edificios de ejemplo |
| `textura_terreno.png` | Textura de color del terreno (la usa el .blend con ruta relativa) |
| `renders/` | Los renders, la hoja del kit y la hoja de contactos |
| `herramientas/geo.py` | Cubo-esfera, coordenadas de diseño y marcos locales |
| `herramientas/diseno.py` | **Todos los datos ajustables**: sitios, río, caminos, colinas, bosques, mirador |
| `herramientas/relieve.py` | El relieve del valle (numpy) |
| `herramientas/terreno_base.py` | Copia del relieve del planeta de prueba (para el empalme) |
| `herramientas/textura.py` | Pinta la textura del terreno |
| `herramientas/malla.py` | Mallas low-poly en Python (primitivas, unión, paso a Blender) |
| `herramientas/materiales.py` | Paleta, ranuras de material, niebla y luces encendidas |
| `herramientas/kit.py` · `edificios.py` | Las piezas del kit y el montaje de edificios |
| `herramientas/pueblos.py` | El trazado de Aurora, Pradoverde y Los Molinos |
| `herramientas/region.py` | Construye la escena y guarda el .blend |
| `herramientas/escena.py` · `render.py` · `contactos.py` | Cielo, sol y cámaras; las vistas; la hoja de contactos |
| `herramientas/kit_blend.py` | Construye el .blend del kit y su hoja |

## Regenerar

Requiere Python 3.13 y `herramientas/requirements.txt` (`bpy` 5.2.3, `numpy`, `scipy`, `pillow`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/region1_valle_del_alba/herramientas/requirements.txt
H=modelos/region1_valle_del_alba/herramientas
.venv/bin/python $H/kit_blend.py --salida modelos/region1_valle_del_alba           # kit + hoja (~5 min)
.venv/bin/python $H/region.py --salida modelos/region1_valle_del_alba              # escena (~11 min; la textura tarda 9)
.venv/bin/python $H/region.py --salida modelos/region1_valle_del_alba --reusar-textura   # sin repintar (~2 min)
.venv/bin/python $H/render.py --blend modelos/region1_valle_del_alba/region1_valle_del_alba.blend \
    --salida modelos/region1_valle_del_alba/renders [--vistas 10,13] [--ancho 1920] [--muestras 64]
```

`region.py --rapido` hace una versión de baja resolución en un minuto, para probar cambios de diseño. Los tiempos
son con 4 núcleos de CPU y sin GPU.
