import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os,time
import utils

BASE_DIR='assets/calendarios'

def agregaLinksDoc(conseguidos):
    sHTML=''
    for text,ligas in conseguidos.items():
        sHTML+=f'<a href={"assets/"+ligas["urlCache"]} target=_blank>{text}</a><br>\n'

    with open(f'{BASE_DIR}/calendariosTemplate.html', 'r') as f:
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
        utils.descargaArchivo('assets/'+hit['href'],urlDoc)
        print(hit.string)
        conseguidos[hit.string]={'urlCache':hit['href'],'urlITAM':urlDoc}

    conLinks=agregaLinksDoc(conseguidos)
    conActualizado=agregarActualizado(conLinks)

    with open('calendarios.html','w+') as f:
        f.write(conActualizado)
