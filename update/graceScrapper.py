from bs4 import BeautifulSoup
import utils
from urllib.parse import urljoin
import requests, re


class GraceScrapper:
    """
    Clase que maneja el scrappeo de Grace (serviciosweb.itam.mx).
    """

    def __init__(
        self,
        dropDownURL: str = None,
        formURL: str = None,
        s: str = None,
        abiertos: bool = False,
        verbose: bool = True,
    ):
        """
        Constructor. Scrapea datos preliminares.
        De no proporcionar los parametros se tratarán de scrappear sus valores automaticamente.

        Parametros:
        ----------
        dropDownURL: str [Opcional].
            URL de la página de Grace con el menú de dropdown con las clases.
            Servicios No Personalizados > Horarios para el período [Periodo].

        formURL: str [Opcional].
            URL del POST que llama la forma de Grace en dropDownURL.
            Inspecciona el HTML de dropDownURL > <form> de "Selecciona una ..." > valor en "action".

        s: str [Opcional].
            Valor de "s" (hidden) en la forma POST descrita en formURL.

        abiertos: bool [Opcional].
            Si se scrappean "Grupos que continúan abiertos".
        """
        # URL de serviciosweb/Grace
        baseURL = "https://servicios.itam.mx/"
        self.abiertos = abiertos
        self.verbose = verbose

        # Si no se pasaron URLs, scrapearlas
        if dropDownURL == None or formURL == None or s == None:
            self.dropDownURL, self.formURL, self.clavePeriodo = self._scrappeaURLs(
                baseURL
            )

            self._print("Se scrappearon las siguientes URLs")
            self._print(
                f"dropDownURL: {self.dropDownURL}\nformUrl: {self.formURL}\ns: {self.clavePeriodo}\n"
            )
        else:
            self.dropDownURL = dropDownURL
            self.formURL = formURL
            self.clavePeriodo = s

        # Determinar periodo
        self.periodo, self.listaClases = self._scrappeaPeriodoListaClases()
        self._print(
            f"Periodo: {self.periodo}\nClave de Periodo: {self.clavePeriodo}\n# de clases: {len(self.listaClases)}"
        )

    def _scrappeaURLs(self, baseURL):
        """
        Intenta scrappear y regresar los valores de dropDownURL, formURL y s.
        """
        # Rechamos si hay redireccion en baseURL
        soup = BeautifulSoup(utils.getHTML(baseURL), "html.parser")
        metas = soup.find_all("meta")
        if len(metas) == 1 and "http-equiv" in metas[0].attrs:
            homePageURL = metas[0]["content"].split("URL=")[1]
        else:
            homePageURL = baseURL

        # Extraer URL de Serv. no personalizados de homePageURL
        urlServiciosNoPersonalizados = None
        soup = BeautifulSoup(utils.getHTML(homePageURL), "html.parser")
        for link in soup.find_all("a"):
            if link.string and "Servicios no personalizados" in link.string:
                urlServiciosNoPersonalizados = urljoin(baseURL, link.attrs["href"])
                break

        # Si no se encontro por texto, intenta por 'ServNoPers' en link
        if urlServiciosNoPersonalizados is None:
            for link in soup.find_all("a"):
                if "ServNoPers" in link.attrs["href"]:
                    urlServiciosNoPersonalizados = urljoin(baseURL, link.attrs["href"])
                    break

        assert urlServiciosNoPersonalizados != None, (
            "No se encontro URL de Servicios no personalizados"
        )
        self._print(
            f"URL de Servicios no personalizados: {urlServiciosNoPersonalizados}"
        )

        # Extraer dropDownURL
        soup = BeautifulSoup(utils.getHTML(urlServiciosNoPersonalizados), "html.parser")
        urls = {}
        for link in soup.find_all("a"):
            if not link.string or "LICENCIATURA" not in link.string:
                continue
            if (not self.abiertos and "Horarios" in link.string) or (
                self.abiertos and "abiertos" in link.string
            ):
                p = re.findall(".*\((.*)\)", link.string)[0]
                if utils.periodoValido(p):
                    urls[p] = link["href"]

        self._print(f"Se encontraron urls:{urls}")
        periodo = utils.periodoMasReciente(list(urls.keys()))
        self._print(f"Periodo mas reciente: {periodo}")
        dropDownURL = urljoin(urlServiciosNoPersonalizados, urls[periodo])

        # Extraer formUrl y s
        soup = BeautifulSoup(utils.getHTML(dropDownURL), "html.parser")
        formURL = urljoin(
            urlServiciosNoPersonalizados, soup.find_all("form")[0]["action"]
        )
        s = soup.find((lambda tag: tag.name == "input" and tag.get("name") == "s"))[
            "value"
        ]

        return dropDownURL, formURL, s

    def _scrappeaPeriodoListaClases(self):
        """
        Regresa periodo y lista de nombre de clases scrapeados de dropDownURL.
        """
        html = utils.getHTML(self.dropDownURL)
        periodo = (html.split("período")[1].split("</h3>")[0]).strip()
        listaClases = [
            i.replace("</option>", "").replace("\n", "")
            for i in html.split("<option>")[1:-1]
        ]
        return periodo, listaClases

    def _getClaseInfo(self, html):
        """
        Dado el html de form_url regresa diccionario de la forma {"grupo":{diccionario con info de grupo}} y un booleado laboratorio.
        """
        if not html:
            return None
        grupos = {}
        teoria = False
        laboratorio = False
        if not self.abiertos:
            info = [
                "depto",
                "clave",
                "grupo",
                "CRN",
                "TL",
                "nombre",
                "prof",
                "cred",
                "horario",
                "dias",
                "salon",
                "campus",
                "comentarios",
            ]  # datos por extraer
        else:
            info = [
                "depto",
                "clave",
                "grupo",
                "TL",
                "nombre",
                "prof",
                "cred",
                "horario",
                "dias",
                "salon",
                "campus",
                "comentarios",
            ]
        soup = BeautifulSoup(html, "html.parser")
        tabla = soup.find_all("table")[2]  # la tabla con la info es la 3ra en el html
        for renglon in tabla.find_all("tr")[1:]:  # saltar renglon con cabecera
            grupo = {i: None for i in info}
            info_index = 0  # indice para navegar info[]
            for columna in renglon.find_all("td"):
                grupo[info[info_index]] = columna.string.strip()
                if info[info_index] == "dias":
                    grupo[info[info_index]] = grupo[info[info_index]].split()
                info_index += 1
            if grupo["TL"] == "L":
                grupo["grupo"] += "L"
            # Arreglar horario en inicio y fin
            inicio, fin = grupo["horario"].split("-")
            grupo["inicio"] = inicio
            grupo["fin"] = fin
            grupos[grupo["grupo"]] = grupo

        return grupos

    def _formateaClases(self, clases):
        """
        Reformatea las clases.
        """
        formated = {}  # clave: info grupo
        for c in clases:
            grupos = []
            gruposLab = []
            for clave, data in c.items():
                originalNombre = (
                    data["depto"] + "-" + data["clave"] + "-" + data["nombre"]
                )
                nombre = (
                    originalNombre if data["TL"] == "T" else originalNombre + "-LAB"
                )
                d = {
                    "grupo": data["grupo"],
                    "nombre": nombre,
                    "profesor": data["prof"],
                    "creditos": data["cred"],
                    "horario": data["horario"],
                    "dias": data["dias"],
                    "salon": data["salon"],
                    "campus": data["campus"],
                    "inicio": data["inicio"],
                    "fin": data["fin"],
                }
                if data["TL"] == "L":
                    gruposLab.append(d)
                elif data["TL"] == "T":
                    grupos.append(d)
            if len(gruposLab) > 0:
                l = {
                    "nombre": originalNombre + "-LAB",
                    "clave": data["depto"] + "-" + data["clave"],
                    "grupos": gruposLab,
                }
                formated[l["clave"] + "-LAB"] = l
            if len(c) > 0:
                t = {
                    "nombre": originalNombre,
                    "clave": data["depto"] + "-" + data["clave"],
                    "grupos": grupos,
                }
                formated[t["clave"]] = t
        return formated

    def _print(self, s):
        if self.verbose:
            print(s)

    def scrap_clase(self, txt_materia):
        """
        Scrappea una clase específica de Grace.
        Devuelve un diccionario con la información de la clase.
        """
        response = requests.post(
            url=self.formURL, data={"s": self.clavePeriodo, "txt_materia": txt_materia}
        )
        return self._getClaseInfo(response.text)

    def scrap(self):
        """
        Scrappea los detalles de las clases de Grace (tardado).
        Almacena resultados en self.clases.
        """
        # Scrapea las clases
        self._print("Scrappeando clases ...")
        clases = []
        for nombre in self.listaClases:
            info = self._getClaseInfo(
                requests.post(
                    url=self.formURL,
                    data={"s": self.clavePeriodo, "txt_materia": nombre},
                ).text
            )
            clases.append(info)

        # Formatea clases
        self.clases = self._formateaClases(clases)
        self._print(f"Se scrappearon {len(self.clases)} clases!")

        # Extrae profesores
        self.profesores = list(
            set(
                [
                    grupo["prof"]
                    for clase in clases
                    for grupo in clase.values()
                    if len(grupo["prof"].strip()) > 1
                ]
            )
        )
        self._print(f"Se encontraron {len(self.profesores)} profesores en Grace!")


if __name__ == "__main__":
    g = GraceScrapper(
        # dropDownURL="https://itaca2.itam.mx:8443/b9prod/edsup/BWZKSENP.P_Horarios1?s=2595",
        # formURL="https://itaca2.itam.mx:8443/b9prod/edsup/BWZKSENP.P_Horarios2",
        # s = "2595",
        abiertos=True,
        verbose=True,
    )
    g.scrap()
