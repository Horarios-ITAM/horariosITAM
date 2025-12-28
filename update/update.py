from graceScrapper import GraceScrapper
from misProfesScrapper import MisProfesScrapper
import json, time, sys
from graceScrapperSecure import GraceScrapperSecureArea, courseUrl
from utils import claveToDepto, periodoMasReciente, dic2js


def profesoresData(clases):
    """
    Regresa un diccionario de la forma nombre profesor:{'link':,'general':,'n':,'grupos'}
    Para uso en profesores.html.
    """
    profesores = {}
    for clase, info in clases.items():
        for grupo in info["grupos"]:
            profesor = grupo["profesor"]
            if profesor not in profesores:
                if profesor in misProfesData:
                    profesores[profesor] = misProfesData[profesor]
                    profesores[profesor]["grupos"] = {}
                else:
                    profesores[profesor] = {"grupos": {}}
            nombreClase = grupo["nombre"]
            if nombreClase not in profesores[profesor]["grupos"]:
                profesores[profesor]["grupos"][nombreClase] = []
            profesores[profesor]["grupos"][nombreClase].append(grupo)
    return profesores


def profesoresPorDepartamento(profesores):
    """
    Regresa un diccionario de la forma departamento:[lista de profesores].
    Se asume que profesores es la salida de profesoresData.

    """
    profesPorDepto = {}
    for profesor, info in profesores.items():
        if not profesor.strip():
            continue
        depto = claveToDepto[list(info["grupos"].keys())[0].split("-")[0]]
        if depto not in profesPorDepto:
            profesPorDepto[depto] = []
        profesPorDepto[depto].append(profesor)
    return profesPorDepto


def mejoresProfesPorDepartamento(profesores, n=10):
    """
    Regresa los n mejores profesores (de acuerdo a 'general' de MisProfes)
    por departamento.
    """
    profesPorDepto = profesoresPorDepartamento(profesores)
    for depto, profes in profesPorDepto.items():
        calif = lambda x: profesores[x]["general"] if "general" in profesores[x] else 0
        profesPorDepto[depto] = sorted(profes, key=lambda x: calif(x), reverse=True)[:n]
    return profesPorDepto


if __name__ == "__main__":
    # -------- CONTROL --------
    credsFile = "update/creds.json"
    dataFile = "js/datos/datos_index.js"
    profesoresDataFile = "js/datos/datos_profesores.js"
    misProfesUrl = "https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003"
    scrappearMisProfes = True
    misProfesBufferFile = "update/misProfesData.json"

    # --------- GRACE ---------
    # Scrapeamos Grace entrando a Secure Area

    # Leer usuario y passwd de grace
    if len(sys.argv) == 1:
        with open(credsFile, "r") as f:
            loginData = json.loads(f.read())
    elif len(sys.argv) == 3:
        loginData = {"sid": sys.argv[1], "PIN": sys.argv[2]}

    secure = GraceScrapperSecureArea(loginData["sid"], loginData["PIN"])

    # Scrapeamos Grace en Servicios No Personalizados
    nonSecure = GraceScrapper()

    # Tomamos la fuente con datos mas recientes
    if not hasattr(secure, "periodo") or nonSecure.periodo == periodoMasReciente(
        [secure.periodo, nonSecure.periodo]
    ):
        # Si empatan le damos preferencia a nonSecure
        print("Tomando nonSecure como mas reciente")
        grace = nonSecure
        scrapGraceSecure = False
    else:
        print("Tomando secure como mas reciente")
        grace = secure
        scrapGraceSecure = True

    grace.scrap()

    # ------- MISPROFES -------
    # Scrapeamos o cargamos de buffer datos de MisProfes
    if scrappearMisProfes:
        misProfes = MisProfesScrapper(misProfesUrl)
        misProfes.scrap()
        misProfesData = misProfes.match(grace.clases)
    else:
        with open(misProfesBufferFile, "r") as f:
            misProfesData = json.loads(f.read())
            print("Usando datos guardados de MisProfes")

    # Guardamos buffer de misProfesData
    with open(misProfesBufferFile, "w+") as f:
        f.write(json.dumps(misProfesData))

    # --------- INDEX ---------
    # Escribimos datos de clases y misProfes (usados en index.html)
    datosIndex = {
        "actualizado": str(time.time() * 1000),  # En milisegundos
        "periodo": grace.periodo,
        "secure": scrapGraceSecure,
        "sGrace": grace.clavePeriodo,
        "dropDownUrl": "#" if scrapGraceSecure else grace.dropDownURL,
        "formPostUrl": courseUrl if scrapGraceSecure else grace.formURL,
        "clases": grace.clases,
        "misProfesData": misProfesData,
    }
    with open(dataFile, "w+") as f:
        f.write(dic2js(datosIndex))
        print("Se escribieron datos en {}".format(dataFile))

    # --------- PROFS ---------
    # Datos para profesores.html
    profesores = profesoresData(grace.clases)
    mejoresPorDepto = mejoresProfesPorDepartamento(profesores)

    datosProfesores = {
        "actualizado": str(time.time() * 1000),  # En milisegundos
        "periodo": grace.periodo,
        "secure": scrapGraceSecure,
        "sGrace": grace.clavePeriodo,
        "dropDownUrl": "#" if scrapGraceSecure else grace.dropDownURL,
        "formPostUrl": courseUrl if scrapGraceSecure else grace.formURL,
        "profesores": profesores,
        "mejoresPorDepto": mejoresPorDepto,
    }

    with open(profesoresDataFile, "w+") as f:
        f.write(dic2js(datosProfesores))
        print("Se escribieron datos en {}".format(profesoresDataFile))

    # test change 1
