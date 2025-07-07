/**
 * Contiene funciones referentes al UI. 
 */


/**
 * Llena el data list de Buscar Clase con los nombres de todas las clases
 */
function llenaDatalist(){
    let datalist=document.getElementById("clases_datalist");
    for(let clave in clases){
        let option=document.createElement("option");
        option.value=clases[clave]["nombre"];
        datalist.appendChild(option);
    }             
}

/**
 * Llena el datalist de Buscar Profesores (con id 'profesores_datalist')
 * con los nombres de los profesores
 */
function llenaDatalistProfesores(){
    let datalist=document.getElementById("profesores_datalist");
    for(let profesor in profesores){
        let option=document.createElement("option");
        option.value=profesor;
        datalist.appendChild(option);
    }             
}

/**
 * Modifica y envia formas para "Ver en Horarios Grace".
 * Si se scrapeo en Secure area se manda una forma y si no la otra.
 * @param {String} clase Nombre de la clase
 */
function post_link(clase){
    // Depende de si se quiere ligar a grace secure area o no
    if(secure){
        document.getElementsByName("sel_subj")[1].value=clase.split('-')[0];
        document.getElementsByName("SEL_CRSE")[0].value=clase.split('-')[1];
        document.getElementsByName("detalles-secure")[0].submit();
        
    }else{
        document.getElementsByName("txt_materia")[0].value=clase;
        document.detalles.submit();
    }
    
}

/**
 * Dado el nombre de una clase regresa su clave.
 * E.g. 'ACT-11301-CALCULO ACTUARIAL II' -> 'ACT-11301'.
 * @param {String} nombreClase Nombre completo de la clase
 * @returns {String} La clave de la clase
 */
function claveDeNombre(nombreClase){
    let clave=nombreClase.split('-')[0]+'-'+nombreClase.split('-')[1]; //TODO Necesario? que las opciones del datalist sean la clave mejor
        let esLab=nombreClase.indexOf('-LAB')!=-1;
        if(esLab)
            clave+="-LAB";
    return clave;
}


/**
 * Callback para el boton "Eliminar" (clase) desde los detalles.
 * Elimina clase de "Clases Agregadas".
 * @param {String} nombreClase El nombre de la clase a eliminar
 */
function eliminar(nombreClase){
    let clave=claveDeNombre(nombreClase);
    if(clave in clasesSeleccionadas){
        // Borra de clasesSeleccionadas
        delete clasesSeleccionadas[clave];
        // Borra table de detalles
        let detalles = document.getElementById(nombreClase);
        detalles.parentNode.removeChild(detalles);
    }
    if(Object.keys(clasesSeleccionadas).length==0){
        // Borra banner de "Classes Seleccionadas" si clasesSeleccionadas es vacio
        let gs=document.getElementsByName("clases_agregadas_banner");
        var g=gs[gs.length-1];
        g.innerHTML="";
    }
}


/**
 * Callback para el boton "Agregar" (clase).
 * Agrega clase a "Clases Agregadas".
 * @param {String} nombreClase Nombre de clase a agregar
 * @param {Boolean} deGuardadas Si la clase se carga desde cookies automaticamente
 * @returns {void}
 */
function agregar(nombreClase,deGuardadas){

    let clave=claveDeNombre(nombreClase);

    if(deGuardadas===undefined)
        deGuardadas=false;

    // Mensajes de error
    if(clave in clasesSeleccionadas){
        if(!deGuardadas)
            alert("Ya agregaste esta clase");
        return;
    }else if(!(clave in clases)){
        alert("Clase no existe. Haz click en la clase que deseas agregar en el menu que aparece cuando empiezas a escribir el nombre de la clase.");
        return;
    }

    // Agregamos banner de "Clases Seleccionadas:" si es la primera que agregamos
    if(Object.keys(clasesSeleccionadas).length==0){
        var out = document.createElement('h3'); // is a node
        out.setAttribute("name", "clases_agregadas_banner");
        out.innerHTML = "<b>Clases seleccionadas</b>";
        document.getElementById("clases_en_horario").appendChild(out);
    }     

    // Construimos clase y agregamos a clasesSeleccionadas 
    let clase=loadClase(clave);      
    clasesSeleccionadas[clave]=clase;

    // Mostramos detalles de clase en "Clases Seleccionadas"
    let detalles = document.createElement('details');
    detalles.id=nombreClase;
    // Generate initial HTML without greying out groups
    detalles.innerHTML = '<summary>'+nombreClase+'</summary><br>'+detallesHTML(clase, true);
    document.getElementById("clases_en_horario").appendChild(detalles);

    // Fetch open group data
    fetch(`https://proxy.horariositam.com/abiertos?txt_materia=${nombreClase}`)
        .then(response => response.json())
        .then(openGroups => {
            console.log('Open groups:', openGroups); // Log the response
            clase.openGroups = openGroups; // Store open groups in the Clase object

            // Update the existing details HTML to grey out closed groups
            // We need to re-generate or modify the specific rows
            const existingDetailsElement = document.getElementById(nombreClase);
            if (existingDetailsElement) {
                // Re-render the details content with open group info
                existingDetailsElement.innerHTML = '<summary>'+nombreClase+'</summary><br>'+detallesHTML(clase);
            }

            // Por ultimo checa si la clase tiene asociado un laboratorio y agregalo
            // This might need adjustment if labs are added before proxy returns
            if(!((clave+'-LAB') in clasesSeleccionadas) && (clave+'-LAB') in clases)
                agregar(nombreClase+'-LAB');
        })
        .catch(error => {
            console.error('Error fetching open groups:', error);
            // Details are already shown, so just log the error.
            // No need to re-add details here as they are added before fetch.
        });

    // If adding a non-lab class, also check and add its lab immediately if it exists.
    // This ensures the lab is also processed, including its own proxy call.
    // We do this outside the fetch for the parent class to avoid complex chaining issues.
    if (!nombreClase.endsWith('-LAB')) {
        const labClave = clave + '-LAB';
        if (!(labClave in clasesSeleccionadas) && (labClave in clases)) {
            agregar(nombreClase + '-LAB');
        }
    }
}

/**
 * Guarda el horario actual (mostrado) en horariosFavoritos.
 */
function guardarHorario(){
    // Indice del resultado actual en horariosFavoritos (-1 si no esta)
    let i=horariosFavoritos.indexOf(horariosGenerados[resultado]);
    // El horario actual
    let h=horariosGenerados[resultado];

    if(i<0){
        // Si no esta en favoritos
        horariosGenerados.splice(horariosFavoritos.length,0,h);
        horariosFavoritos.push(h);
        resultado++;
    }else{
        // Si ya esta en favoritos
        horariosFavoritos.splice(i,1);
        let iF=horariosGenerados.indexOf(h);
        horariosGenerados.splice(iF,1);
        resultado--;
        resultado=Math.max(0,resultado);
    }
    if(resultado<horariosGenerados.length){
        actualizarResultado(resultado);
    }
    actualizaBotonGuardar();
    actualizarGuardadosHTML();
    actualizaCookieFavoritos();
}

/**
 * Actualiza el boton de "Guardar" dependiendo de si el
 * horario actual (desplegado) ya esta en horariosFavoritos o no.
 */
function actualizaBotonGuardar(){
    let i=horariosFavoritos.indexOf(horariosGenerados[resultado]);
    document.getElementById("guardar").value=(i<0?"☆":"★");
}

/**
 * Actualiza el HTML del apartado de "Opciones guardadas".
 */
function actualizarGuardadosHTML(){
    let favElem=document.getElementById("favoritos");
    favElem.innerHTML="";
    if(horariosFavoritos.length>0){
        // Agregamos banner de 'Opciones guardadas'
        let out=document.createElement("h3");
        out.innerHTML="<b>Opciones guardadas</b>";
        favElem.appendChild(out);
        
        // Para cada horario en horariosFavoritos agrega un <li>
        let list=document.createElement("ul");
        list.style="padding:0px;margin:0px;list-style-type:none;";
        let i=1;
        for(let horario of horariosFavoritos){
            let temp=document.createElement("li");
            temp.style="margin-bottom:5px;";
            // Con actualizarResultados al hacer click para mostrar ese horario
            temp.innerHTML="<span style='color:black;' onclick='actualizarResultado("+(i-1)+")'>Opción "+i+"</span>";
            i++;
            list.appendChild(temp);
        }
        favElem.appendChild(list);
        favElem.appendChild(document.createElement("br"));
    }
}

/**
 * Actualiza el valor del cookie favoritos con horariosFavoritos
 */
function actualizaCookieFavoritos(){
    setCookie("favoritos",JSON.stringify(horariosFavoritos),30);
}


/**
 * Lee valores de la forma de preferencias y los usa para construir un objecto de Preferencias
 * @returns {Preferencias} El obj. de Preferencias con los datos
 */
function getPreferencias(){
    // Preferencias:
    // MisProfes
    let mis_profes=document.getElementsByName("mis_profes_score")[0].checked;
    let mis_profes_peso=parseFloat(document.getElementsByName('mis_profes_peso')[0].value)/100;

    // Ir menos dias posibles
    let menos_dias=document.getElementsByName("menos_dias_score")[0].checked;
    let menos_dias_peso=parseFloat(document.getElementsByName('menos_dias_peso')[0].value)/100;

    // Evitar horas muertas
    let horas_muertas=document.getElementsByName("horas_muertas_score")[0].checked;
    let horas_muertas_peso=parseFloat(document.getElementsByName('horas_muertas_peso')[0].value)/100;

    // Rango de Horario
    let start_rango=document.getElementsByName('start_rango')[0].value;
    let end_rango=document.getElementsByName('end_rango')[0].value;
    let peso_rango=parseFloat(document.getElementsByName('peso_rango')[0].value)/100;

    // Mismo grupo teoria y lab
    let mismoGrupo=document.getElementById('mismo_grupo_box').checked;

    // Metodo de generacion
    //let generacion=document.getElementsByName("metodoGeneracion")[0].value;
    let generacion="todos";

    // Grupos seleccionados
    let gruposSeleccionados={}; //de la forma "claveClase":["001","002",...]
    let nGruposSeleccionados=0;


    // Grupos seleccionados:
    // Para cada clase seleccionada
    for(let claveClase in clasesSeleccionadas){
        let seleccionados=[];
        // Para cada grupo en la clase
        for(let numeroGrupo in clasesSeleccionadas[claveClase].grupos){
            // Checa si esta seleccionado y agregalo a seleccionados
            if(document.getElementById(claveClase+numeroGrupo).checked)
                seleccionados.push(numeroGrupo);
        }
        gruposSeleccionados[claveClase]=seleccionados;
        nGruposSeleccionados+=seleccionados.length;
    }
    // Construye objecto
    let preferencias=new Preferencias(
        mis_profes, mis_profes_peso,
        menos_dias,menos_dias_peso,
        start_rango,end_rango,peso_rango,
        horas_muertas,horas_muertas_peso,
        gruposSeleccionados,
        nGruposSeleccionados,
        generacion,
        mismoGrupo
    );
    console.log(preferencias);
    return preferencias;
}   

/**
 * Dado un obj. preferencias modifica los inputs de la forma para reflejarlas.
 * @param {Preferencias} preferencias Las preferencias a 'settear'
 */
function setPreferencias(preferencias){
    // Preferencias:
    // MisProfes
    document.getElementsByName("mis_profes_score")[0].checked=preferencias.misProfes;
    document.getElementsByName('mis_profes_peso')[0].value=preferencias.misProfesPeso*100;

    // Ir menos dias posibles
    document.getElementById('menos_dias_box').checked=preferencias.menosDias;
    document.getElementsByName('menos_dias_peso')[0].value=preferencias.menosDiasPeso*100;

    // Evitar horas muertas
    document.getElementsByName("horas_muertas_score")[0].checked=preferencias.horasMuertas;
    document.getElementsByName('horas_muertas_peso')[0].value=preferencias.horasMuertasPeso*100;

    // Rango de Horario
    document.getElementsByName('start_rango')[0].value=preferencias.rangoStart
    document.getElementsByName('end_rango')[0].value=preferencias.rangoEnd;
    document.getElementsByName('peso_rango')[0].value=preferencias.rangoPeso*100;

    // Mismo grupo teoria y lab
    document.getElementById('mismo_grupo_box').checked=preferencias.mismoGrupo;

    // Grupos seleccionados:
    // Para cada clase seleccionada
    for(let claveClase in preferencias.gruposSeleccionados){

        // Deseleccionamos todos los grupos
        for(let grupo of clases[claveClase].grupos){
            let numeroGrupo=grupo.grupo;
            // console.log(claveClase+numeroGrupo);
            document.getElementById(claveClase+numeroGrupo).checked=false;
        }

        // Para cada grupo en la clase
        for(let numeroGrupo of preferencias.gruposSeleccionados[claveClase]){
            // Selecciona al grupo en el UI
            // console.log(claveClase+numeroGrupo);
            document.getElementById(claveClase+numeroGrupo).checked=true;
        }
        
    }

    return preferencias;
}


/**
 * Callback para el checkbox que selecciona/deselecciona todos los grupos en la tabla de detalles
 * @param {String} claveClase Clave de la clase
 */
function seleccionaTodosGrupos(claveClase){
    // Checa si el selectAll esta seleccionado o no
    let seleccionado=document.getElementById(claveClase+"selectAll").checked;

    if(claveClase in clasesSeleccionadas){
        // Selecciona/deselecciona cada grupo
        for(let numeroGrupo in clasesSeleccionadas[claveClase].grupos){
            document.getElementById(claveClase+numeroGrupo).checked=seleccionado;
        }
    }
}

// ---------- GENERADORES DE HTML -----------

/**
 * Dado una clase construye el HTML de la tabla de detalles
 * @param {Clase} clase Obj. de Clase para la cual generar detalles
 * @param {boolean} initialRender Optional. If true, groups will not be greyed out.
 * @returns {String} El HTML generado
 */
function detallesHTML(clase, initialRender = false){
    // HTML generado es una tabla
    let out='<table style="border-collapse: collapse;border: 1px solid black;">';

    // Encabezado con nombre
    out+='<tr><td id="grupo"><input type="checkbox" id="'+clase.clave+'selectAll" onclick="seleccionaTodosGrupos(\''+clase.clave+'\')" checked/></td><td id="grupo">Grupo</td><td id="grupo">Profesor</td><td id="grupo">Salón</td><td id="grupo">Días</td><td id="grupo">Hrs</td></tr>';
    
    // Para cada grupo agregamos un renglon a la tabla
    for(let numeroGrupo in clase.grupos){
        let grupo=clase.grupos[numeroGrupo];
        // Si tenemos su rating en mis profes lo agregamos
        let rating='';
        if(!isNaN(grupo.profesor.misProfesGeneral)){
            rating=' ('+grupo.profesor.misProfesGeneral+'/10 <a target="_blank" href="'+grupo.profesor.misProfesLink+'">MisProfes</a>)';
        }
        // Check if the group is open
        let isClosed = !initialRender && clase.openGroups && !clase.openGroups.includes(numeroGrupo);
        let rowClass = isClosed ? ' class="grupo-cerrado"' : '';

        // Checkbox para seleccionar grupo
        out+='<tr'+rowClass+'><td id="grupo"><input type="checkbox" id="'+clase.clave+numeroGrupo+'" name="'+clase.clave+'" value="'+numeroGrupo+'" checked/></td>';
        // No. de grupo
        out+='<td id="grupo">'+numeroGrupo+'</td>';
        // Profesor y rating (si lo tenemos)
        out+='<td id="grupo">'+grupo.profesor.nombre+rating+'</td>';
        // Salon
        out+='<td id="grupo">'+grupo.salon+'</td>';
        // Dias
        out+='<td id="grupo">'+grupo.dias+'</td>';
        // Hrs - horario
        out+='<td id="grupo">'+grupo.horario+'</td></tr>';
    }
    out+='</table>'
    // Link de "Ver en Horarios ITAM"
    out+='<span style="color:black;padding-right:10px" onclick="post_link(\''+clase.nombre+'\')"><small><u>Ver en Horarios ITAM<u></small></span>'
    // Link de "Eliminar"
    out+='<span style="color:black" onclick="eliminar(\''+clase.nombre+'\')"><u><small>Eliminar Clase</small></u></span>';
    return out;
}

/**
 * Cambia el horario desplegado en la tabla de resultados dado el indice (de horariosGenerados)
 * @param {Int} indiceNuevo 
 */
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
        // Actualiza el boton de guardar
        actualizaBotonGuardar();
    }
}

/**
 * Genera el HTML del panel de 'Resultados'.
 * @param {Horario} horario 
 * @param {Int} nResultados 
 * @param {Boolean} mobile 
 * @returns {String} El HTML generado
 */
function resultadosHTML(horario,nResultados,mobile){
    let espacioMobil=(mobile?'<br><br>':'');
    // Botones de Navegacion de resultados:
    // Boton de "<<"
    let buttons='<input type="button" class="custom-button" onclick="actualizarResultado(0)" value="&#8804;"/>';
    // Boton de Anterior
    buttons+=' <input type="button" class="custom-button" onclick="actualizarResultado(resultado-1);" value="Anterior"/>';
    // Boton de Imprimir
    //buttons+=' <input type="button" onclick="imprimir()" value="Imprimir"/>';
    // Boton de Agregar a favoritos
    buttons+=' <input type="button" class="custom-button" id="guardar" onclick="guardarHorario()" value="Guardar"/>';
    // Boton de Siguiente
    buttons+=' <input type="button"  class="custom-button" onclick="actualizarResultado(resultado+1);" value="Siguiente"/>';
    // Boton de ">>"
    buttons+=' <input type="button" class="custom-button" onclick="actualizarResultado(horariosGenerados.length-1);" value="&#8805;"/>';
    // Puntaje 
    let puntaje='<div id="puntaje" style="display:inline-block;margin:0px;padding-right:20px;"><b>Puntaje: '+parseInt(horario.puntaje)+'/100</b> </div>'
    // Resultado 1 de x
    let resultado_count='<div id="resultado_count" style="display:inline-block;margin:0px;padding-right:20px;"><b>Resultado 1 de '+nResultados+'</b></div>'

    // Tabla y header con puntaje, botones y contador de resultados:
    // Header
    let out='<div id="header_resultados"><center><h1>Resultados</h1>'+resultado_count+puntaje+espacioMobil+buttons+'<br><br></div>'
    // Cuerpo de tabla
    out+='<div id="tabla">'+tablaHTMLhorario(horario,mobile)+'</div>'
    
    return out
}

/**
 * Regresa el HTML del cuerpo de la tabla horario para mostrar en "Resultados".
 * @param {Horario} horario El horario a mostrar
 * @returns {String} El HTML generado
 */
function tablaHTMLhorario(horario){
    let gruposEnDia=gruposEnDias(horario.grupos);
    let out="";
    // Declaracion de tabla - varia si movil o no
    if(mobile){
        out='<table height="100" width="'+window.innerWidth*0.90+'" style="border-collapse: collapse;border: 1px solid black;">';
    }else{
        out='<table width="580" style="border-collapse: collapse;border: 1px solid black;font-size:10px;">';
    }
    // Cabecera con dias de la semana
    out+='<tr><td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"></td>\n';
    for(dia of ['LU','MA','MI','JU','VI','SA']){
        if(mobile && dia=="SA") continue;
        out+='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"><b>'+dia+'</b></td>\n';
    }
    out+='</tr>\n';

    // Para cada slot de media hr
    let slots=['07:00-07:30','07:30-08:00','08:00-08:30','08:30-09:00','09:00-09:30','09:30-10:00','10:00-10:30','10:30-11:00','11:00-11:30','11:30-12:00','12:00-12:30','12:30-13:00','13:00-13:30','13:30-14:00','14:00-14:30','14:30-15:00','15:00-15:30','15:30-16:00','16:00-16:30','16:30-17:00','17:00-17:30','17:30-18:00','18:00-18:30','18:30-19:00','19:00-19:30','19:30-20:00','20:00-20:30','20:30-21:00','21:00-21:30','21:30-22:00'];
    for(let slot of slots){
        // Crea un grupo 'dummy' con horarios del slot
        let inicioSlot=strToDateHora(slot.split('-')[0]);
        let finSlot=strToDateHora(slot.split('-')[1]);
        let grupoDummy=new Grupo();
        grupoDummy.dtInicio=inicioSlot;
        grupoDummy.dtFin=finSlot;

        // Agrega un renglon
        out+="<tr>\n";
        out+='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE;">'+slot+'</td>\n';

        // Y luego para cada dia de la semana
        for(let dia of ['LU','MA','MI','JU','VI','SA']){
            if(mobile && dia=="SA") continue;
            // Agrega una celda
            let celda='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE">\n';

            // Para cada grupo que tiene horario ese dia
            if(dia in gruposEnDia){
                for(let grupo of gruposEnDia[dia]){
                    grupoDummy.dias=[dia];              
                    // Si las horas del grupo coinciden con el slot
                    if(empalmes([grupo,grupoDummy])>0){
                        // Llena la celda
                        span_text=tooltip_text(grupo);
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

/**
 * Genera el texto a mostrar cuando se hace hover sobre un grupo
 * en la tabla de resultados.
 * @param {Grupo} grupo 
 * @returns {String} El HTML generado
 */
function tooltip_text(grupo){
    let rating='';
    if(!isNaN(grupo.profesor.misProfesGeneral))
        rating=' ('+grupo.profesor.misProfesGeneral+' en MisProfes.com)';

    let out='Nombre: '+clases[grupo.claveClase].nombre; //grupo.claveClase;
    out+='\nGrupo: '+grupo.numero;
    out+='\nProfesor: '+grupo.profesor.nombre+rating+'\n';                               
    return out;
}

// ------ IMPRIMIR --------

/**
 * Regresa el HTML a imprimir al oprimir el boton
 * @returns {String} El HTML generado
 */
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

/**
 * Callback para el boton "Imprimir" en el panel de resultados.
 */
function imprimir(){
    let originalContents = document.body.innerHTML;
    document.body.innerHTML = imprimirContenidoHTML();
    window.print();
    document.body.innerHTML = originalContents;
}

// ------ COOKIES -------

/**
 * TODO checar
 */
function cargaCookieClassesSeleccionadas(){
    // Carga clases guardadas
    let nombresClases=getCookie("clasesSeleccionadas");
    if(nombresClases.length>0){  
        for(let nombreClase of nombresClases.split('*')){
            // Checa si esta en datos
            if(claveDeNombre(nombreClase) in clases){  
                agregar(nombreClase,true);
            }
        }
    }
}

/**
 * Checa si existe cookie "favoritos".
 * Si es el caso crea los objetos Horarios y actualiza las variables globales.
 */
function cargaCookieHorariosFavoritos(){
    let favs=getCookie("favoritos");
    if(favs.length>0){
        // Cargamos el JSON
        let json=JSON.parse(favs);

        // Creamos los objetos Horario
        let out=[];
        for(let horarioJSON of json)
            out.push(horarioFromJSON(horarioJSON));

        // Setteamos variables globales    
        horariosFavoritos=out.slice();
        horariosGenerados=out.slice();

        // Actualiza el HTML de 'Opciones guardadas' 
        actualizarGuardadosHTML();
    }
}

/**
 * Checa si existe cookie "preferencias".
 * Si es el caso crea el objeto Preferencias correspondiente y llama a setPreferencias.
 */
function cargaCookiePreferencias(){
    let prefs=getCookie("preferencias");
    if(prefs.length>0){
        // Obtenemos al objeto del JSON
        preferencias=preferenciasFromJSON(prefs);
        console.log('Got preferencias: ',preferencias);
        setPreferencias(preferencias);
    }
}

/**
 * Regresa valor de cookie. Si no existe regresa "".
 * @param {String} cname Nombre de la cookie
 * @returns {String} Contenido de la cookie o "" si no existe
 */
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

/**
 * Genera y guarda cookie con nombre 'cname', valor 'cvalue' que expire en 'exdays'.
 * @param {String} cname Nombre de cookie a settear
 * @param {String} cvalue Valor de cookie a settear
 * @param {Int} exdays Numero de dias en el que expira la cookie
 */
function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

// ------ FECHAS -------

/**
 * Regresa str con tiempo desde fecha
 * @param {Date} date Fecha con la cual calcular diferencia
 * @returns {String} Cadena con tiempo desde fecha
 */
function timeSince(date) {
    var seconds = Math.floor((new Date() - date) / 1000);
  
    var interval = seconds / 31536000;
  
    if (interval > 1) {
      return Math.floor(interval) + " año(s)";
    }
    interval = seconds / 2592000;
    if (interval > 1) {
      return Math.floor(interval) + " mese(s)";
    }
    interval = seconds / 86400;
    if (interval > 1) {
      return Math.floor(interval) + " día(s)";
    }
    interval = seconds / 3600;
    if (interval > 1) {
      return Math.floor(interval) + " hora(s)";
    }
    interval = seconds / 60;
    if (interval > 1) {
      return Math.floor(interval) + " minuto(s)";
    }
    return Math.floor(seconds) + " segundo(s)";
  }
