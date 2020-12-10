Optimiza tu Horario ITAM

Agrega tus clases y explora los horarios óptimos de acuerdo con tus preferencias.

Datos
<ul>
  <li>Todos los datos son actualizados semanalmente (github no soporta PHP)</li>
  <li>Los clases y horarios son actualizados de http://grace.itam.mx/EDSUP/BWZKSENP.P_Horarios2</li>
<li>Las calificaciones de los profesores de https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003</li>
  <li>Se usa un <a href="https://en.wikipedia.org/wiki/Levenshtein_distance">levenshtein ratio</a> de 90% para enlazar nombres de los profesores de los datos del ITAM y misProfes.com </li>
</ul>
"Optimizador"
<ul>
<li>Por el momento se generan un numero de horarios legales (sin clases a la misma hora) usando el algoritmo <a href="https://en.wikipedia.org/wiki/Min-conflicts_algorithm">MIN CONFLICTS</a> y se rankean de acuerdo a una funcion de optimizacion que refleja las preferencias del usuario.  </li>
</ul>
