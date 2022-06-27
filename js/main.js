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
    let gruposEnDia=0;
    if(dia in gruposDias)
        gruposEnDia=gruposDias[dia].length;
    let totalGrupos=horario.grupos.length;
    return 1-(gruposEnDia/totalGrupos);
}

//Regresa la proporcion de grupos en el horario que caen en el rango
//Un grupos cae en el rango si rango.inicio<=inicio y grupo.fin<=rango.fin
function rangoPuntaje(horario,inicioRango,finRango){
    let inicio=strToDateHora(inicioRango);
    let fin=strToDateHora(finRango);
    let totalGrupos=horario.grupos.length;
    let caenEnRango=0;
    for(let grupo of horario.grupos){
        if(inicio.getTime()<=grupo.dtInicio.getTime() && grupo.dtFin.getTime()<=fin.getTime())
            caenEnRango+=1;
    }
    if(totalGrupos>0)
        return caenEnRango/totalGrupos;
    return 0;
}

//Regresa el tiempo entre clases total en hrs
//Para cada dia checa que grupos tienen clase ese dia y calcula el tiempo entre clases.
//Se repite esto para cada dia de la sema
function tiempoEntreClases(horario){
    let gruposDia=gruposEnDias(horario.grupos);
    let tiempo={}; //por dia
    let total=0;
    for(let dia in gruposDia){
        let grupos=gruposDia[dia];
        if(!(dia in tiempo))
            tiempo[dia]=0;
        //Ordena por hr de inicio
        grupos.sort((a,b)=> a.dtInicio.getTime()-b.dtInicio.getTime());
        for(let i=0;i<grupos.length-1;i++){
            let dif=(grupos[i+1].dtInicio-grupos[i].dtFin)/36e5; //36e5=60*60*1000 para pasar a hrs
            tiempo[dia]+=dif; 
            total+=dif;
        }
    }
    //console.log(tiempo);
    return total;
    
}

//puntaje Juntas. El minimo de tiempo que puede haber es 0. El maximo? (22:00-07:00)5=135?
//Usa tiempoEntreClases y juntas [bool] para calcular un puntaje
function puntajeJuntasSeparadas(horario,juntas){
    let tiempo=tiempoEntreClases(horario);
    let prop=tiempo/135; //(22:00-07:00)5 - TODO ver si tiene sentido
    if(juntas)
        return 1-prop;
    return prop;
}

//Promedio ponderado de preferencias con importancias
function evaluaHorario(horario,preferencias){
    //Promedio de las evaluaciones de los profesores de los grupos en el horario
    let promedioMisProfes=misProfesPuntaje(horario)*preferencias.misProfesPeso;
    //Proporcion de clases que no se encuentran en dia con menos clases preferido
    let diaConMenos=diaConMenosPuntaje(horario,preferencias.diaMenos)*preferencias.diaMenosPeso;
    //Rango horario
    let rangoHorario=rangoPuntaje(horario,preferencias.rangoStart,preferencias.rangoEnd)*preferencias.rangoPeso;
    //Clases Juntas/Separadas TODO
    let juntasSeparadas=puntajeJuntasSeparadas(horario,preferencias.juntas);
    //console.log(promedioMisProfes);
    //console.log(diaConMenos);
    //console.log(rangoHorario);
    //console.log(juntasSeparadas);
    //Sumas
    let sumaPesos=preferencias.misProfesPeso+preferencias.diaMenosPeso+preferencias.rangoPeso;
    let sumaPonderada=(promedioMisProfes+diaConMenos+rangoHorario)/sumaPesos;
    //console.log(sumaPonderada);
    if(sumaPesos>0)
        return sumaPonderada*100;
    return 0;
}

//GENERADORES

//TODOS
//Ayudador recursivo
function _generarTodosHorarios(listaDeClases,i,horarioTemp,horarios,mismoGrupo){
    if(i>=listaDeClases.length){
        if(empalmes(horarioTemp.grupos)==0){ //grupos es lista? si
            horarios.push(horarioTemp);    
        }
        return;
    }
    // Si clase es lab y mismoGrupo teoria y lab
    if(mismoGrupo && listaDeClases[i].nombre.indexOf('-LAB')>=0){
        for(let numeroGrupo in horarioTemp.grupos){
            if(listaDeClases[i].clave.startsWith(horarioTemp.grupos[numeroGrupo].claveClase)){
                let n=horarioTemp.grupos[numeroGrupo].numero+'L';
                let grupo=listaDeClases[i].grupos[n];
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
    for(let numeroGrupo in listaDeClases[i].grupos){
        let grupo=listaDeClases[i].grupos[numeroGrupo];
        let nuevosGrupos=horarioTemp.grupos.slice();
        nuevosGrupos.push(grupo);
        let h=new Horario(nuevosGrupos,0); //TODO checar por que no puedo hacer push pop en vez de crear copia
        _generarTodosHorarios(listaDeClases,i+1,h,horarios,mismoGrupo);
    }
}
//Genera todas las combinaciones de grupos que no se empalman y regresa una lista de objectos Horario
function generarTodosHorarios(clasesSeleccionadas,preferencias){
    let horarios=[];
    //Convertimos clasesSeleccionadas (dict) a lista para usar en recursion
    let listaDeClases=[];
    for(let clave in clasesSeleccionadas)
        listaDeClases.push(clasesSeleccionadas[clave]);
    //Ordenamos para que labs siempre esten despues de teoria
    listaDeClases.sort((a,b)=> a.clave.indexOf('LAB')-b.clave.indexOf('LAB'));

    _generarTodosHorarios(listaDeClases,0,new Horario([],0),horarios,preferencias.mismoGrupo);

    //Evaluamos y ordenamos descendientemente
    for(let horario of horarios)
        horario.puntaje=evaluaHorario(horario,preferencias);
    horarios.sort((a,b)=> b.puntaje-a.puntaje);
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


