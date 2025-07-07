import os, itertools, string, time, argparse
import utils


def fuerza_bruta(url,base_dir):
    """
    Intenta encontrar y descargar boletines por fuerza bruta.
    I.e. asume que no se conocen las claves de los programas ('COM-H')
    y los intenta encontrar.

    Intenta todas las combinaciones del formato AA-A, AAA-A, ..., ZZ-Z, ZZZ-Z.

    Se recomienda usar muy infrecuentemente.
    """

    # El producto cruz 
    prod=itertools.product(
        string.ascii_uppercase,
        string.ascii_uppercase,
        ['']+list(string.ascii_uppercase),
        string.ascii_uppercase,
    )
    # Para cada combinacion
    for i,j,k,letra in prod:
        programa=f'{i}{j}{k}-{letra}'
        try:
            # Intentamos descargar - solo es exitoso si el programa existe.
            print(f'{url}{programa}.pdf')
            utils.descargaArchivo(f'{base_dir}/{programa}.pdf',f'{url}{programa}.pdf')
            print('Encontrado y descargado!')
        except:continue


def semi_fuerza_bruta(url,base_dir):
    """
    Intenta encontrar y descargar boletines por semi-fuerza bruta.
    I.e. asume que se conocen las claves 'COM' de las carreras pero 
    no las letras de los programas ('H').

    Intenta las combinaciones del formato COM-A, COM-B, ..., COM-Z.
    """
    codigos_carreras = set([fname.split('-')[0] for fname in os.listdir(base_dir) if '.pdf' in fname])
    print(f'Codigos de carreras encontrados: {codigos_carreras}')

    for carrera in codigos_carreras:
        # Intenta descargar los programas de la carrera
        for letra in string.ascii_uppercase:
            programa=f'{carrera}-{letra}'
            try:
                utils.descargaArchivo(f'{base_dir}/{programa}.pdf',f'{url}{programa}.pdf')
                print(f'Encontrado y descargado: {url}{programa}.pdf')
            except:
                # print(f'No se pudo descargar {programa}')
                continue

def actualiza_ya_encontrados(url,base_dir):
    """
    Asume que ya existen programas en el directorio 'base_dir'
    e intenta actualizarlos descargando el archivo con el mismo nombre.
    """

    # Para cada archivo PDF en boletines/
    for fname in os.listdir(base_dir):
        if '.pdf' not in fname: continue
        
        print(f'Intentando descargar {fname}')

        # Intenta descargarlo
        try:
            utils.descargaArchivo(f'{base_dir}/{fname}',f'{url}{fname}')
        except:
            print('No se pudo descargar {fname}')


def agregaLinksDoc(base_dir):
    sHTML=''
    # Para cada archivo PDF en boletines/
    for fname in sorted(os.listdir(base_dir)):
        if '.pdf' not in fname: continue
        # Agrega un link a sHTML de la forma:
        sHTML+=f'<a href={base_dir}/{fname} target=_blank>{fname.split(".")[0]}</a><br>\n'

    # Lee el template
    with open(f'{base_dir}/boletinesTemplate.html', 'r') as f:
        template=f.read()
    
    # Y reemplaza la lista de ligas en su lugar
    return template.replace('<!--Lista de links-->',sHTML)

def agregarActualizado(html):
    return html.replace('//Actualizado',str(time.time()*1000))



if __name__=='__main__':

    # Parseador de argumentos
    parser=argparse.ArgumentParser(
        prog='Cache Boletines',
        description='Intenta descargar/actualizar copias de los programas academicos del ITAM.'
    )
    parser.add_argument(
        '--url_boletines',
        default='http://escolar.itam.mx/licenciaturas/boletines/',
        help='La URL donde se encuentran los boletines publicados. Por ejemplo "[url_boletines]/COM-H.pdf".'
    )
    parser.add_argument(
        '--modo',
        choices=['actualiza', 'semi-encuentra', 'encuentra','html'],
        default='actualiza',
        help='Actualiza los boletines ya encontrados y que vivien en --dir (actualiza),\
            encuentra boletines con fuerza bruta (encuentra) o solo actualiza el archivo boletines.html (html).'
    )
    parser.add_argument(
        '--dir',
        default='assets/boletines',
        help='Directorio en el cual se encuentran/guardan los boletines descargados.'
    )
    args=vars(parser.parse_args())


    if args['modo'] == 'encuentra':
        print('Obteniendo boletines por fuerza bruta')
        fuerza_bruta(args['url_boletines'],args['dir'])

    elif args['modo'] == 'semi-encuentra':
        print('Obteniendo boletines por semi-fuerza bruta')
        semi_fuerza_bruta(args['url_boletines'],args['dir'])

    elif args['modo'] == 'actualiza':
        print('Actualizando boletines ya encontrados')
        actualiza_ya_encontrados(args['url_boletines'],args['dir'])
    
    # Agregamos links a template y regresamos el html
    conLinks=agregaLinksDoc(args['dir'])
    # Agregamos la fecha de actualizacion
    conActualizado=agregarActualizado(conLinks)

    # Guardamos en .html
    with open('boletines.html','w+') as f:
        f.write(conActualizado)
    



