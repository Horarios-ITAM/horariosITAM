# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "requests",
# ]
# ///
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
import utils

CAL_DIR = Path("assets/calendarios")
DOCS_DIR = Path("assets/docs")


def agregaLinksDoc(conseguidos):
    sHTML = ""
    for text, ligas in conseguidos.items():
        sURL = requests.utils.requote_uri(str(ligas["local"]))
        sHTML += (
            f'<a href="{sURL}" class="linkCalendario" target="_blank">{text}</a><br>\n'
        )

    with open(CAL_DIR / "calendariosTemplate.html", "r") as f:
        template = f.read()

    return template.replace("<!--Lista de links-->", sHTML)


def agregarActualizado(html):
    return html.replace("//Actualizado", str(time.time() * 1000))


def destino_local(url_doc: str) -> Path:
    """
    Regresa el directorio en el que se debe cachear el archivo.
    - URLs con "/calendarios/" en su ruta -> assets/calendarios
    - Todo lo demás -> assets/docs
    """
    parsed = urlparse(url_doc)
    if "/calendarios/" in parsed.path.lower():
        return CAL_DIR
    return DOCS_DIR


def nombre_archivo(url: str) -> str:
    """
    Obtiene un nombre de archivo seguro a partir de la URL.
    """
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "documento.pdf"


if __name__ == "__main__":
    url = "https://escolar.itam.mx/servicios_escolares/servicios_calendarios.php"

    r = requests.get(url)
    b = BeautifulSoup(r.text, "html.parser")

    conseguidos = {}
    for hit in b.find_all("a", {"class": "enlace"}):
        # Saltamos links raros
        if hit.string is None or hit["href"] is None:
            print("Saltando", hit)
            continue

        # Descargamos el archivo
        urlDoc = urljoin(url, hit["href"])
        base_dir = destino_local(urlDoc)
        base_dir.mkdir(parents=True, exist_ok=True)
        local_path = base_dir / nombre_archivo(urlDoc)

        utils.descargaArchivo(str(local_path), urlDoc)
        conseguidos[hit.string] = {"local": local_path, "urlITAM": urlDoc}

        print(f"Descargado {hit.string} de {urlDoc}")

    # Escribimos
    conLinks = agregaLinksDoc(conseguidos)
    conActualizado = agregarActualizado(conLinks)
    with open("calendarios.html", "w+") as f:
        f.write(conActualizado)
