# Planea tu horario ITAM

Página web que le ayuda a estudiantes de licenciatura del ITAM a planear su horario.    
    
Estudiantes pueden ingresar las clases que desean cursar y después explorar todos los posibles horarios válidos (sin materias empalmadas) que se pueden formar. Para facilitar dicha exploración, se puede ingresar una lista de preferencias con las que se evalúan y ordenan los horarios tal que aquellos que mejor cumplan con ellas se muestran primero. 

El/la estudiante puede ingresar como preferencias, por ejemplo, 
- que sus profesores tengan evaluaciones altas (en MisProfes.com),
- que sus clases empiecen a partir de las 9 am todos los días y 
- que los días con menos clases sean los viernes.

## Datos

La página usa datos que provienen del apartado de [“Servicios No Personalizados”](https://serviciosweb.itam.mx/EDSUP/BWZKSENP.P_MenuServNoPers) de Grace del ITAM y de la [sección dedicada a profesores del ITAM](https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003) en [MisProfes.com](https://www.misprofesores.com/). 

Como los nombres de profesores pueden ser ingresados de formas distintas en MisProfes y en Grace, se usa una [similitud de Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) de 90% para ligarle sus evaluaciones a cada profesor/a.

Los datos son actualizados cada semestre y una vez al día durante la semana de inscripciones.







