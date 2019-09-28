import requests
import urllib.request
import json
import os
"""
Updates data.js with ITAM and MisProfes.com data
"""
def lista_de_clases(url):
    fp = urllib.request.urlopen(url)
    html=fp.read().decode("utf-8", 'ignore')
    fp.close()
    lista=html.split("<option>")
    del(lista[0])
    del(lista[-1])
    clases=[]
    for entry in lista:
        clase=entry.replace('</option>','').replace('\n','')
        #print(clase)
        clases.append(clase)
    #print("Found "+str(len(clases)))
    return clases
def clean(str):
    return str.replace("<b>","").replace("</b>","").replace("\n","").replace("</TD>","")
def load_clase(nombre,html):
    grupos=[]
    clave=''
    entries=html.split("<TR align=center>")
    entries[-1]=entries[-1].split("</TABLE>")[0]
    for entry in entries[2:]:
        data=entry.split("<TD>")
        clave=clean(data[2])
        grupo=clean(data[3])
        profesor=clean(data[6])
        creditos=clean(data[7])
        horario=clean(data[8])
        dias=clean(data[9]).split()
        salon=clean(data[10])
        campus=clean(data[11])
        #print(data,clave,grupo,profesor,creditos,horario,dias,salon,campus)
        grupos.append({'grupo':grupo,'nombre':nombre,'profesor':profesor,'creditos':creditos,'horario':horario,'dias':dias,'salon':salon,'campus':campus})
    return {'clave':clave,'nombre':nombre,'grupos':grupos}


def load_all_clases():
    drop_down_url='http://grace.itam.mx/EDSUP/BWZKSENP.P_Horarios1?s=1573'
    nombres_clases=lista_de_clases(drop_down_url)
    clases=[]
    for clase in nombres_clases:
        post_data = {'s':'1573','txt_materia':clase}
        post_response = requests.post(url='http://grace.itam.mx/EDSUP/BWZKSENP.P_Horarios2', data=post_data)
        clases.append(load_clase(clase,post_response.text))
    return clases

def scrapeHorariosITAM():
    print("Scrapping HorariosITAM ...")
    drop_down_url='http://grace.itam.mx/EDSUP/BWZKSENP.P_Horarios1?s=1573'
    nombres_clases=lista_de_clases(drop_down_url)
    clases=[]
    for clase in nombres_clases:
        post_data = {'s':'1573','txt_materia':clase}
        post_response = requests.post(url='http://grace.itam.mx/EDSUP/BWZKSENP.P_Horarios2', data=post_data)
        clases.append(load_clase(clase,post_response.text))
    #s=json.dumps(clases)
    #print(s)
    return clases
#############################
def levenshtein_ratio(a,b):
    a=a.lower().strip()
    b=b.lower().strip()
    edits_away=0
    for index,letter in enumerate(a):
        try:
            if letter!=b[index]:edits_away+=1
        except:edits_away+=1
    ratio=((len(a)+len(b)) - edits_away) / (len(a)+len(b))
    return ratio
def replace_latin_chars(str):
    translate = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U","á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u"}
    for original,replacement in translate.items():
        str.replace(original,replacement)
    return str
def fix_url(str):
    nombre = str.strip();
    nombre = replace_latin_chars(nombre);
    nombre = nombre.replace("/[^a-zA-Z0-9\s]/", "");
    nombre = nombre.replace("(", "");
    nombre = nombre.replace(")", "");
    nombre = nombre.replace(" -", "-");
    nombre = nombre.replace("- ", "-");
    nombre = nombre.replace("\n", "");
    nombre = nombre.replace("\r", "");
    nombre = nombre.replace("  ", " ");
    nombre = nombre.replace("\\", "");
    nombre = nombre.replace(" ", "-");
    return nombre;
def profesor_url(nombre, apellido, id):
  nombre = fix_url(nombre);
  apellido = fix_url(apellido);
  #print("prof url ",nombre,apellido,id)
  return "/profesores/"+nombre+"-"+apellido+"_"+id;
def match(lista_profesITAM,misProfes):
    matched={}
    count=0
    already=0
    didnt=0
    for profe in lista_profesITAM:
        found=False
        for miprofe in misProfes.keys():
            if levenshtein_ratio(profe,miprofe)>0.90:
                found=True
                rating=misProfes[miprofe]
                #print(count,levenshtein_ratio(profe,miprofe),"profe:",profe,"miprofe:",miprofe,rating)
                count+=1
                try:
                    rating=[float(rating[0]),float(rating[1])]
                    existing=matched.get(profe,None)
                    if existing:
                        already+=1
                        weighted_avrg=((existing[0]*existing[1])+(rating[0]*rating[1]))/(existing[1]+rating[1])
                        rating=[weighted_avrg,existing[1]+rating[1]]
                    matched[profe]=rating
                except:continue
        if not found:didnt+=1
    #print("already:",already)
    #print("didnt:",didnt)
    return matched
def scrapeMisProfes():
    print("Scrapping MisProfes.com ...")
    url='https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003'
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")
    fp.close()
    b=mystr.index("dataSet")
    data=mystr[mystr.index("[",b):mystr.index(";",b)]
    data=json.loads(data)
    stripped={}
    for p in data:
        stripped[p['n']+' '+p['a']]=[p['c'],p['m']]
    return stripped

def getRatings():
    todos_profesores=list(set([grupo['profesor']for clase in clases for grupo in clase['grupos'] if len(grupo['profesor'].strip())>1]))
    matched=match(todos_profesores,scrapeMisProfes())
    print("Matching data:")
    print("\tlen todos_profesores: ",len(todos_profesores))
    print("\tlen matched: ",len(matched))
    return matched
def matchLinks(lista_profesITAM,misProfes):
    links={}
    base_url= "https://www.misprofesores.com"
    count=0
    already=0
    didnt=0
    for profe in lista_profesITAM:
        found=False
        for miprofe in misProfes.keys():
            if levenshtein_ratio(profe,miprofe)>0.90:
                found=True
                id=misProfes[miprofe]
                #print(count,levenshtein_ratio(profe,miprofe),"profe:",profe,"miprofe:",miprofe,rating)
                count+=1
                #print(miprofe.split("*"),len(miprofe.split("*")))
                nombre,apellido=miprofe.split("*")
                links[profe]=base_url+profesor_url(nombre,apellido,id)
        if not found:didnt+=1
    return links
def scrapeMisProfesLinks():
    print("Scrapping links MisProfes.com ...")
    url='https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003'
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")
    fp.close()
    b=mystr.index("dataSet")
    data=mystr[mystr.index("[",b):mystr.index(";",b)]
    data=json.loads(data)
    stripped={}
    for p in data:
        stripped[p['n']+'*'+p['a']]=p['i']
    return stripped
def getLinks():
    todos_profesores=list(set([grupo['profesor']for clase in clases for grupo in clase['grupos'] if len(grupo['profesor'].strip())>1]))
    matched=matchLinks(todos_profesores,scrapeMisProfesLinks())
    print("Matching data:")
    print("\tlen todos_profesores: ",len(todos_profesores))
    print("\tlen matched: ",len(matched))
    return matched
clases=scrapeHorariosITAM()
print("Loaded {} clases!".format(len(clases)))
lista_de_todas_clases=[clase['nombre'] for clase in clases]
ratings=getRatings()
links=getLinks()

with open("data.js","w+",encoding="utf8") as f:
    f.write("\n /**DATA*/")
    f.write("\nvar lista_de_todas_clases="+json.dumps(lista_de_todas_clases))
    f.write("\nvar ratings="+json.dumps(ratings))
    f.write("\nvar clases="+json.dumps(clases))
    f.write("\nvar links="+json.dumps(links))
print("Updated!")
input("Press enter to exit")
