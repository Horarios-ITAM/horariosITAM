# Planea tu horario ITAM

[Página web](https://horariositam.com/) que le ayuda a estudiantes de licenciatura del ITAM a planear su horario.    

Los usuarios pueden ingresar las clases que desean cursar y después explorar todos los posibles horarios válidos que se pueden formar (sin materias empalmadas). Para facilitar la exploración, se puede ingresar una lista de preferencias con las que se evalúan y ordenan los horarios, de tal forma que aquellos que mejor cumplan con ellas se muestran primero. 

## Tecnologías

- Python 3.9 y BeautifulSoup para el scrapeo de datos (scripts en `/update`)
- HTML5 y Javascript para la implementación de la página (`/` y `/js` respectivamente)
- [GitHub Pages](https://pages.github.com/) para hostear la página
- [GitHub Actions](https://docs.github.com/en/actions) para scrappear los datos periódicamente y hacer push al repo.

GitHub Pages y Actions implican que el único costo asociado con el sitio es el del dominio.

## Datos

Las fuentes de datos son:

- “Servicios No Personalizados" [(Grace/ITAM)](https://servicios.itam.mx) si los horarios están disponibles.
- "Registration > Look-up Classes to Add" [(Grace/ITAM)](https://servicios.itam.mx) si los horarios no están disponibles en "Servicios No Personalizados".
- [Sección dedicada a profesores del ITAM](https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003) en [MisProfes.com](https://www.misprofesores.com/). 


## Por mejorar/hacer
- Limpiar/mejorar codigo de python.
- Cachear matches de profes grace <-> mis profes
- Mejorar y probar detalladamente la función que rankea los horarios (main.js > [evaluaHorario](https://github.com/emiliocantuc/horariosITAM/blob/9f12960e16f29bd48e4fbda1258b83c88ef037db/js/main.js#L272)).
