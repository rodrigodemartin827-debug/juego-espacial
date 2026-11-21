"""
Piezas reutilizables para las naves humanas (Interceptor, Fragata, Acorazado) y el kit modular.

Estética humana: metal gris-azulado con paneles y remaches, detalles blancos/negros y neón cyan #3DF2FF
(rojo #FF4444 solo en la bodega del acorazado). Todo con volumen real: cada panel tiene grosor, cada cañón
un cuerpo cilíndrico, cada barandilla barras de verdad. Nada de planos con textura.

Convención de ejes (igual que el resto del proyecto):
  * Se construye en studs. La nave mira a -Y en Blender (el "delante" de Roblox, -Z). Su derecha es -X.
  * +Z es arriba. La cubierta principal se sitúa en z = 0 salvo que se diga otra cosa.
  * comun.objeto_desde_bmesh escala a metros (1 stud = 0,28 m) al crear el objeto.

Cada nave se compone de PIEZAS separadas (un objeto por pieza) para que el director las mueva, las dañe por
secciones y las optimice. El neón va SIEMPRE en objetos aparte (en Studio: Material = Neon). Las marcas de
interacción (dónde se para el jugador) son discos finos de 0,5 studs en su propio objeto.

Las piezas de metal se crean todas con la MISMA lista de materiales, así los índices valen en cualquier bmesh:
  M_CASCO, M_PANEL, M_OSCURO, M_BLANCO, M_GRIP, M_CRISTAL
El neón usa su propia lista: [cyan] o [cyan, rojo].
"""

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

import comun as c

# --------------------------------------------------------------------------------------------------------------
# Paleta humana
# --------------------------------------------------------------------------------------------------------------

PALETA = {
    "Casco":   ("#5A6B86", 0.46, 0.80),   # gris-azulado del blindaje
    "Panel":   ("#45566E", 0.52, 0.72),   # panel algo más oscuro para romper la superficie
    "Oscuro":  ("#222834", 0.55, 0.55),   # grafito de juntas, toberas y detalles negros
    "Blanco":  ("#D7E0EE", 0.40, 0.25),   # franjas y detalles claros
    "Grip":    ("#374152", 0.80, 0.35),   # suelo antideslizante (rugoso, poco metal)
    "Cristal": ("#16324F", 0.06, 0.10),   # ventanas (en Studio: Glass/semitransparente)
}
CYAN = "#3DF2FF"
ROJO = "#FF4444"

# Índices de material para cualquier objeto de metal (orden fijo).
M_CASCO, M_PANEL, M_OSCURO, M_BLANCO, M_GRIP, M_CRISTAL = range(6)
_ORDEN_METAL = ["Casco", "Panel", "Oscuro", "Blanco", "Grip", "Cristal"]


def materiales_metal():
    """Lista de materiales de metal en el orden de los índices M_*."""
    return [c.material(n, c.srgb(PALETA[n][0]), PALETA[n][1], PALETA[n][2]) for n in _ORDEN_METAL]


def materiales_neon(con_rojo=False):
    """Materiales de neón: cyan (y rojo opcional). Emisión fuerte para que se vea espectacular."""
    mats = [c.material("NeonCyan", c.srgb(CYAN), 0.25, 0.0, emision=c.srgb(CYAN), fuerza_emision=6.0)]
    if con_rojo:
        mats.append(c.material("NeonRojo", c.srgb(ROJO), 0.3, 0.0, emision=c.srgb(ROJO), fuerza_emision=5.0))
    return mats


def material_marca():
    """Disco de interacción: cyan tenue, un pelín emisivo para que se distinga en el suelo."""
    return c.material("Marca", c.srgb(CYAN), 0.4, 0.0, emision=c.srgb(CYAN), fuerza_emision=1.4)


# --------------------------------------------------------------------------------------------------------------
# Primitivos de malla (todos escriben en un bmesh dado, en studs)
# --------------------------------------------------------------------------------------------------------------


def caja(bm, centro, tam, mat=0, giro=None):
    """Cubo de dimensiones `tam` centrado en `centro`. `giro` es un Euler opcional."""
    r = bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Diagonal((*tam, 1.0))
    if giro is not None:
        m = (giro.to_matrix() if isinstance(giro, Euler) else giro).to_4x4() @ m
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(centro)) @ m, verts=r["verts"])
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
    return r["verts"]


def cilindro(bm, centro, radio, alto, lados=16, mat=0, eje="Z", giro=None, radio2=None):
    """Cilindro (o cono truncado si radio2) con `alto` a lo largo de `eje`, centrado en `centro`."""
    r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=lados,
                              radius1=radio, radius2=radio if radio2 is None else radio2, depth=alto)
    base = {"Z": Matrix.Identity(4),
            "Y": Matrix.Rotation(math.radians(90), 4, "X"),
            "X": Matrix.Rotation(math.radians(90), 4, "Y")}[eje]
    if giro is not None:
        base = (giro.to_matrix() if isinstance(giro, Euler) else giro).to_4x4() @ base
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(centro)) @ base, verts=r["verts"])
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
    return r["verts"]


def cuna(bm, centro, tam, mat=0, giro=None):
    """Prisma triangular (rampa/ariete): base `tam.x` x `tam.y`, sube hasta `tam.z`. La cara inclinada mira a -Y."""
    sx, sy, sz = tam
    x, y, z = centro
    # Vértices: rectángulo inferior + arista superior trasera.
    v = [bm.verts.new((x - sx / 2, y - sy / 2, z)),
         bm.verts.new((x + sx / 2, y - sy / 2, z)),
         bm.verts.new((x + sx / 2, y + sy / 2, z)),
         bm.verts.new((x - sx / 2, y + sy / 2, z)),
         bm.verts.new((x - sx / 2, y + sy / 2, z + sz)),
         bm.verts.new((x + sx / 2, y + sy / 2, z + sz))]
    caras = [(v[0], v[1], v[2], v[3]), (v[3], v[2], v[5], v[4]),
             (v[0], v[4], v[5], v[1]), (v[0], v[3], v[4]), (v[1], v[5], v[2])]
    fs = []
    for cc in caras:
        try:
            fs.append(bm.faces.new(cc))
        except ValueError:
            pass
    if giro is not None:
        g = (giro.to_matrix() if isinstance(giro, Euler) else giro)
        bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(centro)) @ g.to_4x4() @ Matrix.Translation(-Vector(centro)),
                            verts=v)
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    for f in fs:
        f.material_index = mat
    return v


def superelipse(y, ancho, alto, zc, n, cuadratura, xc=0.0):
    """Sección superelíptica en XZ a la altura `y` (como anillo_superelipse del casco)."""
    pts = []
    for i in range(n):
        a = math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (2 / cuadratura), ca) * ancho / 2
        z = math.copysign(abs(sa) ** (2 / cuadratura), sa) * alto / 2
        pts.append(Vector((xc + x, y, zc + z)))
    return pts


def loft(bm, anillos, tapar_inicio=True, tapar_fin=True, mat=0):
    """Une anillos (mismo nº de puntos) en un tubo. Devuelve (vertices, caras)."""
    vs = [[bm.verts.new(p) for p in a] for a in anillos]
    n = len(anillos[0])
    caras = []
    for k in range(len(vs) - 1):
        for i in range(n):
            j = (i + 1) % n
            caras.append(bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i])))
    if tapar_inicio:
        caras.append(bm.faces.new(list(reversed(vs[0]))))
    if tapar_fin:
        caras.append(bm.faces.new(vs[-1]))
    for f in caras:
        f.material_index = mat
    return vs, caras


def espejo_x(bm, verts):
    """Duplica `verts` y sus caras reflejados en X (para piezas simétricas babor/estribor)."""
    caras = list({f for v in verts for f in v.link_faces if all(w in verts for w in f.verts)})
    if not caras:
        return []
    res = bmesh.ops.duplicate(bm, geom=caras)
    nuevos = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.scale(bm, vec=(-1, 1, 1), verts=nuevos)
    bmesh.ops.reverse_faces(bm, faces=[g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)])
    return nuevos


# --------------------------------------------------------------------------------------------------------------
# Paneles y remaches (para dar relieve de verdad al blindaje)
# --------------------------------------------------------------------------------------------------------------


def placa(bm, centro, tam, mat=M_CASCO, borde=0.12, rehundido=0.06, mat_junta=M_OSCURO, remaches=True, giro=None):
    """
    Placa de blindaje con volumen: un panel central ligeramente rehundido rodeado de un marco (la junta).
    `tam` = (ancho X, fondo Y, grosor Z). El relieve va en +Z (la cara de arriba). `giro` rota la placa entera.
    """
    sx, sy, sz = tam
    x, y, z = centro
    nuevos = []
    # Marco/base.
    nuevos += caja(bm, (x, y, z), (sx, sy, sz), mat=mat_junta)
    # Panel central, un poco más alto para que sobresalga y más estrecho (deja ver la junta).
    px, py = max(0.2, sx - 2 * borde), max(0.2, sy - 2 * borde)
    nuevos += caja(bm, (x, y, z + sz / 2 + (sz * 0.5 - rehundido) / 2), (px, py, max(0.04, sz - rehundido)), mat=mat)
    if remaches and min(px, py) > 1.2:
        rr = 0.07
        for dx in (-px / 2 + borde, px / 2 - borde):
            for dy in (-py / 2 + borde, py / 2 - borde):
                nuevos += cilindro(bm, (x + dx, y + dy, z + sz / 2 + 0.03), rr, 0.05, lados=6, mat=mat_junta)
    if giro is not None:
        g = (giro.to_matrix() if isinstance(giro, Euler) else giro).to_4x4()
        m = Matrix.Translation(Vector(centro)) @ g @ Matrix.Translation(-Vector(centro))
        bmesh.ops.transform(bm, matrix=m, verts=list(set(nuevos)))


def franja_neon(bm_neon, centro, tam, mat=0):
    """Línea de energía: una tira fina. `tam` = (X, Y, Z). Va en un bmesh de neón."""
    caja(bm_neon, centro, tam, mat=mat)


# --------------------------------------------------------------------------------------------------------------
# Barandillas
# --------------------------------------------------------------------------------------------------------------


def barandilla(bm, puntos, alto=0.8, grosor=0.08, mat=M_OSCURO, paso=2.2, mat_pasamanos=M_BLANCO):
    """
    Barandilla a lo largo de `puntos` (lista de Vector en studs, a la altura del suelo).
    Postes verticales cada ~`paso`, pasamanos arriba y barra intermedia. Llega a la cintura de un R6 (~0,8 studs).
    """
    for a, b in zip(puntos, puntos[1:]):
        seg = (b - a)
        largo = seg.length
        if largo < 1e-3:
            continue
        dirn = seg / largo
        # Postes.
        n = max(1, int(round(largo / paso)))
        for i in range(n + 1):
            p = a + dirn * (largo * i / n)
            caja(bm, (p.x, p.y, p.z + alto / 2), (grosor, grosor, alto), mat=mat)
        medio = (a + b) / 2
        ang = math.atan2(dirn.y, dirn.x)
        giro = Euler((0, 0, ang))
        # Pasamanos superior y barra intermedia.
        caja(bm, (medio.x, medio.y, medio.z + alto), (largo, grosor * 1.4, grosor * 1.4), mat=mat_pasamanos, giro=giro)
        caja(bm, (medio.x, medio.y, medio.z + alto * 0.5), (largo, grosor, grosor), mat=mat, giro=giro)


# --------------------------------------------------------------------------------------------------------------
# Estaciones interactivas
# --------------------------------------------------------------------------------------------------------------


def marca(bm_marca, centro, diametro=0.5, mat=0):
    """Disco fino de interacción (donde el director pone el ProximityPrompt). Va en el bmesh de marcas."""
    cilindro(bm_marca, (centro[0], centro[1], centro[2] + 0.03), diametro / 2, 0.06, lados=16, mat=mat)


def canon(bm, bm_neon, base, longitud=2.6, dobles=False, mat=M_CASCO, mat_neon=0, radio=0.26):
    """
    Torreta láser: pedestal + anillo giratorio + horquilla + asiento + 1 o 2 cañones apuntando a -Y, con boca neón.
    `base` es el punto del suelo donde se apoya. Deja clearance para girar (nada pega al suelo salvo el pedestal).
    """
    x, y, z = base
    # Pedestal y anillo de giro.
    cilindro(bm, (x, y, z + 0.25), 0.55, 0.5, lados=16, mat=M_OSCURO)
    cilindro(bm, (x, y, z + 0.55), 0.62, 0.16, lados=20, mat=mat)
    cuerpo_z = z + 0.95
    # Cuerpo giratorio (lo que el director rota): caja compacta.
    caja(bm, (x, y, cuerpo_z), (1.3, 1.3, 0.7), mat=mat)
    placa(bm, (x, y, cuerpo_z + 0.35), (1.1, 1.1, 0.12), mat=M_PANEL, borde=0.18, remaches=False)
    # Asiento del artillero (detrás, hacia +Y).
    caja(bm, (x, y + 0.75, cuerpo_z + 0.1), (0.7, 0.5, 0.12), mat=M_OSCURO)
    caja(bm, (x, y + 1.0, cuerpo_z + 0.5), (0.7, 0.12, 0.8), mat=M_OSCURO)
    # Horquilla y cañones hacia -Y.
    offsets = (-0.3, 0.3) if dobles else (0.0,)
    for ox in offsets:
        cilindro(bm, (x + ox, y - longitud / 2, cuerpo_z + 0.25), radio, longitud, lados=12, eje="Y", mat=M_OSCURO)
        cilindro(bm, (x + ox, y - longitud * 0.78, cuerpo_z + 0.25), radio * 1.25, longitud * 0.3, lados=12,
                 eje="Y", mat=mat)  # manguito
        # Boca neón.
        cilindro(bm_neon, (x + ox, y - longitud - 0.02, cuerpo_z + 0.25), radio * 0.7, 0.14, lados=10,
                 eje="Y", mat=mat_neon)
    return (x, y + 1.15, cuerpo_z + 0.1)  # dónde se para/sienta el artillero (para la marca)


def tobera(bm, bm_neon, centro, radio=0.9, largo=2.4, mat=M_OSCURO, mat_neon=0):
    """Propulsor de plasma: góndola cilíndrica + campana acampanada con pared interior + núcleo brillante (neón)."""
    x, y, z = centro  # y = extremo de popa (la boca mira a +Y)
    # Góndola.
    cilindro(bm, (x, y - largo * 0.7, z), radio, largo, lados=18, eje="Y", mat=M_CASCO)
    cilindro(bm, (x, y - largo * 0.7, z), radio * 1.08, largo * 0.25, lados=18, eje="Y", mat=mat)  # anillo
    # Campana (cono que se abre hacia +Y) con pared interior para que tenga grosor.
    perfil = [(0.0, radio * 0.95), (0.3, radio * 0.9), (0.7, radio * 1.05), (1.15, radio * 1.25), (1.4, radio * 1.3)]
    ext = [superelipse(y + dy, r * 2, r * 2, z, 18, 2.0, xc=x) for dy, r in perfil]
    inte = [superelipse(y + dy, (r - 0.1) * 2, (r - 0.1) * 2, z, 18, 2.0, xc=x) for dy, r in reversed(perfil)]
    _, caras = loft(bm, ext + inte, tapar_inicio=False, tapar_fin=True, mat=mat)
    # Núcleo brillante dentro de la campana.
    cilindro(bm_neon, (x, y + 0.25, z), radio * 0.8, 0.5, lados=16, eje="Y", mat=mat_neon, radio2=radio * 0.45)


def consola_timon(bm, bm_neon, base, mat=M_CASCO, mat_neon=0):
    """Timón: consola inclinada con pantalla holográfica (neón) + aro de timón + joysticks. El piloto va detrás (+Y)."""
    x, y, z = base
    # Pie y cuerpo.
    caja(bm, (x, y, z + 0.4), (1.6, 0.9, 0.8), mat=M_OSCURO)
    caja(bm, (x, y - 0.1, z + 0.95), (1.7, 1.0, 0.5), mat=mat, giro=Euler((math.radians(-28), 0, 0)))
    # Pantalla holográfica inclinada (neón).
    caja(bm_neon, (x, y - 0.33, z + 1.18), (1.35, 0.06, 0.52), mat=mat_neon, giro=Euler((math.radians(-28), 0, 0)))
    # Aro de timón al frente: anillo grueso (dos cilindros concéntricos) + radios.
    cilindro(bm, (x, y - 0.55, z + 1.25), 0.45, 0.08, lados=24, eje="Y", mat=M_BLANCO)
    cilindro(bm, (x, y - 0.56, z + 1.25), 0.33, 0.12, lados=24, eje="Y", mat=M_OSCURO)
    # Joysticks a los lados.
    for s in (-1, 1):
        caja(bm, (x + s * 0.95, y + 0.05, z + 0.95), (0.12, 0.12, 0.45), mat=M_OSCURO)
        cilindro(bm, (x + s * 0.95, y + 0.05, z + 1.2), 0.09, 0.14, lados=8, mat=M_BLANCO)


def ancla(bm, bm_neon, base, plegada=True, mat=M_CASCO, mat_neon=0, lado=-1):
    """
    Ancla magnética: soporte + brazo articulado + garra de 3 dedos + palanca. Cadena de energía (neón).
    `lado` = -1 babor / +1 estribor (apunta hacia fuera en X). `plegada` la pega al casco.
    """
    x, y, z = base
    # Soporte y pivote.
    caja(bm, (x, y, z + 0.4), (1.0, 1.1, 0.8), mat=M_OSCURO)
    cilindro(bm, (x + lado * 0.5, y, z + 0.6), 0.22, 0.5, lados=12, eje="X", mat=mat)
    # Brazo (hacia fuera y abajo).
    bx = x + lado * 1.2
    caja(bm, (bx, y, z + 0.3), (1.6, 0.4, 0.4), mat=mat, giro=Euler((0, math.radians(lado * 25), 0)))
    # Garra: tres dedos.
    gx = x + lado * 2.0
    gz = z - 0.2
    cilindro(bm, (gx, y, gz), 0.35, 0.4, lados=10, eje="X", mat=M_OSCURO)
    for a in (-0.5, 0.0, 0.5):
        caja(bm, (gx + lado * 0.3, y + a * 0.35, gz - 0.25), (0.5, 0.14, 0.5), mat=mat,
             giro=Euler((math.radians(a * 20), math.radians(lado * 35), 0)))
    # Cadena de energía: segmentos de neón entre el soporte y la garra.
    for t in (0.3, 0.55, 0.8):
        px = x + lado * (0.5 + t * 1.5)
        pz = z + 0.5 - t * 0.7
        cilindro(bm_neon, (px, y, pz), 0.08, 0.22, lados=8, eje="X", mat=mat_neon)
    # Palanca de accionamiento (donde interactúa el jugador).
    caja(bm, (x - lado * 0.3, y + 0.5, z + 0.85), (0.1, 0.1, 0.6), mat=M_OSCURO,
         giro=Euler((math.radians(-30), 0, 0)))
    cilindro(bm, (x - lado * 0.3, y + 0.78, z + 1.3), 0.11, 0.14, lados=8, mat=M_BLANCO)
    return (x - lado * 0.3, y + 0.9, z)  # dónde se para el jugador


def escalera(bm, base, ancho=2.6, subida=4.0, fondo=4.0, pasos=7, mat=M_GRIP):
    """Escalera de peldaños que sube `subida` studs desde `base` hacia +Y, `fondo` de largo. Ancho >= 2,5 studs."""
    x, y, z = base
    for i in range(pasos):
        t = i / pasos
        pz = z + subida * (i + 0.5) / pasos
        py = y + fondo * t
        caja(bm, (x, py, pz - 0.15), (ancho, fondo / pasos + 0.1, 0.3), mat=mat)
        caja(bm, (x, py, pz), (ancho, 0.14, subida / pasos), mat=M_OSCURO)  # contrahuella
    # Zancas laterales.
    for s in (-1, 1):
        caja(bm, (x + s * ancho / 2, y + fondo / 2, z + subida / 2 - 0.1), (0.16, fondo * 1.1, 0.4), mat=M_OSCURO,
             giro=Euler((math.atan2(subida, fondo), 0, 0)))


def rampa(bm, base, ancho=4.0, subida=4.0, fondo=5.0, mat=M_GRIP):
    """Rampa inclinada (prisma) que sube `subida` en `fondo` desde `base` hacia +Y."""
    x, y, z = base
    cuna(bm, (x, y + fondo / 2, z), (ancho, fondo, subida), mat=mat)
    # Listones antideslizantes.
    for i in range(1, 6):
        t = i / 6
        caja(bm, (x, y + fondo * t, z + subida * t + 0.06), (ancho * 0.9, 0.12, 0.08), mat=M_OSCURO,
             giro=Euler((math.atan2(subida, fondo), 0, 0)))


def cofre(bm, bm_neon, centro, tam=(2.0, 2.0, 2.0), mat=M_CASCO, mat_neon=0):
    """Contenedor de carga metálico con tapa, cantoneras y un panel neón."""
    sx, sy, sz = tam
    x, y, z = centro
    caja(bm, (x, y, z + sz * 0.42), (sx, sy, sz * 0.84), mat=mat)
    placa(bm, (x, y - sy / 2, z + sz * 0.42), (sx * 0.8, sz * 0.5, 0.08), mat=M_PANEL,
          giro=Euler((math.radians(90), 0, 0)), remaches=False)
    # Tapa.
    caja(bm, (x, y, z + sz * 0.9), (sx * 1.04, sy * 1.04, sz * 0.18), mat=M_OSCURO)
    # Cantoneras.
    for dx in (-1, 1):
        for dy in (-1, 1):
            caja(bm, (x + dx * sx / 2, y + dy * sy / 2, z + sz * 0.42), (0.16, 0.16, sz * 0.84), mat=M_OSCURO)
    # Panel neón en el frente.
    franja_neon(bm_neon, (x, y - sy / 2 - 0.02, z + sz * 0.5), (sx * 0.4, 0.04, 0.14), mat=mat_neon)


def mesa_nav(bm, bm_neon, centro, mat=M_CASCO, mat_neon=0):
    """Mesa de navegación: base + tablero + proyección holográfica (cono de neón con 'planetas')."""
    x, y, z = centro
    cilindro(bm, (x, y, z + 0.1), 1.0, 0.2, lados=8, mat=M_OSCURO)
    cilindro(bm, (x, y, z + 0.55), 0.35, 0.8, lados=8, mat=mat)
    cilindro(bm, (x, y, z + 1.0), 1.3, 0.16, lados=24, mat=mat)  # tablero
    cilindro(bm, (x, y, z + 1.08), 1.15, 0.05, lados=24, mat=M_OSCURO)
    # Proyección: cono de neón hacia arriba + esferas pequeñas.
    cilindro(bm_neon, (x, y, z + 1.7), 1.0, 1.1, lados=20, mat=mat_neon, radio2=0.1)
    for a, rr, h in [(0, 0.45, 1.5), (2.1, 0.7, 1.9), (4.2, 0.55, 2.2)]:
        ic = bmesh.ops.create_icosphere(bm_neon, subdivisions=1, radius=0.12)
        bmesh.ops.transform(bm_neon, matrix=Matrix.Translation(
            (x + math.cos(a) * rr, y + math.sin(a) * rr, z + h)), verts=ic["verts"])
        for f in {f for v in ic["verts"] for f in v.link_faces}:
            f.material_index = mat_neon


def reparacion(bm, bm_neon, centro, mat=M_CASCO, mat_neon=0):
    """Puesto de reparación: panel con pantalla neón + bandeja de herramientas + soldador colgado."""
    x, y, z = centro
    caja(bm, (x, y, z + 1.2), (2.0, 0.3, 2.4), mat=mat)  # panel de pared
    placa(bm, (x, y - 0.15, z + 1.5), (1.6, 1.2, 0.12), mat=M_PANEL,
          giro=Euler((math.radians(90), 0, 0)), remaches=False)
    franja_neon(bm_neon, (x, y - 0.33, z + 1.7), (1.2, 0.04, 0.5), mat=mat_neon)
    # Bandeja de herramientas.
    caja(bm, (x, y - 0.5, z + 0.9), (1.8, 0.7, 0.12), mat=M_OSCURO)
    for dx in (-0.6, -0.2, 0.2, 0.6):
        caja(bm, (x + dx, y - 0.5, z + 1.0), (0.1, 0.1, 0.3), mat=M_BLANCO)  # herramientas


def cama(bm, bm_neon, centro, mat=M_CASCO, mat_neon=0):
    """Litera / punto de respawn: marco metálico + colchón + franja neón bajo el borde."""
    x, y, z = centro
    caja(bm, (x, y, z + 0.3), (2.0, 4.0, 0.3), mat=mat)       # base
    caja(bm, (x, y, z + 0.55), (1.8, 3.8, 0.25), mat=M_BLANCO)  # colchón
    caja(bm, (x, y + 1.9, z + 0.9), (2.0, 0.2, 0.9), mat=mat)   # cabecero
    franja_neon(bm_neon, (x, y, z + 0.1), (2.02, 4.02, 0.06), mat=mat_neon)


# --------------------------------------------------------------------------------------------------------------
# Decoración (para el kit modular)
# --------------------------------------------------------------------------------------------------------------


def lampara(bm, bm_neon, centro, mat=M_OSCURO, mat_neon=0):
    x, y, z = centro
    cilindro(bm, (x, y, z), 0.45, 0.2, lados=12, mat=mat)
    cilindro(bm_neon, (x, y, z - 0.14), 0.33, 0.08, lados=12, mat=mat_neon)


def antena(bm, bm_neon, base, mat=M_OSCURO, mat_neon=0):
    x, y, z = base
    cilindro(bm, (x, y, z + 0.25), 0.22, 0.5, lados=10, mat=mat)
    cilindro(bm, (x, y, z + 1.5), 0.05, 2.5, lados=6, mat=M_BLANCO)
    ic = bmesh.ops.create_icosphere(bm_neon, subdivisions=1, radius=0.14)
    bmesh.ops.transform(bm_neon, matrix=Matrix.Translation((x, y, z + 2.9)), verts=ic["verts"])
    for f in {f for v in ic["verts"] for f in v.link_faces}:
        f.material_index = mat_neon


def bandera(bm, bm_neon, base, mat=M_OSCURO, mat_neon=0):
    x, y, z = base
    cilindro(bm, (x, y, z + 1.5), 0.08, 3.0, lados=8, mat=mat)
    caja(bm, (x, y + 0.6, z + 2.4), (0.06, 1.2, 0.8), mat=M_BLANCO)   # tela (con grosor)
    franja_neon(bm_neon, (x, y + 0.6, z + 2.4), (0.07, 0.9, 0.12), mat=mat_neon)


def tuberia(bm, centro, largo=4.0, radio=0.15, eje="Y", mat=M_OSCURO):
    cilindro(bm, centro, radio, largo, lados=10, eje=eje, mat=mat)
    # Bridas en los extremos.
    off = Vector((0, 0, 0))
    off["XYZ".index(eje)] = largo / 2
    for s in (-1, 1):
        cilindro(bm, Vector(centro) + off * s, radio * 1.4, 0.15, lados=10, eje=eje, mat=M_BLANCO)


def panel_deco(bm, bm_neon, centro, mat=M_CASCO, mat_neon=0):
    x, y, z = centro
    caja(bm, (x, y, z), (2.0, 0.3, 2.0), mat=mat)
    franja_neon(bm_neon, (x, y - 0.17, z), (1.6, 0.04, 1.6), mat=mat_neon)
    # Rejas/datos: barras finas de neón.
    for i in range(-2, 3):
        franja_neon(bm_neon, (x + i * 0.3, y - 0.18, z), (0.06, 0.03, 1.4), mat=mat_neon)


def conector(bm_marca, centro, mat=0, diametro=0.2):
    """Punto de conexión del kit modular: cilindro de 0,2 studs en una cara (para los snaps del director)."""
    cilindro(bm_marca, centro, diametro / 2, 0.08, lados=8, mat=mat)


# --------------------------------------------------------------------------------------------------------------
# Ensamblado y salida
# --------------------------------------------------------------------------------------------------------------


def escribir_mapas_rm(ruta_base, tam, rough=0.46, metal=0.82, semilla=1):
    """Escribe <ruta_base>_roughness/_metalness/_emision.png (la emisión negra: el neón va aparte)."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(semilla)
    base = rng.random((tam // 16, tam // 16)).astype(np.float32)
    grande = np.array(Image.fromarray((base * 255).astype(np.uint8)).resize((tam, tam), Image.BILINEAR),
                      np.float32) / 255
    r = np.clip(rough + (grande - 0.5) * 0.12, 0, 1)
    m = np.clip(metal + (grande - 0.5) * 0.10, 0, 1)
    Image.fromarray((r * 255).astype(np.uint8), "L").save(f"{ruta_base}_roughness.png")
    Image.fromarray((m * 255).astype(np.uint8), "L").save(f"{ruta_base}_metalness.png")
    Image.fromarray(np.zeros((tam, tam), np.uint8), "L").save(f"{ruta_base}_emision.png")
    # Normal neutro (el relieve grande ya está en la geometría y en el color horneado con oclusión; el
    # microdetalle de paneles lo aporta el atlas tileable como SurfaceAppearance en Studio).
    plano = np.zeros((tam, tam, 3), np.uint8)
    plano[..., 0] = 128; plano[..., 1] = 128; plano[..., 2] = 255
    Image.fromarray(plano, "RGB").save(f"{ruta_base}_normal.png")


def a_roblox(p):
    """Blender (x, y, z) studs -> Roblox (x, y, z): X cambia de signo, Z<->Y."""
    x, y, z = p
    return (round(-x, 3), round(z, 3), round(y, 3))


def finalizar_nave(nombre, archivo, salida, piezas, casco, anclajes_rel, vistas_ext,
                   bake_interior=None, vista_interior=None, rapido=False, tam_tex=2048,
                   tope_tris=None, z_suelo=None, r6_pos=None, seccion=None):
    """
    Pipeline de salida común de las naves:
      * hornea el `casco` (color+AO+normal) en el atlas exterior y le pone la textura (lo que verá Studio),
      * escribe los mapas de rugosidad/metal/emisión exteriores (y los de interior si hay `bake_interior`),
      * exporta UN FBX con todas las `piezas` (dict nombre->obj) como objetos separados,
      * guarda el .blend, renderiza la hoja exterior (+ sección interior si se pasan `vista_interior`),
      * escribe anclajes.json con los puntos en ejes de Roblox,
      * imprime el resumen de triángulos y avisa si pasa del tope.
    `casco` es el objeto principal a texturizar. `bake_interior` es un objeto de interior opcional a hornear.
    """
    import os
    objs = list(piezas.values())
    tex = os.path.join(salida, "texturas")
    os.makedirs(tex, exist_ok=True)
    tam = 256 if rapido else tam_tex

    # Horneado del casco exterior.
    desplegar = c.desplegar_uv
    desplegar(casco, margen=0.01)
    c.hornear(casco, None, tam=tam, ruta_color=os.path.join(tex, f"{archivo}_ext_color.png"),
              ruta_normal=None, muestras=6 if rapido else 48)
    escribir_mapas_rm(os.path.join(tex, f"{archivo}_ext"), tam, rough=PALETA["Casco"][1], metal=PALETA["Casco"][2])
    # Normal exterior: baja resolución con relieve del atlas (el casco horneado no tiene alta, así que normal plano útil).
    if bake_interior is not None:
        desplegar(bake_interior, margen=0.01)
        c.hornear(bake_interior, None, tam=tam, ruta_color=os.path.join(tex, f"{archivo}_int_color.png"),
                  ruta_normal=None, muestras=6 if rapido else 40)
        escribir_mapas_rm(os.path.join(tex, f"{archivo}_int"), tam, rough=0.6, metal=0.4, semilla=5)

    # FBX + blend.
    c.exportar_fbx(os.path.join(salida, f"{archivo}.fbx"), objs)
    try:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(salida, f"{archivo}.blend"))
    except Exception as e:  # noqa: BLE001
        print("[aviso] no se pudo guardar .blend:", e)

    # anclajes.json (relativos al centro de la caja del casco, en ejes de Roblox).
    import json
    cmn, cmx = c.caja_limite([casco])
    centro = tuple(((cmn + cmx) / 2) / c.ESTUDIO)
    rel = {k: a_roblox(tuple(Vector(v) - Vector(centro))) for k, v in anclajes_rel.items()}
    rel["Ejes"] = (0.0, 0.0, 0.0)
    with open(os.path.join(salida, "anclajes.json"), "w", encoding="utf-8") as f:
        json.dump({"nota": "studs, ejes de Roblox, relativos al centro de la MeshPart del casco",
                   "Anclajes": rel}, f, indent=2, ensure_ascii=False)

    # Resumen de triángulos.
    tris = {n: c.triangulos(o) for n, o in piezas.items()}
    total = sum(tris.values())
    mn, mx = c.caja_limite(objs)
    dim = (mx - mn) / c.ESTUDIO
    print(f"\n=== {nombre} ===")
    for n in sorted(tris):
        print(f"  {n:28s} {tris[n]:5d} tri")
    aviso = "" if (tope_tris is None or total <= tope_tris) else f"  ¡PASA DEL TOPE {tope_tris}!"
    print(f"  TOTAL {total} tri  ·  {dim.x:.1f} × {dim.y:.1f} × {dim.z:.1f} studs (manga × eslora × alto){aviso}")

    # Render exterior (con un maniquí R6 de pie en la cubierta para comprobar la proporción).
    os.makedirs(os.path.join(salida, "render"), exist_ok=True)
    c.preparar_estudio(z_suelo=(mn.z - 0.3 * c.ESTUDIO) if z_suelo is None else z_suelo * c.ESTUDIO)
    render_objs = list(objs)
    if r6_pos is not None:
        render_objs.append(maniqui_r6(r6_pos))
    rutas = c.renderizar_vistas(render_objs, os.path.join(salida, "_tmp"), vistas_ext,
                                tam=320 if rapido else 520, muestras=16 if rapido else 56, margen=1.02,
                                centro=(mn + mx) / 2)
    c.montar_hoja([rutas], os.path.join(salida, "render", f"{archivo}_exterior.png"),
                  f"{nombre} — exterior",
                  notas=[f"{total} tri  ·  {dim.x:.0f} × {dim.y:.0f} × {dim.z:.0f} studs (manga × eslora × alto)  ·  "
                         f"maniquí R6 (5 studs) para escala · neón cyan #3DF2FF"],
                  columnas=4)
    # Sección transversal / vista interior opcional (corta el casco para enseñar los niveles).
    if seccion is not None:
        _render_seccion(archivo, nombre, salida, piezas, seccion, r6_pos, rapido)
    return total, dim


def _render_seccion(archivo, nombre, salida, piezas, seccion, r6_pos, rapido):
    """Oculta las piezas indicadas (casco/costado) para enseñar el interior, y renderiza 2 vistas."""
    ocultar, vistas = seccion.get("ocultar", []), seccion.get("vistas")
    estado = {}
    for n, o in piezas.items():
        estado[o] = o.hide_render
        if any(k in n for k in ocultar):
            o.hide_render = True
    visibles = [o for n, o in piezas.items() if o.hide_render is False]
    extra = [maniqui_r6(p) for p in seccion.get("r6", ([r6_pos] if r6_pos else []))]
    rutas = c.renderizar_vistas(visibles + extra, os.path.join(salida, "_tmp_int"), vistas,
                                tam=320 if rapido else 520, muestras=16 if rapido else 56, margen=1.04,
                                con_malla=False)
    c.montar_hoja([rutas], os.path.join(salida, "render", f"{archivo}_interior.png"),
                  f"{nombre} — sección interior", columnas=len(rutas) or 2,
                  notas=["sección transversal: casco oculto para ver los niveles · maniquí R6 (5 studs) para escala"])
    for o, hd in estado.items():
        o.hide_render = hd


def maniqui_r6(pos, altura=5.0):
    """
    Maniquí R6 sencillo (cabeza, torso, 2 brazos, 2 piernas) de `altura` studs, con los pies en pos.z.
    Para validar la proporción en los renders (no se exporta). Colores llamativos para distinguirlo.
    """
    bm = bmesh.new()
    x, y, z = pos
    u = altura / 5.0  # escala (R6 ~5 studs)
    # Piernas (0 a 1.9), torso (1.9 a 3.9), cabeza (3.9 a 5.0).
    for s in (-0.45, 0.45):
        caja(bm, (x + s * u, y, z + 0.95 * u), (0.8 * u, 0.9 * u, 1.9 * u), mat=0)
    caja(bm, (x, y, z + 2.9 * u), (2.0 * u, 1.0 * u, 2.0 * u), mat=1)   # torso
    for s in (-1.4, 1.4):
        caja(bm, (x + s * u, y, z + 2.9 * u), (0.8 * u, 0.9 * u, 1.9 * u), mat=2)  # brazos
    caja(bm, (x, y, z + 4.5 * u), (1.1 * u, 1.1 * u, 1.1 * u), mat=3)  # cabeza
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mats = [c.material("r6_pierna", c.srgb("#2E3440"), 0.7),
            c.material("r6_torso", c.srgb("#C94B3B"), 0.6),
            c.material("r6_brazo", c.srgb("#E8C07A"), 0.6),
            c.material("r6_cabeza", c.srgb("#E8C07A"), 0.6)]
    obj = c.objeto_desde_bmesh("Maniqui_R6", bm, mats)
    obj["estudio"] = True  # que renderizar_vistas no lo oculte al filtrar por objetos pedidos
    return obj


def objeto(nombre, bm, materiales, suavizar=35):
    """Cierra un bmesh en un objeto con sus materiales, normales hacia fuera y sombreado suave por ángulo."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = c.objeto_desde_bmesh(nombre, bm, materiales)
    if suavizar:
        c.sombreado_suave(obj, angulo=suavizar)
    return obj


def tris_totales(objs):
    return sum(c.triangulos(o) for o in objs)
