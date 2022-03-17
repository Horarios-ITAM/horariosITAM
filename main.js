//LOADS
//Convierte strings como "07:00" a objectos Date con la misma fecha
function strToDateHora(strHora){
    return new Date('1970-01-01T'+strHora +'-06:00');
}
//Lee y construye una clase en las clases de data.js
function loadClase(clave){
    let clase=clases[clave];
    let c=new Clase(
        clase['nombre'],
        clave,
        loadGrupos(clase['grupos'],clave)
    );
    return c;
}

//Lee grupos de datos, construye sus clases los regresa en lista
//"grupo": "001", "nombre": "ACT-11300-CALCULO ACTUARIAL I", "profesor": "SERGIO GARCIA ALQUICIRA", "creditos": "6", "horario": "19:00-20:30", "dias": ["MA", "JU"], "salon": "RH108", "campus": "RIO HONDO"}
function loadGrupos(gruposList,claveClase){
    let out={};
    for(grupo of gruposList){
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
//Carga profesor con variables globales en data.js
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

//UTILS
//Regresa un diccionario de la forma {'LU':[grupos con clases en lunes],...}
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
//Regresa el numero de empalmes de grupos [lista] asumiendo que comparten dia.
//Usado como subrutina en empalmes().
function empalmesMismoDia(grupos){ //TODO no toma en cuenta dias!!!!
    let gruposOrdenados=grupos.slice();
    //Ordena los grupos por hr de inicio
    gruposOrdenados.sort((a,b)=> a.dtInicio.getTime()-b.dtInicio.getTime());
    let count=0;
    for(let i=0;i<grupos.length-1;i++){
        if(gruposOrdenados[i].dtFin.getTime()>gruposOrdenados[i+1].dtInicio.getTime()){
            count++;
            //console.log(grupos[i],grupos[i+1]);
        }
    }
    return count; //TODO podriamos regresar cuales empalman para feedback al usuario.
}
//Regresa el numero de empalmes de grupos [lista]
function empalmes(grupos){
    let count=0;
    let gruposDias=gruposEnDias(grupos);
    for(let dia in gruposDias){
        let gruposEnDia=gruposDias[dia];
        count+=empalmesMismoDia(gruposEnDia);
    }
    return count;
}
//----FUNCION DE EVALUACION DE HORARIO-----
//Regresa el promedio de las evaluaciones de los profesores de los grupos en el horario.
//Normaliza el promedio para que viva en 0-1.
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
        let promedio=suma/conGeneral; //Vive en 0-10
        return promedio/10; //Normalizamos
    }else{
        return 0;
    }

}
//Regresa la proporcion de clases que no se encuentran en dia.
//Normalizado 0-1.
function diaConMenosPuntaje(horario,dia){
    let gruposDias=gruposEnDias(horario.grupos);
    console.log(gruposDias);
    let gruposEnDia=0;
    if(dia in gruposDias)
        gruposEnDia=gruposDias[dia].length;
    let totalGrupos=horario.grupos.length;
    return 1-(gruposEnDia/totalGrupos);
}

//Promedio ponderado de preferencias con importancias
function evaluaHorario(horario,preferencias){
    //Promedio de las evaluaciones de los profesores de los grupos en el horario
    let promedioMisProfes=misProfesPuntaje(horario)*preferencias.misProfesPeso;
    //Proporcion de clases que no se encuentran en dia con menos clases preferido
    let diaConMenos=diaConMenosPuntaje(horario,preferencias.diaMenos)*preferencias.diaMenosPeso;
    //TODO rango clases y juntas/separadas
    let sumaPesos=preferencias.misProfesPeso+preferencias.diaMenosPeso;
    let sumaPonderada=(promedioMisProfes+diaConMenos)/sumaPesos;
    console.log(sumaPonderada);
    if(sumaPesos>0)
        return sumaPonderada*100;
    return 0;
}

//GENERADORES

//TODOS
//Ayudador recursivo
function _generarTodosHorarios(listaDeClases,i,horarioTemp,horarios){
    if(i>=listaDeClases.length){
        if(empalmes(horarioTemp.grupos)==0){ //grupos es lista? si
            horarios.push(horarioTemp);    
        }
        return;
    }
    for(let numeroGrupo in listaDeClases[i].grupos){
        let grupo=listaDeClases[i].grupos[numeroGrupo];
        let nuevosGrupos=horarioTemp.grupos.slice();
        nuevosGrupos.push(grupo);
        let h=new Horario(nuevosGrupos,0); //TODO checar porque no puedo hacer push pop en vez de crear copia
        _generarTodosHorarios(listaDeClases,i+1,h,horarios);
    }
}
//Genera todas las combinaciones de grupos que no se empalman y regresa una lista de objectos Horario
function generarTodosHorarios(clasesSeleccionadas,preferencias){
    let horarios=[];
    //Convertimos clasesSeleccionadas (dict) a lista para usar en recursion
    let listaDeClases=[];
    for(let clave in clasesSeleccionadas)
        listaDeClases.push(clasesSeleccionadas[clave]);
    
    _generarTodosHorarios(listaDeClases,0,new Horario([],0),horarios);
    //Evaluamos y ordenamos descendientemente
    for(let horario of horarios)
        horario.puntaje=evaluaHorario(horario,preferencias);
    horarios.sort((a,b)=> b.puntaje-a.puntaje);
    console.log("horarios");
    console.log(horarios);
    return horarios;
}

/**
 * Funcion asociada al boton "Generar".
 * Obtiene las preferencias y grupos ingresados por el usario,
 * genera y ordena los horarios validos y muestra el panel de "Resultados".
 */
//function generar(){
    //preferencias=getPreferencias()
    //gruposSeleccionados=getGruposSeleccionados()
    //horarios=getHorarios() ?
    //display resultados

//}


