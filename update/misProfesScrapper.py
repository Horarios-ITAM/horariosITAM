import requests
import utils
import json
import re
from urllib.parse import urljoin


class MisProfesScrapper:
    """
    Clase que maneja el scrapeo de profesores del ITAM de MisProfes.com.
    """

    def __init__(self, url: str, url_profes: str = "https://www.misprofesores.com/profesores/"):
        """
        Parametros:
        ----------
        url: str.
            URL de la página de MisProfes.com designada al ITAM.
        """
        self.url = url
        self.url_profes = url_profes

        # self.data = {}

    @staticmethod
    def arreglaNombre(s):
        """
        Arregla strs de nombres y apellidos de profesores
        """
        replacements = {
            "/[^a-zA-Z0-9\s]/": "",
            "(": "",
            ")": "",
            " -": "-",
            "- ": "-",
            "\n": "",
            "\r": "",
            "  ": " ",
            "\\": "",
            " ": "-",
        }
        s = s.strip()
        for old, new in replacements.items():
            s = s.replace(old, new)
        return s

    def urlProfe(self, nombre, apellido, id):
        """
        Construye la URL del perfil del profesor en MisProfes.com.
        """
        nombre_limpio = self.arreglaNombre(nombre)
        apellido_limpio = self.arreglaNombre(apellido)
        
        path = f"{nombre_limpio}-{apellido_limpio}_{id}"
        return urljoin(self.url_profes, path)
    
    @staticmethod
    def pruebaUrlProfe(url):
        """
        Prueba si la URL del profesor es valida.
        """
        try:
            response = requests.get(url, verify=False)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def scrap(self):

        print("Scrappeando MisProfes ...")
        html = utils.getHTML(self.url)

        # Extrae como JSON la variable `dataSet` del HTML
        match = re.search(r"var\s+dataSet\s*=\s*(\[[\s\S]*?\]);", html)
        if not match:
            raise ValueError("No se pudo encontrar 'dataSet' en el HTML.")

        # Lista de objectos con id (i), nombre (n), apellido (a), departamento (d), calif (c) y no. de evaluaciones (m)
        dataSet = json.loads(match.group(1))

        self.data = {
            p["n"] + " " + p["a"]: {
                "c": p["c"],
                "m": p["m"],
                "i": p["i"],
                "misProfesNom": p["n"] + " " + p["a"],
                "link": self.urlProfe(p["n"], p["a"], p["i"]),
            }
            for p in dataSet
        }
        print(f"Se scrappearon {len(self.data)} profesores de MisProfes!")


    def match(self, profesores, matchRate):
        # Match with levenshteinSimilarity
        matched = {}
        for m in self.data.keys():
            for p in profesores:
                if utils.levenshtein_ratio(p, m) > matchRate:
                    matched[p] = self.data[m]
        # Format
        links = {p: d["link"] for p, d in matched.items()}
        ratings = {
            p: [float(d["c"]), float(d["m"])] for p, d in matched.items() if d["c"]
        }
        formatted = {
            prof: {
                "link": links[prof],
                "general": ratings[prof][0],
                "n": int(ratings[prof][1]),
            }
            for prof in ratings.keys()
        }
        print(
            "Se ligaron {} ({:.2f}%) profesores a evaluaciones de MisProfes".format(
                len(formatted), 100 * len(formatted) / len(profesores)
            )
        )
        return formatted


if __name__ == "__main__":
    url = "https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003"
    scrapper = MisProfesScrapper(url)
    scrapper.scrap()
