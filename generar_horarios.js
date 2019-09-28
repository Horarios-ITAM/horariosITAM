function generarHorarios(lista_de_clases,preferencias={},n=10,max_restarts=1000 ){
    //console.log(lista_de_clases)
    var domains=build_domains(lista_de_clases,clases);
    var horarios=[];
    for(var i=0;i<n;i++){
        for(var restart=0;restart<max_restarts;restart++){
            horario=min_conflicts(domains,100);
            if(horario!="failed"){break;}
        }
        if(!existing_horario(horarios,horario)){
            horarios.push([horario,optimization_function(horario,preferencias)]);
        }
    }
    //console.log("unique?",horarios.length)
    //console.log(h)
    return horarios.sort(function(a,b){return b[1]-a[1]});
}
function enumerateHorarios(lista_de_clases,preferencias={}){
    var domains=build_domains(lista_de_clases,clases);
    var h=enumerate(domains,[],{});
    var horarios=[]
    for(i of h)horarios.push([i,optimization_function(i,preferencias)]);
    return horarios.sort(function(a,b){return b[1]-a[1]});
}
function existing_horario(horarios,h){
    for(h2 of horarios){
        if(same_horario(h,h2[0]))return true;
    }
    return false;
}
function same_horario(h1,h2){
    for(clase of Object.keys(h1)){
        if(h1[clase]!=h2[clase])return false;
    }
    return true;
}
/**OPTIMIZATION FUNCTION*/
function optimization_function(horario,preferencias={}){
    if(Object.keys(preferencias).length==0){
        preferencias=[[mis_profes_score,0.5],[horario_rango_score,0.5,build_date_objects("9:00-16:00")],[clases_juntas_separadas_score,0.5],[dia_libre_score,0.5,'VI']];
        //console.log("test",preferencias[0][0](horario))
        //console.log("preferencias=0")
    }
    var total=0;
    var weights=0.000000001;
    for(f of preferencias){
        if(f.length==3){
            var score=f[0](horario,f[2]);
            total+=score*f[1];
            weights+=f[1];
        }
        else{
            var score=f[0](horario);
            total+=score*f[1];
            weights+=f[1];
        }
        //console.log(f,score);
    }
    return total/weights;
}
function grupos_preferidos_score(horario,grupos_preferidos){
    //console.log("grupos_preferidos_score")
    //console.log(horario)
    var prefNum=0;
    var withPref=0;
    for(clase of Object.keys(horario)){
        if(grupos_preferidos[clase].length>0){withPref++;}
        for(grupo_preferido of grupos_preferidos[clase]){
            //console.log(horario[clase]['grupo'],grupo_preferido)
            if(horario[clase]['grupo']==grupo_preferido)prefNum++;
        }
    }
    //console.log("prefNum:",prefNum)
    //console.log(prefNum/withPref);
    if(withPref==0)return 0;
    return prefNum/withPref;
}
function mis_profes_score(horario){
    var total=0;
    var found=0;
    for(grupo of Object.values(horario)){
        var r=parseFloat(ratings[grupo['profesor']]);
        if(r){
            total=total+r;
            found++;
        }
    }
    if(found==0){return 0;}
    return (total/found)/10;
}
function horario_rango_score(horario,rango){
    var fuera_de_rango=0;
    for(grupo of Object.values(horario)){
        h=grupo['horario'][0];
        if(h<rango[0] || h>rango[1]){
            fuera_de_rango++;
        }
    }
    var n=Object.keys(horario).length
    return (n-fuera_de_rango)/n;
}
function clases_juntas_separadas_score(horario,juntas=true){ //check
    var total_delta=0;
    for(dia of  ['LU','MA','MI','JU','VI','SA']){
        var delta_dia=0;
        var g=grupos_en_dia(horario,dia).sort(function(a,b){return a['horario'][0]-b['horario'][0]});
        for(var i=0;i<g.length-1;i++){
            var a=g[i]['horario'][1];
            var b=g[i+1]['horario'][0];
            delta_dia+=Math.abs((b-a)/(1000 * 60 * 60));
        }
        total_delta+=delta_dia;
    }
    var rescaled=total_delta/65
    if(juntas){return 1-rescaled;}
    return rescaled;
}
function dia_libre_score(horario,dia){//check
    var horas=grupos_en_dia(horario,dia).length;
    var rescale=horas/Object.keys(horario).length;
    return 1-rescale;
}
function grupos_en_dia(horario,dia){
    c=[]
    for(grupo of Object.values(horario)){
        if(grupo['dias'].indexOf(dia)!=-1){c.push(grupo)}
    }
    return c;
}
/**ENUMERATE*/
function enumerate(domains,horarios,horario){
    var clases_a_completar=clases_faltantes(domains,horario);
    //console.log("clases a completar:",clases_a_completar)
    if(clases_a_completar.length==0){horarios.push(horario);return horarios;}
    var clase=clases_a_completar[0];
    var _grupos_legales=grupos_legales(horario,domains,clase);
    //console.log("grupos legales para ",clase,_grupos_legales);
    if(_grupos_legales.length==0)throw "No legal groups";
    for(grupo_legal of _grupos_legales){
        try{
            //var copia=horario;
            //console.log("horario before",horario)
            //console.log("grupo_legal",grupo_legal)
            var copy=Object.assign({}, horario)
            copy[clase]=grupo_legal;
            //console.log(copy[clase],copy);
            //console.log("calling enumerate with ",copy,horarios);
            horarios=enumerate(domains,horarios,copy)
            //horario[clase]=null;
        }
        catch(err){
            //console.log("caught no legal groups");
            continue;
        }
    }
    //console.log("final",horarios);
    return horarios;

}
function clases_faltantes(domains,horario){
    if(Object.keys(domains).length==Object.keys(horario))return [];
    var faltantes=[]
    for(clase of Object.keys(domains)){
        if(Object.keys(horario).indexOf(clase)==-1)faltantes.push(clase);
    }
    return faltantes;
}
function grupos_legales(horario,domains,clase){
    var legales=[]
    for(posible_grupo of domains[clase]){
        var c=false;
        for(grupo_en_horario of Object.values(horario)){
            if(conflicts(posible_grupo,grupo_en_horario)){c=true;}
        }
        if(!c){legales.push(posible_grupo);}
    }
    return legales;
}
/**MIN CONLICTS*/
function min_conflicts(domains,max_steps){
    current=random_horario(domains);
    for(var i=0;i<max_steps;i++){
        c=nconflicts(horario);
        if(sum_values(c)==0){return current;}
        var variable=random_choose(Object.keys(c));
        var value=arg_min(domains,variable,current);//grupo
        current[variable]=value;
    }
    return "failed";
}
function conflicts(grupo,grupo2){
    var dias_en_comun=grupo['dias'].filter(value => -1 !== grupo2['dias'].indexOf(value));
    if(dias_en_comun==0){return false;}
    a=grupo['horario'];
    b=grupo2['horario'];
    if(b[0]>=a[1] || a[0]>=b[1]){return false;}
    return true;

}
function nconflicts(horario){
    //console.log("nconflicts")
    var conf={};
    for(g in horario){
        grupo=horario[g];
        var c=0;
        for(g2 in horario){
            grupo2=horario[g2];
            if(grupo==grupo2){break;}
            if(conflicts(grupo,grupo2)){c++;}
        }
        conf[grupo['nombre']]=c;
    }
    return conf;
}
function conflicts_horarios(a,b){
    if(b[0]>=a[1] || a[0]>=b[1]){return false;}
    return true;

}
function build_domains(lista_de_clases,clases){
    var domains={};
    for(nombre_de_clase of lista_de_clases){
        for(clase of clases){
            if(nombre_de_clase==clase['nombre']){
                domains[nombre_de_clase]=clase['grupos'];
                if(typeof(domains[nombre_de_clase][0]['horario'])=="string"){
                    for(grupo of domains[nombre_de_clase]){
                        grupo['horario']=build_date_objects(grupo['horario']);
                    }
                }
            }
        }
    }
    return domains
}
function build_date_objects(horario_str){
    //console.log(horario_str)
    var a=horario_str.split("-")[0];
    var b=horario_str.split("-")[1];
    if(a.length==4){a='0'+a;}
    if(b.length==4){b='0'+b;}
    var start = new Date('1970-01-01T' +a + '-06:00');
    var finish = new Date('1970-01-01T' +b + '-06:00');
    return [start,finish]
}
function random_horario(domains){
    horario={};
    for(clase in domains){
        horario[clase]=random_choose(domains[clase]);
    }
    return horario;
}
function arg_min(domains,variable,c){
    var lowest=Object.keys(domains).length**2;
    var best;
    for(grupo of domains[variable]){
        c[variable]=grupo;
        var score=sum_values(nconflicts(c));
        if(score<lowest){
            lowest=score;
            var best=c[variable];
        }
    }
    return best;
}
function random_choose(choices) {
  var index = Math.floor(Math.random() * choices.length);
  return choices[index];
}
function sum_values(d){
    total=0;
    for(key in d){total+=d[key];}
    return total;
}
/**AESTETICS*/
function print_horario_html(horario,mobile=false){
    console.log("mobile:",mobile);
    var h=horario[0]
    //console.log("print_horario_html",h)
    var out="";
    if(mobile){
        var out='<table height="100" width="'+window.innerWidth*0.90+'" style="border-collapse: collapse;border: 1px solid black;">';

    }else{
        var out='<table width="580" style="border-collapse: collapse;border: 1px solid black;font-size:10px;">';
    }
    //out+='<tr><th id="grupo2">Puntaje: '+horario[1].toString().substring(0,5)+'/1.0</th></tr>';
    out+='<tr><td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"></td>\n';
    for(day of ['LU','MA','MI','JU','VI','SA']){
        if(mobile && day=="SA"){continue;}
        out+='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"><b>'+day+'</b></td>\n';
    }
    out+='</tr>\n';
    slots=['07:00-07:30','07:30-08:00','08:00-08:30','08:30-09:00','09:00-09:30','09:30-10:00','10:00-10:30','10:30-11:00','11:00-11:30','11:30-12:00','12:00-12:30','12:30-13:00','13:00-13:30','13:30-14:00','14:00-14:30','14:30-15:00','15:00-15:30','15:30-16:00','16:00-16:30','16:30-17:00','17:00-17:30','17:30-18:00','18:00-18:30','18:30-19:00','19:00-19:30','19:30-20:00','20:00-20:30','20:30-21:00','21:00-21:30','21:30-22:00'];
    for(slot of slots){
        out+="<tr>\n";
        out+='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE;">'+slot+'</td>\n';
        for(day of ['LU','MA','MI','JU','VI','SA']){
            //console.log(day)
            if(mobile && day=="SA"){continue;}
            var texto='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE"></td>\n';
            for(grupo of grupos_en_dia(h,day)){
                //console.log("grupo",grupo)
                if(conflicts_horarios(grupo['horario'],build_date_objects(slot))){
                    var r="";
                    try{r=ratings[grupo['profesor']][0]}
                    catch(err){r="";}
                    var span_text='Nombre: '+grupo['nombre']+'\nGrupo: '+grupo['grupo']+'\nProfesor: '+grupo['profesor']+' ('+r+' en MisProfes.com)\nHorario: '+hrs+' '+grupo['dias']+'\n'
                    var texto='<td id="grupo2" style="text-align:CENTER; vertical-align:MIDDLE">\n';
                    var hrs="";
                    try{hrs=grupo['horario'][0].getHours()+":"+grupo['horario'][0].getMinutes()+"-"+grupo['horario'][1].getHours()+":"+grupo['horario'][1].getMinutes()}
                    catch(err){hrs="";}
                    n=grupo['nombre'].split("-");
                    texto+='<span title="'+span_text+'" onclick="post_link(\''+grupo['nombre']+'\')">'
                    texto+=n[0]+n[1]+"("+grupo['grupo']+")";
                    texto+='</span>'
                    texto+='</td>';
                    break;
                }
            }
            out+=texto;
        }
        out+="</tr>\n";
    }
    out+="</table>"//"\n<hr>\n"
    return out;
}
