# Monitorea que el sitio funcione correctamente y notifica si algo esta raro
# Corrido con cronjob (ver .github/workflows/monitorea.yml)

import requests, argparse, time
from bs4 import BeautifulSoup

def notifica(msg, url):
    if not CHANNEL:
        print('No hay canal de notificaciones!')
        exit(1)

    print(f'Notificando {msg}')
    requests.post(
        f"https://ntfy.sh/{CHANNEL}",
        data = msg.encode('utf-8'),
        headers = {
            "Click": url,
            "Tags": "warning,horariositam"
    })

def req(url, exit_on_error = True):
    r = None
    try:
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f'Codigo de respuesta {r.status_code} para {url}')
    except Exception as e:
        print(f'Error al acceder a {url}: {e}')
        notifica(f'Sitio inaccesible: {url}', url)
        if exit_on_error: exit(1)
    return r

def checa_actualizado_hace(url, dias_max = 2):

    r = req(url, exit_on_error = False)
    if r is None: return

    pag = url.split('/')[-1]

    # Debe ser primera linea en formato "var actualizado = 1620000000000;"
    actualizado = r.text.split(';')[0].split('=')[1].replace('"', '').strip()
    dias_desde = (time.time() - float(actualizado) / 1000) / 60 / 60 / 24

    if dias_desde > dias_max:
        print(f'{pag} actualizados hace {dias_desde:.2f} dias')
        notifica(f'{pag} actualizados hace {dias_desde:.2f} dias', url)


if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--url', help = 'url del sitio', default = 'https://horariositam1.com')
    argparser.add_argument('--channel', help = 'ntfy channel for push notifications', required = True)
    args = argparser.parse_args()

    URL_BASE = args.url
    global CHANNEL
    CHANNEL = args.channel


    # Checamos que el sitio este arriba
    req(URL_BASE)

    # Que datos (index y profesores) esten actualizados (no mas de 2 dias)
    checa_actualizado_hace(URL_BASE + '/js/datos/datos_index.js')
    checa_actualizado_hace(URL_BASE + '/js/datos/datos_profesores.js')

    # Que tengamos ligas a calendarios
    r = req(URL_BASE + '/calendarios.html', exit_on_error = False)
    if r is not None:
        b = BeautifulSoup(r.text, "html.parser")
        if not b.find_all("a", {"class": "linkCalendario"}):
            print('No hay ligas a calendarios')
            notifica('No hay ligas a calendarios', URL_BASE + '/calendarios.html')

        # Y que funcionen
        for hit in b.find_all("a", {"class": "linkCalendario"}):
            print('Checando', hit['href'])
            req(URL_BASE + '/' + hit['href'], exit_on_error = False)