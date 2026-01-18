import json
import re
import pickle
from urllib.parse import urljoin

import pandas as pd
from thefuzz import fuzz
from tqdm import tqdm

from utils import normalize_text, claveToDepto, getHTML



class MisProfesScrapper:
    """
    Clase que maneja el scrapeo de profesores del ITAM de MisProfes.com.
    """

    def __init__(
        self,
        url: str,
        url_profes: str = "https://www.misprofesores.com/profesores/",
        pipeline_path: str = "update/match_pipeline.pkl",
        debug: bool = False,
    ):
        """
        Parametros:
        ----------
        url: str.
            URL de la página de MisProfes.com designada al ITAM.
        """
        self.url = url
        self.url_profes = url_profes
        self.pipeline_path = pipeline_path

        self.debug = debug

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

    def scrap(self):
        print("Scrappeando MisProfes ...")
        html = getHTML(self.url)

        # Extrae como JSON la variable `dataSet` del HTML
        match = re.search(r"var\s+dataSet\s*=\s*(\[[\s\S]*?\]);", html)
        if not match:
            raise ValueError("No se pudo encontrar 'dataSet' en el HTML.")

        # Lista de objectos con id (i), nombre (n), apellido (a), departamento (d), calif (c) y no. de evaluaciones (m)
        dataSet = json.loads(match.group(1))

        self.data = {
            p["n"] + " " + p["a"]: {
                "id": p["i"],
                "calif": p["c"],
                "n": p["m"],
                "depto": p["d"],
                "nombre": p["n"] + " " + p["a"],
                "link": self.urlProfe(p["n"], p["a"], p["i"]),
            }
            for p in dataSet
        }
        print(f"Se scrappearon {len(self.data)} profesores de MisProfes!")

    def match(self, clases, threshold=0.5):
        # Carga modelo
        with open(self.pipeline_path, "rb") as f:
            pipeline = pickle.load(f)
        print(pipeline)

        # Construye features
        profesores_deptos = {}  # nombre profesor -> set('COMPUTACION', 'ACTUARIA', ...)
        for clave, claseInfo in clases.items():
            for grupoInfo in claseInfo["grupos"]:
                profesor = grupoInfo["profesor"]
                if not profesor:
                    continue
                if profesor not in profesores_deptos:
                    profesores_deptos[profesor] = set()
                profesores_deptos[profesor].add(claveToDepto[clave.split("-")[0]])

        df = pd.DataFrame(
            [
                {
                    "id": info["id"],
                    "Nombre MisProfes": info["nombre"],
                    "Depto MisProfes": info["depto"],
                }
                for info in self.data.values()
            ]
        )

        # nombre grace -> link de misProfes, calif general, no. de evaluaciones
        matched = {}

        for nombreGrace, deptosGrace in tqdm(profesores_deptos.items()):
            df["Nombre Grace"] = nombreGrace
            df["Deptos Grace"] = ",".join(deptosGrace)

            # features = df.apply(_build_features, axis=1)

            preds = pipeline.predict_proba(df)[:, 1]
            if preds.max() > threshold:
                pred_match = df.iloc[preds.argmax()]
                nombre_match = pred_match["Nombre MisProfes"]
                datos_match = self.data[nombre_match]

                matched[nombreGrace] = {
                    "link": datos_match["link"],
                    "general": float(datos_match["calif"])
                    if datos_match["calif"]
                    else 0.0,
                    "n": int(datos_match["n"]) if datos_match["n"] else 0,
                }

                if self.debug:
                    matched[nombreGrace].update(
                        {
                            "nombre_mis_profes": nombre_match,
                            "max_prob": preds.max(),
                            "features": pipeline[0].iloc[preds.argmax()].to_dict(),
                        }
                    )

        print(
            f"Se ligaron {len(matched)} ({100 * len(matched) / len(profesores_deptos):.2f}%) profesores a evaluaciones de MisProfes"
        )
        return matched


def get_features(df):
    def build_features(row):
        for c in [
            "Nombre Grace",
            "Nombre MisProfes",
            "Deptos Grace",
            "Depto MisProfes",
        ]:
            assert c in row, f"Missing column: {c}"

        nombre_grace = row["Nombre Grace"]
        nombre_misprofes = row["Nombre MisProfes"]

        grace_dept = row["Deptos Grace"].split(",")
        user_dept = normalize_text(row["Depto MisProfes"])

        if not grace_dept or not user_dept:
            scores = [0.0]
        else:
            scores = [
                fuzz.token_set_ratio(normalize_text(d), user_dept) / 100
                for d in grace_dept
            ]

        # Extract features
        features = {
            "name_token_sort": fuzz.token_sort_ratio(
                normalize_text(nombre_grace), normalize_text(nombre_misprofes)
            )
            / 100,
            "name_lev_ratio": fuzz.ratio(
                normalize_text(nombre_grace), normalize_text(nombre_misprofes)
            )
            / 100,
            "dept_max_ratio": max(scores),
        }
        return pd.Series(features)

    return df.apply(build_features, axis=1)


if __name__ == "__main__":
    url = "https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003"
    scrapper = MisProfesScrapper(url)
    scrapper.scrap()

    import pickle

    # nonSecure = GraceScrapper()
    # nonSecure.scrap()

    # # save nonSecure with pickle
    # with open("data/scrappers/nonSecure.pkl", "wb") as f:
    #     pickle.dump(nonSecure, f)

    # load
    with open("update/data/scrappers/grace.pkl", "rb") as f:
        nonSecure = pickle.load(f)

    matched = scrapper.match(nonSecure.clases, threshold=0.5)
    with open("tmp.json", "w") as f:
        json.dump(matched, f, indent=4)
