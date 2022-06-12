

//Llena el data list de Buscar Clase con los nombres de todas las clases
function llenaDatalist(){
    let datalist=document.getElementById("clases_datalist");
    for(let clave in clases){
        let option=document.createElement("option");
        option.value=clases[clave]["nombre"];
        datalist.appendChild(option);
    }             
}
//Llena el datalist de Buscar Profesores con los nombres de los profesores
function llenaDatalistProfesores(){
    let datalist=document.getElementById("profesores_datalist");
    for(let profesor in profesores){
        let option=document.createElement("option");
        option.value=profesor;
        datalist.appendChild(option);
    }             
}
//Modifica y envia forma para "Ver en Horarios Grace"
function post_link(clase){
    document.getElementsByName("txt_materia")[0].value=clase;
    document.detalles.submit();
}

//Dado el nombre de una clase regresa su clave
function claveDeNombre(nombreClase){
    let clave=nombreClase.split('-')[0]+'-'+nombreClase.split('-')[1]; //TODO Necesario? que las opciones del datalist sean la clave mejor
        let esLab=nombreClase.indexOf('-LAB')!=-1;
        if(esLab)
            clave+="-LAB";
    return clave;
}

//Cuando se oprime el boton "Eliminar" (viendo los detalles de una clase agregada)
function eliminar(nombreClase){
    let clave=claveDeNombre(nombreClase);
    if(clave in clasesSeleccionadas){
        //Borra de clasesSeleccionadas
        delete clasesSeleccionadas[clave];
        //Borra table de detalles
        let detalles = document.getElementById(nombreClase);
        detalles.parentNode.removeChild(detalles);
    }
    if(Object.keys(clasesSeleccionadas).length==0){
        //Borra banner de "Classes Seleccionadas" si clasesSeleccionadas es vacio
        let gs=document.getElementsByName("clases_agregadas_banner");
        var g=gs[gs.length-1];
        g.innerHTML="";
    }
}
//Cuando se oprime el boton "Agregar"
function agregar(nombreClase){
    let clave=claveDeNombre(nombreClase);

    if(clave in clasesSeleccionadas){
        alert("Ya agregaste esta clase");
        return;
    }else if(!(clave in clases)){
        alert("Clase no existe. Haz click en la clase que deseas agregar en el menu que aparece cuando empiezas a escribir el nombre de la clase.");
        return;
    }   
    //Agregamos banner de "Clases Seleccionadas:" si es la primera que agregamos
    if(Object.keys(clasesSeleccionadas).length==0 && nombreClase.length>0){ //TODO checa si el nombre/clave si existe
        var out = document.createElement('h4'); // is a node
        out.setAttribute("name", "clases_agregadas_banner");
        out.innerHTML = '<b>Clases seleccionadas</b>';
        document.getElementById("clases_en_horario").appendChild(out);
    }         
    //Construimos clase y agregamos a clasesSeleccionadas 
    let clase=loadClase(clave);      
    clasesSeleccionadas[clave]=clase;
    //Mostramos detalles de clase en "Clases Seleccionadas"  
    let detalles = document.createElement('details');
    detalles.id=nombreClase;
    detalles.innerHTML = '<summary>'+nombreClase+'</summary><br>'+detallesHTML(clase);
    document.getElementById("clases_en_horario").appendChild(detalles);

    //Por ultimo checa si la clase tiene asociado un laboratorio y agregalo
    if(!((clave+'-LAB') in clasesSeleccionadas) && (clave+'-LAB') in clases)
        agregar(nombreClase+'-LAB');
}
//Guarda el horario que se esta mostrando actualmente en horariosFavoritos
function guardarHorario(){
    let i=horariosFavoritos.indexOf(horariosGenerados[resultado]);
    let h=horariosGenerados[resultado];
    if(i<0){ // Si no esta en favoritos
        horariosGenerados.splice(horariosFavoritos.length,0,h);
        horariosFavoritos.push(h);
        resultado++;
    }else{  // Si ya esta en favoritos
        horariosFavoritos.splice(i,1);
        let iF=horariosGenerados.indexOf(h);
        horariosGenerados.splice(iF,1);
        resultado--;
    }
    actualizaBotonGuardar();
    actualizarGuardadosHTML();
}
function actualizaBotonGuardar(){
    let i=horariosFavoritos.indexOf(horariosGenerados[resultado]);
    document.getElementById("guardar").value=(i<0?"☆":"★");
}
function actualizarGuardadosHTML(){
    let favElem=document.getElementById("favoritos");
    favElem.innerHTML="";
    if(horariosFavoritos.length>0){
        let out=document.createElement("h4");
        out.innerHTML="<b>Opciones guardadas</b>";
        favElem.appendChild(out);
        
        let list=document.createElement("ul");
        list.style="padding:0px;margin:0px;list-style-type:none;";
        let i=1;
        for(let horario of horariosFavoritos){
            let temp=document.createElement("li");
            temp.style="margin-bottom:5px;";
            temp.innerHTML="<span style='color:black;' onclick='actualizarResultado("+(i-1)+")'>OPCIÓN "+i+"</span>";
            i++;
            list.appendChild(temp);
        }
        favElem.appendChild(list);
    }

}

//Lee valores de la forma de preferencias y los usa para construir un objecto de Preferencias
function getPreferencias(){
    //MisProfes
    let mis_profes=document.getElementsByName("mis_profes_score")[0].checked;
    let mis_profes_peso=parseFloat(document.getElementsByName('mis_profes_peso')[0].value)/100;
    //Juntas/Separadas -> Leemos solo juntas
    let juntas=document.getElementById('juntas').checked;
    let juntas_peso=parseFloat(document.getElementsByName('juntas_peso')[0].value)/100;
    //Rango de Horario
    let start_rango=document.getElementsByName('start_rango')[0].value;
    let end_rango=document.getElementsByName('end_rango')[0].value;
    let peso_rango=parseFloat(document.getElementsByName('peso_rango')[0].value)/100;
    //Dia con menos clases
    let dia=document.getElementsByName('dia')[0].value;
    let peso_dia=parseFloat(document.getElementsByName('peso_dia')[0].value)/100;
    //Metodo de generacion
    //let generacion=document.getElementsByName("metodoGeneracion")[0].value;
    let generacion="todos";
    //Grupos seleccionados
    let gruposSeleccionados={}; //de la forma "claveClase":["001","002",...]
    let nGruposSeleccionados=0;
    //Para cada clase seleccionada
    for(let claveClase in clasesSeleccionadas){
        let seleccionados=[];
        //Para cada grupo en la clase
        for(let numeroGrupo in clasesSeleccionadas[claveClase].grupos){
            //Checa si esta seleccionado y agregalo a seleccionados
            if(document.getElementById(claveClase+numeroGrupo).checked)
                seleccionados.push(numeroGrupo);
        }
        gruposSeleccionados[claveClase]=seleccionados;
        nGruposSeleccionados+=seleccionados.length;
    }
    //Construye objecto
    let preferencias=new Preferencias(
        mis_profes, mis_profes_peso,
        juntas,juntas_peso,
        start_rango,end_rango,peso_rango,
        dia,peso_dia,
        gruposSeleccionados,
        nGruposSeleccionados,
        generacion
    );
    console.log(preferencias);
    return preferencias;
}


//Callback para el checkbox que selecciona/deselecciona todos los grupos en la tabla de detalles
function seleccionaTodosGrupos(claveClase){
    //Checa si el selectAll esta seleccionado o no
    let seleccionado=document.getElementById(claveClase+"selectAll").checked;
    console.log("select all ",seleccionado);
    if(claveClase in clasesSeleccionadas){
        //Selecciona/deselecciona cada grupo
        for(let numeroGrupo in clasesSeleccionadas[claveClase].grupos){
            document.getElementById(claveClase+numeroGrupo).checked=seleccionado;
        }
    }

}
//----------GENERADORES DE HTML-----------

//Dado una clase Clase construye el HTML de la tabla de detalles
function detallesHTML(clase){
    let out='<table style="border-collapse: collapse;border: 1px solid black;">';
    //Encabezado
    out+='<tr><td id="grupo"><input type="checkbox" id="'+clase.clave+'selectAll" onclick="seleccionaTodosGrupos(\''+clase.clave+'\')" checked/></td><td id="grupo">Grupo</td><td id="grupo">Profesor</td><td id="grupo">Salón</td><td id="grupo">Días</td><td id="grupo">Hrs</td></tr>';
    for(let numeroGrupo in clase.grupos){
        let grupo=clase.grupos[numeroGrupo];
        //Si tenemos su rating en mis profes lo agregamos
        let rating='';
        if(!isNaN(grupo.profesor.misProfesGeneral))
            rating=' ('+grupo.profesor.misProfesGeneral+'/10 <a target="_blank" href="'+grupo.profesor.misProfesLink+'">MisProfes</a>)';
            //Checkbox para seleccionar grupo
            out+='<tr><td id="grupo"><input type="checkbox" id="'+clase.clave+numeroGrupo+'" name="'+clase.clave+'" value="'+numeroGrupo+'" checked/></td>';
            //No. de grupo
            out+='<td id="grupo">'+numeroGrupo+'</td>';
            //Profesor y rating (si lo tenemos)
            out+='<td id="grupo">'+grupo.profesor.nombre+rating+'</td>';
            //Salon
            out+='<td id="grupo">'+grupo.salon+'</td>';
            //Dias
            out+='<td id="grupo">'+grupo.dias+'</td>';
            //Hrs - horario
            out+='<td id="grupo">'+grupo.horario+'</td></tr>';
    }
    out+='</table>'
    //Link de "Ver en Horarios ITAM"
    out+='<span style="color:black;padding-right:10px" onclick="post_link(\''+clase.nombre+'\')"><small><u>Ver en Horarios ITAM<u></small></span>'
    //Link de "Eliminar"
    out+='<span style="color:black" onclick="eliminar(\''+clase.nombre+'\')"><u><small>Eliminar Clase</small></u></span>';
    return out;
}

//Cambia el horario desplegado en la tabla de resultados dado el indice (de horariosGenerados)
function actualizarResultado(indiceNuevo){
    if(indiceNuevo>=0 && indiceNuevo<horariosGenerados.length){
        let horario=horariosGenerados[indiceNuevo];
        document.getElementById("tabla").innerHTML=tablaHTMLhorario(horario,mobile);
        if(indiceNuevo<horariosFavoritos.length){
            document.getElementById("resultado_count").innerHTML='<b>Opción '+(indiceNuevo+1)+' de '+horariosFavoritos.length+'</b>';
        }else{
            document.getElementById("resultado_count").innerHTML='<b>Resultado '+(indiceNuevo+1-horariosFavoritos.length)+' de '+(horariosGenerados.length-horariosFavoritos.length)+'</b>';
        }
        document.getElementById("puntaje").innerHTML='<b>Puntaje: '+parseInt(horario.puntaje)+'/100</b>';
        resultado=indiceNuevo;
        //Actualiza el boton de guardar
        actualizaBotonGuardar();
    }
}
//Genera panel de Resultados
function resultadosHTML(horario,nResultados,mobile){
    let espacioMobil=(mobile?'<br><br>':'');
    //Botones de Navegacion de resultados
    //Boton de "<<"
    let buttons='<input type="button" onclick="actualizarResultado(0)" value="&#8804;"/>';
    //Boton de Anterior
    buttons+=' <input type="button" onclick="actualizarResultado(resultado-1);" value="Anterior"/>';
    //Boton de Imprimir
    //buttons+=' <input type="button" onclick="imprimir()" value="Imprimir"/>';
    //Boton de Agregar a favoritos
    buttons+=' <input type="button" id="guardar" onclick="guardarHorario()" value="Guardar"/>';
    //Boton de Siguiente
    buttons+=' <input type="button" onclick="actualizarResultado(resultado+1);" value="Siguiente"/>';
    //Boton de ">>"
    buttons+=' <input type="button" onclick="actualizarResultado(horariosGenerados.length-1);" value="&#8805;"/>';
    //Puntake
    let puntaje='<div id="puntaje" style="display:inline-block;margin:0px;padding-right:20px;"><b>Puntaje: '+parseInt(horario.puntaje)+'/100</b> </div>'
    //Resultado 1 de x
    let resultado_count='<div id="resultado_count" style="display:inline-block;margin:0px;padding-right:20px;"><b>Resultado 1 de '+nResultados+'</b></div>'
    //Tabla y header con puntaje, botones y contador de resultados
    let out='<div id="header_resultados"><center><h1>Resultados</h1>'+resultado_count+puntaje+espacioMobil+buttons+'<br><br></div>'
    out+='<div id="tabla">'+tablaHTMLhorario(horario,mobile)+'</div>'
    return out
}


//Regresa el HTML de la tabla del horario para mostrar en "Resultados"
function tablaHTMLhorario(horario){
    let gruposEnDia=gruposEnDias(horario.grupos);
    let out="";
    //Declaracion de tabla - varia si movil o no
    if(mobile){
        out='<table height="100" width="'+window.innerWidth*0.90+'" style="border-collapse: collapse;border: 1px solid black;">';

    }else{
        out='<table width="580" style="border-collapse: collapse;border: 1px solid black;font-size:10px;">';
    }
    //Cabecera con dias de la semana
    out+='<tr><td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"></td>\n';
    for(dia of ['LU','MA','MI','JU','VI','SA']){
        if(mobile && dia=="SA") continue;
        out+='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"><b>'+dia+'</b></td>\n';
    }
    out+='</tr>\n';
    //Para cada slot de media hr
    let slots=['07:00-07:30','07:30-08:00','08:00-08:30','08:30-09:00','09:00-09:30','09:30-10:00','10:00-10:30','10:30-11:00','11:00-11:30','11:30-12:00','12:00-12:30','12:30-13:00','13:00-13:30','13:30-14:00','14:00-14:30','14:30-15:00','15:00-15:30','15:30-16:00','16:00-16:30','16:30-17:00','17:00-17:30','17:30-18:00','18:00-18:30','18:30-19:00','19:00-19:30','19:30-20:00','20:00-20:30','20:30-21:00','21:00-21:30','21:30-22:00'];
    for(let slot of slots){
        let inicioSlot=strToDateHora(slot.split('-')[0]);
        let finSlot=strToDateHora(slot.split('-')[1]);
        let grupoDummy=new Grupo();
        grupoDummy.dtInicio=inicioSlot;
        grupoDummy.dtFin=finSlot;
        //Agrega un renglon
        out+="<tr>\n";
        out+='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE;">'+slot+'</td>\n';
        //Para cada dia de la semana
        for(let dia of ['LU','MA','MI','JU','VI','SA']){
            if(mobile && dia=="SA") continue;
            //Agrega una celda
            let celda='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE">\n';
            //Para cada grupo que tiene horario ese dia
            if(dia in gruposEnDia){
                for(let grupo of gruposEnDia[dia]){
                    grupoDummy.dias=[dia];              
                    //Si las horas del grupo coinciden con el slot
                    if(empalmes([grupo,grupoDummy])>0){
                        //Para tooltip (hover de mouse)  
                        let rating="";
                        if(!isNaN(grupo.profesor["misProfesGeneral"]))
                            rating=grupo.profesor["misProfesGeneral"];
                        let hrs=grupo.horario;
                        //TODO nombre no es nombre
                        let span_text='Nombre: '+grupo.claveClase+'\nGrupo: '+grupo.numero+'\nProfesor: '+grupo.profesor.nombre+' ('+rating+' en MisProfes.com)\nHorario: '+hrs+' '+grupo.dias+'\n';                                 
                        celda+='<span title="'+span_text+'" onclick="post_link(\''+grupo.claveClase+'\')">';
                        celda+=grupo.claveClase.split("-")[0]+grupo.claveClase.split("-")[1]+"("+grupo.numero+")";
                        celda+='</span>';
                        break;
                    }
                }
            }
            celda+="</td>";
            out+=celda;
        }
        out+="</tr>\n";
    }
    out+="</table>";
    return out;
}
//------IMPRIMIR--------
//Regresa el contenido en HTML a imprimir del horario actual
//TODO podriamos imprimir todos los horarios "favoritos" (a implementar)
function imprimirContenidoHTML(){
    let horario=horariosGenerados[resultado];
    let out="<br><center><h3>INSTITUTO TECNOLOGICO AUTONOMO DE MEXICO</h3><h4>HORARIO NO OFICIAL</h4>";
    let detalles="<table style='border-collapse: collapse;border: 1px solid black;font-size:10px;'><tr><th id='grupo3'><b>CLAVE</b</th><th id='grupo3'>GRUPO</th><th id='grupo3'>MATERIA</th><th id='grupo3'>HORARIO</th><th id='grupo3'>SALON</th><th id='grupo3'>PROFESOR</th></tr>";
    for(let grupo of horario.grupos){
        let nombre=clasesSeleccionadas[grupo.claveClase].nombre;
        detalles+='<tr><td id="grupo3">'+grupo.claveClase+'</td><td id="grupo3">'+grupo.numero+'</td><td id="grupo3">'+nombre+'</td><td id="grupo3">'+grupo.horario+' '+grupo.dias+'</td><td id="grupo3">'+grupo.salon+'</td><td id="grupo3">'+grupo.profesor.nombre+'</td></tr>';
        //detalles+='<tr><td>grupo aqui</td></tr>'
    }
    detalles+="</table><br><br>";
    out += detalles;
    out += document.getElementById("tabla").innerHTML;
    out +='<br><br><br>Planeador de Horarios ITAM (emiliocantuc.github.io)<br><br><small><b>Importante </b><br>Ya que esta página no esta asociada con el ITAM los datos de las clases pueden estar atrasados/incorrectos. Por favor verificalos en http://grace.itam.mx/EDSUP/BWZKSENP.P_Horarios2</small>';
    return out;
}
//Para el boton "Imprimir" en el panel de resultados
function imprimir(){
    let originalContents = document.body.innerHTML;
    document.body.innerHTML = imprimirContenidoHTML();
    window.print();
    document.body.innerHTML = originalContents;
}

//------COOKIES-------

function cargaDeCookies(){
    //Carga clases guardadas
    let nombresClases=getCookie("clasesSeleccionadas");
    if(nombresClases.length>0 && confirm("Usar lista de clases guardada?")){  
        for(let nombreClase of nombresClases.split('*')){
            //Checa si esta en datos
            if(claveDeNombre(nombreClase) in clases){  
                agregar(nombreClase);
            }
        }
    }

    //TODO carga preferencias guardadas
}

//Regresa valor de cookie. Si no existe regresa "".
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
        c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
        return c.substring(name.length, c.length);
        }
    }
    return "";
}
//Genera y guarda cookie con nombre cname, valor cvalue que expire en exdays.
function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}
