# Planea tu horario ITAM

[Página web](https://horariositam.com/) que le ayuda a estudiantes de licenciatura del ITAM a planear su horario.    
    
## Descripción del proyecto

El usuario puede ingresar las clases que desea cursar y después explorar todos los posibles horarios válidos que se pueden formar (sin materias empalmadas). Para facilitar la exploración, se puede ingresar una lista de preferencias con las que se evalúan y ordenan los horarios, de tal forma que aquellos que mejor cumplan con ellas se muestran primero. 

El usuario puede preferir, por ejemplo, que

- sus profesores tengan evaluaciones altas (en MisProfes.com),
- sus clases empiecen a partir de las 9 am todos los días y 
- los días con menos clases sean los viernes.


## Tecnologías Utilizadas

- HTML5 y Javascript para la implementación de la página, usando elementos DOM para hacerla interactiva.
- GitHub Pages para hostear la página.  
- Python 3.9 y BeautifulSoup para el scrapeo de datos.

## Datos

La página usa datos que provienen del apartado de [“Servicios No Personalizados”](https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_MenuServNoPers) de Grace del ITAM y de la [sección dedicada a profesores del ITAM](https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003) en [MisProfes.com](https://www.misprofesores.com/). 

Como los nombres de profesores pueden ser ingresados de formas distintas en MisProfes y en Grace, se usa una [similitud de Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) de 90% para ligarle sus evaluaciones a cada profesor/a.

Los datos son actualizados cada semestre y una vez al día durante la semana de inscripciones.







