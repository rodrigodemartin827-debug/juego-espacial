# Pistolas de portales

Las dos versiones de la pistola de portales (CLAUDE.md, «Descubrimiento y portales»: es de **después de la v1**).
Solo son los modelos; el código del juego (abrir portales, combustible, tiempo de espera) no está hecho.

| Carpeta | Qué es | Triángulos | Tamaño (studs, ancho × alto × largo) |
| --- | --- | --- | --- |
| `chatarra/` | **Normal**: la fabrica el jugador con restos. Gasta combustible en cada portal | ~3.900 | 0,83 × 1,56 × 2,67 |
| `vip/` | **VIP** (gamepass de 500 Robux): limpia y tecnológica, sin depósito | ~3.900 | 0,66 × 1,45 × 2,41 |

Las dos por debajo de 4.000 triángulos, con **un atlas de 1024** cada una (color, normales, metal y rugosidad).

- `hoja_contactos_5.png`: la hoja final. Arriba la normal y abajo la VIP, con las mismas vistas: frente, los dos
  lados (derecho e izquierdo del que la sostiene), arriba, 3/4 delantera y trasera, en la mano de un muñeco R6 y la malla.
- `comparacion_5.png`: las dos juntas en la misma foto (de lado y en 3/4) y dos muñecos R6, cada uno con la suya.
- `rondas/`: las hojas de las rondas anteriores (las 1, 2 y 4 en modo rápido, con menos resolución).

## Diseño

**Normal («de chatarra»).** Parece montada en un taller con lo que había, pero se lee como un aparato que funciona:

- Un cajón de acero oxidado y abollado con dos chapas desparejadas: verde pintada a la izquierda (con tornillos
  hexagonales) y galvanizada a la derecha (con remaches).
- Detrás, una **lata azul** atornillada con una brida de seis tornillos y un cordón de soldadura alrededor.
- El cañón es un tubo galvanizado soldado al cajón, con un manguito de latón, una **bobina de cobre** de cuatro
  vueltas y medio, y en la punta una **lata roja abierta** (con pared de verdad) con tres clavos doblados que hacen
  de guía del portal.
- Bajo el cañón, el **depósito de cristal** con el combustible verde brillante, lleno a tres cuartos, con burbujas,
  tapones de latón y azul, dos abrazaderas de chapa con su tornillo, tres varillas de jaula y una manguera de goma
  que sube del tapón al cañón. Se ve entero desde los dos lados y desde delante.
- **Rueda de válvula** roja a la derecha (pieza aparte, para que gire) y **manivela** con mango amarillo a la
  izquierda. Encima, un **manómetro** de latón y una bombilla verde que indica el combustible.
- **Cables sueltos** (rojo, amarillo y negro) que van de la lata al cañón, del manómetro a la boca y de la bombilla
  al depósito, sujetos con una **brida** negra y un trozo de **cinta americana**.
- Empuñadura de tubo envuelta en **cinta americana** (cuatro vueltas torcidas), con una tuerca grande de tapón;
  gatillo de pletina y guardamonte de alambre.

**VIP.** Lo contrario: piezas que encajan, metal pulido oscuro y luz.

- Culata y cabeza de grafito pulido (con ranuras de panel grabadas), con placas blancas encajadas en los costados
  y en la empuñadura.
- En el centro, la **cámara del núcleo**: un hueco abierto entre la culata y la cabeza, cerrado solo por dos raíles,
  dos aros de cromo y cuatro garras, con el **núcleo de energía morado** flotando dentro y una órbita de luz cian.
  No hay depósito: no gasta combustible.
- **Tres anillos que flotan** alrededor del cañón, separados del cuerpo y entre sí, cada vez más pequeños; el del
  medio es violeta. Cada uno tiene tres bloques de cromo en el canto (para que se note el giro) y un aro de luz.
- **Líneas de luz cian** por los costados, por el lomo, por el raíl de la cámara, en la cabeza (una V) y por
  delante de la empuñadura.
- Cañón negro con tres hojas de guía, punta de cromo y disco emisor de luz.

Ninguna copia una pistola existente: la normal es un tubo con depósito por debajo, bobina y lata (nada de cúpula
de cristal arriba ni de mango de pistola de juguete), y la VIP se reconoce por la cámara abierta y los anillos.

## Mallas

### Normal: `chatarra/Pistola_Chatarra.fbx`

| Malla | Qué es | En Studio |
| --- | --- | --- |
| `Chatarra_Cuerpo` | Todo lo fijo (cajón, cañón, latas, cables, cinta, manómetro, empuñadura...) | **Handle**. SurfaceAppearance con el atlas |
| `Chatarra_Rueda` | Rueda de válvula | SurfaceAppearance con el **mismo** atlas. Gira sobre X (Weld `Giro`) |
| `Chatarra_Deposito` | Cristal del depósito (cilindro macizo) | Material **Glass**, `#B9E6D2`, Transparency 0,55 |
| `Chatarra_Combustible` | Líquido y burbujas, dentro del cristal | Material **Neon**, `#7DFF3A` |
| `Chatarra_Luces` | Bombilla de encima y fondo de la boca | Material **Neon**, `#7DFF3A` |

Texturas: `chatarra/texturas/Chatarra_{color,normal,metal,rugosidad}.png`.

### VIP: `vip/Pistola_VIP.fbx`

| Malla | Qué es | En Studio |
| --- | --- | --- |
| `VIP_Cuerpo` | Cuerpo, cámara, cañón, empuñadura | **Handle**. SurfaceAppearance con el atlas |
| `VIP_Anillo1`, `VIP_Anillo2`, `VIP_Anillo3` | Los anillos flotantes (de atrás adelante) | SurfaceAppearance con el **mismo** atlas. Giran sobre el eje del cañón (Weld `Giro`) |
| `VIP_Anillo1_Luz` … `VIP_Anillo3_Luz` | El aro de luz de cada anillo | Material **Neon**, `#3FF0FF`. Soldado a su anillo (gira con él) |
| `VIP_Nucleo` | Núcleo de energía | Material **Neon**, `#A64BFF` |
| `VIP_Luces` | Líneas de luz del cuerpo, órbita del núcleo y emisor | Material **Neon**, `#3FF0FF` |

Texturas: `vip/texturas/VIP_{color,normal,metal,rugosidad}.png`.

Los colores de neón y del cristal están en `NEON` y `CRISTAL`, arriba de `herramientas/pistola_portales.py`.
Las piezas con textura de cada pistola comparten **un solo atlas**: se sube una vez y se pone el mismo ID en todas.

### Anclajes

Cada FBX lleva dos Empty, y `Pistola_<nombre>.json` da su posición (studs, ejes de Roblox, en el marco del modelo):

- **`Boca`**: la boca del cañón. De ahí sale el efecto del portal. Su `LookVector` mira hacia delante.
- **`Agarre`**: donde cae el `RightGripAttachment` del brazo derecho R6 (el centro de la cara del extremo del
  brazo). Está entre el gatillo y la empuñadura, a media altura: así la mano R6 envuelve la empuñadura y el cuerpo
  de la pistola queda encima del brazo, como en la foto «En la mano».

El JSON da también el centro y el tamaño de cada malla, los pivotes de las piezas que giran y, por malla, la
comprobación de la geometría (triángulos, aristas abiertas = 0, volumen positivo = normales hacia fuera).

## Montarla en Roblox como Tool

> Sin probar en Studio (esta sesión no tiene Studio). Lo tiene que comprobar el director.

1. **Avatar → Import 3D** con `Pistola_Chatarra.fbx` (o `Pistola_VIP.fbx`). **Scale Unit = Stud** (se modela en
   studs, con la misma receta de exportación que la región 1). Anchored desactivado.
2. Sube el atlas (los cuatro PNG de `texturas/`) con el Asset Manager y apunta los IDs.
3. Abre `montar_chatarra.luau` (o `montar_vip.luau`), pega los IDs en `IDS_TEXTURA` arriba del todo, selecciona el
   modelo importado, pega el script en la **barra de comandos** y pulsa Enter. El script:
   - corrige el **giro de importación** (`GIRO_IMPORTACION = CFrame.Angles(0, math.pi, 0)`: el importador mete las
     mallas giradas 180° sobre su eje vertical, como se vio con la región 1) y coloca cada pieza en su sitio;
   - crea la **Tool** (`PistolaPortales` / `PistolaPortalesVIP`); el cuerpo pasa a llamarse `Handle`;
   - suelda el resto al Handle (WeldConstraint). La rueda y los anillos llevan en cambio un **`Weld` llamado
     `Giro`** con el atributo `C0Base`; los aros de luz van soldados a su anillo;
   - pone Neon, Glass y los colores, y una **SurfaceAppearance** (ColorMap, NormalMap, MetalnessMap, RoughnessMap)
     en las piezas con textura;
   - crea los Attachment `Boca` y `Agarre` en el Handle y pone `Tool.Grip` a partir de `Agarre`;
   - todas las piezas con `CanCollide = false`, y las que no son el Handle, `Massless`.
4. Comprueba: con la Tool equipada, el cañón mira adonde mira el personaje y la empuñadura queda en el puño.
   **Si el cañón sale hacia atrás o las piezas descolocadas**, el importador no ha girado las mallas: vuelve a
   importar, pon `GIRO_IMPORTACION = CFrame.identity` en el script y repite.
5. Mete la Tool en `ServerStorage` (o donde la vaya a dar el juego).

Para hacer girar los anillos (en el cliente, solo con la Tool equipada):

```lua
local giro = anillo:FindFirstChild("Giro") :: Weld
local base = giro:GetAttribute("C0Base") :: CFrame
-- en cada fotograma; cada anillo a su velocidad y alternando el sentido queda mejor
giro.C0 = base * CFrame.Angles(0, 0, angulo)
```

La rueda de la chatarra igual (por ejemplo, media vuelta cada vez que se abre un portal).

**Transparencia.** El único transparente es el cristal del depósito, y es una malla aparte **sin textura** (Material
Glass + Transparency), así que no necesita SurfaceAppearance para eso. Las texturas del atlas no tienen canal alfa.
Si algún día se pinta el cristal con una textura con alfa, tendrá que ir en una SurfaceAppearance con
`AlphaMode = Transparency` (con `TextureID` Roblox pinta mal la transparencia, ver la región 1).

**Rendimiento en móvil.** ~3.900 triángulos y un atlas de 1024 por pistola; cinco mallas la normal y nueve la VIP
(los anillos tienen que ir sueltos para girar). Si hace falta una luz, una `PointLight` en `Boca` solo mientras se
abre el portal, no fija.

## Reglas de importación que cumple

- **Grosor real**: todo son sólidos cerrados (cintas, bridas, chapas, cables, las paredes de la lata, los anillos).
  Ninguna malla tiene aristas abiertas (`aristas_abiertas: 0` en el JSON).
- **Normales hacia fuera**: recalculadas en cada pieza; el volumen con signo de cada malla es positivo.
- **Giro de importación**: `GIRO_IMPORTACION` en el script de montaje (ver arriba).
- **SurfaceAppearance** para las texturas; la transparencia va en una malla sin textura.
- Solo R6: el muñeco de las fotos es un R6 de cajas (Torso 2×2×1, brazos 1×2×1).

Nota: las «reglas de importación de Roblox» que pedía el encargo no están escritas en `CLAUDE.md`; se han seguido
las que dejó la región 1 en `modelos/region1_valle_del_alba/README.md` («Probado en Studio»).

## Regenerar

```bash
.venv/bin/python modelos/herramientas/pistola_portales.py --salida modelos/pistola_portales --ronda 5
```

Con `--rapido` las texturas y los renders salen a baja resolución (unos 40 s). A calidad completa, unos 3 minutos
con 4 núcleos. El script escribe los FBX, las texturas, los JSON, los dos `montar_*.luau` (a partir de
`herramientas/plantilla_montar_pistola.luau`), la hoja de contactos y la comparación.

## Las rondas

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| 1 | Las dos se leen y se distinguen al momento. Pero: la VIP pasaba de 5.000 triángulos y la normal de 4.000; el líquido y las líneas brillaban tanto que salían blancos; las placas blancas de la VIP ocupaban medio costado y las líneas de luz eran gruesas (parecía un dibujo con rotulador neón); en la foto «las dos» se tapaban una a otra | — |
| 2 | Ya en presupuesto (3.840 y 3.880). La comparación salía recortada; el cristal del depósito no se leía como cristal; la VIP era una silueta negra | Neón más bajo, anillos de 20 lados con un solo aro de luz, placas blancas pequeñas, líneas finas y sin la línea baja, comparación de lado con una pistola detrás de otra |
| 3 | Primera a calidad completa: la normal funciona (óxido, chapas desparejadas, cables, cinta). La VIP seguía casi negra y el núcleo salía rosa pálido | Varillas de jaula en el depósito, comparación sin recortes, VIP en gris metal menos oscuro |
| 4 | El metal de la VIP solo reflejaba el estudio oscuro: negro. Las aletas de arriba parecían antenas | Caja de luz cenital (como el cielo en Roblox), metal y cromo más claros, núcleo morado más intenso, aletas bajas, placas blancas en la empuñadura |
| 5 (final) | Al reimportar los FBX salieron dos fallos: el JSON tenía el cañón hacia +Z y los Empty de la VIP se llamaban `Agarre.001`. Y el muñeco sostenía la pistola con la mano izquierda (en Blender, mirando a -Y, la derecha es -X) | Placas de la empuñadura que asoman de verdad, marco del JSON con el cañón hacia -Z, Empty con su nombre, pistola en la mano derecha del R6 y lados de la hoja bien etiquetados |
