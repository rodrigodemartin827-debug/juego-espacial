# Armas y herramientas

Catálogo de armas de «Humanos vs Monstruos», generado con `modelos/herramientas/armas.py` (Blender sin pantalla,
`bpy`). Nada está hecho a mano: cada arma es una función con sus medidas en studs arriba del todo y se puede
regenerar.

**Estado:** están las armas **#1 a #12** del catálogo. El encargo original se cortaba en mitad de la #12 (Revólver
Estelar: «Mira frontal: post elevado con punto lum…»), así que **faltan las especificaciones de las armas #13 a
#26** para poder modelarlas.

| # | Arma | Archivo | Rareza | Triángulos (máx.) | Piezas |
| --- | --- | --- | --- | --- | --- |
| 1 | Espada de Plasma | `espada_plasma.fbx` | Común | 1.854 (2.500) | Hoja, Guarda, Empunadura, Pomo, Neon_01 |
| 2 | Hoja de Cristal | `hoja_cristal.fbx` | Poco común | ~2.200 (3.000) | Hoja, Vetas, Guarda, Empunadura, Gema, Neon_01–02 |
| 3 | Sable Gravitacional | `sable_gravitacional.fbx` | Raro | ~3.700 (4.000) | Hoja, Guarda, Empunadura, Anillo_01–03, Neon_01–03 |
| 4 | Espada Estelar | `espada_estelar.fbx` | Legendario | ~3.700 (6.500) | Hoja, Guarda, Empunadura, Pomo, Fragmento_01–06, Neon_01–05 |
| 5 | Hoja del Vacío | `hoja_vacio.fbx` | Mítico | ~4.500 (8.000) | Hoja, Aura, Garra_Izq/Der, Orbe, Empunadura, Ojo, Fragmento_01–08, Neon_01–03 |
| 6 | Hacha de Meteorito | `hacha_meteorito.fbx` | Poco común | ~2.000 (3.000) | Cabeza, Roca, Mango, Anillos, Neon_01 |
| 7 | Martillo de Pulsar | `martillo_pulsar.fbx` | Épico | ~3.300 (5.000) | Cabeza, Punta, Nucleo, Conductos, Mango, Grip, Contrapeso, Neon_01–03 |
| 8 | Guadaña Nebular | `guadana_nebular.fbx` | Legendario | ~3.200 (6.500) | Hoja, Wisps, Anillo, Puas, Mango, Runas, Gema, Neon_01–03 |
| 9 | Pistola de Plasma | `pistola_plasma.fbx` | Común | 1.852 (2.500) | Cuerpo, Canon, Gatillo, Grip, Celda, Neon_01–02 |
| 10 | Láser de Precisión | `laser_precision.fbx` | Raro | 2.616 (4.000) | Cuerpo, Canon, Mira, Cristal, Grip, Estabilizador, Neon_01–03 |
| 11 | Blaster de Iones | `blaster_iones.fbx` | Poco común | 2.036 (3.000) | Cuerpo, Canon_Izq/Der, Grip, Cargador, Neon_01–02 |
| 12 | Revólver Estelar | `revolver_estelar.fbx` | Épico | ~3.500 (5.000) | Cuerpo, Canon, Tambor, Martillo, Grip, Gatillo, Detalle_01, Neon_01–03 |

Las cifras exactas de cada versión están en `<arma>.json` (`triangulos`) y en la cabecera de cada hoja de `rondas/`.
Todas las piezas llevan el prefijo del arma (`EspadaPlasma_Hoja`...), sin acentos ni ñ.

## Qué hay en la carpeta

| Archivo | Para qué |
| --- | --- |
| `<arma>.fbx` | El modelo: todas las piezas (cuerpo + neón) y los Empty `Handle` (y `Handle_Frontal` en las de dos manos) |
| `<arma>.json` | Rareza, triángulos, texturas, cada pieza con su rol y su centro, y los agarres en ejes de Roblox |
| `montar/<arma>.luau` | Script de la barra de comandos que convierte el modelo importado en un `Tool` listo (ver abajo) |
| `texturas/<Arma>_color.png` | Albedo con oclusión ambiental (con alfa en las armas que tienen piezas translúcidas) |
| `texturas/<Arma>_normal.png` | Normales en espacio tangente (grip diamantado, cuero, madera, hierro meteorítico, grabados...) |
| `texturas/<Arma>_roughness.png` | Rugosidad (metal pulido ~0,15, grips ~0,7, cristal ~0,05) |
| `texturas/<Arma>_metalness.png` | Metalicidad (hojas y cañones 1; cuero, madera, hueso y cristal 0) |
| `texturas/<Arma>_emision.png` | Máscara: blanco donde va una pieza `_Neon` encima (Roblox no tiene mapa de emisión) |
| `rondas/<arma>_ronda_N.jpg` | Turnaround de cada ronda de revisión |

Las **4 texturas son un atlas compartido** por todas las piezas con textura de un arma: todas usan la misma
`SurfaceAppearance`. Tamaño según la rareza: 1024² para Común y Poco común, 2048² de Raro para arriba.

## Medidas y ejes

- Se modela en **studs** (1 unidad del script = 1 stud) y se exporta en metros con 1 stud = 0,28 m, que es lo que
  lee el importador de Roblox: con *Scale Unit = Meter* llegan a Studio con su tamaño en studs. Es la misma
  convención que el resto de `modelos/`.
- **Giro de importación.** No se gira 180° a mano: la exportación de `armas_kit.py` convierte los ejes igual que el
  resto de modelos del juego (Blender `(x, y, z)` → Roblox `(-x, z, y)`). Si al importar un arma sale al revés,
  se corrige ahí (`axis_forward`) para todas.
- Cuerpo a cuerpo: la hoja apunta hacia arriba (+Y en Roblox) y el `Handle` está en el centro de la empuñadura con
  su eje Y hacia la hoja. Armas de fuego: el cañón mira al frente (-Z en Roblox) y el `Handle` está en el grip con
  el eje Y hacia la boca. En las de dos manos, `Handle` es la mano de abajo y `Handle_Frontal` la de arriba.
- La vista «Escala R6» de cada hoja pone un brazo R6 (1 × 2 × 1 studs, translúcido) con la mano en el `Handle`,
  para comprobar las proporciones.

## Importar y montar en Studio

1. **Import 3D** con el `.fbx`: *Scale Unit = Meter*, *Anchored* desactivado e *Import only as model*.
2. Sube las texturas de `texturas/<Arma>_*.png` (Asset Manager → Bulk Import) y pega los IDs en la tabla
   `TEXTURAS` al principio de `montar/<arma>.luau`. Si el importador ya creó la `SurfaceAppearance`, se puede
   dejar vacía.
3. Selecciona el modelo importado y pega `montar/<arma>.luau` en la barra de comandos. El script:
   - crea un `Tool` con un `Handle` invisible en el punto de agarre (eje Y hacia la hoja o el cañón),
   - suelda todas las piezas con `WeldConstraint` (sin colisión, `Massless`),
   - pone **Material = Neon** y el color en las piezas `_Neon` (cian `#3DF2FF`; la Hoja del Vacío usa sus rojos),
   - pone **Glass** en las piezas de cristal (celda, núcleo, cristal de la mira) con su transparencia,
   - pone `AlphaMode = Transparency` en las armas con piezas translúcidas (Hoja de Cristal, aura del Vacío,
     fragmentos de la Estelar, jirones de la Guadaña), y
   - en las de dos manos, añade el Attachment `ManoIzquierda` en el agarre frontal.

**Lo que hay que comprobar en Studio** (esta sesión no tiene Studio; nada está probado allí todavía):

- Que el arma sale en la mano y apuntando hacia delante; si no, ajustar `Tool.Grip`.
- Que el importador crea la `SurfaceAppearance` y que las texturas se ven bien en el atlas compartido.
- El tamaño del neón en móvil (las piezas `_Neon` son mallas pequeñas: no deberían pesar).
- Rareza Épica o superior: la tabla pide partículas y aura. Eso no es geometría: el JSON del Martillo de Pulsar y
  del Revólver Estelar lo anota para añadir un `ParticleEmitter` en Studio (reutilizado, pocas partículas).
- Piezas que se animan: los anillos del Sable Gravitacional y los fragmentos de la Estelar y del Vacío van sueltos
  para animarlos, pero su brillo (`Neon_03`, `Neon_04`) es una pieza común como pide el catálogo: al animarlos hay
  que mover también el neón o separarlo por anillo.

## Decisiones donde el catálogo se contradecía

- **Espada Estelar, canal «naranja incandescente → blanco».** La regla del juego es que todo el neón es cian salvo
  la Hoja del Vacío. El canal lleva la lava naranja en la **textura** y el núcleo de neón (`Neon_01`) es cian y más
  estrecho, así se ven las dos cosas.
- **Guadaña Nebular, `Neon_01` = «hoja entera».** Si toda la hoja fuera Neon, la textura de nebulosa púrpura-cian no
  se vería (el Neon de Roblox es un color plano). `Neon_01` es el filo que brilla en las dos caras; la nebulosa
  está en la textura.
- **Revólver Estelar.** La descripción llegaba cortada: las piezas siguen la convención de las demás
  (`Cuerpo`, `Canon`, `Tambor`, `Martillo`, `Grip`, `Gatillo`, `Detalle_01` para el hueso, `Neon_01` cámaras,
  `Neon_02` punto de la mira, `Neon_03` líneas del cañón).
- **FBX.** Se exporta FBX binario 7.4 (el exportador de Blender); Roblox lo lee igual que el 2020.

## Regenerar

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/herramientas/requirements.txt
.venv/bin/python modelos/herramientas/armas.py --salida modelos/armas --ronda 3
.venv/bin/python modelos/herramientas/armas.py --salida modelos/armas --ronda 3 --solo espada_plasma,hoja_vacio
.venv/bin/python modelos/herramientas/armas.py --salida modelos/armas --ronda prueba --rapido   # segundos por arma
```

Las 12 armas tardan ~16 minutos con 4 núcleos. `armas_kit.py` tiene las formas (barrido de hojas con sección a
medida, tubos huecos, bandas, perfiles), los materiales con patrón de relieve, el horneado del atlas, la exportación
y el turnaround; `plantilla_montar_arma.luau` es la plantilla del script de montaje.

## Rondas de revisión

En cada ronda se renderiza el turnaround (frente, perfil derecho, trasera, perfil izquierdo, 3/4, malla y escala
R6), se revisa como director de arte y se corrige el script. La ronda 0 es en modo rápido.

| Arma | Ronda 0 → 1 | Ronda 1 → 2 |
| --- | --- | --- |
| Espada de Plasma | Los metales salían negros: el color se horneaba con la pasada difusa, que en un metal es negra. Se pasó a hornear el color base por emisión (afecta a todas) y se aclaró el estudio | Guarda más clara: se perdía contra el mango negro |
| Hoja de Cristal | Las vetas eran barras rectas pegadas que parecían neón: pasan a fracturas en zigzag que cambian de dirección, cristal más vivo y gema más grande | Vetas blancas más altas (no se veían) y guarda en C más gruesa y clara |
| Sable Gravitacional | Superaba el límite (4.534 de 4.000): menos lados en conductos y anillos y bisel solo en las aristas vivas (3.686) | Hoja menos negra y con más relieve de «metal derretido», y más ensanchada hacia la punta (falchion) |
| Espada Estelar | El oro salía marrón y los fragmentos eran diminutos: fragmentos del doble, más separados, y un sol de 8 rayos en la guarda para que se reconozca de lejos | Las vetas naranjas parecían cañas de bambú: el oro pasa a manchas suaves y los fragmentos a dorado intenso |
| Hoja del Vacío | El aura no se veía y los fragmentos eran puntos: aura más ancha con borde de humo y fragmentos más grandes | Ojo del pomo más grande (iris y pupila se leen desde el frente) |
| Hacha de Meteorito | Las rocas eran bloques negros: rocas más grandes y subdivididas, con manchas naranjas y vetas que brillan en las juntas | Las grietas de neón eran rayas rectas: pasan a zigzag |
| Martillo de Pulsar | El núcleo era un disco gris opaco: cilindro de vidrio con la esfera de neón dentro y un anillo orbital | Blindaje más claro para que se lean los paneles |
| Guadaña Nebular | La hoja era casi toda cian y los jirones parecían púas grises: degradado púrpura → cian con nubes, y jirones planos en S | Jirones más blancos y opacos |
| Pistola de Plasma | Todo salía negro: gunmetal más claro | — (correcta; solo hereda los cambios comunes) |
| Láser de Precisión | Bien desde la primera: se mantiene | — |
| Blaster de Iones | Cuerpo negro: carrocería y acentos más claros | — |
| Revólver Estelar | El martillo flotaba suelto y el hueso parecía una bola: martillo pegado al armazón con estrías | El hueso era un borrón blanco: placa ovalada encastrada con una estrella de oro; estrías del tambor más hondas |

Pendiente para una ronda 3 (no bloquea): en las hojas el oro y los metales oscuros se ven apagados porque el estudio
es gris uniforme; un entorno con degradado los haría brillar más en las capturas (en Roblox reflejan el cielo).
