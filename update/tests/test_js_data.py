import pytest
import json
import re

from update.utils import periodoValido


@pytest.mark.parametrize("filepath", [
    "js/datos/datos_index.js",
    "js/datos/datos_profesores.js"
])
def test_datos_compartidos(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # regex para cada variable
    re_actualizado = re.search(r'let actualizado="(\d+\.\d+)";', content)
    re_periodo = re.search(r'let periodo="(.*?)";', content)
    re_secure = re.search(r"let secure=(true|false);", content)
    re_sGrace = re.search(r'let sGrace="(\d+)";', content)
    re_dropDownUrl = re.search(r'let dropDownUrl="(.*?)";', content)
    re_formPostUrl = re.search(r'let formPostUrl="(.*?)";', content)

    # Checa presencia
    assert re_actualizado, "Falta variable 'actualizado'."
    assert re_periodo, "Falta variable 'periodo'."
    assert re_secure, "Falta variable 'secure'."
    assert re_sGrace, "Falta variable 'sGrace'."
    assert re_dropDownUrl, "Falta variable 'dropDownUrl'."
    assert re_formPostUrl, "Falta variable 'formPostUrl'."

    # Convierte a tipos
    actualizado = float(re_actualizado.group(1))
    periodo = re_periodo.group(1)
    dropDownUrl = re_dropDownUrl.group(1)
    formPostUrl = re_formPostUrl.group(1)

    # Checa actualizado
    assert actualizado > 0, "El valor de 'actualizado' debe ser positivo."

    # Checa periodo
    assert periodoValido(periodo), f"Periodo '{periodo}' no es valido."

    # Checa urls
    assert dropDownUrl.startswith("https://")
    assert formPostUrl.startswith("https://")


def test_datos_index(filepath="js/datos/datos_index.js"):

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    re_clases = re.search(r"let clases=(\{[\s\S]*?\});", content)
    re_misProfesData = re.search(r"let misProfesData=(\{[\s\S]*?\});", content) 

    assert re_clases, "Falta variable 'clases'."
    assert re_misProfesData, "Falta variable 'misProfesData'."

    # Extrae 'clases' y parsea como JSON
    clases_str = re_clases.group(1)
    try:
        clases = json.loads(clases_str)
    except json.JSONDecodeError:
        raise ValueError("objecto 'clases' no es un JSON valido.")

    # Valida estructura de 'clases'
    assert isinstance(clases, dict)
    assert len(clases) > 0

    for course_code, course_data in clases.items():
        assert isinstance(course_code, str) and len(course_code) > 0, (
            "Course code should be a non-empty string."
        )
        assert "nombre" in course_data
        assert "clave" in course_data
        assert "grupos" in course_data and isinstance(course_data["grupos"], list)

        for group in course_data["grupos"]:
            validar_grupo(group)

    # Valida 'misProfesData'
    misProfesData_str = re_misProfesData.group(1)
    try:
        misProfesData = json.loads(misProfesData_str)
    except json.JSONDecodeError:
        raise ValueError("objecto 'misProfesData' no es un JSON valido.")
    
    assert isinstance(misProfesData, dict)

    for profe, data in misProfesData.items():

        assert isinstance(profe, str) and len(profe) > 0
        assert isinstance(data, dict)
        assert "link" in data and isinstance(data["link"], str) and data["link"].startswith("https://")
        assert "general" in data and isinstance(data["general"], float)
        assert "n" in data and isinstance(data["n"], int)

    print(f"data.js format test PASSED for {filepath}")

def test_datos_profesores(filepath="js/datos/datos_profesores.js"):

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    re_profesores = re.search(r"let profesores=(\{[\s\S]*?\});", content)

    assert re_profesores, "Falta variable 'profesores'."

    # Extrae 'profesores' y parsea como JSON
    profesores_str = re_profesores.group(1)
    try:
        profesores = json.loads(profesores_str)
    except json.JSONDecodeError:
        raise ValueError("objecto 'profesores' no es un JSON valido.")

    # Valida estructura de 'profesores'
    assert isinstance(profesores, dict)
    assert len(profesores) > 0

    for profe, data in profesores.items():
        assert isinstance(profe, str) # and len(profe) > 0 TODO 
        assert isinstance(data, dict)

        # Si esta ligado a misProfes, valida todos los campos
        if "link" in data or "general" in data or "n" in data:
            assert "link" in data and isinstance(data["link"], str) and data["link"].startswith("https://")
            assert "general" in data and isinstance(data["general"], float)
            assert "n" in data and isinstance(data["n"], int)

        assert "grupos" in data and isinstance(data["grupos"], dict) and len(data["grupos"]) > 0

        for clase, listaGrupos in data["grupos"].items():
            assert isinstance(clase, str) and len(clase) > 0
            assert isinstance(listaGrupos, list) and len(listaGrupos) > 0
            for grupo in listaGrupos:
                validar_grupo(grupo)

    print(f"datos_profesores.js format test PASSED for {filepath}")


def validar_grupo(grupo):

    assert isinstance(grupo, dict), "Cada grupo debe ser un diccionario."
    assert "grupo" in grupo and isinstance(grupo["grupo"], str), "El grupo debe tener una clave 'grupo' con un valor de tipo string."
    assert "profesor" in grupo and isinstance(grupo["profesor"], str), "El grupo debe tener una clave 'profesor' con un valor de tipo string."
    assert "dias" in grupo and isinstance(grupo["dias"], list), "El grupo debe tener una clave 'dias' con un valor de tipo lista."
    
    assert len(grupo["dias"]) > 0, "La lista de dias no debe estar vacia."
    for dia in grupo["dias"]:
        assert isinstance(dia, str) and len(dia) == 2, "Cada dia debe ser una cadena de longitud 2."