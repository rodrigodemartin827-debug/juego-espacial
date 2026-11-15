"""Ronda 11: piezas de nave modular I (modelos 63-70): cascos, cabinas, alas y motor básico.

Convención de las piezas de nave: el morro mira a -Y, arriba +Z; el ORIGEN de cada pieza es su punto de acople y las
anclas del JSON dicen dónde se acoplan las demás (Cabina, AlaIzq, AlaDer, Motor..., Arma..., Tren..., Estabilizador).
Se exporta el ala DERECHA (crece hacia +X). Su perfil es simétrico arriba/abajo, así que la izquierda es la misma
malla girada 180° sobre el eje morro-cola de la nave (Roblox no puede reflejar mallas)."""

import math

from comunes import tira
from lib import anillo_y


def _casco(g, L, W, H, n=12, franjas=2, plazas=1):
    """Fuselaje por secciones: morro afilado, panza plana oscura y cola truncada para los motores."""
    y0 = -L / 2
    secs = ((0.0, 0.05, 0.08, 0.0), (0.08, 0.34, 0.36, 0.0), (0.22, 0.72, 0.7, 0.02), (0.42, 1.0, 1.0, 0.04), (0.7, 1.0, 1.0, 0.04),
            (0.9, 0.86, 0.9, 0.05), (1.0, 0.7, 0.78, 0.06))
    anillos = [anillo_y(y0 + t * L, W / 2 * kx, H / 2 * kz, n, pot=2.6, cz=cz * H, plano=-H * 0.34) for t, kx, kz, cz in secs]
    g.loft("n_casco", anillos)
    # Panza oscura (quilla) y franjas naranjas que rodean el casco.
    g.loft("n_panza", [anillo_y(y0 + t * L, W / 2 * kx * 0.8, H * 0.08, 8, pot=3, cz=-H * 0.36) for t, kx in
                       ((0.1, 0.4), (0.3, 0.85), (0.6, 1.0), (0.95, 0.85))])
    for i in range(franjas):
        t = 0.3 + i * 0.5 / max(franjas, 1)
        kx = 0.88 if t < 0.4 else 1.0
        g.loft("h_naranja_liso", [anillo_y(y0 + (t + d) * L, W / 2 * kx * 1.015, H / 2 * kx * 1.02, n, pot=2.6, cz=0.03 * H,
                                           plano=-H * 0.335) for d in (0.0, 0.035)])
    # Tapa trasera con el aro de acople de los motores y luces de posición.
    yc = y0 + L
    g.caja("h_oscuro", (W * 0.62, 0.3, H * 0.62), (0, yc + 0.1, 0.06 * H), bisel=0.08)
    g.toro("h_neon", min(W, H) * 0.24, 0.07, (0, yc + 0.27, 0.06 * H), (90, 0, 0), seg=12, lados=4)
    for s in (-1, 1):
        tira(g, "h_neon", (s * W * 0.5, y0 + L * 0.45, 0.1), (s * W * 0.5, y0 + L * 0.68, 0.1), 0.1)
        g.caja("h_gris", (0.5, L * 0.3, H * 0.3), (s * W * 0.5, y0 + L * 0.58, -H * 0.05), bisel=0.08)   # raíz de ala
        g.ancla("AlaDer" if s > 0 else "AlaIzq", (s * (W * 0.5 + 0.25), y0 + L * 0.58, -H * 0.05))
    # Lomo: carenado dorsal con antena, y tomas de aire.
    g.loft("n_casco", [anillo_y(y0 + t * L, W * 0.16 * k, H * 0.12 * k, 6, cz=H * 0.5) for t, k in ((0.5, 0.3), (0.62, 1.0), (0.9, 1.0), (0.99, 0.5))])
    g.cil("h_metal", 0.05, H * 0.5, (0, y0 + L * 0.7, H * 0.6), lados=4)
    for s in (-1, 1):
        g.caja("h_oscuro", (W * 0.14, L * 0.1, H * 0.2), (s * W * 0.36, y0 + L * 0.36, H * 0.28), rot=(0, s * 25, 0), sup=(0.7, 1), bisel=0.05)
    g.ancla("Cabina", (0, y0 + L * 0.3, H * 0.42))
    g.ancla("Estabilizador", (0, y0 + L * 0.9, H * 0.6))
    return y0, yc


def casco_nave_pequeno(g):
    L, W, H = 13.0, 4.2, 3.2
    y0, yc = _casco(g, L, W, H, franjas=1)
    g.ancla("Motor", (0, yc + 0.3, 0.06 * H))
    g.ancla("ArmaIzq", (-W * 0.3, y0 + L * 0.2, -H * 0.3))
    g.ancla("ArmaDer", (W * 0.3, y0 + L * 0.2, -H * 0.3))
    g.ancla("TrenMorro", (0, y0 + L * 0.25, -H * 0.42))
    g.ancla("TrenIzq", (-W * 0.3, y0 + L * 0.75, -H * 0.42))
    g.ancla("TrenDer", (W * 0.3, y0 + L * 0.75, -H * 0.42))
    g.ancla("Escudo", (0, y0 + L * 0.55, H * 0.55))


def casco_nave_mediano(g):
    L, W, H = 20.0, 6.4, 4.4
    y0, yc = _casco(g, L, W, H, n=14, franjas=2)
    # Ventanillas laterales de la bodega y escotilla.
    for s in (-1, 1):
        for k in range(3):
            g.caja("h_cristal", (0.12, 1.3, 0.8), (s * W * 0.495, y0 + L * (0.3 + k * 0.09), H * 0.2), rot=(0, s * -12, 0))
        g.ancla("Motor" + ("Der" if s > 0 else "Izq"), (s * W * 0.22, yc + 0.3, 0.06 * H))
        g.ancla("Arma" + ("Der" if s > 0 else "Izq"), (s * W * 0.34, y0 + L * 0.2, -H * 0.3))
        g.ancla("Tren" + ("Der" if s > 0 else "Izq"), (s * W * 0.32, y0 + L * 0.75, -H * 0.42))
    g.caja("h_gris", (2.2, 0.16, 2.6), (W * 0.5 - 0.1, y0 + L * 0.78, H * 0.0), rot=(0, 0, 90), bisel=0.05)
    g.ancla("TrenMorro", (0, y0 + L * 0.22, -H * 0.42))
    g.ancla("Escudo", (0, y0 + L * 0.55, H * 0.6))
    g.ancla("ArmaDorsal", (0, y0 + L * 0.5, H * 0.55))


def casco_nave_grande(g):
    L, W, H = 30.0, 9.6, 6.4
    y0, yc = _casco(g, L, W, H, n=16, franjas=3)
    for s in (-1, 1):
        # Dos filas de ventanillas, góndolas laterales y refuerzos.
        for k in range(6):
            g.caja("h_cristal", (0.12, 1.3, 0.9), (s * W * 0.497, y0 + L * (0.3 + k * 0.075), H * 0.22), rot=(0, s * -10, 0))
        g.loft("n_casco", [anillo_y(y0 + t * L, 1.1 * k, 1.0 * k, 8, cz=-H * 0.1, cx=s * (W * 0.5 + 0.5)) for t, k in
                           ((0.5, 0.2), (0.6, 1.0), (0.92, 1.0), (1.0, 0.8))])
        g.caja("h_oscuro", (1.6, 0.3, 1.5), (s * (W * 0.5 + 0.5), yc + 0.05, -H * 0.1), bisel=0.08)
        g.ancla("Motor" + ("Der" if s > 0 else "Izq"), (s * (W * 0.5 + 0.5), yc + 0.25, -H * 0.1))
        g.ancla("Arma" + ("Der" if s > 0 else "Izq"), (s * W * 0.36, y0 + L * 0.18, -H * 0.3))
        g.ancla("Tren" + ("Der" if s > 0 else "Izq"), (s * W * 0.34, y0 + L * 0.75, -H * 0.42))
        g.ancla("Tren" + ("MedioDer" if s > 0 else "MedioIzq"), (s * W * 0.34, y0 + L * 0.48, -H * 0.42))
    # Rampa de carga trasera (pieza articulada) y puente dorsal.
    g.pieza("rampa", pivote=(0, yc - 2.6, -H * 0.32))
    g.caja("h_gris", (W * 0.4, 2.6, 0.3), (0, yc - 1.3, -H * 0.36), bisel=0.06)
    g.caja("h_peligro", (W * 0.4, 0.5, 0.32), (0, yc - 0.3, -H * 0.36))
    g.pieza("cuerpo")
    g.caja("n_casco", (W * 0.4, L * 0.16, H * 0.2), (0, y0 + L * 0.62, H * 0.56), sup=(0.8, 0.8), bisel=0.12)
    g.caja("h_cristal", (W * 0.3, 0.15, H * 0.1), (0, y0 + L * 0.545, H * 0.58), rot=(-20, 0, 0))
    g.ancla("MotorCentro", (0, yc + 0.3, 0.06 * H))
    g.ancla("TrenMorro", (0, y0 + L * 0.2, -H * 0.42))
    g.ancla("Escudo", (0, y0 + L * 0.45, H * 0.62))
    g.ancla("ArmaDorsal", (0, y0 + L * 0.36, H * 0.52))


def _cabina(g, L, W, H, avanzada):
    n = 10
    # Zócalo que asienta sobre el casco, con borde naranja.
    g.loft("n_casco", [anillo_y(-L / 2 + t * L, W / 2 * k, 0.35, n, pot=3, cz=0.2, plano=0.0) for t, k in
                       ((0.0, 0.25), (0.15, 0.8), (0.5, 1.0), (0.85, 0.9), (1.0, 0.6))])
    g.loft("h_naranja_liso", [anillo_y(-L / 2 + t * L, W / 2 * k * 1.03, 0.1, n, pot=3, cz=0.42) for t, k in ((0.1, 0.62), (0.5, 1.0), (0.9, 0.8))])
    # Interior: asiento, respaldo, palanca y consola con pantallas.
    g.caja("h_oscuro", (W * 0.4, W * 0.4, 0.4), (0, L * 0.12, 0.5), base=True, bisel=0.06)
    g.caja("h_naranja_liso", (W * 0.4, 0.3, H * 0.62), (0, L * 0.12 + W * 0.2, 0.5), base=True, rot=(8, 0, 0), bisel=0.06)
    g.caja("h_gris", (W * 0.6, 0.6, 0.5), (0, -L * 0.2, 0.5), base=True, sup=(1, 0.5), desv=(0, -0.1))
    g.caja("h_neon", (W * 0.5, 0.06, 0.3), (0, -L * 0.2 + 0.24, 0.92), rot=(40, 0, 0))
    g.cil("h_metal", 0.05, 0.5, (0, -L * 0.08, 0.5), (15, 0, 0), lados=4)
    # Cúpula de cristal (con grosor) y arcos del marco.
    perfil = ((0.02, 0.3, 0.2), (0.2, 0.8, 0.75), (0.5, 0.97, 1.0), (0.8, 0.85, 0.82), (0.98, 0.5, 0.35))
    ext = [anillo_y(-L / 2 + t * L, W / 2 * kx * 0.9, H * kz, n, pot=2.3, cz=0.45, plano=0.45) for t, kx, kz in perfil]
    g.loft("h_cristal", [[(0, -L / 2 + 0.01 * L, 0.5)]] + ext + [[(0, L / 2 - 0.01 * L, 0.5)]])
    marcos = (0.5,) if not avanzada else (0.28, 0.5, 0.72)
    for t in marcos:
        kx, kz = [(a, b) for tt, a, b in perfil if abs(tt - t) < 0.26][0] if not avanzada else {0.28: (0.88, 0.86), 0.5: (0.97, 1.0), 0.72: (0.9, 0.9)}[t]
        pts = [(W / 2 * kx * 0.93 * math.cos(math.pi * i / 8), -L / 2 + t * L, 0.45 + H * kz * 1.02 * math.sin(math.pi * i / 8)) for i in range(9)]
        g.tubo("h_gris", pts, 0.09, lados=4, suave=False)
    g.tubo("h_gris", [(0, -L / 2 + L * t, 0.47 + H * kz * 1.02) for t, kx, kz in perfil], 0.08, lados=4, suave=False)
    g.ancla("Piloto", (0, L * 0.12, 0.9))


def cabina_basica(g):
    _cabina(g, 5.2, 2.8, 1.7, False)


def cabina_avanzada(g):
    L, W, H = 8.0, 4.0, 2.2
    _cabina(g, L, W, H, True)
    # Segundo asiento, sensores laterales, antena y tiras de neón.
    g.caja("h_oscuro", (W * 0.36, W * 0.36, 0.4), (0, L * 0.3, 0.5), base=True, bisel=0.06)
    g.caja("h_naranja_liso", (W * 0.36, 0.3, H * 0.55), (0, L * 0.3 + W * 0.18, 0.5), base=True, rot=(8, 0, 0), bisel=0.06)
    for s in (-1, 1):
        g.loft("h_gris", [anillo_y(-L * 0.1 + t * L * 0.4, 0.34 * k, 0.3 * k, 6, cz=0.35, cx=s * (W / 2 + 0.2)) for t, k in ((0, 0.3), (0.25, 1), (0.8, 1), (1, 0.6))])
        g.esfera("h_neon", 0.2, (s * (W / 2 + 0.2), -L * 0.1, 0.35), lados=6, anillos=4)
        tira(g, "h_neon", (s * W * 0.47, -L * 0.2, 0.47), (s * W * 0.47, L * 0.25, 0.47), 0.08)
    g.cil("h_metal", 0.04, 1.4, (0.5, L * 0.42, 0.6), (-25, 0, 0), lados=4)
    g.caja("h_oscuro", (0.7, 0.9, 0.3), (0, L * 0.44, 0.55), bisel=0.06)
    g.ancla("Copiloto", (0, L * 0.3, 0.9))


def _seccion(x, cuerda, grosor, n, yc=0.0, zc=0.0):
    """Perfil de ala simétrico (en el plano YZ) en la posición x: borde de ataque redondo y de salida afilado."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        y = yc - cuerda / 2 * ca * (1.0 if ca > 0 else 1.0)
        afila = 1.0 if ca > 0 else (1 - 0.75 * (-ca))        # hacia la cola (+Y... ca<0) se afila
        pts.append((x, y, zc + grosor / 2 * sa * afila))
    return pts


def _ala(g, envergadura, cuerda_raiz, cuerda_punta, flecha, grosor, n=10):
    xs = (0.0, 0.25, 0.6, 0.92, 1.0)
    secs = []
    for t in xs:
        c = cuerda_raiz + (cuerda_punta - cuerda_raiz) * t
        secs.append(_seccion(t * envergadura, c * (0.75 if t == 1.0 else 1.0), grosor * (1 - 0.6 * t), n, yc=flecha * t))
    g.loft("n_casco", secs)
    # Punta naranja, raíz reforzada, alerón y luz de posición.
    ct = cuerda_punta
    g.loft("h_naranja_liso", [_seccion(envergadura * t, (cuerda_raiz + (cuerda_punta - cuerda_raiz) * t) * k * 1.02, grosor * (1 - 0.6 * t) * 1.08, n,
                                       yc=flecha * t) for t, k in ((0.86, 1.0), (0.94, 1.0), (1.01, 0.72))])
    g.caja("h_gris", (0.5, cuerda_raiz * 0.9, grosor * 1.3), (0.2, 0, 0), bisel=0.08)
    g.caja("n_panza", (envergadura * 0.45, cuerda_raiz * 0.16, grosor * 0.36), (envergadura * 0.45, flecha * 0.45 + cuerda_raiz * 0.33, 0),
           rot=(0, 0, math.degrees(math.atan2(flecha, envergadura))))
    g.esfera("h_neon", grosor * 0.22, (envergadura * 1.01, flecha, 0), lados=6, anillos=4)
    tira(g, "h_neon", (envergadura * 0.3, flecha * 0.3 - cuerda_raiz * 0.42, 0), (envergadura * 0.3 + 0.02, flecha * 0.3 - cuerda_raiz * 0.42 + 0.0, 0), 0.0) if False else None
    g.ancla("Raiz", (0, 0, 0))
    g.ancla("Punta", (envergadura, flecha, 0))


def ala_pequena(g):
    _ala(g, 5.0, 4.2, 1.8, 1.6, 0.6)
    g.ancla("Arma", (2.4, 0.4, -0.3))


def ala_grande(g):
    E = 10.0
    _ala(g, E, 6.0, 2.2, 3.2, 0.85, n=12)
    # Soporte de motor a media ala: pilón simétrico con aro de acople detrás, y dos anclajes de arma.
    xm, ym = E * 0.42, 3.2 * 0.42
    g.loft("h_gris", [anillo_y(ym - 1.8 + t * 4.6, 0.75 * k, 0.75 * k, 8, cx=xm) for t, k in ((0, 0.2), (0.2, 0.85), (0.7, 1.0), (1.0, 0.95))])
    g.cil("h_oscuro", 0.62, 0.25, (xm, ym + 2.8, 0), (-90, 0, 0), lados=8)
    g.toro("h_neon", 0.66, 0.06, (xm, ym + 2.84, 0), (90, 0, 0), seg=8, lados=4)
    g.caja("h_naranja_liso", (1.56, 0.6, 1.56), (xm, ym + 0.2, 0), bisel=0.1)
    g.ancla("Motor", (xm, ym + 3.05, 0))
    g.ancla("Arma", (E * 0.72, 3.2 * 0.72 - 0.4, -0.3))
    g.ancla("Arma2", (E * 0.2, 0.2, -0.4))


def motor_basico(g):
    # Eje a lo largo de Y: se acopla por delante (origen) y expulsa hacia +Y.
    R = 0.95
    g.cil("h_oscuro", R * 0.75, 0.35, (0, 0, 0), (-90, 0, 0), lados=10)
    g.rev("n_casco", [(R * 0.8, 0.3), (R, 0.8), (R, 2.6), (R * 0.85, 3.1), (R * 0.6, 3.1), (0.0, 3.0)], (0, 0, 0), (-90, 0, 0), lados=12)
    g.toro("h_naranja_liso", R * 1.0, 0.09, (0, 1.2, 0), (90, 0, 0), seg=12, lados=4)
    # Tobera cónica con el núcleo luminoso dentro.
    g.rev("n_tobera", [(R * 0.62, 3.0), (R * 0.95, 4.4), (R * 0.86, 4.4), (R * 0.55, 3.1)], (0, 0, 0), (-90, 0, 0), lados=12, tapas=(False, False))
    g.rev("h_neon", [(0.0, 3.05), (R * 0.5, 3.1), (R * 0.72, 4.0), (0.0, 4.2)], (0, 0, 0), (-90, 0, 0), lados=10)
    for i in range(4):
        a = math.radians(90 * i + 45)
        g.caja("h_gris", (0.16, 1.6, 0.4), (R * 1.02 * math.cos(a), 1.9, R * 1.02 * math.sin(a)), rot=(0, -math.degrees(a) + 90, 0))
    g.ancla("Acople", (0, 0, 0))
    g.ancla("Escape", (0, 4.4, 0))


MODELOS = [
    ("casco_nave_pequeno", "nave", 5000, casco_nave_pequeno),
    ("casco_nave_mediano", "nave", 5000, casco_nave_mediano),
    ("casco_nave_grande", "nave", 5000, casco_nave_grande),
    ("cabina_basica", "nave", 5000, cabina_basica),
    ("cabina_avanzada", "nave", 5000, cabina_avanzada),
    ("ala_pequena", "nave", 5000, ala_pequena),
    ("ala_grande", "nave", 5000, ala_grande),
    ("motor_basico", "nave", 5000, motor_basico),
]
