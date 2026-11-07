"""
Escribe (y vuelve a leer) un .rbxmx con una KeyframeSequence de R6, para meter la animación en Studio sin el
importador de FBX: se arrastra el archivo a Studio (o clic derecho en el rig -> Insert from File) y aparece la
KeyframeSequence, que el Animation Editor abre y publica como cualquier otra.

De Blender a Roblox:
  * Ejes: Roblox mira a -Z con Y arriba y la derecha en +X. En el rig de Blender el personaje mira a -Y, Z es arriba
    y la derecha es -X. Cambio de base B: (x, y, z)_Blender -> (-x, z, y)_Roblox (es una rotación, no un espejo).
  * Cada Pose guarda el Motor6D.Transform de su articulación. Roblox coloca la pieza como
    Part1 = Part0 * C0 * Transform * C1:Inverse(), y en el R6 estándar C0 y C1 tienen la misma rotación R. Así que si
    en Blender el hueso gira q (respecto a su padre) y se desplaza d, el Transform es:
        rotación = R^-1 * (B q B^-1) * R        posición = R^-1 * (B d)
  * HumanoidRootPart es la raíz: su Pose no mueve nada, solo contiene a Torso, y de Torso cuelgan las demás.
"""

import xml.etree.ElementTree as ET

from mathutils import Matrix, Vector

# C0 de cada Motor6D del R6 estándar (Rig Builder), en coordenadas de Roblox: (posición, filas de la rotación).
# C1 tiene la misma rotación en todos, que es lo único que necesita la conversión (la posición la da el C0).
MOTORES = {
    "Torso": ((0, 0, 0), ((-1, 0, 0), (0, 0, 1), (0, 1, 0))),  # RootJoint (HumanoidRootPart -> Torso)
    "Head": ((0, 1, 0), ((-1, 0, 0), (0, 0, 1), (0, 1, 0))),  # Neck
    "Right Arm": ((1, 0.5, 0), ((0, 0, 1), (0, 1, 0), (-1, 0, 0))),  # Right Shoulder
    "Left Arm": ((-1, 0.5, 0), ((0, 0, -1), (0, 1, 0), (1, 0, 0))),  # Left Shoulder
    "Right Leg": ((1, -1, 0), ((0, 0, 1), (0, 1, 0), (-1, 0, 0))),  # Right Hip
    "Left Leg": ((-1, -1, 0), ((0, 0, -1), (0, 1, 0), (1, 0, 0))),  # Left Hip
}
C1 = {
    "Torso": (0, 0, 0),
    "Head": (0, -0.5, 0),
    "Right Arm": (-0.5, 0.5, 0),
    "Left Arm": (0.5, 0.5, 0),
    "Right Leg": (0.5, 1, 0),
    "Left Leg": (-0.5, 1, 0),
}
HIJOS_DEL_TORSO = ("Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg")
B = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
PRIORIDADES = {"Idle": 0, "Movement": 1, "Action": 2, "Action2": 3, "Action3": 4, "Action4": 5, "Core": 1000}


def transform(hueso, q, d):
    """Motor6D.Transform (rotación 3x3, posición) para la rotación q y el desplazamiento d (studs) del hueso."""
    R = Matrix(MOTORES[hueso][1])
    rot = R.transposed() @ B @ q.to_matrix() @ B.transposed() @ R
    pos = R.transposed() @ (B @ Vector(d))
    return rot, pos


def _num(x):
    x = 0.0 if abs(x) < 1e-9 else x
    return f"{x:.6g}"


class _Ref:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return f"RBX{self.n:06d}"


def _prop(props, tipo, nombre, valor):
    e = ET.SubElement(props, tipo, name=nombre)
    e.text = valor
    return e


def _pose(padre, ref, nombre, rot=None, pos=None):
    item = ET.SubElement(padre, "Item", {"class": "Pose", "referent": ref()})
    props = ET.SubElement(item, "Properties")
    cf = ET.SubElement(props, "CoordinateFrame", name="CFrame")
    rot = rot if rot is not None else Matrix.Identity(3)
    pos = pos if pos is not None else Vector((0, 0, 0))
    for eje, v in zip("XYZ", pos):
        ET.SubElement(cf, eje).text = _num(v)
    for i in range(3):
        for j in range(3):
            ET.SubElement(cf, f"R{i}{j}").text = _num(rot[i][j])
    _prop(props, "token", "EasingDirection", "0")
    _prop(props, "token", "EasingStyle", "0")  # Linear: hay una clave por fotograma con el easing ya aplicado
    _prop(props, "string", "Name", nombre)
    _prop(props, "float", "Weight", "1")
    return item


def escribir(ruta, nombre, calcular_pose, ultimo, fps, prioridad, bucle=True):
    ref = _Ref()
    raiz = ET.Element(
        "roblox",
        {
            "xmlns:xmime": "http://www.w3.org/2005/05/xmlmime",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://www.roblox.com/roblox.xsd",
            "version": "4",
        },
    )
    seq = ET.SubElement(raiz, "Item", {"class": "KeyframeSequence", "referent": ref()})
    props = ET.SubElement(seq, "Properties")
    _prop(props, "bool", "Loop", "true" if bucle else "false")
    _prop(props, "string", "Name", nombre)
    _prop(props, "token", "Priority", str(PRIORIDADES[prioridad]))
    for f in range(ultimo + 1):
        pose = calcular_pose(f)
        kf = ET.SubElement(seq, "Item", {"class": "Keyframe", "referent": ref()})
        kp = ET.SubElement(kf, "Properties")
        _prop(kp, "string", "Name", "Keyframe")
        _prop(kp, "float", "Time", _num(f / fps))
        raiz_pose = _pose(kf, ref, "HumanoidRootPart")
        rot, pos = transform("Torso", pose.q["Torso"], pose.loc["Torso"])
        torso = _pose(raiz_pose, ref, "Torso", rot, pos)
        for h in HIJOS_DEL_TORSO:
            rot, pos = transform(h, pose.q[h], pose.loc[h])
            _pose(torso, ref, h, rot, pos)
    ET.indent(raiz, space="\t")
    ET.ElementTree(raiz).write(ruta, encoding="utf-8", xml_declaration=False)
    return ruta


# ---------------------------------------------------------------------------------------------
# Lectura y reproducción (para comprobar el archivo sin Studio)
# ---------------------------------------------------------------------------------------------


def _cframe(item):
    cf = item.find("Properties/CoordinateFrame[@name='CFrame']")
    pos = Vector([float(cf.find(e).text) for e in "XYZ"])
    rot = Matrix([[float(cf.find(f"R{i}{j}").text) for j in range(3)] for i in range(3)])
    return rot, pos


def _nombre(item):
    return item.find("Properties/string[@name='Name']").text


def leer(ruta):
    """Devuelve (propiedades, [(tiempo, {pieza: (rot, pos)})])."""
    arbol = ET.parse(ruta).getroot()
    seq = arbol.find("Item[@class='KeyframeSequence']")
    props = {e.get("name"): e.text for e in seq.find("Properties")}
    claves = []
    for kf in seq.findall("Item[@class='Keyframe']"):
        t = float(kf.find("Properties/float[@name='Time']").text)
        poses = {}

        def recorrer(item, padre):
            nombre = _nombre(item)
            poses[nombre] = (_cframe(item), padre)
            for hijo in item.findall("Item[@class='Pose']"):
                recorrer(hijo, nombre)

        for p in kf.findall("Item[@class='Pose']"):
            recorrer(p, None)
        claves.append((t, poses))
    return props, claves


def centros_roblox(poses):
    """Reproduce Part1 = Part0 * C0 * T * C1^-1 con el HumanoidRootPart en (0, 3, 0): centro de cada pieza (Roblox)."""
    piezas = {"HumanoidRootPart": (Matrix.Identity(3), Vector((0, 3, 0)))}

    def cf_mul(a, b):
        return a[0] @ b[0], a[1] + a[0] @ b[1]

    def cf_inv(a):
        r = a[0].transposed()
        return r, -(r @ a[1])

    orden = ["Torso", *HIJOS_DEL_TORSO]
    for h in orden:
        (rot_t, pos_t), padre = poses[h]
        R = Matrix(MOTORES[h][1])
        c0 = (R, Vector(MOTORES[h][0]))
        c1 = (R, Vector(C1[h]))
        piezas[h] = cf_mul(cf_mul(cf_mul(piezas[padre], c0), (rot_t, pos_t)), cf_inv(c1))
    return {h: v[1] for h, v in piezas.items()}
