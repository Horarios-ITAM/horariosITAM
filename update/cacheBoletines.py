import os,itertools,requests,string,time,sys
import utils

BASE_DIR='assets/boletines'

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
            utils.descargaArchivo(f'{BASE_DIR}/{programa}.pdf',f'{URL}{programa}.pdf')
            print('Encontrado y descargado!')
        except:continue

def actualiza_ya_encontrados(URL):
    # Para cada archivo PDF en boletines/
    for fname in os.listdir(BASE_DIR):
        if '.pdf' not in fname: continue
        print(fname)

        # Intenta descargarlo
        try:
            utils.descargaArchivo(f'{BASE_DIR}/{fname}',f'{URL}{fname}')
        except:
            print('No se pudo descargar {fname}')


def agregaLinksDoc():
    sHTML=''
    # Para cada archivo PDF en boletines/
    for fname in sorted(os.listdir(BASE_DIR)):
        if '.pdf' not in fname: continue
        # Agrega un link a sHTML de la forma:
        sHTML+=f'<a href={BASE_DIR}/{fname} target=_blank>{fname.split(".")[0]}</a><br>\n'

    # Lee el template
    with open(f'{BASE_DIR}/boletinesTemplate.html', 'r') as f:
        template=f.read()
    
    # Y reemplaza la lista de ligas en su lugar
    return template.replace('<!--Lista de links-->',sHTML)

def agregarActualizado(html):
    return html.replace('//Actualizado',str(time.time()*1000))



if __name__=='__main__':
    # Direccion base de boletines
    URL='http://escolar.itam.mx/licenciaturas/boletines/'


    if len(sys.argv)>1 and sys.argv[1]=='bruta':
        print('Obteniendo boletines por fuerza bruta')
        fuerza_bruta(URL)

    else:
        print('Actualizando boletines ya encontrados')
        actualiza_ya_encontrados(URL)
    
    # Agregamos links a template y regresamos el html
    conLinks=agregaLinksDoc()
    # Agregamos la fecha de actualizacion
    conActualizado=agregarActualizado(conLinks)

    # Guardamos en .html
    with open('boletines.html','w+') as f:
        f.write(conActualizado)
    



