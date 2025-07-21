import urllib.request
import json, os, re, unicodedata, requests

claveToDepto = {
    "ACT": "ACTUARIA Y SEGUROS",
    "ADM": "ADMINISTRACION",
    "CSO": "CIENCIA POLITICA",
    "COM": "COMPUTACION",
    "CON": "CONTABILIDAD",
    "CEB": "CTRO DE ESTUDIO DEL BIENESTAR",
    "DER": "DERECHO",
    "ECO": "ECONOMIA",
    "EST": "ESTADISTICA",
    "EGN": "ESTUDIOS GENERALES",
    "EIN": "ESTUDIOS INTERNACIONALES",
    "IIO": "ING. INDUSTRIAL Y OPERACIONES",
    "CLE": "LENGUAS (CLE)",
    "LEN": "LENGUAS (LEN)",
    "MAT": "MATEMATICAS",
    "SDI": "SISTEMAS DIGITALES",
}

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def getHTML(url):
    """
    Regresa el contenido HTML del url.
    """
    try:
        with urllib.request.urlopen(url) as u:
            html = u.read().decode("utf-8", "ignore")
    except:
        response = requests.get(url, verify=False)
        html = response.content.decode("utf-8", "ignore")

    return html


def descargaArchivo(path, url):
    """
    Intenta descargar el archivo en url en el directorio local path.
    Si el directorio no existe lo crea. Si no encuentra el archivo avienta error.
    """
    dir = os.path.dirname(path)
    os.makedirs(dir, exist_ok=True)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Not found @ {url}")
    else:
        open(path, "wb").write(response.content)


def replace_latin_chars(str):
    """
    Reemplaza letras con acentos por letras sin acentos y ñ con n en str.
    """
    translate = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ñ": "N",
        "Ü": "U",
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "ü": "u",
    }
    for original, replacement in translate.items():
        str.replace(original, replacement)
    return str



def periodoValido(periodo):
    periodos = ["PRIMAVERA", "VERANO", "OTOÑO"]
    if len(periodo.split(" ")) != 3:
        return False
    op, yr, lic = periodo.split()
    if lic != "LICENCIATURA" or op not in periodos or not str.isnumeric(yr):
        return False
    return True


def rankPeriodo(periodo_str):
    """
    Asigna numerico usado para ordenar a cadena del tipo 'OTOÑO 2022 LICENCIATURA'.
    """
    assert periodo_str.count(" ") == 2, "Periodo invalido"
    sem, yr, _ = periodo_str.split()
    periodos = ["PRIMAVERA", "VERANO", "OTOÑO"]
    assert sem in periodos, "Periodo invalido"
    opOffset = periodos.index(sem)
    return 10 * int(yr) + int(opOffset)


def periodoMasReciente(periodos):
    return max(periodos, key=rankPeriodo)


def dic2js(d):
    out = ""
    for k, v in d.items():
        if isinstance(v, str):
            out += f'let {k}="{v}";\n'
        else:
            out += f"let {k}={json.dumps(v, indent=2)};\n"
    return out


if __name__ == "__main__":
    # Prueba rankPeriodo
    # periodos=['PRIMAVERA 2011 LICENCIATURA','PRIMAVERA 2010 LICENCIATURA','VERANO 2010 LICENCIATURA','OTOÑO 2010 LICENCIATURA']
    # ordenados=sorted(periodos,key=rankPeriodo,reverse=True)
    # assert ordenados==periodos
    # for p in periodos:
    #     assert periodoValido(p)

    # i=['PRIMAVERA 2023 LICENCIATURA','VERANO 2023 LICENCIATURA']
    # print(sorted(i,key=rankPeriodo,reverse=True))
    print(
        periodoMasReciente(["PRIMAVERA 2024 LICENCIATURA", "OTOÑO 2023 LICENCIATURA"])
    )
