# Orden de trabajo para la v1

Es una propuesta: no se ha empezado nada. Cada paso va en su propia rama y su propio PR, probado en Studio y con
capturas antes de fusionar. El orden sigue las dependencias: primero lo que necesitan los demás.

## Fase 0: antes de empezar (en curso)

1. **Terminar la región 1** (PR #16): pasar a la rama del PR lo probado en `prueba/region1-valle-alba` (suelo
   fijo, puente, silueta, casas, salto, subida con Open Cloud) y revisarlo.
2. **Velocidad de carga.** Hoy, al entrar, generar el planeta tarda unos 44 s (colinas 31,6 s, corteza 11,4 s) y
   la memoria de terreno pasa de 35 a 364 MB. Hay que bajar las dos cosas antes de añadir más contenido encima.
3. **Decidir qué pasa con los PR abiertos** de los que depende la v1:
   - #12 bandos;
   - #13 persianas;
   - #14 modelos 3D;
   - #15 planeta de prueba;
   - #17 animaciones R6.

## Fase 1: progresión (casi todo lo demás depende de esto)

4. **Niveles hasta 3.000.**
   - Curva de XP en un módulo de datos y XP dada solo por el servidor.
   - Guardado con migración del esquema.
   - Con 3.000 niveles, la curva hay que diseñarla y probarla con números antes de programarla.
5. **Misiones.**
   - Datos de misiones (picar X minerales, cazar X criaturas, entregar...) y un servicio que cuenta los avances.
   - Para contar, escucha a la minería, el escáner y el combate, que ya existen.
   - Recompensa: XP y monedas.
   - Al principio sencillas; más difíciles con el nivel.
6. **NPCs.**
   - R6, con animación de reposo y diálogo o panel de misiones.
   - Primero en los pueblos de la región 1 (Pradoverde y Aurora). Necesita la región 1 fusionada.

## Fase 2: combate y armas

7. **Completar la lista de poderes y armas de la v1:** 8-10 poderes y 3-4 armas, con su calidad de VFX y de
   animación.
8. **Maestría.**
   - Cada arma y cada poder cuenta sus enemigos derrotados y desbloquea sus ataques: 1 enemigo para el primero,
     300 para el último.
   - Los números van en datos. Vale para los dos bandos.
9. **Poderes humanos desbloqueables.**
   - Requisitos: nivel, dinero y llegar a un sitio especial del planeta humano. Los monstruos los tienen de
     serie.
   - Depende de los bandos (#12) y de los niveles (4).
10. **Forja básica:** recetas de armas con minerales y una estación de forja en la ciudad. Se apoya en el crafteo
    que ya existe.

## Fase 3: naves

11. **Naves por piezas en el hangar.**
    - Piezas: cabina, casco, motores, alas, armas y escudos.
    - Cada pieza cambia cómo vuela, a través de la física de naves que ya existe.
    - Se ensamblan con puntos de anclaje y tienen un editor en el hangar.
    - Las mejoras actuales (Casco, Escudo, Motor, Armas, Escaner, Carga) pasan a ser piezas, con migración del
      guardado.
    - Sustituye a la nave actual, que parece un avión. Es el paso más grande; necesita modelos nuevos de Blender.
12. **Misión inicial «forja tu primera nave»** con la gente del planeta, enlazada con el tutorial.

## Fase 4: mundo y contenido

13. **Los 4 planetas pequeños**, con sus recursos, criaturas y peligros. Uno de ellos es el planeta disputado
    con PvP.
14. **El campo de asteroides, los eventos del primer viaje y las zonas seguras** alrededor de los planetas de
    bando.
15. **Un jefe.** Gigante, con fases y materiales raros. Hay que elegir cuál (ver «Por decidir»).
16. **Lo propio de cada bando**: pantalla de elección con la grieta, persianas, andar terrorífico de los
    monstruos y su recurso exclusivo. Parte de esto ya está en los PR #12-#14.

## Fase 5: lanzamiento

17. **Tutorial completo**: moverse, pelear, escanear, craftear y la primera nave.
18. **Monetización de la v1**: x2 monedas, VIP, almacén extra y skins. La pistola de portales VIP queda para
    después.
19. **Rendimiento en móvil, pruebas de carga con varios jugadores y repaso final de calidad.**

## Por decidir

- **Qué jefe entra en la v1.** El Leviatán custodia un sector exterior, y los sectores exteriores (con la Llave
  Maestra) son de después. ¿Un jefe en el planeta disputado o en el de los monstruos?
- **Dónde está el sitio especial** donde los humanos desbloquean sus poderes.
- **La curva de XP hasta el nivel 3.000**, y cuánto se tarda en llegar a los niveles 100, 1.000 y 2.000.
- **Si hay misiones diarias o repetibles**, o solo una cadena fija.
