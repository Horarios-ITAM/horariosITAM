import re
import logging
from typing import Optional, Tuple, List, Dict, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import utils # Assuming utils.py is in the same directory or accessible

logger = logging.getLogger(__name__)

class GraceScrapperException(Exception):
    """Custom exception for errors during GraceScrapper operations."""
    pass

class GraceScrapper:
    """
    Clase que maneja el scrapeo de Grace (serviciosweb.itam.mx)
    desde la sección de "Servicios No Personalizados".
    """
    
    BASE_ITAM_URL = "https://servicios.itam.mx/"
    # Selectors and search strings
    SERVICIOS_NO_PERS_TEXT = "Servicios no personalizados"
    SERVICIOS_NO_PERS_HREF_SUBSTRING = "ServNoPers"
    HORARIOS_LIC_TEXT = "Horarios" # Combined with "LICENCIATURA"
    LICENCIATURA_TEXT = "LICENCIATURA"
    PERIODO_SPLIT_TEXT = "período" # Used in old parsing logic for periodo name
    H3_TAG_TEXT = "</h3>" # Used in old parsing logic
    OPTION_TAG_TEXT = "<option>" # Used in old parsing logic
    HIDDEN_INPUT_S_NAME = "s" # Name of the hidden input field for clavePeriodo


    def __init__(self, dropDownURL: Optional[str] = None, formURL: Optional[str] = None, clavePeriodo: Optional[str] = None):
        """
        Constructor. Scrapea datos preliminares.
        Si no se proporcionan dropDownURL, formURL y clavePeriodo, se intentará scrappearlos automáticamente.

        Parámetros:
        ----------
        dropDownURL: str, opcional
            URL de la página de Grace con el menú desplegable de clases.
            Ej: Servicios No Personalizados > Horarios para el período [Periodo].
        formURL: str, opcional
            URL del POST que utiliza el formulario en dropDownURL.
        clavePeriodo: str, opcional
            Valor del campo oculto "s" (clave del período) en el formulario POST.

        Levanta:
        -------
        GraceScrapperException: Si no se pueden obtener las URLs o datos iniciales.
        utils.NetworkError: Si hay problemas de red durante el scrapeo inicial.
        """
        self.session = requests.Session() # Use a session for all requests

        if not all([dropDownURL, formURL, clavePeriodo]):
            logger.info("URLs/clavePeriodo no proporcionados, intentando scrapearlos automáticamente.")
            try:
                self.dropDownURL, self.formURL, self.clavePeriodo = self._discover_urls_and_period_key()
                logger.info(f"URLs y clave de período scrapeadas:")
                logger.info(f"  dropDownURL: {self.dropDownURL}")
                logger.info(f"  formURL: {self.formURL}")
                logger.info(f"  clavePeriodo: {self.clavePeriodo}")
            except (utils.NetworkError, ValueError) as e:
                msg = f"Fallo al auto-descubrir URLs/clavePeriodo: {e}"
                logger.error(msg)
                raise GraceScrapperException(msg) from e
        else:
            self.dropDownURL = dropDownURL
            self.formURL = formURL
            self.clavePeriodo = clavePeriodo
            logger.info("Usando URLs/clavePeriodo proporcionadas.")

        try:
            self.periodo, self.listaClases = self._scrape_period_and_class_list()
            logger.info(f"Período determinado: {self.periodo}")
            logger.info(f"Clave de Período: {self.clavePeriodo}")
            logger.info(f"# de clases encontradas en dropdown: {len(self.listaClases)}")
        except (utils.NetworkError, ValueError) as e:
            msg = f"Fallo al scrapear período y lista de clases: {e}"
            logger.error(msg)
            raise GraceScrapperException(msg) from e

        self.clases: Dict[str, Any] = {} # Stores formatted class data
        self.profesores: List[str] = []


    def _fetch_html(self, url: str) -> str:
        """Wrapper to fetch HTML using utils.getHTML, handling potential SSL issues for itam.mx."""
        # ITAM sites sometimes have SSL issues, allow flexibility if needed by utils.getHTML
        # utils.getHTML has verify_ssl=True by default.
        return utils.getHTML(url)

    def _discover_urls_and_period_key(self) -> Tuple[str, str, str]:
        """
        Intenta scrapear y regresar los valores de dropDownURL, formURL y clavePeriodo (s).
        """
        # 1. Determinar la URL de la homepage de servicios (puede haber redirección)
        logger.debug(f"Accediendo a la URL base: {self.BASE_ITAM_URL}")
        html_main = self._fetch_html(self.BASE_ITAM_URL)
        soup_main = BeautifulSoup(html_main, "html.parser")
        meta_refresh = soup_main.find("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)})
        
        home_page_url = self.BASE_ITAM_URL
        if meta_refresh and meta_refresh.get("content"):
            content_parts = meta_refresh["content"].split("URL=")
            if len(content_parts) > 1:
                redirect_url = content_parts[1].strip()
                home_page_url = urljoin(self.BASE_ITAM_URL, redirect_url)
                logger.debug(f"Redirección detectada a: {home_page_url}")

        # 2. Extraer URL de "Servicios no personalizados"
        logger.debug(f"Buscando link a 'Servicios no personalizados' en {home_page_url}")
        html_home = self._fetch_html(home_page_url)
        soup_home = BeautifulSoup(html_home, "html.parser")

        link_serv_no_pers = soup_home.find("a", string=re.compile(self.SERVICIOS_NO_PERS_TEXT, re.I))
        if not link_serv_no_pers:
            logger.debug(f"No se encontró por texto, buscando por substring en href: '{self.SERVICIOS_NO_PERS_HREF_SUBSTRING}'")
            link_serv_no_pers = soup_home.find("a", href=re.compile(self.SERVICIOS_NO_PERS_HREF_SUBSTRING, re.I))

        if not link_serv_no_pers or not link_serv_no_pers.get("href"):
            raise ValueError("No se encontró el link a 'Servicios no personalizados'.")

        url_servicios_no_personalizados = urljoin(home_page_url, link_serv_no_pers["href"])
        logger.info(f"URL de Servicios no personalizados encontrada: {url_servicios_no_personalizados}")

        # 3. Extraer dropDownURL (Horarios de Licenciatura más reciente)
        logger.debug(f"Buscando links a Horarios de Licenciatura en {url_servicios_no_personalizados}")
        html_serv_no_pers = self._fetch_html(url_servicios_no_personalizados)
        soup_serv_no_pers = BeautifulSoup(html_serv_no_pers, "html.parser")

        candidate_period_links: Dict[str, str] = {}
        for link_tag in soup_serv_no_pers.find_all("a", string=re.compile(self.HORARIOS_LIC_TEXT, re.I)):
            link_text = link_tag.string.strip()
            if self.LICENCIATURA_TEXT in link_text:
                # Extraer el nombre del período, ej. "OTOÑO 2023 LICENCIATURA"
                match_period_name = re.search(r"\((.*?LICENCIATURA.*?)\)", link_text)
                if match_period_name:
                    period_name_full = match_period_name.group(1).strip()
                    if utils.periodoValido(period_name_full) and link_tag.get("href"):
                        candidate_period_links[period_name_full] = link_tag["href"]

        if not candidate_period_links:
            raise ValueError("No se encontraron links a Horarios de Licenciatura válidos.")

        logger.debug(f"Links de períodos encontrados: {candidate_period_links}")
        latest_period_name = utils.periodoMasReciente(list(candidate_period_links.keys()))
        logger.info(f"Período más reciente seleccionado: {latest_period_name}")

        dropdown_url = urljoin(url_servicios_no_personalizados, candidate_period_links[latest_period_name])

        # 4. Extraer formURL y clavePeriodo (s) desde la dropDownURL
        logger.debug(f"Extrayendo formURL y clave de período desde: {dropdown_url}")
        html_dropdown = self._fetch_html(dropdown_url)
        soup_dropdown = BeautifulSoup(html_dropdown, "html.parser")

        form_tag = soup_dropdown.find("form")
        if not form_tag or not form_tag.get("action"):
            raise ValueError(f"No se encontró la etiqueta <form> o su atributo 'action' en {dropdown_url}")

        form_url = urljoin(dropdown_url, form_tag["action"]) # form action can be relative

        input_s_tag = soup_dropdown.find("input", {"name": self.HIDDEN_INPUT_S_NAME, "type": "hidden"})
        if not input_s_tag or input_s_tag.get("value") is None : # value can be empty string
            raise ValueError(f"No se encontró el input oculto '{self.HIDDEN_INPUT_S_NAME}' o su valor en {dropdown_url}")

        clave_periodo = input_s_tag["value"]

        return dropdown_url, form_url, clave_periodo

    def _scrape_period_and_class_list(self) -> Tuple[str, List[str]]:
        """
        Obtiene el nombre del período y la lista de nombres de clases desde la dropDownURL.
        Intenta usar BeautifulSoup para una extracción más robusta.
        """
        logger.debug(f"Scrapeando nombre del período y lista de clases desde: {self.dropDownURL}")
        html = self._fetch_html(self.dropDownURL)
        soup = BeautifulSoup(html, "html.parser")

        # Intentar extraer el período de manera más robusta
        periodo_name = "Desconocido"
        # Buscar un h3 que contenga "período"
        h3_tag = soup.find("h3", string=re.compile(self.PERIODO_SPLIT_TEXT, re.I))
        if h3_tag:
            # Tomar el texto después de "período" y antes de cualquier tag anidado si existe, o al final del texto del h3
            match = re.search(fr"{self.PERIODO_SPLIT_TEXT}\s*(.*?)(?:<.*|$)", h3_tag.decode_contents(), re.I | re.S)
            if match:
                periodo_name = match.group(1).strip()
            else: # Fallback a la lógica original si la regex no funciona bien con la estructura
                 periodo_name = (html.split(self.PERIODO_SPLIT_TEXT)[1].split(self.H3_TAG_TEXT)[0]).strip()
        else: # Fallback si no se encuentra h3
            try:
                # Lógica original de split (muy frágil)
                periodo_name = (html.split(self.PERIODO_SPLIT_TEXT)[1].split(self.H3_TAG_TEXT)[0]).strip()
                logger.warning("Se usó método de split para extraer el nombre del período (frágil).")
            except IndexError:
                logger.error("No se pudo extraer el nombre del período usando el método de split.")
                raise ValueError("No se pudo determinar el nombre del período desde la página de dropdown.")

        # Extraer lista de clases de las opciones del dropdown
        class_options = soup.find_all("option")
        lista_clases = []
        if class_options:
            for option_tag in class_options:
                # El primer option suele ser "Selecciona una..." o similar, lo saltamos si no tiene valor o un valor específico.
                # O, como en el original, se saltaba el primero y el último.
                # Aquí, tomaremos todos los que tengan texto no vacío.
                if option_tag.string:
                    class_name = option_tag.string.strip()
                    if class_name and class_name.upper() != "TODAS": # Evitar "TODAS" si existe
                        lista_clases.append(class_name)
            if not lista_clases and html.count(self.OPTION_TAG_TEXT) > 1 : # Fallback si BS4 no extrajo bien
                 # Lógica original de split (muy frágil)
                lista_clases = [i.replace('</option>', '').replace('\n', '').strip() for i in html.split(self.OPTION_TAG_TEXT)[1:-1] if i.strip()]
                logger.warning("Se usó método de split para extraer la lista de clases (frágil).")

        if not lista_clases:
            raise ValueError("No se pudo extraer la lista de clases desde la página de dropdown.")
            
        return periodo_name, lista_clases
    def _getClaseInfo(self, html_clase_info: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Dado el HTML de la página de información de una clase (obtenido por POST a formURL),
        extrae los datos de cada grupo.
        Regresa un diccionario de la forma {"<NumeroGrupo>": {<datos_del_grupo>}}.
        """
        if not html_clase_info:
            logger.warning("HTML de información de clase vacío, no se puede parsear.")
            return None

        soup = BeautifulSoup(html_clase_info, 'html.parser')

        expected_cols = [
            "depto", "clave", "grupo", "CRN", "TL", "nombre", "prof", "cred",
            "horario", "dias", "salon", "campus", "comentarios"
        ]

        data_table = None
        all_tables = soup.find_all('table')

        if len(all_tables) > 2:
            data_table = all_tables[2]
            logger.debug("Tabla de información de clase seleccionada por índice [2].")
        else:
            # Fallback: buscar tabla con un `<caption>` que contenga "Horario de Clases" o similar
            # O una tabla con un `<th>` específico.
            # Este es un punto muy frágil.
            for table_candidate in all_tables:
                caption = table_candidate.find('caption')
                if caption and "horario" in caption.text.lower(): # Ejemplo de heurística
                    data_table = table_candidate
                    logger.info("Tabla de información de clase encontrada por caption 'horario'.")
                    break
                # Otra heurística: tiene muchos `<tr>` con `<td>`
                elif len(table_candidate.find_all('tr')) > 5 and len(table_candidate.find_all('td')) > 20 : # Arbitrario
                    data_table = table_candidate
                    logger.info("Tabla de información de clase encontrada por heurística de tamaño.")
                    break
            if not data_table:
                 logger.warning(f"Se encontraron {len(all_tables)} tablas. No se pudo identificar la tabla de datos correcta.")
                 return None


        parsed_grupos: Dict[str, Dict[str, Any]] = {}
        rows = data_table.find_all('tr')
        if len(rows) < 2:
            logger.debug("Tabla encontrada no parece tener filas de datos (solo cabecera o vacía).")
            return parsed_grupos

        for row_idx, row in enumerate(rows[1:], 1): # Saltar la fila de cabecera
            cells = row.find_all('td')
            grupo_data: Dict[str, Any] = {col: "" for col in expected_cols} # Initialize with empty strings

            for i, cell in enumerate(cells):
                if i < len(expected_cols):
                    col_name = expected_cols[i]
                    grupo_data[col_name] = cell.string.strip() if cell.string else ""
                else:
                    logger.debug(f"Fila {row_idx} con más celdas ({len(cells)}) que columnas esperadas ({len(expected_cols)}). Celdas extra ignoradas.")
                    break

            if grupo_data.get("dias"):
                grupo_data["dias"] = str(grupo_data["dias"]).split()
            else:
                grupo_data["dias"] = [] # Asegurar que sea lista

            if grupo_data.get("TL") == "L" and grupo_data.get("grupo"):
                grupo_data["grupo"] += "L"

            horario_str = grupo_data.get("horario", "")
            if horario_str and "-" in horario_str:
                parts = horario_str.split("-", 1)
                grupo_data["inicio"] = parts[0].strip()
                grupo_data["fin"] = parts[1].strip() if len(parts) > 1 else ""
            else:
                grupo_data["inicio"] = ""
                grupo_data["fin"] = ""

            grupo_key = grupo_data.get("grupo")
            if grupo_key: # Asegurar que el grupo tiene una clave (número de grupo)
                parsed_grupos[str(grupo_key)] = grupo_data
            else:
                logger.warning(f"Grupo en fila {row_idx} saltado por no tener número de grupo (columna 'grupo'): {grupo_data}")

        return parsed_grupos
    
    def _formateaClases(self, raw_clases_data_list: List[Optional[Dict[str, Dict[str, Any]]]]) -> Dict[str, Dict[str, Any]]:
        """
        Reformatea la lista de datos de clases (cada elemento es el output de _getClaseInfo)
        en un diccionario anidado por clave de materia y luego por tipo (Teoría/Laboratorio).
        """
        formatted_data: Dict[str, Any] = {}

        for clase_info_dict in raw_clases_data_list:
            if not clase_info_dict:
                continue

            # Para construir el nombre base y la clave base de la materia,
            # es más seguro iterar por los grupos y tomar el primero que tenga datos válidos.
            depto_base, clave_materia_base, nombre_materia_base = "", "", ""
            found_base_info = False
            for g_data_temp in clase_info_dict.values():
                if g_data_temp.get('depto') and g_data_temp.get('clave') and g_data_temp.get('nombre'):
                    depto_base = g_data_temp['depto']
                    clave_materia_base = g_data_temp['clave']
                    nombre_materia_base = g_data_temp['nombre']
                    found_base_info = True
                    break

            if not found_base_info:
                logger.warning(f"No se pudo determinar la información base (depto, clave, nombre) para un conjunto de grupos: {clase_info_dict}")
                continue

            original_materia_nombre_completo = f"{depto_base}-{clave_materia_base}-{nombre_materia_base}"
            materia_id_base = f"{depto_base}-{clave_materia_base}"

            grupos_teoria: List[Dict[str, Any]] = []
            grupos_lab: List[Dict[str, Any]] = []

            for grupo_numero, data_grupo in clase_info_dict.items():
                # El nombre de la materia para el grupo específico puede incluir -LAB
                nombre_materia_para_grupo = original_materia_nombre_completo
                if data_grupo.get('TL') == 'L':
                    nombre_materia_para_grupo += '-LAB'

                grupo_formateado = {
                    'grupo': data_grupo.get('grupo', ''),
                    'nombre': nombre_materia_para_grupo,
                    'profesor': data_grupo.get('prof', ''),
                    'creditos': data_grupo.get('cred', ''),
                    'horario': data_grupo.get('horario', ''),
                    'dias': data_grupo.get('dias', []),
                    'salon': data_grupo.get('salon', ''),
                    'campus': data_grupo.get('campus', ''),
                    'inicio': data_grupo.get('inicio', ''),
                    'fin': data_grupo.get('fin', '')
                }

                if data_grupo.get('TL') == 'L':
                    grupos_lab.append(grupo_formateado)
                elif data_grupo.get('TL') == 'T':
                    grupos_teoria.append(grupo_formateado)

            if grupos_lab:
                lab_entry_key = f"{materia_id_base}-LAB"
                formatted_data[lab_entry_key] = {
                    'nombre': f"{original_materia_nombre_completo}-LAB",
                    'clave': lab_entry_key,
                    'grupos': grupos_lab
                }

            if grupos_teoria:
                formatted_data[materia_id_base] = {
                    'nombre': original_materia_nombre_completo,
                    'clave': materia_id_base,
                    'grupos': grupos_teoria
                }

        return formatted_data
    
    def scrap(self) -> None:
        """
        Scrappea los detalles de todas las clases listadas (obtenidas en __init__).
        Realiza un POST por cada clase para obtener su información detallada.
        Los resultados formateados se almacenan en `self.clases` y la lista de profesores en `self.profesores`.
        """
        if not self.listaClases:
            logger.warning("No hay lista de clases para scrapear. El scrapeo detallado se saltará.")
            self.clases = {}
            self.profesores = []
            return

        logger.info(f"Iniciando scrapeo detallado de {len(self.listaClases)} clases desde {self.formURL}...")

        raw_data_por_clase: List[Optional[Dict[str, Dict[str, Any]]]] = []
        for nombre_clase_en_dropdown in self.listaClases:
            payload = {"s": self.clavePeriodo, "txt_materia": nombre_clase_en_dropdown}
            logger.debug(f"Solicitando información para: '{nombre_clase_en_dropdown}' con payload: {payload}")

            try:
                response = self.session.post(self.formURL, data=payload, timeout=utils.DEFAULT_TIMEOUT)
                response.raise_for_status()

                info_clase_html = response.text
                # Verificar si el HTML es inesperadamente corto o indica un error no HTTP
                if len(info_clase_html) < 200: # Umbral arbitrario, Grace a veces regresa páginas casi vacías
                    logger.warning(f"HTML recibido para '{nombre_clase_en_dropdown}' es muy corto (longitud: {len(info_clase_html)}). Podría estar vacío o ser una página de error no estándar.")

                grupo_info = self._getClaseInfo(info_clase_html)
                if grupo_info:
                    raw_data_por_clase.append(grupo_info)
                else:
                    logger.warning(f"No se obtuvo información de grupos para la clase: '{nombre_clase_en_dropdown}'. HTML recibido:\n{info_clase_html[:500]}...") # Loggear inicio del HTML
            except requests.exceptions.HTTPError as e:
                logger.error(f"Error HTTP solicitando datos para '{nombre_clase_en_dropdown}': {e.response.status_code} - {e.response.reason}")
            except requests.exceptions.Timeout:
                logger.error(f"Timeout solicitando datos para '{nombre_clase_en_dropdown}'.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error de red solicitando datos para '{nombre_clase_en_dropdown}': {e}")
            except Exception as e:
                logger.error(f"Error inesperado procesando '{nombre_clase_en_dropdown}': {e}", exc_info=True)

        self.clases = self._formateaClases(raw_data_por_clase)
        logger.info(f"Procesamiento detallado completado. Total de materias (teoría/lab) formateadas: {len(self.clases)}.")

        # Extracción de profesores
        set_profesores = set()
        for clase_info_dict in raw_data_por_clase: # Iterar sobre la lista de diccionarios (uno por POST)
            if clase_info_dict: # Cada dict es {"grupo_num": data_grupo}
                for data_grupo in clase_info_dict.values(): # Iterar sobre los datos de cada grupo
                    prof_name = data_grupo.get('prof')
                    if prof_name and isinstance(prof_name, str) and prof_name.strip():
                        set_profesores.add(prof_name.strip())

        self.profesores = sorted(list(set_profesores))
        logger.info(f"Se encontraron {len(self.profesores)} profesores únicos en los datos de Grace.")


if __name__ == "__main__":
    # Configurar logging para la prueba
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(message)s'
    )

    logger.info("Ejecutando GraceScrapper en modo de prueba (auto-descubrimiento)...")
    try:
        g_scraper = GraceScrapper()
        # Para probar con URLs/clave específicas (ejemplo, pueden estar desactualizadas):
        # g_scraper = GraceScrapper(
        #     dropDownURL="https://itaca2.itam.mx:8443/b9prod/edsup/BWZKSENP.P_Horarios1?s=2595",
        #     formURL="https://itaca2.itam.mx:8443/b9prod/edsup/BWZKSENP.P_Horarios2",
        #     clavePeriodo = "2595"
        # )
        
        logger.info(f"Scrapper inicializado. Dropdown URL: {g_scraper.dropDownURL}")
        logger.info(f"Periodo: {g_scraper.periodo}, Clave Periodo: {g_scraper.clavePeriodo}")
        logger.info(f"Primeras 5 clases en dropdown: {g_scraper.listaClases[:5] if g_scraper.listaClases else 'Ninguna'}")

        if g_scraper.listaClases: # Solo scrapear si hay clases
            g_scraper.scrap()

            logger.info(f"Scrapeo detallado completado. Total de materias (teoría/lab) procesadas: {len(g_scraper.clases)}")
            if g_scraper.clases:
                # Loguear un ejemplo de los datos de una materia
                first_class_key = list(g_scraper.clases.keys())[0]
                logger.info(f"Ejemplo de materia: Clave='{first_class_key}', Nombre='{g_scraper.clases[first_class_key]['nombre']}'")
                # Para ver más detalle (puede ser muy largo):
                # logger.debug(f"Datos completos de '{first_class_key}': {g_scraper.clases[first_class_key]}")

            logger.info(f"Total de profesores únicos encontrados: {len(g_scraper.profesores)}")
            if g_scraper.profesores:
                 logger.info(f"Algunos profesores (primeros 5): {g_scraper.profesores[:5]}")
        else:
            logger.info("No se encontraron clases en el dropdown, el scrapeo detallado no se ejecutará.")

    except GraceScrapperException as e:
        logger.error(f"Error crítico durante la ejecución de GraceScrapper: {e}", exc_info=True)
    except Exception as e: # Otros errores inesperados
        logger.error(f"Error inesperado no manejado en la prueba de GraceScrapper: {e}", exc_info=True)
