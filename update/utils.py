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


def dic2js(d):
    """
    Convierte un diccionario a un string de javascript de la forma
    let key="value";
    let key2={"key": "value", "key2": "value2"};
    """
    out = ""
    for k, v in d.items():
        if isinstance(v, str):
            out += f'let {k}="{v}";\n'
        else:
            out += f"let {k}={json.dumps(v, indent=2)};\n"
    return out


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


SEMESTRES = ["PRIMAVERA", "VERANO", "OTOÑO"]


class Periodo:
    def __init__(self, periodo_str):
        """
        Recibe cadena del tipo 'OTOÑO 2022 LICENCIATURA'.
        """
        assert periodo_str.count(" ") == 2

        self.periodo_str = periodo_str.upper()
        self.sem, self.yr, self.lic = periodo_str.split()

        assert self.yr.isdigit()
        self.yr = int(self.yr)

        assert self.lic == "LICENCIATURA"
        assert self.sem in SEMESTRES

    def rank(self):
        return 10 * self.yr + int(SEMESTRES.index(self.sem))

    def __lt__(self, other):
        if not isinstance(other, Periodo):
            return NotImplemented
        return self.rank() < other.rank()

    def __eq__(self, other):
        if not isinstance(other, Periodo):
            return NotImplemented
        return self.rank() == other.rank()

    def __str__(self):
        return self.periodo_str


def periodoValido(periodo: str) -> bool:
    try:
        Periodo(periodo)
        return True
    except AssertionError:
        return False


def periodoMasReciente(periodos: list[str]) -> str:
    return str(max(Periodo(p) for p in periodos))
