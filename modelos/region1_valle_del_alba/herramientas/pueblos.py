"""
Trazado de los tres sitios del Valle del Alba: Aurora (la capital), Pradoverde (el pueblo inicial) y Los Molinos.

Cada sitio se traza en sus coordenadas LOCALES (u hacia el este, v hacia el norte, en studs, desde su centro; ver
geo.Sitio) y devuelve:
  * `colocaciones`: qué va dónde (edificios montados con el kit, piezas del kit, piezas especiales) con su giro;
  * `suelos`: formas del suelo para pintarlas en la textura del terreno (adoquín, losas de plaza, tierra, césped...);
  * `parcelas`: los campos de cultivo (solo Los Molinos).

Convención de giro: `frente` es el rumbo (grados desde el este, antihorario) hacia el que MIRA la fachada principal.
Los edificios se colocan dando el punto medio de su fachada.

Todo es determinista (semillas fijas): el mismo código da siempre el mismo pueblo.
"""

import math
from dataclasses import dataclass, field

import numpy as np

import edificios as ED
import kit as K
from malla import Ry, S, T, compone


@dataclass
class Colocacion:
    nombre: str
    tipo: str  # "edificio" (lista de piezas del kit) o "pieza" (un grupo de GRUPOS)
    u: float
    v: float
    giro: float  # grados: giro del eje X local respecto al este
    pieza: str = ""  # para tipo "pieza": nombre en GRUPOS
    edificio: object = None  # para tipo "edificio": edificios.Edificio
    dz: float = 0.0
    escala: float = 1.0
    caja: tuple = None  # huella (u0, v0, u1, v1) para comprobar solapes


@dataclass
class Trazado:
    nombre: str
    colocaciones: list = field(default_factory=list)
    suelos: list = field(default_factory=list)  # (tipo, forma)
    parcelas: list = field(default_factory=list)
    ocupado: list = field(default_factory=list)


# Objetos que se colocan en los trazados: nombre -> lista de (pieza del kit, matriz local, color o None = el de la
# pieza). La mayoría son una sola pieza; la torre del reloj y los molinos son varias (cada una con su color).
_I = np.eye(4)


def _uno(pieza, color=None):
    return [(pieza, _I, color)]


GRUPOS = {
    "Farola": _uno("Farola"), "Banco": _uno("Banco"), "Barril": _uno("Barril"), "Caja": _uno("Caja"),
    "Maceta": _uno("Maceta"), "Maceta_B": _uno("Maceta"), "Valla_Madera": _uno("Valla_Madera"),
    "Valla_Piedra": _uno("Valla_Piedra"), "Puesto_A": _uno("Puesto", "#C2413A"), "Puesto_B": _uno("Puesto", "#3F6FA8"),
    "Puesto_C": _uno("Puesto", "#E8B840"), "Tablon_Misiones": _uno("Tablon_Misiones"), "Pozo": _uno("Pozo"),
    "Carro": _uno("Carro"), "Pajar": _uno("Pajar"), "Espantapajaros": _uno("Espantapajaros"), "Fuente": _uno("Fuente"),
    "Torre_Reloj": [("Torre_Reloj", _I, None), ("Chapitel", T(0, 0, 67.1), None)],
    **{n: [("Molino_Torre", _I, None), ("Molino_Caperuza", _I, None),
           ("Molino_Aspas", compone(T(0, -9.7, 30.0), Ry(a)), None)]
       for n, a in (("Molino", 20.0), ("Molino_B", 52.0), ("Molino_C", 5.0))},
    "Portal_Ciudad": [("Portal_Ciudad", _I, None), ("Farola", T(-9.8, 0, 12.4) @ S(0.4), None),
                      ("Farola", T(9.8, 0, 12.4) @ S(0.4), None), ("Valla_Piedra", T(-21.6, -0.2, 0) @ S(1.25, 1, 1), None),
                      ("Valla_Piedra", T(11.6, -0.2, 0) @ S(1.25, 1, 1), None)],
    "Poste_Indicador": _uno("Poste_Indicador"), "Arbol_Flor": _uno("Arbol_Flor"), "Arbol_Flor_B": _uno("Arbol_Flor_B"),
    "Arbol_Frondoso": _uno("Frondoso_b"), "Arbol_Grande": _uno("Arbol_Grande"), "Arbusto": _uno("Arbusto_a"),
    "Arbusto_B": _uno("Arbusto_b"),
}


def _yaw(frente):
    """Giro del eje X local para que la fachada (que mira a -Y local) mire al rumbo `frente`."""
    return frente + 90.0


def _caja_rotada(u0, v0, ancho, fondo, giro):
    a = math.radians(giro)
    ex = np.array([math.cos(a), math.sin(a)])
    ey = np.array([-math.sin(a), math.cos(a)])
    o = np.array([u0, v0])
    pts = np.array([o, o + ex * ancho, o + ex * ancho + ey * fondo, o + ey * fondo])
    return (pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max())


def _solapa(c, otras, margen=0.0):
    for o in otras:
        if c[0] < o[2] + margen and c[2] > o[0] - margen and c[1] < o[3] + margen and c[3] > o[1] - margen:
            return True
    return False


def _cabe(t, ed, fu, fv, frente, margen=1.0):
    giro = _yaw(frente)
    a = math.radians(giro)
    ou = fu - ed.ancho / 2 * math.cos(a)
    ov = fv - ed.ancho / 2 * math.sin(a)
    return not _solapa(_caja_rotada(ou, ov, ed.ancho, ed.fondo, giro), t.ocupado, margen)


def poner_edificio(t, nombre, ed, fu, fv, frente, comprobar=True, margen=1.0):
    """Coloca un edificio con el centro de su fachada en (fu, fv) mirando a `frente`."""
    giro = _yaw(frente)
    a = math.radians(giro)
    ou = fu - ed.ancho / 2 * math.cos(a)
    ov = fv - ed.ancho / 2 * math.sin(a)
    caja = _caja_rotada(ou, ov, ed.ancho, ed.fondo, giro)
    if comprobar and _solapa(caja, t.ocupado, margen):
        return False
    t.ocupado.append(caja)
    t.colocaciones.append(Colocacion(nombre, "edificio", ou, ov, giro, edificio=ed, caja=caja))
    return True


def poner(t, pieza, u, v, giro=0.0, dz=0.0, escala=1.0, nombre=None):
    t.colocaciones.append(Colocacion(nombre or pieza, "pieza", u, v, giro, pieza=pieza, dz=dz, escala=escala))


def rellenar_frente(t, prefijo, p0, p1, frente, rng, tipos, pisos=(2, 3), fondos=(2, 3), anchos=(2, 3, 4),
                    hueco=(1.5, 5.0), tiendas=0.0, emblemas=("bolsa",)):
    """Llena de edificios un frente de calle: la línea de fachadas va de p0 a p1 y las fachadas miran a `frente`."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    largo = float(np.linalg.norm(p1 - p0))
    d = (p1 - p0) / largo
    s = float(rng.uniform(0, 3))
    n = 0
    while s < largo - 16:
        nx = int(rng.choice(anchos))
        ancho = nx * K.M
        if s + ancho > largo:
            nx = int((largo - s) // K.M)
            if nx < 2:
                break
            ancho = nx * K.M
        np_ = int(rng.choice(pisos))
        es_tienda = rng.uniform() < tiendas
        tipo = "tienda" if es_tienda else str(rng.choice(tipos))
        puesto = False
        # si no cabe, se prueba más estrecho y menos hondo antes de saltar
        for ny in sorted(set(fondos), reverse=bool(rng.uniform() < 0.5)):
            for nx2 in [nx] + [k for k in (3, 2) if k < nx]:
                ancho = nx2 * K.M
                c = p0 + d * (s + ancho / 2)
                ed_prueba = ED.Edificio(None, ancho, ny * K.M, 0, None)
                if _cabe(t, ed_prueba, c[0], c[1], frente):
                    ed = ED.edificio(nx2, ny, np_, int(rng.integers(1 << 30)), tipo, emblema=str(rng.choice(emblemas)))
                    poner_edificio(t, f"{prefijo}_{n:02d}", ed, c[0], c[1], frente, comprobar=False)
                    puesto = True
                    break
            if puesto:
                break
        if puesto:
            n += 1
            s += ancho + float(rng.uniform(*hueco))
        else:
            s += 4.0
    return n


# ==============================================================================================================
# Aurora
# ==============================================================================================================

AURORA = dict(
    plaza=44.0,  # semilado de la plaza mayor
    acera=3.0,
    calle_mayor=7.0,  # semiancho
    avenida=6.5,
    ronda=122.0,  # posición de la ronda (eje)
    ronda_semiancho=5.0,
    secundaria=4.5,
    limite=200.0,
)


def aurora():
    A = AURORA
    t = Trazado("Aurora")
    rng = np.random.default_rng(2024)
    P, ac, cm, av, R, rs, Lm = (A["plaza"], A["acera"], A["calle_mayor"], A["avenida"], A["ronda"],
                                A["ronda_semiancho"], A["limite"])

    # ---------------------------------------------------------------- suelo y calles
    t.suelos.append(("cesped_ciudad", ("rect", -Lm, -Lm, Lm, Lm, 30.0)))
    # Retícula: (eje, posición, semiancho, desde, hasta). Eje "h": calle este-oeste en v = posición.
    calles = [
        ("h", 0.0, cm, -Lm - 30, Lm + 30),  # calle mayor: sale por las puertas este y oeste
        ("v", 0.0, av, -Lm - 30, -P),  # avenida sur
        ("v", 0.0, av, 86.0, Lm + 30),  # avenida norte (empieza detrás del ayuntamiento)
        ("h", R, rs, -R - rs, R + rs), ("h", -R, rs, -R - rs, R + rs),  # ronda
        ("v", R, rs, -R - rs, R + rs), ("v", -R, rs, -R - rs, R + rs),
        ("h", 82.0, A["secundaria"], -R, R), ("h", -82.0, A["secundaria"], -R, R),  # calles secundarias
        ("v", 82.0, A["secundaria"], -R, R), ("v", -82.0, A["secundaria"], -R, R),
    ]
    for (eje, c, w, a0, a1) in calles:
        r = (a0, c - w, a1, c + w) if eje == "h" else (c - w, a0, c + w, a1)
        t.suelos.append(("adoquin", ("rect", *r, 0.0)))
        t.ocupado.append(r)
    # aceras (losas claras) junto a las fachadas de la calle mayor y la plaza
    t.suelos.append(("losas", ("rect", -Lm, -cm - ac, Lm, cm + ac, 0.0)))
    t.suelos.append(("losas", ("rect", -av - ac, -Lm, av + ac, -P, 0.0)))
    t.suelos.append(("losas", ("rect", -P - ac - 1, -P - ac - 1, P + ac + 1, 80, 4.0)))
    t.suelos.append(("plaza", ("rect", -P, -P, P, P, 6.0)))
    t.suelos.append(("plaza_anillo", ("circulo", 0.0, 0.0, 17.0)))
    t.ocupado.append((-P - ac, -P - ac, P + ac, P + ac))

    # ---------------------------------------------------------------- plaza mayor
    poner(t, "Fuente", 0.0, 0.0)
    for k in range(8):  # bancos alrededor de la fuente, mirando a ella
        a = 2 * math.pi * (k + 0.5) / 8
        poner(t, "Banco", 21 * math.cos(a), 21 * math.sin(a), math.degrees(a) + 90 + 180)
    for sx in (-1, 1):  # cerezos en las esquinas de la plaza
        for sy in (-1, 1):
            poner(t, "Maceta_B", sx * (P - 6), sy * (P - 6), 0.0, escala=2.2)
            poner(t, "Arbol_Flor" if sx * sy > 0 else "Arbol_Flor_B", sx * (P - 6), sy * (P - 6), 30.0 * sx, dz=4.0)
    for k in range(9):  # farolas en el perímetro
        x = -P + 4 + k * (2 * P - 8) / 8
        if abs(x) > 9:
            poner(t, "Farola", x, -P + 2.5)
            poner(t, "Farola", x, P - 2.5)
            poner(t, "Farola", -P + 2.5, x)
            poner(t, "Farola", P - 2.5, x)
    # mercado: puestos en la mitad sur de la plaza
    for k, x in enumerate((-32.0, -21.0, 21.0, 32.0)):
        poner(t, ("Puesto_A", "Puesto_B", "Puesto_C")[k % 3], x - 4, -30.0, 0.0)
    poner(t, "Carro", -36.0, -16.0, 75.0)
    poner(t, "Barril", 26.0, -20.0)
    poner(t, "Caja", 28.0, -21.5, 20.0)
    poner(t, "Tablon_Misiones", -22.0, 34.0, 0.0)

    # ayuntamiento al norte, mirando a la plaza; torre del reloj en la esquina noreste
    ayto = ED.ayuntamiento()
    poner_edificio(t, "Aurora_Ayuntamiento", ayto, 0.0, P + ac + 4.0, -90.0, comprobar=False)
    t.ocupado.append((-P - 4, P + ac, P + 4, 80))
    poner(t, "Torre_Reloj", P + 18.0, P + 16.0, 0.0)
    t.ocupado.append((P + 8, P + 6, P + 28, P + 26))
    for x in (-12.0, 12.0):
        poner(t, "Maceta", x, P + ac + 0.5)

    # tiendas de la plaza (planta baja con escaparate, toldo y cartel)
    tiendas_plaza = [
        ("Aurora_Tienda_General", "bolsa", (P + ac, 26.0), 180.0),
        ("Aurora_Armeria", "espada", (P + ac, -26.0), 180.0),
        ("Aurora_Materiales", "gema", (-P - ac, 26.0), 0.0),
        ("Aurora_Pociones", "pocion", (-P - ac, -26.0), 0.0),
        ("Aurora_Taller_Naves", "yunque", (-26.0, -P - ac), 90.0),
        ("Aurora_Panaderia", "pan", (26.0, -P - ac), 90.0),
    ]
    for k, (nombre, emb, (fu, fv), fr) in enumerate(tiendas_plaza):
        ed = ED.edificio(4, 3, 3, 500 + k, "tienda", emblema=emb)
        poner_edificio(t, nombre, ed, fu, fv, fr, comprobar=False)
    # casas de tres pisos que cierran las esquinas de la plaza junto al ayuntamiento
    poner_edificio(t, "Aurora_Plaza_NO", ED.edificio(2, 3, 3, 520, "casa"), -P - ac, P - 8.0, 0.0, comprobar=False)

    # ---------------------------------------------------------------- frentes de calle
    # Cada calle tiene dos frentes (uno por lado); se parten en los cruces con las calles perpendiculares.
    emb = ("bolsa", "pan", "pocion", "gema")
    f = 0
    for (eje, c, w, a0, a1) in calles:
        cortes = sorted([cc for (e2, cc, w2, b0, b1) in calles if e2 != eje and b0 - 1 <= c <= b1 + 1])
        anchos = {cc: w2 for (e2, cc, w2, b0, b1) in calles if e2 != eje}
        lim = [max(a0, -Lm + 4)] + [x for cc in cortes for x in (cc - anchos[cc] - 2, cc + anchos[cc] + 2)] + \
              [min(a1, Lm - 4)]
        principal = eje == "h" and c == 0.0
        for k in range(0, len(lim) - 1, 2):
            s0, s1 = lim[k], lim[k + 1]
            if s1 - s0 < 18:
                continue
            e = w + (ac if principal else 2.0)
            pisos = (2, 3, 3) if principal else (2, 2, 3)
            tiendas = 0.35 if principal else 0.08
            if eje == "h":
                f += rellenar_frente(t, f"Aurora_C{f}", (s0, c + e), (s1, c + e), -90.0, rng, ("casa",), pisos=pisos,
                                     tiendas=tiendas, emblemas=emb, hueco=(0.6, 2.0))
                f += rellenar_frente(t, f"Aurora_C{f}", (s1, c - e), (s0, c - e), 90.0, rng, ("casa",), pisos=pisos,
                                     tiendas=tiendas, emblemas=emb, hueco=(0.6, 2.0))
            else:
                f += rellenar_frente(t, f"Aurora_C{f}", (c + e, s1), (c + e, s0), 180.0, rng, ("casa",), pisos=pisos,
                                     hueco=(0.6, 2.0))
                f += rellenar_frente(t, f"Aurora_C{f}", (c - e, s0), (c - e, s1), 0.0, rng, ("casa",), pisos=pisos,
                                     hueco=(0.6, 2.0))

    # ---------------------------------------------------------------- mobiliario de calles
    for x in np.arange(-Lm + 10, Lm - 5, 24.0):
        if abs(x) > P + 6 and abs(abs(x) - R) > rs + 4:
            poner(t, "Farola", x, cm + 1.5)
            poner(t, "Farola", x + 12, -cm - 1.5)
    for y in list(np.arange(-Lm + 10, -P - 6, 24.0)) + list(np.arange(84, Lm - 5, 24.0)):
        if abs(abs(y) - R) > rs + 4:
            poner(t, "Farola", av + 1.5, y)
            poner(t, "Farola", -av - 1.5, y + 12)
    # portales en las cuatro entradas
    poner(t, "Portal_Ciudad", Lm - 2, 0.0, 90.0)
    poner(t, "Portal_Ciudad", -Lm + 2, 0.0, 90.0)
    poner(t, "Portal_Ciudad", 0.0, -Lm + 2, 0.0)
    poner(t, "Portal_Ciudad", 0.0, Lm - 2, 0.0)

    # ---------------------------------------------------------------- jardines: árboles donde no hay nada
    huecos = 0
    for k in range(2600):
        u, v = rng.uniform(-Lm + 6, Lm - 6, 2)
        c = (u - 3, v - 3, u + 3, v + 3)
        if not _solapa(c, t.ocupado, 2.5):
            poner(t, str(rng.choice(["Arbol_Frondoso", "Arbol_Flor", "Arbusto", "Arbusto_B", "Arbol_Flor_B"],
                                    p=[0.35, 0.12, 0.25, 0.2, 0.08])), u, v, float(rng.uniform(0, 360)),
                  escala=float(rng.uniform(0.75, 1.05)))
            t.ocupado.append((u - 5, v - 5, u + 5, v + 5))
            huecos += 1
            if huecos > 140:
                break
    return t


# ==============================================================================================================
# Pradoverde
# ==============================================================================================================


def pradoverde():
    t = Trazado("Pradoverde")
    rng = np.random.default_rng(77)
    # suelo: tierra apisonada en el centro y los caminos, césped en el prado
    t.suelos.append(("cesped_pueblo", ("rect", -60, -60, 60, 60, 20.0)))
    t.suelos.append(("tierra", ("circulo", 0.0, 0.0, 26.0)))
    t.suelos.append(("prado", ("circulo", 0.0, 0.0, 11.0)))
    t.suelos.append(("tierra", ("linea", [(-75.0, 0.0), (-24.0, 0.0)], 9.0)))
    t.suelos.append(("tierra", ("linea", [(22.0, 4.0), (40.0, 12.0), (75.0, 10.0)], 6.0)))
    t.suelos.append(("tierra", ("linea", [(-10.0, -24.0), (-12.0, -48.0)], 5.0)))
    t.suelos.append(("tierra", ("linea", [(6.0, 24.0), (14.0, 44.0)], 5.0)))
    t.ocupado += [(-60, -5, -24, 5), (-26, -26, 26, 26)]

    poner(t, "Pozo", 0.0, 0.0, 15.0)
    poner(t, "Tablon_Misiones", -20.0, -8.0, 90.0)  # de cara al que llega por el camino del oeste
    poner(t, "Poste_Indicador", -24.0, 7.0, 0.0)
    # la casa del jugador: al este, mirando al prado, con su jardín vallado
    casa = ED.edificio(2, 2, 2, 31, "rustica", puerta_en="frente", puerta_i=1,
                       remap_extra={"PUERTA": "Pintura_Azul", "PINTURA": "Pintura_Azul", "PARED": "Yeso_Blanco",
                                    "TEJA": "Teja_Roja", "TEJA_B": "Teja_Roja_Oscura"})
    poner_edificio(t, "Pradoverde_Casa_Jugador", casa, 34.0, -8.0, 180.0, comprobar=False)
    t.ocupado.append((34, -16, 52, 10))
    for k in range(3):
        poner(t, "Valla_Madera", 31.0, -26.0 + 8 * k + 0.0, 90.0)  # lado oeste del jardín (sur de la casa)
    for k in range(3):
        poner(t, "Valla_Madera", 31.0 + 8 * k, -26.0, 0.0)
    poner(t, "Arbol_Flor", 44.0, -20.0, 10.0)
    poner(t, "Banco", 36.0, -18.0, 180.0)
    poner(t, "Maceta", 30.5, -1.0)
    poner(t, "Maceta_B", 30.5, 9.5)
    # la tienda del pueblo, al noroeste, mirando al sur
    tienda = ED.edificio(3, 2, 2, 41, "tienda", emblema="bolsa", remap_extra={"PARED": "Yeso_Amarillo"})
    poner_edificio(t, "Pradoverde_Tienda", tienda, -22.0, 30.0, -90.0, comprobar=False)
    t.ocupado.append((-34, 30, -10, 48))
    poner(t, "Barril", -36.0, 27.0)
    poner(t, "Caja", -38.5, 24.0, 12.0)
    poner(t, "Carro", -42.0, 16.0, 200.0)
    # casas pequeñas
    casas = [((10.0, 32.0), -90.0, 2, 2, 2), ((32.0, 34.0), -90.0, 2, 2, 1), ((-30.0, -30.0), 90.0, 2, 2, 2),
             ((-4.0, -34.0), 90.0, 3, 2, 1), ((22.0, -38.0), 90.0, 2, 2, 2), ((-46.0, 34.0), -90.0, 2, 2, 1),
             ((-48.0, -24.0), 0.0, 2, 2, 2)]
    for k, ((fu, fv), fr, nx, ny, np_) in enumerate(casas):
        ed = ED.edificio(nx, ny, np_, 60 + k, "rustica")
        poner_edificio(t, f"Pradoverde_Casa_{k:02d}", ed, fu, fv, fr, comprobar=False)
    # vallas de huertos, pajar, cerezos, farolas
    for k in range(4):
        poner(t, "Valla_Madera", -58.0 + 8 * k, -44.0, 0.0)
        poner(t, "Valla_Madera", 8.0 + 8 * k, -54.0, 0.0)
    poner(t, "Pajar", -52.0, -48.0, 0.0)
    for (u, v, s) in ((-14.0, 18.0, 1.0), (16.0, -18.0, 0.9), (-38.0, 20.0, 0.85), (50.0, 26.0, 1.1), (-8.0, 50.0, 0.9)):
        poner(t, "Arbol_Flor" if u < 0 else "Arbol_Flor_B", u, v, float(rng.uniform(0, 360)), escala=s)
    for (u, v) in ((-24.0, -14.0), (16.0, 20.0), (22.0, -6.0), (-12.0, -22.0)):
        poner(t, "Farola", u, v)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(50, 64)
        poner(t, str(rng.choice(["Arbusto", "Arbusto_B"])), r * math.cos(a), r * math.sin(a), 0.0)
    return t


# ==============================================================================================================
# Los Molinos
# ==============================================================================================================


def los_molinos(valle=None, sitio=None):
    t = Trazado("LosMolinos")
    rng = np.random.default_rng(303)
    t.suelos.append(("cesped_pueblo", ("rect", -60, -60, 60, 60, 20.0)))
    t.suelos.append(("tierra", ("rect", -26, -30, 20, 14, 8.0)))  # era (patio de trillar)
    t.suelos.append(("tierra", ("linea", [(0.0, 75.0), (0.0, 14.0)], 8.0)))
    t.suelos.append(("tierra", ("linea", [(0.0, -30.0), (0.0, -75.0)], 7.0)))
    for (u, v, nombre, giro) in ((-34.0, 34.0, "Molino", 225.0), (24.0, 42.0, "Molino_B", 225.0),
                                 (44.0, -22.0, "Molino_C", 225.0)):
        # las aspas miran al suroeste, de donde viene el viento; escala 1,5: el molino manda sobre las casas
        poner(t, nombre, u, v, _yaw(giro), escala=1.5)
        t.suelos.append(("tierra", ("circulo", u, v, 18.0)))
        t.ocupado.append((u - 16, v - 16, u + 16, v + 16))
    casas = [((-34.0, -8.0), 0.0, 3, 2, 2, "rustica"), ((-4.0, -36.0), 90.0, 4, 3, 1, "rustica"),
             ((16.0, 4.0), -90.0, 2, 2, 2, "rustica"), ((30.0, -44.0), 90.0, 2, 2, 1, "rustica")]
    for k, ((fu, fv), fr, nx, ny, np_, tipo) in enumerate(casas):
        ed = ED.edificio(nx, ny, np_, 90 + k, tipo, remap_extra={"PARED": ["Yeso_Blanco", "Yeso_Crema"][k % 2]})
        poner_edificio(t, f"LosMolinos_Casa_{k:02d}", ed, fu, fv, fr, comprobar=False)
    poner(t, "Pozo", -6.0, -8.0, 0.0)
    poner(t, "Tablon_Misiones", 6.0, 16.0, 0.0)
    poner(t, "Carro", -14.0, 4.0, 30.0)
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi)
        poner(t, "Pajar", -12 + 14 * math.cos(a) * 0.5, -18 + 8 * math.sin(a) * 0.6 + k * 0.0, 0.0)
    for (u, v) in ((10.0, -14.0), (12.0, -10.0), (-20.0, -22.0)):
        poner(t, "Barril", u, v)
    poner(t, "Caja", -22.0, -25.0, 30.0)
    for k in range(6):
        poner(t, "Valla_Madera", -56.0 + 8 * k, 56.0, 0.0)
        poner(t, "Valla_Madera", 56.0, -56.0 + 8 * k, 90.0)
    for (u, v) in ((-4.0, 20.0), (8.0, -20.0)):
        poner(t, "Farola", u, v)
    # campos de cultivo alrededor: parcelas en una retícula girada
    t.parcelas = parcelas_molinos(rng)
    for p in t.parcelas:
        if p["cultivo"] in ("trigo", "barbecho") and rng.uniform() < 0.35:
            cu, cv = p["centro"]
            poner(t, "Espantapajaros", cu, cv, float(rng.uniform(0, 360)))
    return t


CULTIVOS = ["trigo", "trigo", "col", "arado", "lavanda", "calabaza", "barbecho", "trigo"]


def parcelas_molinos(rng, radio=(300.0, 250.0), giro=18.0):
    """Parcelas rectangulares (u, v locales) en una retícula girada, fuera del núcleo del pueblo."""
    parcelas = []
    g = math.radians(giro)
    eu = np.array([math.cos(g), math.sin(g)])
    ev = np.array([-math.sin(g), math.cos(g)])
    for i in range(-6, 7):
        for j in range(-4, 5):
            ancho = 46.0
            largo = 74.0
            c = eu * i * (ancho + 4) + ev * j * (largo + 4) + eu * rng.uniform(-2, 2)
            if (c[0] / radio[0]) ** 2 + (c[1] / radio[1]) ** 2 > 1.0:
                continue
            if abs(c[0]) < 70 + ancho / 2 and abs(c[1]) < 70 + largo / 2:
                continue
            parcelas.append(dict(centro=(float(c[0]), float(c[1])), ancho=ancho, largo=largo, giro=giro,
                                 cultivo=str(rng.choice(CULTIVOS))))
    return parcelas


def todos():
    return {"Aurora": aurora(), "Pradoverde": pradoverde(), "LosMolinos": los_molinos()}
