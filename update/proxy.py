# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "fastapi",
#     "requests",
#     "uvicorn",
# ]
# ///


from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from graceScrapper import GraceScrapper
import requests # Used for catching requests.exceptions.RequestException
import uvicorn # For running the FastAPI application

app = FastAPI()

# Initialize GraceScrapper once when the FastAPI app starts.
# We'll use a global variable, but in a larger FastAPI app,
# you might use a dependency or an event listener (on_startup).
g: GraceScrapper = None

@app.on_event("startup")
async def startup_event():
    """
    Initializes GraceScrapper when the FastAPI application starts up.
    """
    global g
    try:
        g = GraceScrapper(abiertos=True, verbose=True)
        print("GraceScrapper inicializado correctamente.")
        print(f"Período actual: {g.periodo}, clavePeriodo: {g.clavePeriodo}, URL del formulario: {g.formURL}")

    except Exception as e:
        print(f"ERROR: Fallo al inicializar GraceScrapper al iniciar el servidor: {e}")
        print("El servicio proxy podría no funcionar correctamente hasta que se resuelva esto.")
        g = None # Set g to None if initialization fails

@app.get('/abiertos')
async def proxy_grace(txt_materia: str | None = None):
    """
    Endpoint proxy para obtener información de una clase específica de servicios.itam.mx.
    Parámetro de consulta esperado: txt_materia (ej. MAT-101).
    """
    if not txt_materia:
        raise HTTPException(
            status_code=400,
            detail="Parámetro de consulta 'txt_materia' requerido faltante."
        )

    if g is None:
        raise HTTPException(
            status_code=503,
            detail="Servicio de scraping no disponible. El servidor no pudo inicializar GraceScrapper."
        )

    try:
        clase_info = g.scrap_clase(txt_materia)

        if not clase_info:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró información detallada para la clase '{txt_materia}'. Podría no existir, la estructura de datos en Grace cambió, o es una sección de laboratorio que no se muestra individualmente."
            )
        
    except ValueError as e:
        print(f"Error de validación/lógica en el cliente para '{txt_materia}': {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de clase inválido o clase no reconocida por el scraper: {str(e)}"
        )
    except requests.exceptions.RequestException as e:
        print(f"Error de red/HTTP al hacer scraping de '{txt_materia}': {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Fallo al recuperar información de la clase de servicios.itam.mx. El servicio externo podría no estar disponible temporalmente o ser inaccesible. Detalles: {e}"
        )
    except Exception as e:
        print(f"Ocurrió un error inesperado al hacer scraping de '{txt_materia}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno en el servidor al procesar su solicitud."
        )
    
    # Assuming clase_info is a dictionary where keys are class group identifiers
    # and the user wants a list of these keys.
    # If the user wants the full dict: return JSONResponse(content=clase_info)
    return JSONResponse(content=list(clase_info.keys()))

if __name__ == '__main__':
    # Para ejecutar la aplicación FastAPI, usa Uvicorn:
    # `uvicorn app:app --host 0.0.0.0 --port 5000 --reload`
    # --reload es para desarrollo (recarga automática al cambiar el código)
    uvicorn.run(app, host="0.0.0.0", port=6969)
