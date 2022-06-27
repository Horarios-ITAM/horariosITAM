//De datos
class Profesor{
    constructor(nombre,misProfesGeneral,misProfesN,misProfesLink){
        this.nombre=nombre;
        this.misProfesGeneral=misProfesGeneral;
        this.misProfesN=misProfesN;
        this.misProfesLink=misProfesLink;
    }
}
function profesorFromJSON(json){
    return new Profesor(
        json["nombre"],
        json["misProfesGeneral"],
        json["misProfesN"],
        json["misProfesLink"]
    );
}
//De datos
class Clase{
    constructor(nombre,clave,grupos){
        this.nombre=nombre;
        this.clave=clave;
        this.grupos=grupos;
    }
}
//De datos
class Grupo{
    constructor(numero,claveClase,profesor,salon,dias,inicio,fin,dtInicio,dtFin,horario){
        this.numero=numero; //string
        this.claveClase=claveClase; //string
        this.profesor=profesor; //clase Profesor
        this.salon=salon; //string
        this.dias=dias; //[string,string,...]
        this.inicio=inicio; //string eg. "7:00"
        this.fin=fin; //string eg. "7:00"
        this.dtInicio=dtInicio; //Date
        this.dtFin=dtFin; //Date
        this.horario=horario;
    }
}

function grupoFromJSON(json){
    return new Grupo(
        json["numero"],
        json["claveClase"],
        profesorFromJSON(json["profesor"]),
        json["salon"],
        json["dias"],
        json["inicio"],
        json["fin"],
        new Date(json["dtInicio"]),
        new Date(json["dtFin"]),
        json["horario"]
    );
}

class Preferencias{
    constructor(misProfes,misProfesPeso,juntas,juntasPeso,rangoStart,
        rangoEnd,rangoPeso,diaMenos,diaMenosPeso,gruposSeleccionados,nGruposSeleccionados,generacion,mismoGrupo){
            this.misProfes=misProfes;
            this.misProfesPeso=misProfesPeso;
            this.juntas=juntas;
            this.juntasPeso=juntasPeso;
            this.rangoStart=rangoStart;
            this.rangoEnd=rangoEnd;
            this.rangoPeso=rangoPeso;
            this.diaMenos=diaMenos;
            this.diaMenosPeso=diaMenosPeso;
            this.gruposSeleccionados=gruposSeleccionados;
            this.nGruposSeleccionados=nGruposSeleccionados;
            this.generacion=generacion;
            this.mismoGrupo=mismoGrupo;
        }
}
//A construir
class Horario{
    constructor(grupos,puntaje){
        this.grupos=grupos;
        this.puntaje=puntaje;
    }    
}

function horarioFromJSON(json){
    let grupos=[];
    for(let grupoJSON of json["grupos"])
        grupos.push(grupoFromJSON(grupoJSON));
    return new Horario(
        grupos,
        json["puntaje"]
    );
}   