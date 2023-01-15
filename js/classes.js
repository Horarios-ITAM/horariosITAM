/**
 * Contiene las classes que contienen los datos de profesores, clases, grupos y
 * horarios al igual que funciones que permiten crear los objetos correspondientes
 * de datos contenidos en JSON.
 */

class Profesor{
    /**
     * Construye objeto que representa a un profesor.
     * @param {String} nombre del profesor
     * @param {Float} misProfesGeneral Promedio general de evaluaciones
     * @param {Int} misProfesN Numero de evaluaciones
     * @param {String} misProfesLink Link a su pagina de MisProfes.com
     */
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

class Clase{
    /**
     * Construye a objeto que representa una clase.
     * @param {String} nombre de la materia
     * @param {String} clave de la materia
     * @param {[Grupo]} grupos Lista de objs. Grupo que corresponden a la clase
     */
    constructor(nombre,clave,grupos){
        this.nombre=nombre;
        this.clave=clave;
        this.grupos=grupos;
    }
}

class Grupo{
    /**
     * Construye objeto que representa a un grupo de una clase.
     * @param {String} numero El id del grupo i.e '001'
     * @param {String} claveClase La clave de la clase a la que pertenece el grupo
     * @param {Profesor} profesor El obj. Profesor del que imparte el grupo
     * @param {String} salon El salon correspondiente
     * @param {[String]} dias Lista de dias en los que se imparte
     * @param {String} inicio Cadena de inicio de la sesion i.e '07:00'
     * @param {String} fin Cadena de fin de la sesion i.e '09:00'
     * @param {Date} dtInicio Obj. Date correspondiente a inicio
     * @param {Date} dtFin Obj. Date correspondiente a fin
     * @param {String} horario Cadena de la forma 07:00-09:00
     */
    constructor(numero,claveClase,profesor,salon,dias,inicio,fin,dtInicio,dtFin,horario){
        this.numero=numero;
        this.claveClase=claveClase;
        this.profesor=profesor;
        this.salon=salon;
        this.dias=dias;
        this.inicio=inicio;
        this.fin=fin; 
        this.dtInicio=dtInicio; 
        this.dtFin=dtFin;
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
    /**
     * Construye objeto que representa las preferencias del usuario.
     * Los argumentos 'peso' se refieren a cuanto pesa esa parte de la
     * funcion que evalua a los horarios generados (i.e. cuanta importancia se le da).
     * 
     * @param {Boolean} misProfes Si tomar en cuenta o no las calificaciones de profesores en MisProfes
     * @param {Float} misProfesPeso Cuanto pesan las calificaciones de MisProfes
     * @param {Boolean} menosDias Si intentar o no minimizar los dias en que se atiende clase
     * @param {Float} menosDiasPeso El peso que se le da a minimizar los dias a atender
     * @param {String} rangoStart Cadena de inicio del rango de "Rango de horario"
     * @param {String} rangoEnd Cadena de fin del rango de "Rango de horario"
     * @param {Float} rangoPeso Peso que se le da a que se respete el "Rango de horario"
     * @param {Boolean} horasMuertas Si intentar o no minimizar horas muertas
     * @param {Float} horasMuertasPeso El peso de minimizar horas muertas
     * @param {Map<String,[String]>} gruposSeleccionados Dict. Clave Materia -> Lista de claves de grupos seleccionados
     * @param {Int} nGruposSeleccionados Numero de grupos seleccionados
     * @param {String} generacion Cadena que indica como generar los horarios ("todos" por defecto)
     * @param {Boolean} mismoGrupo Mismo grupo teoría y lab (ingenierías)
     */
    constructor(misProfes,misProfesPeso,menosDias,menosDiasPeso,rangoStart,
        rangoEnd,rangoPeso,horasMuertas,horasMuertasPeso,gruposSeleccionados,nGruposSeleccionados,generacion,mismoGrupo){
            this.misProfes=misProfes;
            this.misProfesPeso=misProfesPeso;
            this.menosDias=menosDias;
            this.menosDiasPeso=menosDiasPeso;
            this.rangoStart=rangoStart;
            this.rangoEnd=rangoEnd;
            this.rangoPeso=rangoPeso;
            this.horasMuertas=horasMuertas;
            this.horasMuertasPeso=horasMuertasPeso;
            this.gruposSeleccionados=gruposSeleccionados;
            this.nGruposSeleccionados=nGruposSeleccionados;
            this.generacion=generacion;
            this.mismoGrupo=mismoGrupo;
        }
}
function preferenciasFromJSON(json){
    // TODO test for other browsers
    return Object.setPrototypeOf(JSON.parse(json),Preferencias.prototype)
}

class Horario{
    /**
     * Construye objeto que representa a un horario
     * @param {[Grupo]} grupos Lista de objs. Grupo
     * @param {Float} puntaje El puntaje calculado con las preferencias del usuario
     */
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
