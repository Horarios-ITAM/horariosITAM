import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os, time
import utils

BASE_DIR = "assets/calendarios"


def agregaLinksDoc(conseguidos):
    sHTML = ""
    for text, ligas in conseguidos.items():
        sHTML += f'<a href={"assets/" + ligas["urlCache"]} class="linkCalendario" target=_blank>{text}</a><br>\n'

    with open(os.path.join(BASE_DIR, "calendariosTemplate.html"), "r") as f:
        template = f.read()

    return template.replace("<!--Lista de links-->", sHTML)


def agregarActualizado(html):
    return html.replace("//Actualizado", str(time.time() * 1000))


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
        utils.descargaArchivo(os.path.join("assets", hit["href"]), urlDoc)
        conseguidos[hit.string] = {"urlCache": hit["href"], "urlITAM": urlDoc}

        print(f"Descargado {hit.string} de {urlDoc}")

    # Escribimos
    conLinks = agregaLinksDoc(conseguidos)
    conActualizado = agregarActualizado(conLinks)
    with open("calendarios.html", "w+") as f:
        f.write(conActualizado)
