# Planeta Monstruo: modelos 3D

--TOTAL-- modelos del hogar de los monstruos (--TRIS-- triángulos en total): guaridas, vegetación, las bestias
cósmicas que hacen de naves, la zona de guerra, props y terreno. Todo es biología, hueso, cristal y carne; nada de
metal ni tecnología.

Están generados con scripts de Python en Blender sin pantalla (`bpy`): no hay nada hecho a mano y todo se puede
regenerar desde `modelos/herramientas/planeta_monstruo/`.

**Estado: sin probar en Roblox Studio.** Cada FBX se ha reimportado en Blender y se ha comprobado (piezas,
triángulos, tamaño, normales hacia fuera y UV), pero ninguno se ha importado todavía en Studio. Hasta que el
director los vea en Studio con capturas, no están dados por buenos.

## Qué hay en cada carpeta

`<nombre>/` contiene:

| Archivo | Qué es |
| --- | --- |
| `<nombre>.fbx` | El modelo, con una malla por pieza. 1 unidad = 1 stud. |
| `<nombre>_color.png` | Atlas 1024 de color (con la oclusión ambiental ya metida). |
| `<nombre>_normal.png` | Normales (espacio tangente, formato OpenGL, Y+). |
| `<nombre>_roughness.png` · `<nombre>_metalness.png` | Rugosidad y metal, en gris. |
| `<nombre>_emision.png` | Emisión. Solo si el modelo tiene partes que brillan. |
| `<nombre>_turnaround.png` | 6 vistas: frente, 3/4, lateral, 3/4 trasera, arriba y malla. |
| `<nombre>.json` | Triángulos, tamaño en studs, piezas, verificación del FBX y, si las hay, articulaciones y monturas. |
| `montar_<nombre>.luau` | Solo en las bestias: script para la barra de comandos que las monta con Motor6D y asientos. |

Todas las piezas de un modelo comparten el mismo atlas.

## Convenciones

- **Escala:** 1 unidad de Blender = 1 stud, exportado con *Apply Scalings: FBX All*. Si en Studio un modelo sale
  3,57 veces más grande o más pequeño, es la unidad del importador: en *File General → Scale Unit* elige **Stud**.
- **Giro de importación:** los modelos se exportan ya girados 180° sobre la vertical: en el archivo FBX el frente
  mira a +Z y, como el importador de Studio gira las mallas 180° (ver `MontarRegion.GIRO_IMPORTACION`), en Studio
  quedan mirando a -Z, el «delante» de Roblox. Las posiciones de los JSON (centros, pivotes, monturas) están en
  studs, relativas al origen del modelo y en los ejes del archivo FBX. Los scripts de montaje de las bestias
  averiguan solos cómo ha quedado girado el modelo, así que funcionan aunque Studio no lo gire o lo gires tú.
- **Origen:** el centro de la base. En lo que cuelga (lianas, capullos, nido aéreo, baba, amuleto, enredadera), el
  centro de arriba. En lo que flota (esporas, roca e isla flotantes), el centro. Lo dice el campo `origen` del JSON.
- **Piezas que brillan:** van en mallas aparte con sufijo `_neon` o `_biolum`: ponles `Material = Neon` y el color
  que indica `roblox.color` en el JSON (violeta `#C04DFF`, verde `#39FF14`...). Las `_cristal` son translúcidas:
  `Material = Glass` y la transparencia de `roblox.transparencia`. El resto lleva `SurfaceAppearance` con los cuatro
  mapas (`ColorMap`, `NormalMap`, `RoughnessMap`, `MetalnessMap`).
- **Todo tiene volumen:** no hay planos sueltos. Membranas, banderas, pétalos, telarañas e hilos tienen grosor.
- **Presupuesto de triángulos:** estructuras grandes 15.000, medianas 8.000, props 2.000, vegetación 4.000, bestias
  20.000 y crías 8.000. El campo `presupuesto_triangulos` de cada JSON dice cuál le toca.

## Bestias cósmicas

Las «naves» de los monstruos. Van por piezas rígidas (cabeza, cuerpo, alas o patas, cola...), sin huesos ni
deformación, igual que los enemigos R6.

1. Importa el FBX, selecciona el modelo importado y pega `montar_<nombre>.luau` en la barra de comandos.
2. El script junta las piezas en un `Model`, une cada pieza móvil a su padre con un `Motor6D` en su articulación,
   suelda las demás, crea un `Seat` por punto de montura y añade `AnimationController` + `Animator`.
3. En el JSON: `articulaciones` (pieza, padre y pivote), `puntos_montura` (posición y hacia dónde mira cada asiento)
   y, en las grandes (ballena, gusano, hidra), `bahia_carga`.

Los asientos tienen su silla modelada en el lomo, así que el punto de montura se ve en el propio modelo.

## Modelos con partes móviles que no son bestias

`puerta_mandibula`, `jaula_prisioneros`, `corral_bestias`, `catapulta_organica`, `cofre_organico` y
`campana_resonancia` llevan la parte móvil en una malla aparte y su pivote en `articulaciones`. `arbol_tentaculo`
lleva tres poses de los tentáculos (`tentaculos_pose_a/b/c`): se muestra una cada vez.

## Regenerar

```bash
pip install bpy scikit-image scipy pillow numpy
```

```bash
python modelos/herramientas/planeta_monstruo/ejecutar.py --ronda 1 -j 4
```

```bash
python modelos/herramientas/planeta_monstruo/ejecutar.py bestia_dragon
```

```bash
python modelos/herramientas/planeta_monstruo/indice.py
```

`lib.py` es la cadena completa (modelado por volumen, materiales procedurales, horneado, turnaround, FBX,
verificación y JSON); `ronda_XX.py` son los modelos, diez por archivo; `formas.py`, las formas que se repiten
(cráneos, huesos, setas, sillas), que se generan de nuevo en cada modelo con sus propias proporciones.
