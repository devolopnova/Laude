from pathlib import Path

from config import ROOT_DIR, EXCLUDED_DIRS, HTML_EXTENSIONS


def debe_excluir(ruta: Path):
    """
    Comprueba si una ruta pertenece
    a una carpeta que debemos ignorar.
    """

    return any(
        parte in EXCLUDED_DIRS
        for parte in ruta.parts
    )


def buscar_html():

    archivos_html = []

    for archivo in ROOT_DIR.rglob("*"):

        if archivo.is_file():

            if debe_excluir(archivo):
                continue

            if archivo.suffix.lower() in HTML_EXTENSIONS:
                archivos_html.append(archivo)

    return archivos_html


if __name__ == "__main__":

    archivos = buscar_html()

    print(f"HTML encontrados: {len(archivos)}")

    for archivo in archivos[:20]:
        print(archivo)