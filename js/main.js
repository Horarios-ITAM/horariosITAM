/**
 * Convierte strings como "07:00" a objectos Date con la misma fecha
 * @param {String} strHora El string de la forma "07:00"
 * @returns {Date} Obj. Date con la hora. 
 */
function strToDateHora(strHora){
    return new Date('1970-01-01T'+strHora +'-06:00');
}

/**
 * Lee y construye una clase en las clases de data.js
 * @param {String} clave La clave de la clase a cargar.
 * @returns {Clase} La clase cargada como obj. Clase.
 */
function loadClase(clave){
    let clase=clases[clave];
    let c=new Clase(
        clase['nombre'],
        clave,
        loadGrupos(clase['grupos'],clave)
    );
    return c;
}

/**
 * Dado el dict. de 'grupos' de una clase (data.js), construye sus objectos los regresa en lista.
 * @param {*} gruposDict 
 * @param {String} claveClase 
 * @returns {[Grupo]} Lista de objs. Grupo.
 */
function loadGrupos(gruposDict,claveClase){
    let out={};
    for(grupo of gruposDict){
        let inicio=grupo['inicio'];
        let dtInicio=strToDateHora(inicio);
        let fin=grupo['fin'];
        let dtFin=strToDateHora(fin);
        g=new Grupo(
            grupo['grupo'],
            claveClase,
            loadProfesor(grupo['profesor']),
            grupo['salon'],
            grupo['dias'],
            inicio,
            fin,
            dtInicio,
            dtFin,
            grupo['horario']
        );
        out[grupo['grupo']]=g;
    }
    return out;
}

/**
 * Lee datos (data.js) y construye obj. de Profesor dado su nombre. 
 * Si no se encuentra al profesor en misProfesData, se asignan NaNs a
 * 'general','n' y 'link'.
 * @param {String} nombreProfesor 
 * @returns {Profesor} Obj. del profesor.
 */
function loadProfesor(nombreProfesor){
    if(nombreProfesor in misProfesData)
        return new Profesor(
            nombreProfesor,
            misProfesData[nombreProfesor]["general"], 
            misProfesData[nombreProfesor]["n"],
            misProfesData[nombreProfesor]["link"]
        );
    return new Profesor(
        nombreProfesor,
        NaN,
        NaN,
        NaN,
    );
}

// UTILS
/**
 * Regresa un diccionario de la forma {'LU':[grupos con clases en lunes], etc.}
 * NOTA: Solo incluye dias que tienen alguna clase.
 * @param {[Grupo]} grupos Lista de objs. Grupo.
 * @returns {Map<String,[Grupo]>} Dict. dia -> [objs. grupo]
 */
function gruposEnDias(grupos){
    let out={};
    for(let grupo of grupos){
        for(let dia of grupo.dias){
            if(!(dia in out)){
                out[dia]=[];
            }
            out[dia].push(grupo);
        }
    }
    return out;
}

/**
 * Regresa el numero de empalmes de una lista de grupos ASUMIENDO que comparten dia. 
 * (Es decir, todos los grupos se asumen son del mismo dia)
 * Usado como subrutina en empalmes().
 * @param {[Grupo]} grupos Lista de objs. Grupo. 
 * @returns {Int} El no. de empalmes detectados. 
 */
function empalmesMismoDia(grupos){ //TODO no toma en cuenta dias!!!!
    // Hacemos copia local
    let gruposOrdenados=grupos.slice();
    // Ordena los grupos por hora de inicio
    gruposOrdenados.sort((a,b)=> a.dtInicio.getTime()-b.dtInicio.getTime());
    let count=0;
    // Recorremos la lista ordenada
    for(let i=0;i<grupos.length-1;i++){
        // Si se cumple que la i-esima clase termina despues del inicio de la (i+1)-esima hay empalme.
        if(gruposOrdenados[i].dtFin.getTime()>gruposOrdenados[i+1].dtInicio.getTime()){
            count++;
        }
    }
    return count; // TODO podriamos regresar cuales empalman para feedback al usuario.
}

/**
 * Regresa el numero de empalmes entre una lista de grupos.
 * @param {[Grupo]} grupos Lista de objs. Grupo.
 * @returns {Int} El no. de empalmes detectados.
 */
function empalmes(grupos){
    let count=0;
    let gruposDias=gruposEnDias(grupos);
    for(let dia in gruposDias){
        let gruposEnDia=gruposDias[dia];
        count+=empalmesMismoDia(gruposEnDia);
    }
    return count;
}

// ----FUNCION DE EVALUACION DE HORARIO-----
/**
 * NOTA: Todas las componentes de la f. evaluadora deben regresar valores
 * en [0,1] y entre mas alto mejor.
*/

/**
 * Regresa el promedio normalizado [0-1] de las evaluaciones de los profesores de los grupos en el horario.
 * Mayor promedio general de profesores implica mayor puntaje.
 * @param {Horario} horario Obj. Horario al que calificar
 * @returns {Float} Puntaje correspondiente
 */
function misProfesPuntaje(horario){
    let suma=0;
    let conGeneral=0;
    for(let grupo of horario.grupos){
        let general=grupo.profesor.misProfesGeneral;
        if(!isNaN(general)){
            suma+=general;
            conGeneral+=1;
        }
    }
    if(conGeneral>0){
        let promedio=suma/conGeneral; // Vive en 0-10
        return promedio/10; // Normalizamos
    }else{
        return 0;
    }
}

/**
 * Penaliza de acuerdo a la proporcion de clases en 'dia'.
 * @param {Horario} horario Obj. Horario al que calificar
 * @param {String} dia Dia para evaluar
 * @returns {Float} Puntaje correspondiente
 */
function diaConMenosPuntaje(horario,dia){
    let gruposDias=gruposEnDias(horario.grupos);
    let gruposEnDia=0;
    if(dia in gruposDias)
        gruposEnDia=gruposDias[dia].length;
    let totalGrupos=horario.grupos.length;
    return 1-(gruposEnDia/totalGrupos);
}

/**
 * Penaliza de acuerdo a la proporcion de dias que tiene que asistir. 
 * @param {Horario} horario Obj. Horario a evaluar.
 * @returns {Float} Puntaje correspondiente.
 */
function menosDiasPuntaje(horario){
    // Numero de dias que tiene que ir
    let nDias=Object.keys(gruposEnDias(horario.grupos)).length;
    return 1-(nDias/6);
}

/**
 * Regresa la proporcion de grupos que caen dentro el rango indicado por el usuario.
 * @param {Horario} horario Obj. Horario a evaluar
 * @param {String} inicioRango Inicio del rango '07:00'
 * @param {String} finRango Fin del rando '09:00'
 * @returns {Float} Puntaje correspondiente
 */
function rangoPuntaje(horario,inicioRango,finRango){
    // Convertimos a objs. Date 
    let inicio=strToDateHora(inicioRango);
    let fin=strToDateHora(finRango);

    // Calculamos cuantos caen dentro del rango
    let caenEnRango=0;
    for(let grupo of horario.grupos){
        // Cae dentro del rango si su hora de inicio es mayor a la del rango
        // y si su hora de fin es menor a la del rango.
        if(inicio.getTime()<=grupo.dtInicio.getTime() && grupo.dtFin.getTime()<=fin.getTime())
            caenEnRango+=1;
    }
    // Calculamos la proporcion
    let totalGrupos=horario.grupos.length;
    if(totalGrupos>0)
        return caenEnRango/totalGrupos;
    return 0;
}

/**
 * Regresa el tiempo entre clases total en horas.
 * Para cada dia se checan los grupos del dia y calcula el tiempo entre clases.
 * Usado como subrutina en puntajeJuntasSeparadas().
 * @param {Horario} horario Obj. Horario que contiene los grupos.
 * @returns {Float} El no. de horas entre clases.
 */
function tiempoEntreClases(horario){
    // Dia -> [Grupos que tienen clase]
    let gruposDia=gruposEnDias(horario.grupos);
    // Dia -> hrs entre clases
    let tiempo={};
    let total=0;
    // Para cada dia
    for(let dia in gruposDia){
        let grupos=gruposDia[dia];
        if(!(dia in tiempo))
            tiempo[dia]=0;

        // Ordenamos los grupos del dia por hr de inicio
        grupos.sort((a,b)=> a.dtInicio.getTime()-b.dtInicio.getTime());

        // Sumamos la diferencia en horas entre el comienzo de la (i+1)-esima clase y el fin de la i-esima.
        for(let i=0;i<grupos.length-1;i++){
            // Para convertir de milisegundos a hrs divide entre 60*60*1000=36e5
            let dif=(grupos[i+1].dtInicio-grupos[i].dtFin)/36e5;
            tiempo[dia]+=dif; 
            total+=dif;
        }
    }
    return total; 
}

/**
 * TODO
 * @param {*} horario 
 * @param {*} juntas 
 * @returns 
 */
function horasMuertasPuntaje(horario){
    let tiempo=tiempoEntreClases(horario);
    return 1-(tiempo/(1+tiempo));
}


/**
 * Calcula la evaluacion total de un horario usando las preferencias del usuario.
 * Es un peso ponderado usando los pesos en preferencias.
 * El resultado vive en [0,100]. 
 * @param {Horario} horario Obj. Horario a evaluar
 * @param {Preferencias} preferencias Obj. Preferencias que corresponden al usuario.
 * @returns {Float} El puntaje correspondiente en [0,100].
 */
function evaluaHorario(horario,preferencias){
    // Promedio de las evaluaciones de los profesores de los grupos en el horario
    let promedioMisProfes=misProfesPuntaje(horario)*preferencias.misProfesPeso;

    // Penaliza entre mas dias de la semana se tenga que atender
    let menosDias=menosDiasPuntaje(horario)*preferencias.menosDiasPeso;

    // Penaliza entre mas horas muertas entre clase
    let horasMuertas=horasMuertasPuntaje(horario)*preferencias.horasMuertasPeso

    // Rango horario
    let rangoHorario=rangoPuntaje(horario,preferencias.rangoStart,preferencias.rangoEnd)*preferencias.rangoPeso;

    // console.log(promedioMisProfes);
    // console.log(menosDias);
    // console.log(horasMuertas);
    // console.log(rangoHorario);

    

    let sumaPesos=preferencias.misProfesPeso+preferencias.menosDiasPeso+preferencias.horasMuertasPeso+preferencias.rangoPeso;
    if(sumaPesos>0){
        // Vive en [0,100]
        let sumaPonderada=(promedioMisProfes+menosDias+horasMuertas+rangoHorario)/sumaPesos;
        return sumaPonderada*100;
    }else{
        return 0;
    }
}

// GENERADORES

// Ayudador recursivo
/**
 * Genera horario recursivamente. Usado como subrutina en generarTodosHorarios().
 * Guarda los horarios generados en la lista referenciada 'horarios'.
 * 
 * NOTA: Asume que listaDeClases es tal que grupos con -LAB aparecen despues de su
 * grupo de teoria.
 * 
 * @param {[Clase]} listaDeClases 
 * @param {Int} i 
 * @param {Horario} horarioTemp 
 * @param {[Horario]} horarios 
 * @param {Bool} mismoGrupo Corresponde a preferencias.mismoGrupo.
 * Indica si tomar el mismo grupo de teoria y laboratorio en caso de tener.
 * @returns {null}
 */
function _generarTodosHorarios(listaDeClases,i,horarioTemp,horarios,mismoGrupo){
    // Si ya recorrimos toda la lista
    if(i>=listaDeClases.length){
        // Y no hay empalmes en el horario que armamos
        if(empalmes(horarioTemp.grupos)==0){
            // Guardamos el horario
            horarios.push(horarioTemp);    
        }
        return;
    }
    // Si clase es lab y mismoGrupo=true agregamos el lab y recursamos
    if(mismoGrupo && listaDeClases[i].nombre.indexOf('-LAB')>=0){
        // Buscamos su grupo de teoria
        for(let numeroGrupo in horarioTemp.grupos){
            // Si la clave de la clase actual empieza con la clave del grupo
            if(listaDeClases[i].clave.startsWith(horarioTemp.grupos[numeroGrupo].claveClase)){
                // El numero de grupo con L al final para distinguirlo como LAB. 
                let n=horarioTemp.grupos[numeroGrupo].numero+'L';
                let grupo=listaDeClases[i].grupos[n];

                // Igual que normal (ver for de abajo)
                let nuevosGrupos=horarioTemp.grupos.slice();
                nuevosGrupos.push(grupo);
                let h=new Horario(nuevosGrupos,0);
                _generarTodosHorarios(listaDeClases,i+1,h,horarios,mismoGrupo);
                return;
            }else{
                console.log("Todavia no hay teoria");
            }
        }
    }
    // Para cada grupo en la clase actual
    for(let numeroGrupo in listaDeClases[i].grupos){
        let grupo=listaDeClases[i].grupos[numeroGrupo];
        // Le hacemos una copia a horarioTemp.grupos
        let nuevosGrupos=horarioTemp.grupos.slice();
        // A la cual le agregamos el grupo
        nuevosGrupos.push(grupo);
        // Creamos nuevo horarioTemp con nuevosGrupos
        let h=new Horario(nuevosGrupos,0);
        // Llamada recursiva
        _generarTodosHorarios(listaDeClases,i+1,h,horarios,mismoGrupo);
    }
}

/**
 * Genera todas las combinaciones de grupos que no se empalman y regresa una lista
 * de objectos Horario ordenada descendientemente por su puntaje.
 * 
 * @param {Map<String,Clase>} clasesSeleccionadas Las clases seleccionadas por el usuario
 * @param {Preferencias} preferencias Obj. de Preferencias correspondiente al usuario.
 * @returns {[Horario]} Lista de horarios ordenada descendientemente por puntaje.
 */
function generarTodosHorarios(clasesSeleccionadas,preferencias){
    // Convertimos clasesSeleccionadas (dict) a lista para usar en recursion
    let listaDeClases=[];
    for(let clave in clasesSeleccionadas)
        listaDeClases.push(clasesSeleccionadas[clave]);

    // Ordenamos para que labs siempre esten despues de teoria
    listaDeClases.sort((a,b)=> a.clave.indexOf('LAB')-b.clave.indexOf('LAB'));

    // Horarios generados
    let horarios=[];

    // Llamamos al generador recursivo
    _generarTodosHorarios(listaDeClases,0,new Horario([],0),horarios,preferencias.mismoGrupo);

    // Evaluamos y ordenamos descendientemente
    for(let horario of horarios)
        horario.puntaje=evaluaHorario(horario,preferencias);
    horarios.sort((a,b)=> b.puntaje-a.puntaje);

    return horarios;
}

// --- Autocomplete Functionality ---

/**
 * Initializes the autocomplete functionality for the class search input.
 */
function initAutocomplete() {
    const input = document.getElementById('a');
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.setAttribute('id', 'autocomplete-suggestions');
    // input.parentNode is now the .autocomplete-wrapper
    // Insert suggestionsContainer into the wrapper, after the input
    input.parentNode.appendChild(suggestionsContainer); // Appending as the last child within the wrapper

    input.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        suggestionsContainer.innerHTML = ''; // Clear previous suggestions
        suggestionsContainer.style.display = 'none';

        if (query.length < 1) { // Minimum characters to trigger autocomplete
            return;
        }

        const matchedClases = Object.values(clases).filter(clase => {
            return clase.nombre.toLowerCase().includes(query);
        });

        if (matchedClases.length > 0) {
            suggestionsContainer.style.display = 'block';
            matchedClases.forEach(clase => {
                const suggestionItem = document.createElement('div');
                suggestionItem.classList.add('autocomplete-item');
                suggestionItem.textContent = clase.nombre;
                suggestionItem.addEventListener('click', function() {
                    input.value = clase.nombre;
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                });
                suggestionsContainer.appendChild(suggestionItem);
            });
        }
    });

    // Optional: Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== input && e.target.parentNode !== suggestionsContainer) {
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.style.display = 'none';
        }
    });
}

/**
 * Initializes the autocomplete functionality for the professor search input.
 */
function initAutocompleteProfesores() {
    const input = document.getElementById('profesorSeleccionado');
    if (!input) return; // Safety check, in case it's called on a page without this input

    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.setAttribute('id', 'autocomplete-suggestions-profesores'); // Unique ID
    // input.parentNode is now the .autocomplete-wrapper
    // Insert suggestionsContainer into the wrapper, after the input
    input.parentNode.appendChild(suggestionsContainer); // Appending as the last child within the wrapper

    input.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        suggestionsContainer.innerHTML = '';
        suggestionsContainer.style.display = 'none';

        if (query.length < 1) {
            return;
        }

        // Use Object.keys to get professor names, then filter
        const matchedProfesores = Object.keys(profesores).filter(profName => {
            return profName && profName.toLowerCase().includes(query); // Filter out empty string key and match
        });

        if (matchedProfesores.length > 0) {
            suggestionsContainer.style.display = 'block';
            matchedProfesores.forEach(profName => {
                const suggestionItem = document.createElement('div');
                suggestionItem.classList.add('autocomplete-item'); // Can reuse class if styling is identical
                suggestionItem.textContent = profName; // Professor name is the key
                suggestionItem.addEventListener('click', function() {
                    input.value = profName;
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                    // Optionally, trigger the original onChange behavior if still needed after selection
                    if (typeof buscarProfesor === 'function') {
                        buscarProfesor();
                    }
                });
                suggestionsContainer.appendChild(suggestionItem);
            });
        }
    });

    document.addEventListener('click', function(e) {
        if (e.target !== input && e.target.parentNode !== suggestionsContainer) {
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.style.display = 'none';
        }
    });
}
