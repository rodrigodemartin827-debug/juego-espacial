# Dragón Leviatán (boss final)

El depredador supremo del cosmos: horror cósmico con forma de reptil, de 50 × 65 × 35 studs (envergadura × largo ×
alto), en pose de combate agazapada con las alas abiertas al 70 %. Todo sale de scripts de Python en Blender sin
pantalla (`modelos/herramientas/dragon_*.py`) y se puede regenerar.

| Archivo | Qué es |
| --- | --- |
| `dragon_leviatan.fbx` | Las 25 piezas del rig + 5 cubos de los puntos de montaje. Texturas incrustadas |
| `dragon_leviatan_color.png` | Atlas de color 4096 × 4096 (con la oclusión ambiental multiplicada) |
| `dragon_leviatan_normal.png` | Normales en espacio tangente (escamas, cicatrices, venas, grietas) |
| `dragon_leviatan_roughness.png` | Rugosidad |
| `dragon_leviatan_metalness.png` | Metal: 0 en lo orgánico, 0,8–0,9 en los fragmentos de nave, arpones y cadenas |
| `dragon_leviatan_emision.png` | Emisión: ojos, garganta, grietas volcánicas (#FF4500 / #FF2200) |
| `dragon_leviatan_turnaround.png` | 8 vistas con texturas finales y un jugador R6 (gris) para la escala |
| `dragon_leviatan.json` | Triángulos, tamaño, piezas con pivote y padre, puntos de montaje y la verificación del FBX |
| `montar_dragon_leviatan.luau` | Script de la barra de comandos que monta el rig en Studio |
| `proceso/` | Todas las rondas de revisión (arcilla, piezas por colores, silueta, texturas) |

## Importar en Studio

1. **Avatar → Import 3D** y elige `dragon_leviatan.fbx`. Deja **Scale Unit = Meter** (el FBX está en metros con
   1 stud = 0,28 m, como el resto de modelos del repositorio) e **Import only as model**.
2. Si el importador no crea la `SurfaceAppearance`, créala en cada `MeshPart` con `ColorMap`, `NormalMap`,
   `RoughnessMap` y `MetalnessMap` (las 25 piezas comparten el mismo atlas).
3. Emisión: si tu versión de Studio tiene emisión en `SurfaceAppearance`, usa `dragon_leviatan_emision.png` como
   máscara (tinte `#FF4500`). Si no, la `Cresta_Dorsal` puede ir con **Material = Neon** y los ojos/garganta se
   quedan con el brillo pintado en el color.
4. Selecciona el modelo importado y pega `montar_dragon_leviatan.luau` en la barra de comandos: crea el `Model`
   con el Torso como `PrimaryPart`, los 24 `Motor6D` en cadena (cada pieza con su padre y el pivote en la
   articulación) y convierte los 5 cubos de montaje en `Attachment`.

**Comprueba que mira a −Z** (la cabeza hacia el `LookVector`). Se exporta con `GIRO_IMPORTACION = 180°` alrededor
del eje vertical y los ejes por defecto del FBX de Blender; si en tu importador sale al revés, cambia esa constante
en `modelos/herramientas/dragon_leviatan.py` y vuelve a exportar.

## Rig (25 piezas, Motor6D)

Cada pieza es rígida, con rotación 0,0,0 y el origen en su articulación. Entre piezas hay 0,02 studs de hueco.

`Torso` (raíz) → `Cuello_Base` → `Cuello_Medio` → `Cuello_Superior` → `Cabeza` → `Mandibula`;
`Cabeza` → `Cornamenta`; `Torso` → `Cresta_Dorsal`;
`Torso` → `Ala_X_Hombro` → `Ala_X_Antebrazo` → `Ala_X_Mano`;
`Torso` → `Pata_Del_X_Muslo` → `Pata_Del_X_Garra`; `Torso` → `Pata_Tras_X_Muslo` → `Pata_Tras_X_Tibia`;
`Torso` → `Cola_Base` → `Cola_Media` → `Cola_Punta`.

Los pivotes exactos (en coordenadas de Roblox) están en el JSON. Puntos de montaje (solo para la cría del 3 %):
`Montura_Cria_Piloto`, `Montura_Cria_Pasajero`, `Agarre_Cuello_Izq/Der` y `Punto_Aliento` (dentro de la boca, de
donde sale el aliento).

## Regenerar

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/herramientas/requirements.txt scikit-image scipy
```

```bash
.venv/bin/python modelos/herramientas/dragon_mallas.py --cache bestias/dragon_leviatan/_cache
```

```bash
.venv/bin/python modelos/herramientas/dragon_leviatan.py --cache bestias/dragon_leviatan/_cache --salida bestias/dragon_leviatan --fase todo --ronda 9
```

`dragon_mallas.py` malla el cuerpo por campos de distancia (~25 min con 4 núcleos); `--rapido` lo hace a baja
resolución en ~8 min. `--fase previa` en el segundo script monta y renderiza en arcilla sin hornear (2 min).

| Script | Para qué |
| --- | --- |
| `dragon_anatomia.py` | **Medidas y posiciones**: articulaciones, pose y masas musculares |
| `dragon_sdf.py` | Primitivas de campo de distancia, ruido y mallado (marching cubes por bloques) |
| `dragon_cuerpo.py` | Cuerpo completo con el detalle tallado, reparto en piezas y pintura de la piel |
| `dragon_items.py` | Generadores de piezas duras: dientes, garras, cuernos, placas, cadenas, metal, ojos... |
| `dragon_montaje.py` | Coloca el detalle duro, las membranas de las alas, la cresta y la cornamenta |
| `dragon_mallas.py` | Malla las piezas del cuerpo (alta y baja) en una caché |
| `dragon_leviatan.py` | Montaje en Blender, UV del atlas, horneado, renders, FBX, JSON y script de montaje |
