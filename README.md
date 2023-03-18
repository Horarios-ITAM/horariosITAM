# Planea tu horario ITAM

[Página web](https://horariositam.com/) que le ayuda a estudiantes de licenciatura del ITAM a planear su horario.    

Los usuarios pueden ingresar las clases que desean cursar y después explorar todos los posibles horarios válidos que se pueden formar (sin materias empalmadas). Para facilitar la exploración, se puede ingresar una lista de preferencias con las que se evalúan y ordenan los horarios, de tal forma que aquellos que mejor cumplan con ellas se muestran primero. 

## Tecnologías utilizadas

- Python 3.9 y BeautifulSoup para el scrapeo de datos (scripts en `/update`)
- HTML5 y Javascript para la implementación de la página (`/` y `/js` respectivamente)
- [GitHub Pages](https://pages.github.com/) para hostear la página
- [GitHub Actions](https://docs.github.com/en/actions) para scrappear los datos periódicamente y hacer push al repo.

GitHub Pages y Actions implican que el único costo asociado con el sitio es el del dominio.

## Datos

Las fuentes de datos son:

- [“Servicios No Personalizados" (Grace/ITAM)](https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_MenuServNoPers) si los horarios están disponibles.
- ["Registration > Look-up Classes to Add" (Grace/ITAM)]("https://serviciosweb.itam.mx/EDSUP/bwskfcls.p_sel_crse_search") si los horarios no están disponibles en "Servicios No Personalizados".
- [Sección dedicada a profesores del ITAM](https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003) en [MisProfes.com](https://www.misprofesores.com/). 

Como los nombres de profesores pueden ser ingresados de formas distintas en MisProfes y en Grace, se usa una [similitud de Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) de 90% para ligarle sus evaluaciones a cada profesor/a.
