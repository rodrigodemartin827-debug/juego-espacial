# Tiendas humanas: lista de comprobación en Studio

Esta lista es para el **director** (Claude Code en local, con Studio conectado por MCP) y para Rodrigo. Las pruebas
automáticas (`lune run pruebas/ejecutar Tiendas`) cubren las reglas de compra, la persiana y el cableado de red, pero **nada
de esto se ha visto todavía en Studio**: la sesión que lo programó no tiene Studio. Nada está terminado hasta marcar esta
lista con capturas.

Marca cada casilla y guarda una captura (`screen_capture`) donde se indique 📸. Si algo falla, anota qué ves y la salida de
`get_console_output`.

## 0. Preparación

- [ ] `rojo serve` conectado y **Play**. En la consola: `[Servidor] Juego espacial iniciado` y ningún aviso `[Tiendas] ...`.
- [ ] En el Explorer: `Workspace.ZonaDePruebas.Tienda_MercadoColonia` existe, con los atributos `TiendaId = MercadoColonia`
      y `PersianaBajada = false`, y las piezas `Origen`, `Cortina` (Lama1..Lama14, Barra, Asa, Rotulo), `Cajon`, `Baliza`,
      `Estado`, `ZonaPolvo` y `Mostrador` (con su ProximityPrompt).
- [ ] La tienda está en el **rincón oeste** de la plataforma (unos 90 studs a la izquierda del punto de aparición, hacia
      el fondo), mirando hacia el centro. Hay un cartel encima, un cofre dorado de monedas cerca y un pedestal gris
      «Olvidar bando» junto al punto de aparición.

## 1. Aspecto de la tienda abierta 📸

- [ ] El local se ve completo y limpio: paredes, toldo a rayas azul y blanco, letrero «MERCADO DE LA COLONIA», cartel
      verde «ABIERTO» en el pilar derecho, mostrador con franja azul, estanterías con cajas de colores y luz cálida dentro.
- [ ] La persiana está **recogida**: solo asoma la barra inferior (oscura, con asa) justo bajo el cajón. No se ve ninguna
      lama fuera del cajón ni por encima de él, ni parpadeos (z-fighting).
- [ ] La baliza (sobre el cajón, a la izquierda) está apagada.
- [ ] 📸 *Antes*: la tienda abierta, de frente, a unos 25 studs.

## 2. Comprar como Humano

- [ ] Elige **Humanos** en su pedestal. Coge monedas en el cofre (`+500 monedas`), varias veces si hace falta.
- [ ] Acércate al mostrador: aparece el aviso **E · Comprar · Mercado de la Colonia**. Púlsalo: se abre el panel.
- [ ] 📸 El panel: título, lema, tus monedas arriba a la derecha, lista de artículos con precio a la izquierda (verde si
      te llega, gris si no) y el detalle a la derecha.
- [ ] Compra **1 Hierro**: aviso verde «Comprado: Hierro», bajan las monedas lo que dice el precio y sube «tienes N».
      Abre la bodega (I) y comprueba que está.
- [ ] Compra **× 5** y **× 10** de un material: se cobra 5 y 10 veces el precio.
- [ ] Compra una **mejora** (p. ej. Casco reforzado): sube de nivel (el subtítulo pasa a «nivel 1 → 2»), el precio del
      siguiente nivel es mayor y la estadística (Vida del casco) cambia.
- [ ] Sin monedas suficientes: el botón está gris y al pulsarlo sale «No tienes monedas suficientes» (no se cobra nada).
- [ ] Bodega llena (compra material hasta llenarla): sale el aviso de bodega llena y no se cobra.
- [ ] Aléjate del mostrador: el panel se cierra solo.
- [ ] En `execute_luau` (servidor), comprueba que las monedas y el inventario del jugador coinciden con lo que muestra el
      panel.

## 3. La persiana baja cuando llega un Monstruo 📸

Con un solo jugador: usa el pedestal **Olvidar bando** y elige **Monstruos**. Con dos jugadores (mejor: *Test → Clients and
Servers → 2 Players*), uno Humano junto al mostrador con el panel abierto y otro Monstruo que se acerca.

- [ ] Como Monstruo, acércate andando a la tienda. A unos **40 studs del mostrador** la persiana baja.
- [ ] La animación se ve **espectacular y con peso**, en este orden:
  - [ ] suena la **alarma** y la **baliza** se enciende en rojo y empieza a latir;
  - [ ] **anticipación**: la persiana asoma un poco del cajón y se recoge;
  - [ ] **caída** acelerada, con el sonido de la bajada;
  - [ ] **impacto**: se queda clavada un instante (hitstop), sale **polvo** hacia la calle y saltan **chispas** de la barra,
        suena el **golpe** y la cámara **tiembla** (más flojo cuanto más lejos);
  - [ ] **rebota** dos veces y se queda quieta;
  - [ ] el cartel del pilar pasa a **«CERRADO»** en rojo y en la persiana se lee **«CERRADO · NO SE ATIENDE A MONSTRUOS»**.
- [ ] 📸 *Después*: la tienda con la persiana bajada, de frente. 📸 Una captura en mitad de la caída y otra en el impacto
      (polvo y chispas).
- [ ] El Monstruo ve el aviso rojo «Los humanos te bajan la persiana...».
- [ ] En el Explorer, el atributo `PersianaBajada` del modelo es `true` y el ProximityPrompt del mostrador está desactivado.
- [ ] Si el Humano tenía el panel abierto, se cierra con el aviso «¡Monstruo cerca! La tienda ha bajado la persiana».
- [ ] Las lamas no atraviesan el suelo ni se ven por encima del cajón en ningún momento de la animación.

## 4. No se vende a los Monstruos

- [ ] Como Monstruo nunca se llega a ver el aviso del mostrador: la persiana baja a 40 studs y el aviso solo aparece a unos
      11. (Si aun así lo usara en el instante entre medias, el servidor responde «Aquí no se atiende a los monstruos» y no
      abre el panel.)
- [ ] Como Monstruo, manda la compra a mano desde la consola del **cliente**:
      `game.ReplicatedStorage.Remotos.ComprarArticulo:FireServer(workspace.ZonaDePruebas.Tienda_MercadoColonia, "Hierro", 1)`
      → respuesta «Aquí no se atiende a los monstruos» y ni monedas ni inventario cambian.
- [ ] Como Humano, con la persiana **bajada**, la misma orden responde «La tienda está cerrada: hay un monstruo cerca».
- [ ] Como Humano, lejos de la tienda, la misma orden responde «Estás demasiado lejos del mostrador».
- [ ] Basura: `FireServer(workspace.ZonaDePruebas.Suelo, "Hierro")`, `FireServer(tienda, "NoExiste")`,
      `FireServer(tienda, "Hierro", 0/0)` → el servidor las descarta en silencio (un aviso `[Red] Petición ... descartada`
      en la consola del servidor) y no cambia nada.

## 5. La persiana sube cuando el Monstruo se va 📸

- [ ] Aléjate a más de **55 studs**. A los **2,5 s** suena el **cerrojo**, la persiana tiembla al soltarse, **sube suave**,
      se asienta en el cajón, la baliza se apaga y el cartel vuelve a **«ABIERTO»** en verde.
- [ ] Ronda el borde (entre 40 y 55 studs): la persiana **no** sube y baja sin parar.
- [ ] Vuelve a acercarte mientras está subiendo: baja otra vez desde donde estaba, sin saltos.
- [ ] Muere como Monstruo cerca de la tienda: la persiana vuelve a subir (un muerto no cuenta).
- [ ] 📸 La tienda otra vez abierta.

## 6. Streaming, rendimiento y móvil

- [ ] Con `Workspace.StreamingEnabled = true`, aléjate hasta que la tienda salga del streaming, haz que la persiana cambie
      (con otro jugador) y vuelve: la tienda aparece ya en el estado correcto, sin animación y sin piezas sueltas.
- [ ] *MicroProfiler* / *Developer Console → Memory*: con la persiana quieta no hay coste por fotograma de las tiendas (el
      bucle se apaga); durante la animación es mínimo.
- [ ] Repite la bajada varias veces: no se acumulan emisores ni sonidos (en el Explorer del cliente, cada `ZonaPolvo`
      tiene **un** `PolvoPersiana` y **un** `ChispasPersiana`; el `Cajon`, un sonido de cada).
- [ ] Emulador de móvil (*Test → Device*): el panel cabe en pantalla, los botones de compra se leen y se pueden pulsar.
- [ ] Con `Calidad.Forzar("Bajo")` hay menos polvo y chispas y la baliza no ilumina el entorno.

## 7. Sonidos (pendiente de sustituir)

- [ ] Los sonidos actuales son **provisionales** (sonidos que trae Roblox: `electronicpingshort`, `swoosh`, `hit`,
      `clickfast`). Comprueba que suenan; si alguno no carga, saldrá un aviso en la consola.
- [ ] Sustitúyelos en `src/shared/Tiendas/Datos/Persiana.luau` (`Persiana.Sonidos`) por sonidos de persiana de verdad
      (traqueteo metálico, golpe seco, cerrojo) subidos a Roblox, y ajusta volumen y tono a oído.

## 8. Para Rodrigo

- [ ] Capturas del **antes** (tienda abierta) y del **después** (persiana bajada), más la secuencia de la caída.
- [ ] Decidir si con la persiana bajada la tienda cierra **para todos** (ahora sí: así un monstruo que entra en la ciudad
      deja a los humanos sin tienda, lo que da tensión y motivo para echarlo) o solo para los monstruos
      (`Config.CerradaParaTodosConPersianaBajada = false`).
- [ ] Revisar precios en `src/shared/Tiendas/Datos/Catalogo.luau` (las mejoras compradas cuestan más del doble en monedas
      que en la mesa de crafteo, para que siga compensando explorar).
