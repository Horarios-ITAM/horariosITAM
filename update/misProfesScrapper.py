import utils, json


class MisProfesScrapper:
    """
    Clase que maneja el scrapeo de profesores del ITAM de MisProfes.com.
    """

    def __init__(self, url: str):
        """
        Constructor.

        Parametros:
        ----------
        url: str.
            URL de la página de MisProfes.com designada al ITAM.
        """
        self.url = url

    def _fixStr(self, s):
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

    def _urlProfe(self, nombre, apellido, id):
        return (
            "https://www.misprofesores.com/profesores/"
            + self._fixStr(nombre)
            + "-"
            + self._fixStr(apellido)
            + "_"
            + id
        )

    def scrap(self):
        print("Scrappeando MisProfes ...")
        html = utils.getHTML(self.url)
        start = html.index("var dataSet = ") + len("var dataSet = ")
        tempData = json.loads(html[start : html.index("];", start) + 1])
        profesores = {
            p["n"] + " " + p["a"]: {
                "c": p["c"],
                "m": p["m"],
                "i": p["i"],
                "misProfesNom": p["n"] + " " + p["a"],
                "link": self._urlProfe(p["n"], p["a"], p["i"]),
            }
            for p in tempData
        }
        print("Se scrappearon {} profesores de MisProfes!".format(len(profesores)))
        self.data = profesores

    def match(self, profesores, matchRate):
        # Match with levenshteinSimilarity
        matched = {}
        for m in self.data.keys():
            for p in profesores:
                if (
                    utils.levenshtein_ratio(p, m) > matchRate
                ):  # utils.levenshteinSimilarity(p,m)>matchRate:
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
