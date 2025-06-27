# Planea tu horario ITAM

[Página web](https://horariositam.com/) que le ayuda a estudiantes de licenciatura del ITAM a planear su horario.    

Los usuarios pueden ingresar las clases que desean cursar y después explorar todos los posibles horarios válidos que se pueden formar (sin materias empalmadas). Para facilitar la exploración, se puede ingresar una lista de preferencias con las que se evalúan y ordenan los horarios, de tal forma que aquellos que mejor cumplan con ellas se muestran primero. 

## Tecnologías utilizadas

- Python 3.9+ para el scrapeo y procesamiento de datos (scripts en `/update`).
  - Se utiliza [uv](https://github.com/astral-sh/uv) para la gestión del entorno virtual y las dependencias (definidas en `pyproject.toml`).
  - El código de los scrapers ha sido refactorizado para mejorar su robustez, mantenibilidad y adherencia a buenas prácticas (logging, manejo de errores, timeouts, etc.).
  - Librerías principales: `requests` para peticiones HTTP y `BeautifulSoup4` para el parseo de HTML.
- HTML5 y Javascript para la implementación de la página (`/` y `/js` respectivamente).
- [GitHub Pages](https://pages.github.com/) para hostear la página.
- [GitHub Actions](https://docs.github.com/en/actions) para ejecutar los scrapers periódicamente, actualizar los datos y monitorear el sitio.

GitHub Pages y Actions implican que el único costo asociado con el sitio es el del dominio.

## Datos

Las fuentes de datos son:

- [“Servicios No Personalizados" (Grace/ITAM)](https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_MenuServNoPers) si los horarios están disponibles.
- ["Registration > Look-up Classes to Add" (Grace/ITAM)]("https://serviciosweb.itam.mx/EDSUP/bwskfcls.p_sel_crse_search") si los horarios no están disponibles en "Servicios No Personalizados".
- [Sección dedicada a profesores del ITAM](https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003) en [MisProfes.com](https://www.misprofesores.com/). 


## Por mejorar/hacer
- **Mantenimiento de Scrapers**: Los scrapers han sido refactorizados para mayor robustez, pero el scrapeo web es inherentemente frágil. Se requiere monitoreo continuo y posibles ajustes si las estructuras de las páginas fuente cambian.
- Intentar usar datos de 'Grupos que continuan abiertos' para el periodo.
- Mejorar el [fuzzy name matching](https://www.rosette.com/name-matching-algorithms/) (MisProfesScrapper > `match_profesores`) que se hace para ligar a profesores obtenidos de Grace y de MisProfes.
- Mejorar y probar detalladamente la función que rankea los horarios (main.js > `evaluaHorario`).
