import json
import logging
from urllib.parse import urljoin
from datetime import datetime
from typing import Dict, Tuple, List, Any, Optional

import requests
from bs4 import BeautifulSoup

from utils import claveToDepto, DEFAULT_TIMEOUT, NetworkError # Import necessary items from utils

logger = logging.getLogger(__name__)

# --- Constants for URLs ---
BASE_SECURE_URL = "https://serviciosweb.itam.mx/EDSUP/"
LOGIN_URL = urljoin(BASE_SECURE_URL, "twbkwbis.P_WWWLogin")
VALIDATE_LOGIN_URL = urljoin(BASE_SECURE_URL, "twbkwbis.P_ValLogin")
TERM_SELECTION_URL = urljoin(BASE_SECURE_URL, "bwskfcls.p_sel_crse_search") # For selecting term
DEPT_LIST_URL = urljoin(BASE_SECURE_URL, "bwckgens.p_proc_term_date") # For getting department list for a term
COURSE_SEARCH_URL = urljoin(BASE_SECURE_URL, "bwskfcls.P_GetCrse") # For searching courses and viewing sections

class GraceSecureLoginError(Exception):
    """Custom exception for login failures."""
    pass

class GraceSecureScrapperError(Exception):
    """Custom exception for general errors in GraceSecureAreaScrapper."""
    pass


class GraceScrapperSecureArea:
    """
    Clase que maneja el scrapeo de Grace (serviciosweb.itam.mx) desde
    Secure Area > Registration > Look-up Classes to Add.
    Requiere credenciales (usuario y PIN) para iniciar sesión.
    """
    
    def __init__(self, usuario: str, pin: str):
        """
        Constructor. Inicia sesión en Grace y obtiene el período académico más reciente.

        Parámetros:
        ----------
        usuario : str
            Usuario de Grace (Clave Única a 9 dígitos).
        pin : str
            Contraseña (PIN) de Grace.

        Levanta:
        -------
        GraceSecureLoginError
            Si el inicio de sesión falla.
        GraceSecureScrapperError
            Si no se puede determinar el período académico.
        utils.NetworkError
            Si ocurren problemas de red durante el inicio de sesión o la obtención del período.
        """
        self.session = requests.Session()
        self.usuario = usuario
        self.clavePeriodo: Optional[str] = None
        self.periodo: Optional[str] = None
        self.clases: Dict[str, Any] = {}
        self.profesores: List[str] = []

        logger.info(f"Iniciando GraceScrapperSecureArea para usuario: {self.usuario}")

        self._perform_login(self.usuario, pin) # login ahora levanta excepción si falla

        try:
            current_period, current_period_key = self._get_latest_term()
            self.periodo = current_period
            self.clavePeriodo = current_period_key
            logger.info(f"Período académico obtenido: {self.periodo} (Clave: {self.clavePeriodo})")
        except (NetworkError, ValueError) as e:
            msg = f"No se pudo obtener el período académico tras el login: {e}"
            logger.error(msg)
            raise GraceSecureScrapperError(msg) from e

        if not self.periodo or not self.clavePeriodo:
             msg = "El período o la clave de período no se pudieron determinar."
             logger.error(msg)
             raise GraceSecureScrapperError(msg)


    def _perform_login(self, usuario: str, pin: str) -> None:
        """
        Realiza el proceso de inicio de sesión en Grace.
        Levanta GraceSecureLoginError si falla.
        """
        logger.info("Intentando iniciar sesión en Grace...")
        login_payload = {"sid": usuario, "PIN": pin}

        try:
            # Paso 1: Obtener cookies iniciales de la página de login (opcional, pero buena práctica)
            self.session.get(LOGIN_URL, timeout=DEFAULT_TIMEOUT)

            # Paso 2: Enviar credenciales
            response_post_login = self.session.post(VALIDATE_LOGIN_URL, data=login_payload, allow_redirects=True, timeout=DEFAULT_TIMEOUT)
            response_post_login.raise_for_status() # Checar errores HTTP

            # Checar si el login fue exitoso buscando "welcome" o similar
            # Grace a veces redirige a una página intermedia con un meta refresh.
            if 'welcome' not in response_post_login.text.lower() and 'bienvenido' not in response_post_login.text.lower():
                # Podría ser una página de error de PIN incorrecto, etc.
                # El texto "Please enter your User ID" indica que sigue en la página de login.
                if "please enter your" in response_post_login.text.lower() or "favor de teclear" in response_post_login.text.lower() :
                    logger.error("Login fallido: Grace redirigió a la página de login (probable PIN incorrecto).")
                    raise GraceSecureLoginError("Credenciales incorrectas o login fallido (redirigido a login).")
                logger.error(f"Login fallido: 'welcome' o 'bienvenido' no encontrado en la respuesta. Contenido: {response_post_login.text[:500]}")
                raise GraceSecureLoginError("Respuesta inesperada tras el intento de login.")

            soup_login_resp = BeautifulSoup(response_post_login.text, "html.parser")
            meta_refresh = soup_login_resp.find("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)})

            final_landing_url = response_post_login.url # URL actual después de POST y redirecciones
            if meta_refresh and meta_refresh.get("content"):
                content_parts = meta_refresh["content"].split("URL=")
                if len(content_parts) > 1:
                    redirect_path = content_parts[1].strip()
                    final_landing_url = urljoin(VALIDATE_LOGIN_URL, redirect_path) # Base es la URL del POST
                    logger.debug(f"Detectada meta refresh tras login a: {final_landing_url}")
                    response_after_refresh = self.session.get(final_landing_url, timeout=DEFAULT_TIMEOUT)
                    response_after_refresh.raise_for_status()
                    # Aquí, el texto de `response_after_refresh` debería ser la página principal del área segura.
                    if 'registration' not in response_after_refresh.text.lower() and 'inscripción' not in response_after_refresh.text.lower():
                         logger.error(f"Login pareció exitoso, pero la página final no contiene 'registration' o 'inscripción'. URL: {final_landing_url}")
                         raise GraceSecureLoginError("Página de aterrizaje post-login inesperada.")

            logger.info(f"Sesión iniciada exitosamente. Cookies: {self.session.cookies.get_dict()}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP durante el login: {e.response.status_code} - {e.response.reason}")
            raise GraceSecureLoginError(f"Error HTTP durante login: {e}") from e
        except requests.exceptions.Timeout:
            logger.error("Timeout durante el proceso de login.")
            raise GraceSecureLoginError("Timeout durante login.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red durante el login: {e}")
            raise GraceSecureLoginError(f"Error de red durante login: {e}") from e


    def _is_login_page(self, html_content: str) -> bool:
        """Verifica si el HTML corresponde a la página de login de Grace."""
        return "please enter your" in html_content.lower() or "favor de teclear" in html_content.lower()

    def _get_latest_term(self) -> Tuple[str, str]:
        """
        Obtiene el semestre más reciente y su clave desde la página de selección de término.
        Regresa una tupla (nombre_semestre, clave_semestre).
        Levanta ValueError si no se encuentra o NetworkError si falla la petición.
        """
        logger.debug(f"Obteniendo lista de períodos desde: {TERM_SELECTION_URL}")
        try:
            response = self.session.get(TERM_SELECTION_URL, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            if self._is_login_page(response.text): # Checar si la sesión expiró o no se inició bien
                logger.error("Se detectó página de login al intentar obtener términos. Sesión inválida.")
                raise GraceSecureLoginError("Sesión inválida o expirada al obtener términos.")

            soup = BeautifulSoup(response.text, 'html.parser')

            latest_value = 0
            latest_sem_name = ""

            options = soup.find_all("option")
            if not options:
                raise ValueError("No se encontraron opciones de período en la página.")

            for opt_tag in options:
                if opt_tag.string and 'LICENCIATURA' in opt_tag.string.upper(): # Buscar LICENCIATURA
                    try:
                        term_val_str = opt_tag.get('value')
                        if not term_val_str: continue
                        term_val = int(term_val_str)

                        if term_val > latest_value:
                            latest_value = term_val
                            latest_sem_name = opt_tag.string.strip()
                    except (ValueError, TypeError):
                        logger.warning(f"No se pudo parsear el valor del período para la opción: {opt_tag.string}")
                        continue

            if not latest_sem_name or latest_value == 0:
                raise ValueError("No se pudo determinar el período de licenciatura más reciente.")

            latest_sem_name = latest_sem_name.replace('(View only)', '').replace('(Solo Consulta)', '').strip()
            logger.info(f"Período más reciente encontrado: {latest_sem_name} (Clave: {latest_value})")
            return latest_sem_name, str(latest_value)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red obteniendo términos: {e}")
            raise NetworkError(f"Error de red obteniendo términos: {e}") from e


    def getClavesDeptos(self) -> Dict[str,str]:
        """
        Regresa un diccionario {clave_depto: nombre_depto} para el período actual.
        """
        if not self.clavePeriodo:
            raise GraceSecureScrapperError("Clave de período no establecida. No se pueden obtener departamentos.")

        logger.debug(f"Obteniendo lista de departamentos para el período {self.clavePeriodo} desde {DEPT_LIST_URL}")
        payload = {
            "p_term": self.clavePeriodo,
            "p_calling_proc": "P_CrseSearch" # Parece ser un parámetro requerido
        }

        try:
            response = self.session.post(DEPT_LIST_URL, data=payload, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            if self._is_login_page(response.text):
                logger.error("Se detectó página de login al obtener departamentos. Sesión inválida.")
                raise GraceSecureLoginError("Sesión inválida o expirada al obtener departamentos.")

            soup = BeautifulSoup(response.text, 'html.parser')
            deptos: Dict[str, str] = {}
            # Los departamentos están en un <select id="subj_id">
            select_subj = soup.find("select", {"id": "subj_id"})
            if not select_subj:
                logger.warning("No se encontró el <select> de departamentos (id='subj_id').")
                return deptos # Devolver vacío si no se encuentra

            for opt_tag in select_subj.find_all("option"):
                value = opt_tag.get('value')
                text = opt_tag.string
                if value and text: # Asegurar que ambos existan y no sean vacíos
                    # A veces el valor es '%' lo que significa 'Todos', se ignora.
                    if value != '%':
                        deptos[value.strip()] = text.strip()

            logger.info(f"Se encontraron {len(deptos)} departamentos.")
            return deptos
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red obteniendo departamentos: {e}")
            raise NetworkError(f"Error de red obteniendo departamentos: {e}") from e


    def getClavesMaterias(self, depto_code: str) -> List[str]:
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

