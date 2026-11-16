"""Registro de los 105 modelos del Planeta Humano: cada función de modelado se apunta con @modelo."""

MODELOS = {}

ZONAS = {"residencial": "Zona residencial", "comercial": "Zona comercial", "industrial": "Zona industrial",
         "hangar": "Zona del hangar", "naturaleza": "Naturaleza y terreno", "especiales": "Edificios especiales"}


def modelo(num, zona, categoria, objetivo):
    """objetivo = (ancho, fondo, alto) en studs."""
    def deco(fn):
        MODELOS[fn.__name__] = {"fn": fn, "num": num, "zona": ZONAS[zona], "categoria": categoria,
                                "objetivo": objetivo}
        return fn
    return deco
