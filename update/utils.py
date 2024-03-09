import urllib.request
import json,os,requests

claveToDepto={
 'ACT': 'ACTUARIA Y SEGUROS',
 'ADM': 'ADMINISTRACION',
 'CSO': 'CIENCIA POLITICA',
 'COM': 'COMPUTACION',
 'CON': 'CONTABILIDAD',
 'CEB': 'CTRO DE ESTUDIO DEL BIENESTAR',
 'DER': 'DERECHO',
 'ECO': 'ECONOMIA',
 'EST': 'ESTADISTICA',
 'EGN': 'ESTUDIOS GENERALES',
 'EIN': 'ESTUDIOS INTERNACIONALES',
 'IIO': 'ING. INDUSTRIAL Y OPERACIONES',
 'CLE': 'LENGUAS (CLE)',
 'LEN': 'LENGUAS (LEN)',
 'MAT': 'MATEMATICAS',
 'SDI': 'SISTEMAS DIGITALES'
 }

def getHTML(url):
    """
    Regresa el contenido HTML del url.
    """
    with urllib.request.urlopen(url) as u:
        html=u.read().decode("utf-8","ignore")
    return html
    # response = requests.get(url, verify=False)
    # html = response.content.decode("utf-8", "ignore")
    # return html

def descargaArchivo(path,url):
    """
    Intenta descargar el archivo en url en el directorio local path.
    Si el directorio no existe lo crea. Si no encuentra el archivo avienta error.
    """
    dir=os.path.dirname(path)
    os.makedirs(dir,exist_ok=True)
    response=requests.get(url)
    if response.status_code!=200:
        raise Exception(f'Not found @ {url}')
    else:
        open(path, "wb").write(response.content)

def replace_latin_chars(str):
    """
    Reemplaza letras con acentos por letras sin acentos y ñ con n en str.
    """
    translate = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U","á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u"}
    for original,replacement in translate.items():
        str.replace(original,replacement)
    return str

def levenshtein(s0, s1):
    """
    Calculates the levenshtein distance.
    Taken from https://github.com/luozhouyang/python-string-similarity/blob/master/strsimpy/levenshtein.py
    """
    if s0 == s1:
        return 0.0
    if len(s0) == 0:
        return len(s1)
    if len(s1) == 0:
        return len(s0)

    v0 = [0] * (len(s1) + 1)
    v1 = [0] * (len(s1) + 1)

    for i in range(len(v0)):
        v0[i] = i

    for i in range(len(s0)):
        v1[0] = i + 1
        for j in range(len(s1)):
            cost = 1
            if s0[i] == s1[j]:
                cost = 0
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0, v1 = v1, v0

    return v0[len(s1)]

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

def levenshteinSimilarity(s0,s1):
    """
    Returns the normalized levenshtein similarity
    """
    m=max(len(s0),len(s1))
    if m==0:
        return 1.0
    return 1-(levenshtein(s0,s1)/m)

def periodoValido(periodo):
    periodos=['PRIMAVERA','VERANO','OTOÑO']
    if len(periodo.split(' '))!=3:
        return False
    op,yr,lic=periodo.split()
    if lic!="LICENCIATURA" or op not in periodos or not str.isnumeric(yr):
        return False
    return True
def rankPeriodo(periodo_str):
    """
    Asigna numerico usado para ordenar a cadena del tipo 'OTOÑO 2022 LICENCIATURA'. 
    """
    assert periodo_str.count(' ')==2,'Periodo invalido'
    sem,yr,_=periodo_str.split()
    periodos=['PRIMAVERA','VERANO','OTOÑO']
    assert sem in periodos,'Periodo invalido'
    opOffset=periodos.index(sem)
    return 10*int(yr)+int(opOffset)


def periodoMasReciente(periodos):
    return max(periodos,key=rankPeriodo)

def dic2js(d):
    out=''
    for k,v in d.items():
        if isinstance(v,str):
            out+=f'let {k}="{v}";\n'
        else:
            out+=f'let {k}={json.dumps(v,indent=2)};\n'
    return out
    

    

if __name__=="__main__":
    # Prueba rankPeriodo
    # periodos=['PRIMAVERA 2011 LICENCIATURA','PRIMAVERA 2010 LICENCIATURA','VERANO 2010 LICENCIATURA','OTOÑO 2010 LICENCIATURA']
    # ordenados=sorted(periodos,key=rankPeriodo,reverse=True)
    # assert ordenados==periodos
    # for p in periodos:
    #     assert periodoValido(p)

    # i=['PRIMAVERA 2023 LICENCIATURA','VERANO 2023 LICENCIATURA']
    # print(sorted(i,key=rankPeriodo,reverse=True))
    print(periodoMasReciente(['PRIMAVERA 2024 LICENCIATURA','OTOÑO 2023 LICENCIATURA'])) 

    