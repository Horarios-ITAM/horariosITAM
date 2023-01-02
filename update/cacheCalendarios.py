import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os,time

def descargaArchivo(path,url):
    dir=os.path.dirname(path)
    os.makedirs(dir,exist_ok=True)
    response=requests.get(url)
    open(path, "wb").write(response.content)

def agregaLinksDoc(conseguidos):
    sHTML=''
    for text,ligas in conseguidos.items():
        sHTML+=f'<a href={ligas["urlCache"]} target=_blank>{text}</a><br>\n'

    with open('calendarios/calendariosTemplate.html', 'r') as f:
        template=f.read()
    
    return template.replace('<!--Lista de links-->',sHTML)

def agregarActualizado(html):
    return html.replace('//Actualizado',str(time.time()*1000))



if __name__=='__main__':
    url='http://escolar.itam.mx/servicios_escolares/calendarios.php'

    r=requests.get(url)

    b=BeautifulSoup(r.text, "html.parser")
    conseguidos={}
    for hit in b.find_all("a", {"class": "enlace"}):
        urlDoc=urljoin(url,hit['href'])
        descargaArchivo(hit['href'],urlDoc)
        print(hit.string)
        conseguidos[hit.string]={'urlCache':hit['href'],'urlITAM':urlDoc}

    conLinks=agregaLinksDoc(conseguidos)
    conActualizado=agregarActualizado(conLinks)

    with open('calendarios.html','w+') as f:
        f.write(conActualizado)
