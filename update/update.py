
from graceScrapper import GraceScrapper
from misProfesScrapper import MisProfesScrapper
import json
from utils import claveToDepto

def profesoresData(clases):
    """
    Regresa un diccionario de la forma nombre profesor:{'link':,'general':,'n':,'grupos'}
    Para uso en profesores.html.
    """
    profesores={}
    for clase, info in clases.items():
        for grupo in info['grupos']:
            profesor=grupo['profesor']
            if profesor not in profesores:
                if profesor in misProfesData:
                    profesores[profesor]=misProfesData[profesor]
                    profesores[profesor]['grupos']={}
                else:
                    profesores[profesor]={'grupos':{}}
            nombreClase=grupo['nombre']
            if nombreClase not in profesores[profesor]['grupos']:
                profesores[profesor]['grupos'][nombreClase]=[]
            profesores[profesor]['grupos'][nombreClase].append(grupo)
    return profesores

def profesoresPorDepartamento(profesores):
    """
    Regresa un diccionario de la forma departamento:[lista de profesores].
    Se asume que profesores es la salida de profesoresData.

    """
    profesPorDepto={}
    for profesor,info in profesores.items():
        depto=claveToDepto[list(info['grupos'].keys())[0].split('-')[0]]
        if depto not in profesPorDepto:
            profesPorDepto[depto]=[]
        profesPorDepto[depto].append(profesor)
    return profesPorDepto

def mejoresProfesPorDepartamento(profesores,n=10):
    """
    Regresa los n mejores profesores (de acuerdo a 'general' de MisProfes)
    por departamento.
    """
    profesPorDepto=profesoresPorDepartamento(profesores)
    for depto,profes in profesPorDepto.items():
        calif=lambda x:profesores[x]['general'] if 'general' in profesores[x] else 0
        profesPorDepto[depto]=sorted(profes,key=lambda x:calif(x),reverse=True)[:n]
    return profesPorDepto



if __name__=="__main__":
    dataFile="../js/dataTemp.js"
    profesoresDataFile="../js/profesoresTemp.js"
    misProfesUrl="https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003"
    profesoresMatchRate=0.8

    grace=GraceScrapper()
    grace.scrap()

    misProfes=MisProfesScrapper(misProfesUrl)
    misProfes.scrap()
    misProfesData=misProfes.match(grace.profesores,profesoresMatchRate)

    with open(dataFile,"w+") as f:
        f.write("let periodo='"+grace.periodo+"';")
        f.write("\nlet sGrace='"+grace.s+"';")
        f.write("\nlet dropDownUrl='"+grace.dropDownURL+"';")
        f.write("\nlet formPostUrl='"+grace.formURL+"';")
        f.write("\nlet clases="+json.dumps(grace.clases,indent=2)+";")

        f.write("\nlet misProfesData="+json.dumps(misProfesData,indent=2)+";") 

        print("Se escribieron datos en {}".format(dataFile))
    
    # Datos para profesores.html
    profesores=profesoresData(grace.clases)
    mejoresPorDepto=mejoresProfesPorDepartamento(profesores)

    with open(profesoresDataFile,"w+") as f:
        f.write("let periodo='"+grace.periodo+"';")
        f.write("\nlet sGrace='"+grace.s+"';")
        f.write("\nlet dropDownUrl='"+grace.dropDownURL+"';")
        f.write("\nlet formPostUrl='"+grace.formURL+"';")
        f.write("\nlet profesores="+json.dumps(profesores,indent=2)+";")
        f.write("\nlet mejoresPorDepto="+json.dumps(mejoresPorDepto,indent=2)+";")

        print("Se escribieron datos en {}".format(profesoresDataFile))





    
