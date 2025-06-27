import json
import re
import logging
from typing import Dict, List, Any, Optional

import utils

logger = logging.getLogger(__name__)

class MisProfesScrapper:
    """
    Clase que maneja el scrapeo de datos de profesores del ITAM desde MisProfes.com.
    Extrae una lista de profesores y sus evaluaciones.
    """
    BASE_URL_PROFE_PROFILE = "https://www.misprofesores.com/profesores/"
    DATASET_VAR_NAME = "var dataSet = " # Used to find the start of the JSON data in HTML

    def __init__(self, itam_misprofes_url: str):
        """
        Constructor.

        Parámetros:
        ----------
        itam_misprofes_url: str
            URL de la página de MisProfes.com designada al ITAM.
        """
        self.itam_misprofes_url = itam_misprofes_url
        self.data: Dict[str, Dict[str, Any]] = {} # Stores {full_name: data}

    def _sanitize_name_for_url(self, name_part: str) -> str:
        """
        Limpia y formatea una parte del nombre (nombre o apellido) para usar en una URL.
        Elimina caracteres no alfanuméricos (excepto espacios que luego son guiones),
        maneja espacios extra, y convierte espacios a guiones.
        """
        if not isinstance(name_part, str):
            logger.warning(f"Se esperaba string para _sanitize_name_for_url, se obtuvo {type(name_part)}. Se convierte a str.")
            name_part = str(name_part)

        s = name_part.strip()
        # 1. Quitar caracteres problemáticos (paréntesis, saltos de línea, backslashes)
        s = s.replace("(", "").replace(")", "")
        s = s.replace("\n", "").replace("\r", "")
        s = s.replace("\\", "")

        # 2. Eliminar caracteres no alfanuméricos (excepto espacios, que se manejarán después)
        #    La regex original "/[^a-zA-Z0-9\s]/" significaba "no (^) alfanum o espacio".
        s = re.sub(r'[^a-zA-Z0-9\sÁÉÍÓÚÑÜáéíóúñü]', '', s, flags=re.UNICODE) # Permitir acentos y ñ/ü temporalmente

        # 3. Normalizar espacios y guiones alrededor de espacios
        s = s.replace(" -", "-").replace("- ", "-")
        s = re.sub(r'\s+', ' ', s) # Reemplazar múltiples espacios con uno solo

        # 4. Convertir espacios a guiones
        s = s.replace(" ", "-")

        # 5. Eliminar guiones duplicados que podrían haberse formado
        s = re.sub(r'-+', '-', s)

        # 6. Quitar guiones al inicio o final, si los hay
        s = s.strip('-')

        # Opcional: convertir a minúsculas si las URLs son case-insensitive,
        # pero las URLs de MisProfes parecen ser case-sensitive para nombres.
        # s = s.lower()
        return s

    def _construct_profe_url(self, nombre: str, apellido: str, profe_id: str) -> str:
        """Construye la URL del perfil de un profesor."""
        sanitized_nombre = self._sanitize_name_for_url(nombre)
        sanitized_apellido = self._sanitize_name_for_url(apellido)
        return f"{self.BASE_URL_PROFE_PROFILE}{sanitized_nombre}-{sanitized_apellido}_{profe_id}"

    def scrap(self) -> None:
        """
        Obtiene y parsea los datos de los profesores desde la URL del ITAM en MisProfes.com.
        Los datos parseados se almacenan en `self.data`.
        Levanta `utils.NetworkError` o `ValueError` si la página o los datos no se pueden obtener/parsear.
        """
        logger.info(f"Iniciando scrapeo de MisProfes desde: {self.itam_misprofes_url}")
        try:
            html = utils.getHTML(self.itam_misprofes_url)
        except utils.NetworkError as e:
            logger.error(f"Error de red obteniendo datos de MisProfes: {e}")
            raise  # Re-raise para que el llamador lo maneje

        try:
            # Buscar el inicio del JSON de forma más robusta
            match_json = re.search(r"var dataSet\s*=\s*(\[.*?\]);", html, re.DOTALL | re.IGNORECASE)
            if not match_json:
                logger.error("No se encontró el bloque de datos 'var dataSet = [...]' en el HTML.")
                raise ValueError("Formato de HTML inesperado: 'dataSet' no encontrado.")

            json_str = match_json.group(1)
            raw_profes_data = json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON de MisProfes: {e}")
            raise ValueError(f"Error de parseo JSON: {e}")
        except ValueError as e: # Para el ValueError que levantamos nosotros
            raise
        except Exception as e: # Captura general para otros errores inesperados durante el parseo
            logger.error(f"Error inesperado parseando HTML de MisProfes: {e}")
            raise ValueError(f"Error inesperado de parseo: {e}")


        profesores_scraped: Dict[str, Dict[str, Any]] = {}
        for p_data in raw_profes_data:
            # Asumimos que 'n' es nombre, 'a' es apellido, 'i' es id, 'c' es calificación, 'm' es número de materias/opiniones
            nombre_completo = f"{p_data.get('n', '')} {p_data.get('a', '')}".strip()
            if not nombre_completo:
                logger.warning(f"Profesor saltado por no tener nombre o apellido: {p_data}")
                continue

            prof_id = p_data.get('i')
            if not prof_id:
                logger.warning(f"Profesor '{nombre_completo}' saltado por no tener ID: {p_data}")
                continue

            profesores_scraped[nombre_completo] = {
                'calificacion_general': p_data.get('c'), # Podría ser None o string vacío
                'num_evaluaciones': p_data.get('m'),   # Podría ser None o string vacío
                'id_misprofes': prof_id,
                'nombre_misprofes': nombre_completo, # Guardar el nombre como aparece en MisProfes
                'link_misprofes': self._construct_profe_url(p_data.get('n', ''), p_data.get('a', ''), prof_id)
            }
        
        self.data = profesores_scraped
        logger.info(f"Se scrappearon {len(self.data)} profesores de MisProfes.")
        if not self.data:
            logger.warning("No se extrajo ningún dato de profesor de MisProfes.")


    def match_profesores(self, grace_profes_nombres: List[str], match_threshold: float) -> Dict[str, Dict[str, Any]]:
        """
        Compara una lista de nombres de profesores (obtenidos de Grace)
        con los datos de MisProfes (en `self.data`).
        Regresa un diccionario donde las claves son los nombres de Grace y los valores
        son los datos correspondientes de MisProfes si el match supera `match_threshold`.
        """
        if not self.data:
            logger.warning("No hay datos de MisProfes cargados para hacer matching. Ejecute scrap() primero.")
            return {}

        logger.info(f"Iniciando matching de {len(grace_profes_nombres)} profesores de Grace con {len(self.data)} de MisProfes.")

        matched_data: Dict[str, Dict[str, Any]] = {}
        for nombre_grace in grace_profes_nombres:
            best_match_score = -1.0
            best_misprofes_entry: Optional[Dict[str, Any]] = None

            for nombre_misprofes, data_misprofes in self.data.items():
                # Usar utils.levenshtein_ratio o utils.levenshteinSimilarity
                # La firma de levenshtein_ratio fue (a,b), levenshteinSimilarity es (s0,s1)
                # Ambas normalizan y comparan strings. ratio es custom, Similarity es más estándar.
                # El plan original indicaba que levenshtein_ratio se usaba.
                similarity = utils.levenshtein_ratio(nombre_grace, nombre_misprofes)

                if similarity > best_match_score:
                    best_match_score = similarity
                    best_misprofes_entry = data_misprofes

            if best_misprofes_entry and best_match_score >= match_threshold:
                # Formatear la salida como se hacía antes
                calif_str = best_misprofes_entry.get('calificacion_general')
                num_eval_str = best_misprofes_entry.get('num_evaluaciones')

                try:
                    general_rating = float(calif_str) if calif_str and calif_str.strip() else 0.0
                    num_ratings = int(float(num_eval_str)) if num_eval_str and num_eval_str.strip() else 0
                except ValueError:
                    logger.warning(f"No se pudo convertir rating '{calif_str}' o num_eval '{num_eval_str}' para {best_misprofes_entry.get('nombre_misprofes')}")
                    general_rating = 0.0
                    num_ratings = 0

                matched_data[nombre_grace] = {
                    "link": best_misprofes_entry.get('link_misprofes', ''),
                    "general": general_rating,
                    "n": num_ratings
                }

        num_grace_profes = len(grace_profes_nombres)
        percentage_matched = (len(matched_data) / num_grace_profes * 100) if num_grace_profes > 0 else 0
        logger.info(
            f"Se ligaron {len(matched_data)} de {num_grace_profes} profesores de Grace "
            f"({percentage_matched:.2f}%) a evaluaciones de MisProfes (umbral: {match_threshold*100}%)."
        )
        return matched_data