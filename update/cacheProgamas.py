import os,itertools,requests,string,time


def descargaArchivo(path,url):
    dir=os.path.dirname(path)
    os.makedirs(dir,exist_ok=True)
    response=requests.get(url)
    if response.status_code!=200:
        raise Exception('Not found')
    else:
        open(path, "wb").write(response.content)

def fuerza_bruta(URL):
    prod=itertools.product(
        string.ascii_uppercase,
        string.ascii_uppercase,
        ['']+list(string.ascii_uppercase),
        string.ascii_uppercase,
    )
    for i,j,k,letra in prod:
        programa=f'{i}{j}{k}-{letra}'
        try:
            print(f'{URL}{programa}.pdf')
            descargaArchivo(f'boletines/{programa}.pdf',f'{URL}{programa}.pdf')
            print('Encontrado y descargado!')
        except:continue

def actualiza_ya_encontrados(URL):
    for fname in os.listdir('boletines'):
        if '.pdf' in fname: continue
        descargaArchivo(f'boletines/{fname}',f'{URL}{fname}')


def agregaLinksDoc():
    sHTML=''
    for fname in sorted(os.listdir('boletines')):
        if '.pdf' not in fname: continue
        sHTML+=f'<a href=boletines/{fname} target=_blank>{fname.split(".")[0]}</a><br>\n'

    with open('boletines/boletinesTemplate.html', 'r') as f:
        template=f.read()
    
    return template.replace('<!--Lista de links-->',sHTML)

def agregarActualizado(html):
    return html.replace('//Actualizado',str(time.time()*1000))



if __name__=='__main__':
    URL='http://escolar.itam.mx/licenciaturas/boletines/'
    #fuerza_bruta(URL)
    actualiza_ya_encontrados(URL)

    conLinks=agregaLinksDoc()
    conActualizado=agregarActualizado(conLinks)

    with open('boletines.html','w+') as f:
        f.write(conActualizado)



