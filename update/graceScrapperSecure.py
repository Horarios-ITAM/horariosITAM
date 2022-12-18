import requests,json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from utils import claveToDepto
# URLs and constants
loginUrl="https://serviciosweb.itam.mx/EDSUP/twbkwbis.P_WWWLogin"
loginForm="https://serviciosweb.itam.mx/EDSUP/twbkwbis.P_ValLogin"

# Registration > Look-up Classes to Add
termUrl="https://serviciosweb.itam.mx/EDSUP/bwskfcls.p_sel_crse_search"

# > Look-up Classes to Add
deptosUrl=urljoin(loginUrl,"/EDSUP/bwckgens.p_proc_term_date")

#
courseUrl=urljoin(loginUrl,"/EDSUP/bwskfcls.P_GetCrse")

class GraceScrapperSecureArea:
    """
    Clase que maneja el scrappeo de Grace (serviciosweb.itam.mx) de
    Secure Area > Registration > Look-up Classes to Add.

    Requiere credenciales para hacer login en Grace.

    Los URLs de Grace y otras constantes se encuentran guardadas en este archivo.
    """
    
    def __init__(self,usuario:str,passwd:str,verbose:bool=True):
        """
        Constructor. Hace login y scrapea datos preliminares.

        Parametros:
        ----------
        usuario: str.
            Usuario de Grace (serviciosweb.itam.mx). Clave Unica a 9 digitos.

        passwd: str.
            Contraseña de Grace.
        """
        self.verbose=verbose

        # Sesion de requests para mantener cookies
        self.session = requests.Session()

        # Intentamos hacer login con usuario y passwd
        if self.login(usuario,passwd):

            # Si logramos hacer login obtenemos 
            self.periodo,self.clavePeriodo=self._getTerm()
            if verbose:
                print(f'Periodo: {self.periodo}\nClave de periodo: {self.clavePeriodo}')

    def login(self,usuario,passwd):
        """
        Inicia sesion en Grace con sesion s.
        """
        loginData={
            "sid":usuario,
            "PIN":passwd
        }
        s=self.session
        s.get(loginUrl)
        r=s.post(loginForm,loginData,allow_redirects=True)
        if 'WELCOME' in r.text:
            b=BeautifulSoup(r.text, "html.parser")
            redir=b.find_all("meta")[0].attrs['content'].split("url=")[1]
            url=urljoin(loginUrl,redir)
            r=s.get(url)
            if 'Admissions' in r.text:
                self._print(f'Sesion iniciada con cookies {s.cookies.get_dict()}')
                return True
            else:
                print('Error iniciando sesion')
                return False
        else:
            print('Outer Error')
            return False

    def _isLoginPage(self,html):
        """
        Checa si el html corresponde a la pagina de login de Grace.
        """
        return "Please enter your" in html

    def _getTerm(self):
        """
        Regresa el semestre (e.g. 'PRIMAVERA 2022 LICENCIATURA') y 
        valor correspondiente del semestre (e.g. 202301) (tupla)
        más reciente de licenciatura que encuentra en termUrl.
        """
        response=self.session.get(termUrl)
        b=BeautifulSoup(response.text,'html.parser')
        value=0
        sem=""
        for opt in b.find_all("option"):
            if 'LICENCIATURA' in opt.text:
                tempVal=int(opt.attrs['value'])
                if tempVal>value:
                    value=tempVal
                    sem=opt.text
        sem=sem.replace('(View only)','')
        sem=sem.strip()
        return sem,str(value)

    def getClavesDeptos(self):
        """
        Regresa un dict. {clave depto: nombre} que encuentra en deptosUrl.
        """
        data={
            "p_term":self.clavePeriodo,
            "p_calling_proc":"P_CrseSearch"
        }
        r=self.session.post(deptosUrl,data,allow_redirects=True)
        deptos={}
        b=BeautifulSoup(r.text,'html.parser')
        for opt in b.find_all("option"):
            if opt.parent.attrs['id']=="subj_id":
                deptos[opt.attrs['value']]=opt.text.strip()
        return deptos

    def getClavesMaterias(self,depto):
        """
        Regresa una lista de las claves de las materias que ofrece depto
        en el termino term que encuentra haciendo post a courseUrl.
        """
        data="rsts=dummy&crn=dummy&term_in={}&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_subj={}&sel_crse=&sel_title=&sel_from_cred=&sel_to_cred=&sel_ptrm=%25&begin_hh=0&begin_mi=0&end_hh=0&end_mi=0&begin_ap=x&end_ap=y&path=1&SUB_BTN=Course+Search".format(self.clavePeriodo,depto)
        r=self.session.post(courseUrl,data,allow_redirects=True)
        codes=[]
        b=BeautifulSoup(r.text,'html.parser')
        for i in b.find_all('input'):
            if i.attrs.get('name','')=='SEL_CRSE':
                codes.append(i.attrs['value'])
        return codes

    def getHTMLclase(self,depto,clave):
        """
        Regresa el HTML de la pagina de una clase que encuentra
        haciendo post a courseUrl.
        """
        data="term_in={}&sel_subj=dummy&sel_subj={}&SEL_CRSE={}&SEL_TITLE=&BEGIN_HH=0&BEGIN_MI=0&BEGIN_AP=a&SEL_DAY=dummy&SEL_PTRM=dummy&END_HH=0&END_MI=0&END_AP=a&SEL_CAMP=dummy&SEL_SCHD=dummy&SEL_SESS=dummy&SEL_INSTR=dummy&SEL_INSTR=%25&SEL_ATTR=dummy&SEL_ATTR=%25&SEL_LEVL=dummy&SEL_LEVL=%25&SEL_INSM=dummy&sel_dunt_code=&sel_dunt_unit=&call_value_in=&rsts=dummy&crn=dummy&path=1&SUB_BTN=View+Sections".format(self.clavePeriodo,depto,clave)
        r=self.session.post(courseUrl,data)
        return r.text
    
    
    def parseaGrupos(self,htmlClase):
        """
        Dado el HTML de una clase, parsea los grupos.
        Regresa una lista de diccionarios (uno por cada grupo) con los datos.
        """
        b=BeautifulSoup(htmlClase,"html.parser")
        # Las columnas de la tabla con horarios. None indica que no nos importa.
        cols=[None, None, 'depto', 'clave', 'grupo', None, 'creditos', 'nombre', None, 'dias', 'horario', 'profesor', None, 'salon']
        grupos=[]
        table=b.find('table',{'class':'datadisplaytable'})
        if table==None: return grupos
        for tr in table.find_all('tr')[2:]:
            temp={}
            for i,td in enumerate(tr.find_all('td')):
                equiv=cols[i]
                if equiv:
                    temp[equiv]=td.text.strip()
                # Si es lab estas columnas estan vacias. Toma del grupo anterior (teoria).
                if equiv and temp[equiv]=='' and equiv in ['depto','clave','grupo','creditos','nombre']:
                    temp[equiv]=grupos[-1][equiv]
                    if equiv=='clave' or equiv=='nombre':
                        temp[equiv]+='-LAB'
                    elif equiv=='grupo':
                        temp[equiv]+='L'
            grupos.append(temp)
        return grupos
    
    def formateaGrupo(self,grupo):
        """
        Formatea los dados obtenidos de parseaGrupo.
        Regresa un diccionario con los datos.
        """
        out={}
        try:
            out['grupo']=grupo['grupo']
            out['nombre']=grupo['depto']+'-'+grupo['clave'].replace('-LAB','')+'-'+grupo['nombre']
            out['profesor']=grupo['profesor'].replace('/',' ').replace('(P)','').strip()
            out['profesor']=" ".join(out['profesor'].split())
            out['creditos']=str(int(float(grupo['creditos'])))
            inicio,fin=grupo['horario'].split('-')
            out['inicio']=self._to24hr(inicio)
            out['fin']=self._to24hr(fin)
            out['horario']=out['inicio']+'-'+out['fin']
            dias={
                'M':'LU',
                'T':'MA',
                'W':'MI',
                'R':'JU',
                'F':'VI',
                'S':'SA',
            }
            out['dias']=[dias[d] for d in list(grupo['dias'])]
            if len(grupo['salon'].split())>1:
                out['salon']=grupo['salon'].split()[1].strip() # TODO checar
            else:
                out['salon']=grupo['salon'].strip()

            out['campus']='RIO HONDO' if 'RH' in grupo['salon'] else 'SANTA TERESA'
            
        except Exception:
            print(' Error formateando grupo:')
            print(grupo)
        return out
    
    def scrap(self,scrapDeptos=False):
        """
        Scrappea los detalles de las clases de Grace (tardado).
        Almacena resultados en self.clases.

        Si scrapDeptos=True se scrapean las claves de los departamentos
        usando getClavesDeptos().
        """
        if scrapDeptos:
            deptos=self.getClavesDeptos()
        else:
            deptos=claveToDepto
        
        self._print("Scrappeando clases de depto ...")

        self.clases={}
        for depto in deptos.keys():
            nClases,nGrupos=0,0
            for clave in self.getClavesMaterias(depto):
                html=self.getHTMLclase(depto,clave)
                grupos=self.parseaGrupos(html)
                grupos=[self.formateaGrupo(g) for g in grupos]

                # Separamos en teoria y lab
                teorias,labs=[],[]
                for g in grupos:
                    if 'L' in g['grupo']:
                        labs.append(g)
                    else:
                        teorias.append(g)
                
                claveF=lambda nombre:'-'.join(nombre.split('-')[:2])
                # Agregamos teorias
                if len(teorias)>0:
                    clave=claveF(teorias[0]['nombre'])
                    self.clases[clave]={
                        'nombre':teorias[0]['nombre'],
                        'clave':clave,
                        'grupos':teorias
                    }
                # Agregamos labs
                if len(labs)>0:
                    clave=claveF(labs[0]['nombre'])+'-LAB'
                    self.clases[clave]={
                        'nombre':labs[0]['nombre'],
                        'clave':clave,
                        'grupos':labs
                    }

                nGrupos+=(len(teorias)+len(labs))
                nClases+=1

            self._print(f"{depto}: {nClases} clases y {nGrupos} grupos")
                
        self._print("Se scrappearon {} clases!".format(len(self.clases)))

        # Extrae profesores
        self.profesores=list(set([grupo['profesor'] for clase in self.clases.values() for grupo in clase['grupos'] if len(grupo['profesor'].strip())>1]))
        
        self._print("Se encontraron {} profesores en Grace!".format(len(self.profesores)))



    def _to24hr(self,s):
        """
        Convierte el formato str de horario de 12 a 24 hrs.
        Ej. 2:00 pm -> 14:00.
        """
        s=s.strip()
        temp=datetime.strptime(s, "%I:%M %p")
        return datetime.strftime(temp, "%H:%M")

    def _print(self,s):
        if self.verbose:
            print(s)

if __name__=='__main__':
    with open("creds.json") as f:
        loginData=json.loads(f.read())
    g=GraceScrapperSecureArea(loginData['sid'],loginData['PIN'])
    g.scrap()

