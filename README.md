# Planea tu horario ITAM

[Página web](https://horariositam.com/) que le ayuda a estudiantes de licenciatura del ITAM a planear su horario.    

Los usuarios pueden ingresar las clases que desean cursar y después explorar todos los posibles horarios válidos que se pueden formar (sin materias empalmadas). Para facilitar la exploración, se puede ingresar una lista de preferencias con las que se evalúan y ordenan los horarios, de tal forma que aquellos que mejor cumplan con ellas se muestran primero. 

## Tecnologías utilizadas

- Python 3.9 y BeautifulSoup para el scrapeo de datos (scripts en `/update`)
- HTML5 y Javascript para la implementación de la página (`/` y `/js` respectivamente)
- GitHub Pages para hostear la página
- Un servidor de Linode ($5 USD/mes) para correr los scripts de scrapeo periódicamente

## Datos

Las fuentes de datos son:

- [“Servicios No Personalizados" (Grace/ITAM)](https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_MenuServNoPers) si los horarios están disponibles.
- ["Registration > Look-up Classes to Add" (Grace/ITAM)]("https://serviciosweb.itam.mx/EDSUP/bwskfcls.p_sel_crse_search") si los horarios no están disponibles en "Servicios No Personalizados".
- [Sección dedicada a profesores del ITAM](https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003) en [MisProfes.com](https://www.misprofesores.com/). 

Como los nombres de profesores pueden ser ingresados de formas distintas en MisProfes y en Grace, se usa una [similitud de Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) de 90% para ligarle sus evaluaciones a cada profesor/a.







Sat Mar 18 16:39:35 UTC 2023
Sesion iniciada con cookies {'cookiesession1': '678A3E0E1EAADB2DACAF330880E61FA7', 'SESSID': 'TTNHNUFBMTg5NDM0', 'TESTID': 'set'}
Periodo: PRIMAVERA 2023 LICENCIATURA
Clave de periodo: 202301
Se scrappearon las siguientes URLs
dropDownURL: https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_Horarios1?s=2242
formUrl: https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_Horarios2
s: 2242

Periodo: PRIMAVERA 2023 LICENCIATURA
Clave de Periodo: 2242
# de clases: 446
Tomando nonSecure como mas reciente
Scrappeando clases ...
Se scrappearon 475 clases!
Se encontraron 500 profesores en Grace!
Scrappeando MisProfes ...
Se scrappearon 1407 profesores de MisProfes!
Se ligaron 294 (58.80%) profesores a evaluaciones de MisProfes
Se escribieron datos en js/datos/datos_index.js
Se escribieron datos en js/datos/datos_profesores.js
