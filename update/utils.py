import json
import os
import requests
from typing import List, Dict, Any, Tuple, Union # Added for type hinting

# Default timeout for requests
DEFAULT_TIMEOUT = 10  # seconds

claveToDepto: Dict[str, str] = {
    'ACT': 'ACTUARIA Y SEGUROS',
    'ADM': 'ADMINISTRACION',
    'CSO': 'CIENCIA POLITICA',
    'COM': 'COMPUTACION',
    'CON': 'CONTABILIDAD',
    'CEB': 'CTRO DE ESTUDIO DEL BIENESTAR',
    'DER': 'DERECHO',
    'ECO': 'ECONOMIA',
    'EST': 'ESTADISTICA',
    'EGN': 'ESTUDIOS GENERALES',
    'EIN': 'ESTUDIOS INTERNACIONALES',
    'IIO': 'ING. INDUSTRIAL Y OPERACIONES',
    'CLE': 'LENGUAS (CLE)',
    'LEN': 'LENGUAS (LEN)',
    'MAT': 'MATEMATICAS',
    'SDI': 'SISTEMAS DIGITALES'
}

class NetworkError(Exception):
    """Custom exception for network-related errors."""
    pass

def getHTML(url: str, timeout: int = DEFAULT_TIMEOUT, verify_ssl: bool = True) -> str:
    """
    Regresa el contenido HTML del url.
    Utiliza requests.get() y maneja errores comunes.
    """
    try:
        response = requests.get(url, timeout=timeout, verify=verify_ssl)
        response.raise_for_status()  # Levanta HTTPError para respuestas 4xx/5xx
        # requests uses apparent_encoding if charset header is not set.
        # Using response.text handles decoding.
        # If specific encoding issues arise, one might need:
        # html = response.content.decode('utf-8', 'replace')
        return response.text
    except requests.exceptions.HTTPError as e:
        # Specific HTTP errors (4xx, 5xx)
        raise NetworkError(f"Error HTTP obteniendo {url}: {e.response.status_code} - {e}")
    except requests.exceptions.ConnectionError as e:
        # Errors like DNS failure, refused connection
        raise NetworkError(f"Error de conexión obteniendo {url}: {e}")
    except requests.exceptions.Timeout as e:
        # Request timed out
        raise NetworkError(f"Timeout obteniendo {url}: {e}")
    except requests.exceptions.RequestException as e:
        # Catch-all for other requests issues (e.g., too many redirects)
        raise NetworkError(f"Error obteniendo {url}: {e}")


def descargaArchivo(path: str, url: str, timeout: int = DEFAULT_TIMEOUT, verify_ssl: bool = True) -> None:
    """
    Intenta descargar el archivo en url en el directorio local path.
    Si el directorio no existe lo crea. Levanta error si no se encuentra o hay problemas.
    """
    parent_dir = os.path.dirname(path)
    if parent_dir: # Only create if parent_dir is not empty (e.g. not saving in current dir)
        os.makedirs(parent_dir, exist_ok=True)

    try:
        response = requests.get(url, timeout=timeout, verify=verify_ssl, stream=True) # stream=True for large files
        response.raise_for_status() # Levanta HTTPError para respuestas 4xx/5xx

        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    except requests.exceptions.HTTPError as e:
        raise NetworkError(f"Error HTTP descargando {url}: {e.response.status_code} - {e}")
    except requests.exceptions.ConnectionError as e:
        raise NetworkError(f"Error de conexión descargando {url}: {e}")
    except requests.exceptions.Timeout as e:
        raise NetworkError(f"Timeout descargando {url}: {e}")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Error descargando {url}: {e}")
    except IOError as e:
        raise NetworkError(f"Error de I/O guardando archivo {path} de {url}: {e}")


def replace_latin_chars(text_input: str) -> str:
    """
    Reemplaza letras con acentos por letras sin acentos y ñ con n en text_input.
    """
    # Fixed: strings are immutable, must reassign. str_input -> text_input
    translation_map = {
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u"
    }
    for original, replacement in translation_map.items():
        text_input = text_input.replace(original, replacement)
    return text_input

def levenshtein(s0: str, s1: str) -> float:
    """
    Calculates the levenshtein distance.
    Taken from https://github.com/luozhouyang/python-string-similarity/blob/master/strsimpy/levenshtein.py
    """
    if s0 == s1:
        return 0.0
    if len(s0) == 0:
        return len(s1)
    if len(s1) == 0:
        return len(s0)

    v0 = [0] * (len(s1) + 1)
    v1 = [0] * (len(s1) + 1)

    for i in range(len(v0)):
        v0[i] = i

    for i in range(len(s0)):
        v1[0] = i + 1
        for j in range(len(s1)):
            cost = 1
            if s0[i] == s1[j]:
                cost = 0
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0, v1 = v1, v0

    return v0[len(s1)]

def levenshtein_ratio(s1: str, s2: str) -> float: # Renamed params for clarity
    """
    Calculates a custom ratio based on character comparison.
    Note: This is a custom implementation. Behavior might differ from standard libraries.
    """
    s1_lower = s1.lower().strip()
    s2_lower = s2.lower().strip()

    edits_away = 0
    len_s1 = len(s1_lower)
    len_s2 = len(s2_lower)

    # Iterate over the shorter string length if strings are different lengths
    # or up to len_s1 if they are of the same length or s1 is shorter.
    # The original code iterated up to len(a) (s1_lower here).
    # Penalize length difference directly.
    edits_away += abs(len_s1 - len_s2)

    for i in range(min(len_s1, len_s2)):
        if s1_lower[i] != s2_lower[i]:
            edits_away += 1

    # Original calculation: ratio=((len(a)+len(b)) - edits_away) / (len(a)+len(b))
    # This can be problematic if len_s1 + len_s2 is 0.
    denominator = len_s1 + len_s2
    if denominator == 0:
        return 1.0  # Both strings are empty, considered identical

    # The original ratio calculation could result in negative values if edits_away is large.
    # A similarity ratio should ideally be between 0 and 1.
    # Let's ensure edits_away does not exceed denominator for a sensible ratio.
    # A common approach for similarity: (L1 + L2 - D) / (L1 + L2)
    # where D is Levenshtein distance. This custom one is different.
    # Clamping similarity to be >= 0.
    similarity = (denominator - edits_away) / denominator
    return max(0.0, similarity)


def levenshteinSimilarity(s0: str, s1: str) -> float:
    """
    Returns the normalized Levenshtein similarity.
    Similarity = 1 - (LevenshteinDistance / MaxLength)
    """
    len_s0 = len(s0)
    len_s1 = len(s1)

    m = max(len_s0, len_s1)
    if m == 0:
        return 1.0  # Both strings are empty

    dist = levenshtein(s0, s1)
    return 1.0 - (dist / m)

def periodoValido(periodo: str) -> bool:
    """
    Valida si una cadena de periodo tiene el formato esperado
    (e.g., 'PRIMAVERA 2022 LICENCIATURA').
    """
    parts = periodo.split(' ')
    if len(parts) != 3:
        return False

    sem, yr_str, tipo = parts
    valid_sems = ['PRIMAVERA', 'VERANO', 'OTOÑO']

    if tipo != "LICENCIATURA" or sem not in valid_sems or not yr_str.isnumeric():
        return False
    return True

def rankPeriodo(periodo_str: str) -> int:
    """
    Asigna un valor numérico a una cadena de periodo para facilitar el ordenamiento.
    Ej. 'OTOÑO 2022 LICENCIATURA'.
    """
    if periodo_str.count(' ') != 2:
        raise ValueError(f"Formato de periodo inválido: '{periodo_str}'. Debe ser como 'SEMESTRE AÑO TIPO'.")

    sem, yr_str, tipo = periodo_str.split()

    periodos_orden = ['PRIMAVERA', 'VERANO', 'OTOÑO']
    if sem not in periodos_orden or tipo != "LICENCIATURA" or not yr_str.isnumeric():
        raise ValueError(f"Componentes de periodo inválidos: '{periodo_str}'.")

    opOffset = periodos_orden.index(sem)
    year = int(yr_str)
    return 10 * year + opOffset # Prioritizes year, then semester part


def periodoMasReciente(periodos: List[str]) -> str:
    """
    Dada una lista de cadenas de periodo, regresa la más reciente.
    """
    if not periodos:
        raise ValueError("La lista de periodos no puede estar vacía.")
    return max(periodos, key=rankPeriodo)

def dic2js(data_dict: Dict[str, Any]) -> str: # Renamed param for clarity
    """
    Convierte un diccionario de Python a una cadena de declaraciones 'let' en JavaScript.
    """
    js_lines: List[str] = []
    for key, value in data_dict.items():
        # Ensure key is a valid JS identifier (simple check)
        if not key.isidentifier():
            # Consider logging a warning or raising an error for invalid keys
            # For now, skip or replace invalid characters if necessary
            print(f"Warning: La clave '{key}' podría no ser un identificador JS válido.")

        if isinstance(value, str):
            # Escape backticks, newlines, and quotes properly for JS string template
            js_value = value.replace('\\', '\\\\').replace('`', '\\`').replace('"', '\\"').replace('\n', '\\n')
            js_lines.append(f'let {key} = "{js_value}";')
        else:
            # For numbers, booleans, arrays, objects
            js_lines.append(f'let {key} = {json.dumps(value, indent=2)};')
    return "\n".join(js_lines) + "\n" # Add trailing newline for cleaner files


if __name__ == "__main__":
    # Example usage of periodoMasReciente
    print(
        "Ejemplo de periodoMasReciente:",
        periodoMasReciente(['PRIMAVERA 2024 LICENCIATURA', 'OTOÑO 2023 LICENCIATURA'])
    )
    # Example of dic2js with a potentially problematic key
    # test_dict = {"actualizado": 123, "data-value": "test", "anotherKey": "value"}
    # print("\nEjemplo de dic2js:")
    # print(dic2js(test_dict))