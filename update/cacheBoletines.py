# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
import os, itertools, string, time, argparse
from urllib.parse import urljoin
import utils


def fuerza_bruta(base_url, base_dir):
    """
    Intenta encontrar y descargar boletines por fuerza bruta.
    I.e. asume que no se conocen las claves de los programas ('COM-H')
    y los intenta encontrar.

    Intenta todas las combinaciones del formato AA-A, AAA-A, ..., ZZ-Z, ZZZ-Z.

    Se recomienda usar muy infrecuentemente.
    """

    # El producto cruz
    prod = itertools.product(
        string.ascii_uppercase,
        string.ascii_uppercase,
        [""] + list(string.ascii_uppercase),
        string.ascii_uppercase,
    )
    # Para cada combinacion
    for i, j, k, letra in prod:
        programa = f"{i}{j}{k}-{letra}"
        try:
            url = urljoin(base_url, f"{programa}.pdf")
            local_path = os.path.join(base_dir, f"{programa}.pdf")

            utils.descargaArchivo(local_path, url)
            print(f"Encontrado y descargado: {url}")

        except:
            continue


def semi_fuerza_bruta(base_url, base_dir):
    """
    Intenta encontrar y descargar boletines por semi-fuerza bruta.
    I.e. asume que se conocen las claves 'COM' de las carreras pero
    no las letras de los programas ('H').

    Intenta las combinaciones del formato COM-A, COM-B, ..., COM-Z.
    """
    codigos_carreras = set(
        [fname.split("-")[0] for fname in os.listdir(base_dir) if ".pdf" in fname]
    )
    print(f"Codigos de carreras encontrados: {codigos_carreras}")

    for carrera in codigos_carreras:
        # Intenta descargar los programas de la carrera
        for letra in string.ascii_uppercase:
            programa = f"{carrera}-{letra}"
            try:
                url = urljoin(base_url, f"{programa}.pdf")
                local_path = os.path.join(base_dir, f"{programa}.pdf")
                utils.descargaArchivo(local_path, url)
                print(f"Encontrado y descargado: {url}")
            except:
                continue


def actualiza_ya_encontrados(base_url, base_dir):
    """
    Asume que ya existen programas en el directorio 'base_dir'
    e intenta actualizarlos descargando el archivo con el mismo nombre.
    """

    # Para cada archivo PDF en boletines/
    for fname in os.listdir(base_dir):
        if ".pdf" not in fname:
            continue

        # Intenta descargarlo
        try:
            url = urljoin(base_url, fname)
            local_path = os.path.join(base_dir, fname)
            utils.descargaArchivo(local_path, url)
            print(f"Descargado {fname} exitosamente.")
        except Exception as e:
            print(f"No se pudo descargar {fname}: {e}")


def agregaLinksDoc(base_dir):
    sHTML = ""
    # Para cada archivo PDF en boletines/
    for fname in sorted(os.listdir(base_dir)):
        if ".pdf" not in fname:
            continue
        # Agrega un link a sHTML de la forma:
        sHTML += (
            f"<a href={base_dir}/{fname} target=_blank>{fname.split('.')[0]}</a><br>\n"
        )

    # Lee el template
    with open(os.path.join(base_dir, "boletinesTemplate.html"), "r") as f:
        template = f.read()

    # Y reemplaza la lista de ligas en su lugar
    return template.replace("<!--Lista de links-->", sHTML)


def agregarActualizado(html):
    return html.replace("//Actualizado", str(time.time() * 1000))


if __name__ == "__main__":

    modos_fn = {
        "actualiza": actualiza_ya_encontrados,
        "encuentra": fuerza_bruta,
        "semi-encuentra": semi_fuerza_bruta,
        "html": lambda *_: None,
    }

    parser = argparse.ArgumentParser(
        prog="Cache Boletines",
        description="Intenta descargar/actualizar copias de los programas academicos del ITAM.",
    )
    parser.add_argument(
        "--url_boletines",
        default="http://escolar.itam.mx/licenciaturas/boletines/",
        help='La URL donde se encuentran los boletines publicados. Por ejemplo "[url_boletines]/COM-H.pdf".',
    )
    parser.add_argument(
        "--modo",
        choices=list(modos_fn.keys()),
        default="actualiza",
        help="Actualiza los boletines ya encontrados y que vivien en --dir (actualiza),\
            encuentra boletines con fuerza bruta (encuentra) o solo actualiza el archivo boletines.html (html).",
    )
    parser.add_argument(
        "--dir",
        default="assets/boletines",
        help="Directorio en el cual se encuentran/guardan los boletines descargados.",
    )
    args = vars(parser.parse_args())

    os.makedirs(args["dir"], exist_ok=True)

    print(f"Modo: {args['modo']}")
    modos_fn[args["modo"]](args["url_boletines"], args["dir"])

    # Agregamos links a template y regresamos el html
    conLinks = agregaLinksDoc(args["dir"])

    # Agregamos la fecha de actualizacion
    conActualizado = agregarActualizado(conLinks)

    # Guardamos en .html
    with open("boletines.html", "w+") as f:
        f.write(conActualizado)
