import json
import time
import sys
import logging
import os
from typing import Dict, Any, List, Optional, Union

# Importaciones de módulos del proyecto
from graceScrapper import GraceScrapper, GraceScrapperException
from misProfesScrapper import MisProfesScrapper
# GraceScrapperSecureArea y sus excepciones específicas
from graceScrapperSecure import GraceScrapperSecureArea, GraceSecureLoginError, GraceSecureScrapperError
# COURSE_SEARCH_URL es una constante en graceScrapperSecure, podría ser importada o definida aquí
from graceScrapperSecure import COURSE_SEARCH_URL as GRACE_SECURE_COURSE_URL

from utils import claveToDepto, periodoMasReciente, dic2js, NetworkError

# --- Configuración de Logging ---
# Configurar logging para que también escriba a un archivo
log_file_path = os.path.join(os.path.dirname(__file__), 'update_process.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout), # Log a consola
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8') # Log a archivo
    ]
)
logger = logging.getLogger(__name__)

# --- Constantes de Configuración ---
CREDS_FILE = os.path.join(os.path.dirname(__file__), "creds.json")
DATA_FILE_INDEX = "js/datos/datos_index.js" # Asumiendo que corre desde la raíz del proyecto
PROFESORES_DATA_FILE = "js/datos/datos_profesores.js"
MISPROFES_ITAM_URL = "https://www.misprofesores.com/escuelas/ITAM-Instituto-Tecnologico-Autonomo-de-Mexico_1003"
PROFESORES_MATCH_RATE = 0.9 # Umbral para el matching de profesores
SCRAP_MISPROFES_LIVE = True # Controla si se scrapea MisProfes en vivo o se usa buffer
MISPROFES_BUFFER_FILE = os.path.join(os.path.dirname(__file__), "misProfesData.json")


# Variable global para almacenar datos de MisProfes, usada por profesoresData
# Esto no es ideal, pero mantiene la estructura original.
# Sería mejor pasar misProfesData como argumento a profesoresData.
global_misProfesData: Dict[str, Any] = {}


def load_credentials() -> Optional[Dict[str, str]]:
    """Carga las credenciales desde el archivo o argumentos de línea de comandos."""
    if len(sys.argv) == 3:
        logger.info("Usando credenciales de SID y PIN desde argumentos de línea de comandos.")
        return {'sid': sys.argv[1], 'PIN': sys.argv[2]}
    elif len(sys.argv) == 1:
        logger.info(f"Intentando cargar credenciales desde: {CREDS_FILE}")
        try:
            with open(CREDS_FILE, "r", encoding="utf-8") as f:
                creds = json.load(f)
            if 'sid' not in creds or 'PIN' not in creds:
                logger.error("'sid' o 'PIN' no encontrados en el archivo de credenciales.")
                return None
            return creds
        except FileNotFoundError:
            logger.error(f"Archivo de credenciales no encontrado: {CREDS_FILE}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error decodificando JSON del archivo de credenciales: {CREDS_FILE}")
            return None
    else:
        logger.error("Uso incorrecto de argumentos. Proporcione SID y PIN o ninguno para usar creds.json.")
        return None

def initialize_grace_scrapers(login_data: Dict[str, str]) -> Tuple[Optional[GraceScrapperSecureArea], Optional[GraceScrapper]]:
    """Intenta inicializar ambos scrapers de Grace."""
    secure_scraper = None
    non_secure_scraper = None

    try:
        logger.info("Inicializando GraceScrapperSecureArea...")
        secure_scraper = GraceScrapperSecureArea(login_data['sid'], login_data['PIN'])
        logger.info(f"GraceScrapperSecureArea inicializado. Periodo: {secure_scraper.periodo}")
    except (GraceSecureLoginError, GraceSecureScrapperError, NetworkError) as e:
        logger.warning(f"Fallo al inicializar GraceScrapperSecureArea: {e}. Se intentará con NonSecure.")
    except Exception as e: # Captura general para errores inesperados en __init__
        logger.error(f"Error inesperado inicializando GraceScrapperSecureArea: {e}", exc_info=True)

    try:
        logger.info("Inicializando GraceScrapper (no seguro)...")
        non_secure_scraper = GraceScrapper()
        logger.info(f"GraceScrapper (no seguro) inicializado. Periodo: {non_secure_scraper.periodo}")
    except (GraceScrapperException, NetworkError) as e: # GraceScrapperException es la que levanta GraceScrapper
        logger.warning(f"Fallo al inicializar GraceScrapper (no seguro): {e}.")
    except Exception as e:
        logger.error(f"Error inesperado inicializando GraceScrapper (no seguro): {e}", exc_info=True)

    return secure_scraper, non_secure_scraper

def select_grace_instance(secure: Optional[GraceScrapperSecureArea], non_secure: Optional[GraceScrapper]) -> Tuple[Optional[Union[GraceScrapperSecureArea, GraceScrapper]], bool]:
    """Selecciona la instancia de Grace a usar basado en la disponibilidad y el período más reciente."""
    grace_instance = None
    is_secure_mode = False

    if secure and secure.periodo and non_secure and non_secure.periodo:
        logger.info(f"Ambos scrapers de Grace disponibles. Secure: {secure.periodo}, NonSecure: {non_secure.periodo}")
        latest_period = periodoMasReciente([secure.periodo, non_secure.periodo])
        if non_secure.periodo == latest_period: # Prefer non-secure if periods match or non-secure is newer
            logger.info("Tomando GraceScrapper (no seguro) como fuente de datos (período más reciente o igual).")
            grace_instance = non_secure
            is_secure_mode = False
        else:
            logger.info("Tomando GraceScrapperSecureArea como fuente de datos (período más reciente).")
            grace_instance = secure
            is_secure_mode = True
    elif secure and secure.periodo:
        logger.info("Usando GraceScrapperSecureArea (NonSecure no disponible o sin período).")
        grace_instance = secure
        is_secure_mode = True
    elif non_secure and non_secure.periodo:
        logger.info("Usando GraceScrapper (no seguro) (Secure no disponible o sin período).")
        grace_instance = non_secure
        is_secure_mode = False
    else:
        logger.error("Ninguna instancia de GraceScrapper pudo ser inicializada correctamente con un período válido.")

    return grace_instance, is_secure_mode

def profesoresData(clases_data: Dict[str, Any], misprofes_data_map: Dict[str, Any]) -> Dict[str, Any]:
    """
    Regresa un diccionario de la forma nombre profesor:{'link':,'general':,'n':,'grupos'}
    Para uso en profesores.html.
    """
    profesores_output_map: Dict[str, Any] = {}
    if not clases_data:
        logger.warning("No hay datos de clases para procesar en profesoresData.")
        return profesores_output_map

    for _, info_clase in clases_data.items():
        for grupo_info in info_clase.get('grupos', []):
            profesor_nombre = grupo_info.get('profesor')
            if not profesor_nombre:
                continue

            if profesor_nombre not in profesores_output_map:
                # Si el profesor está en MisProfes, copiar sus datos base
                if profesor_nombre in misprofes_data_map:
                    profesores_output_map[profesor_nombre] = dict(misprofes_data_map[profesor_nombre]) # Copiar
                    profesores_output_map[profesor_nombre]['grupos'] = {}
                else:
                    profesores_output_map[profesor_nombre] = {'grupos': {}}

            nombre_clase_actual = grupo_info.get('nombre')
            if nombre_clase_actual: # Asegurar que el nombre de la clase exista
                if nombre_clase_actual not in profesores_output_map[profesor_nombre]['grupos']:
                    profesores_output_map[profesor_nombre]['grupos'][nombre_clase_actual] = []
                profesores_output_map[profesor_nombre]['grupos'][nombre_clase_actual].append(grupo_info)

    return profesores_output_map

def profesoresPorDepartamento(profesores_map: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Regresa un diccionario de la forma departamento:[lista de profesores].
    Se asume que profesores_map es la salida de profesoresData.
    """
    profes_por_depto: Dict[str, List[str]] = {}
    if not profesores_map: return profes_por_depto

    for profesor_nombre, info_profesor in profesores_map.items():
        grupos_prof = info_profesor.get('grupos', {})
        if not grupos_prof: continue

        # Tomar el departamento de la primera clase listada para ese profesor
        # Esto asume que un profesor usualmente pertenece a un depto principal
        # o que la primera clase es representativa.
        primera_clase_nombre = next(iter(grupos_prof.keys()), None)
        if not primera_clase_nombre: continue

        depto_code = primera_clase_nombre.split('-')[0] # Ej: "ECO-123-Teoria Moderna" -> "ECO"
        depto_nombre = claveToDepto.get(depto_code, "Desconocido")

        if depto_nombre not in profes_por_depto:
            profes_por_depto[depto_nombre] = []
        profes_por_depto[depto_nombre].append(profesor_nombre)

    return profes_por_depto

def mejoresProfesPorDepartamento(profesores_map: Dict[str, Any], n_mejores: int = 10) -> Dict[str, List[str]]:
    """
    Regresa los n mejores profesores (de acuerdo a 'general' de MisProfes)
    por departamento.
    """
    profes_por_depto = profesoresPorDepartamento(profesores_map)
    mejores_por_depto_final: Dict[str, List[str]] = {}

    for depto_nombre, lista_profes_depto in profes_por_depto.items():
        # Sortear por calificación 'general', luego por 'n' (número de evaluaciones) como desempate.
        # Profesores sin 'general' o 'n' se tratan como 0.
        def sort_key(prof_nombre_key: str):
            prof_data = profesores_map.get(prof_nombre_key, {})
            general_rating = prof_data.get('general', 0.0) # Asumir float
            num_ratings = prof_data.get('n', 0) # Asumir int
            return (general_rating, num_ratings)

        lista_profes_depto.sort(key=sort_key, reverse=True)
        mejores_por_depto_final[depto_nombre] = lista_profes_depto[:n_mejores]

    return mejores_por_depto_final


def main():
    """Función principal que orquesta el proceso de actualización."""
    logger.info("==== Iniciando proceso de actualización de datos de Horarios ITAM ====")

    login_credentials = load_credentials()
    if not login_credentials:
        logger.critical("No se pudieron cargar las credenciales. Terminando proceso.")
        sys.exit(1)

    # --- Scrapeo de Grace ---
    logger.info("--- Iniciando Scrapeo de Grace ---")
    secure_g, non_secure_g = initialize_grace_scrapers(login_credentials)
    grace_active_instance, is_secure_mode_active = select_grace_instance(secure_g, non_secure_g)

    if not grace_active_instance or not grace_active_instance.periodo:
        logger.critical("No se pudo obtener una instancia de Grace válida con datos de período. Terminando.")
        sys.exit(1)

    logger.info(f"Instancia de Grace seleccionada: {'Secure' if is_secure_mode_active else 'NonSecure'}")
    logger.info(f"Periodo de Grace activo: {grace_active_instance.periodo}")

    try:
        grace_active_instance.scrap() # Ejecutar el scrapeo detallado
        logger.info("Scrapeo detallado de Grace completado.")
        logger.info(f"Clases obtenidas de Grace: {len(grace_active_instance.clases)}")
        logger.info(f"Profesores obtenidos de Grace: {len(grace_active_instance.profesores)}")
    except Exception as e: # Capturar cualquier error durante el scrapeo de Grace
        logger.critical(f"Error crítico durante el scrapeo detallado de Grace: {e}. Terminando.", exc_info=True)
        sys.exit(1)

    # --- Scrapeo/Carga de MisProfes ---
    logger.info("--- Iniciando Scrapeo/Carga de MisProfes ---")
    global global_misProfesData # Acceder a la variable global
    if SCRAP_MISPROFES_LIVE:
        logger.info(f"Scrapeando MisProfes en vivo desde: {MISPROFES_ITAM_URL}")
        misprofes_scraper = MisProfesScrapper(MISPROFES_ITAM_URL)
        try:
            misprofes_scraper.scrap() # Levanta excepciones si falla
            if grace_active_instance.profesores: # Solo hacer match si hay profesores de Grace
                global_misProfesData = misprofes_scraper.match_profesores(
                    grace_active_instance.profesores,
                    PROFESORES_MATCH_RATE
                )
            else:
                logger.warning("No hay profesores de Grace para hacer match con MisProfes.")
                global_misProfesData = {}

            # Guardar en buffer
            try:
                with open(MISPROFES_BUFFER_FILE, "w+", encoding="utf-8") as f:
                    json.dump(global_misProfesData, f, indent=2, ensure_ascii=False)
                logger.info(f"Datos de MisProfes guardados en buffer: {MISPROFES_BUFFER_FILE}")
            except IOError as e:
                logger.error(f"Error guardando buffer de MisProfes: {e}")
            except TypeError as e:
                 logger.error(f"Error de tipo serializando MisProfes a JSON: {e}")

        except (NetworkError, ValueError) as e: # Errores durante el scrapeo de MisProfes
            logger.error(f"Error scrapeando MisProfes: {e}. Se intentará cargar desde buffer.")
            SCRAP_MISPROFES_LIVE = False # Forzar carga de buffer si el scrapeo en vivo falla
        except Exception as e:
            logger.error(f"Error inesperado scrapeando MisProfes: {e}. Se intentará cargar desde buffer.", exc_info=True)
            SCRAP_MISPROFES_LIVE = False


    if not SCRAP_MISPROFES_LIVE or not global_misProfesData: # Si no se scrapeó en vivo o falló
        logger.info(f"Cargando datos de MisProfes desde buffer: {MISPROFES_BUFFER_FILE}")
        try:
            with open(MISPROFES_BUFFER_FILE, "r", encoding="utf-8") as f:
                global_misProfesData = json.load(f)
            logger.info(f"Datos de MisProfes cargados exitosamente desde buffer: {len(global_misProfesData)} entradas.")
        except FileNotFoundError:
            logger.error(f"Archivo buffer de MisProfes no encontrado: {MISPROFES_BUFFER_FILE}. No habrá datos de MisProfes.")
            global_misProfesData = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON del buffer de MisProfes: {e}. No habrá datos de MisProfes.")
            global_misProfesData = {}
        except Exception as e:
            logger.error(f"Error inesperado cargando buffer de MisProfes: {e}", exc_info=True)
            global_misProfesData = {}


    # --- Generación de Archivos de Datos ---
    logger.info("--- Generando Archivos de Datos para el Sitio Web ---")
    
    # Datos para index.html
    form_post_url_val = GRACE_SECURE_COURSE_URL if is_secure_mode_active else grace_active_instance.formURL # type: ignore
    dropdown_url_val = "#" if is_secure_mode_active else grace_active_instance.dropDownURL # type: ignore

    datos_index_content = {
        "actualizado": str(time.time() * 1000),
        "periodo": grace_active_instance.periodo,
        "secure": is_secure_mode_active,
        "sGrace": grace_active_instance.clavePeriodo,
        "dropDownUrl": dropdown_url_val,
        "formPostUrl": form_post_url_val,
        "clases": grace_active_instance.clases,
        "misProfesData": global_misProfesData
    }
    try:
        with open(DATA_FILE_INDEX, "w+", encoding="utf-8") as f:
            f.write(dic2js(datos_index_content))
        logger.info(f"Archivo de datos para INDEX generado: {DATA_FILE_INDEX}")
    except IOError as e:
        logger.error(f"Error escribiendo archivo de datos para INDEX ({DATA_FILE_INDEX}): {e}")
    except Exception as e: # Otro error, ej. en dic2js
        logger.error(f"Error inesperado generando datos para INDEX: {e}", exc_info=True)

    # Datos para profesores.html
    # La función profesoresData ahora usa global_misProfesData internamente.
    # Sería mejor refactorizar profesoresData para tomar misprofes_data_map como argumento.
    profesores_map_html = profesoresData(grace_active_instance.clases, global_misProfesData)
    mejores_por_depto_html = mejoresProfesPorDepartamento(profesores_map_html)

    datos_profesores_content = {
        "actualizado": str(time.time() * 1000),
        "periodo": grace_active_instance.periodo,
        "secure": is_secure_mode_active,
        "sGrace": grace_active_instance.clavePeriodo,
        "dropDownUrl": dropdown_url_val,
        "formPostUrl": form_post_url_val,
        "profesores": profesores_map_html,
        "mejoresPorDepto": mejores_por_depto_html
    }
    try:
        with open(PROFESORES_DATA_FILE, "w+", encoding="utf-8") as f:
            f.write(dic2js(datos_profesores_content))
        logger.info(f"Archivo de datos para PROFESORES generado: {PROFESORES_DATA_FILE}")
    except IOError as e:
        logger.error(f"Error escribiendo archivo de datos para PROFESORES ({PROFESORES_DATA_FILE}): {e}")
    except Exception as e:
        logger.error(f"Error inesperado generando datos para PROFESORES: {e}", exc_info=True)

    logger.info("==== Proceso de actualización de datos finalizado ====")

if __name__ == "__main__":
    main()
