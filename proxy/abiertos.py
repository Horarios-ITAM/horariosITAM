# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4",
#     "fastapi",
#     "requests",
#     "uvicorn",
# ]
# ///

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from graceScrapper import GraceScrapper
import requests  # Used for catching requests.exceptions.RequestException
import uvicorn  # For running the FastAPI application
import os
import json
import threading
import datetime
from collections import defaultdict
from html import escape as _esc

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ["https://horariositam.com"], # Allow only this origin
    allow_credentials=True,  # Allow cookies, authorization headers, etc.
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

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
        print(
            f"Período actual: {g.periodo}, clavePeriodo: {g.clavePeriodo}, URL del formulario: {g.formURL}"
        )

    except Exception as e:
        print(f"ERROR: Fallo al inicializar GraceScrapper al iniciar el servidor: {e}")
        print(
            "El servicio proxy podría no funcionar correctamente hasta que se resuelva esto."
        )
        g = None  # Set g to None if initialization fails

    # Genera el snapshot diario de grupos abiertos/cerrados en segundo plano para
    # NO bloquear el arranque del servidor (el scrape puede tardar). El reinicio
    # diario del proxy es lo que da la cadencia; no hace falta cron ni timers.
    if g is not None:
        threading.Thread(
            target=generate_snapshot, name="snapshot", daemon=True
        ).start()


@app.get("/abiertos")
async def proxy_grace(txt_materia: str | None = None):
    """
    Endpoint proxy para obtener información de una clase específica de servicios.itam.mx.
    Parámetro de consulta esperado: txt_materia (ej. MAT-101).
    """
    if not txt_materia:
        raise HTTPException(
            status_code=400,
            detail="Parámetro de consulta 'txt_materia' requerido faltante.",
        )

    if g is None:
        raise HTTPException(
            status_code=503,
            detail="Servicio de scraping no disponible. El servidor no pudo inicializar GraceScrapper.",
        )

    try:
        clase_info = g.scrap_clase(txt_materia)

        if not clase_info:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró información detallada para la clase '{txt_materia}'. Podría no existir, la estructura de datos en Grace cambió, o es una sección de laboratorio que no se muestra individualmente.",
            )

    except HTTPException:
        # Dejar pasar las HTTPException que levantamos a propósito (p. ej. 404).
        # Si no, el `except Exception` de abajo las atraparía y las convertiría en 500.
        raise
    except ValueError as e:
        print(f"Error de validación/lógica en el cliente para '{txt_materia}': {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de clase inválido o clase no reconocida por el scraper: {str(e)}",
        )
    except requests.exceptions.RequestException as e:
        print(f"Error de red/HTTP al hacer scraping de '{txt_materia}': {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Fallo al recuperar información de la clase de servicios.itam.mx. El servicio externo podría no estar disponible temporalmente o ser inaccesible. Detalles: {e}",
        )
    except Exception as e:
        print(f"Ocurrió un error inesperado al hacer scraping de '{txt_materia}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno en el servidor al procesar su solicitud.",
        )

    # Assuming clase_info is a dictionary where keys are class group identifiers
    # and the user wants a list of these keys.
    # If the user wants the full dict: return JSONResponse(content=clase_info)
    return JSONResponse(content=list(clase_info.keys()))


@app.get("/ver", response_class=HTMLResponse)
async def ver_datos(txt_materia: str | None = None):
    if not txt_materia:
        raise HTTPException(
            status_code=400,
            detail="Parámetro de consulta 'txt_materia' requerido faltante.",
        )
    if g is None:
        raise HTTPException(
            status_code=503,
            detail="Servicio de scraping no disponible. El servidor no pudo inicializar GraceScrapper.",
        )

    try:
        resp = requests.post(
            url=g.formURL,
            data={"s": g.clavePeriodo, "txt_materia": txt_materia},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Fallo al recuperar HTML de servicios.itam.mx: {e}",
        )

    # Banner que deja claro que esto es un proxy de servicios.itam.mx,
    # no la página oficial. Se inserta justo después de <body>.
    banner = (
        '<div style="position:sticky;top:0;z-index:99999;background:#b30000;'
        'color:#fff;font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        'line-height:1.4;padding:10px 16px;text-align:center;'
        'box-shadow:0 2px 6px rgba(0,0,0,0.3);">'
        '⚠️ Estás viendo una copia (proxy) de '
        '<strong>servicios.itam.mx</strong> servida por '
        '<strong>horariosITAM</strong>. Los datos podrían estar desactualizados. '
        'Navega manualmente desde '
        '<a href="https://servicios.itam.mx" target="_blank" rel="noopener" '
        'style="color:#fff;text-decoration:underline;">Servicios ITAM</a> '
        'para confirmar info importante.'
        '</div>'
    )

    html = resp.text
    lower = html.lower()
    idx = lower.find("<body")
    if idx != -1:
        # Insertar después de la etiqueta <body ...> de apertura
        body_end = html.find(">", idx)
        if body_end != -1:
            html = html[: body_end + 1] + banner + html[body_end + 1 :]
        else:
            html = banner + html
    else:
        html = banner + html

    return HTMLResponse(content=html, status_code=200)


# ---------------------------------------------------------------------------
# Dashboard de grupos abiertos / cerrados (snapshot diario por periodo y depto)
# ---------------------------------------------------------------------------
# Idea: el universo de grupos OFRECIDOS casi no cambia dentro de un periodo, así
# que se scrapea completo una sola vez (abiertos=False) y se cachea en
# catalog_<clave>.json. Cada día, al reiniciar, solo scrapeamos los grupos
# ABIERTOS (set ligero) y los comparamos contra el catálogo para sacar cerrados.
# El resultado se guarda como snapshots/<fecha>.json para poder consultarlo luego.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")

# Estado de la última generación de snapshot (se muestra en el dashboard).
snapshot_status = {"state": "idle", "detail": ""}


def _dept(nombre: str) -> str:
    """Depto = prefijo antes del primer '-' (e.g. 'COM-14113-...' -> 'COM')."""
    return nombre.split("-", 1)[0].strip()


def _catalog_path(clave: str) -> str:
    return os.path.join(BASE_DIR, f"catalog_{clave}.json")


def _scrape_groups(scrapper, nombres) -> dict:
    """Para cada clase regresa la lista de claves de grupo que ve el scrapper.
    Con abiertos=False son todos los grupos; con abiertos=True solo los abiertos.
    Las clases que fallan se omiten (se registra el error)."""
    result = {}
    for nombre in nombres:
        try:
            info = scrapper.scrap_clase(nombre)
            result[nombre] = list(info.keys()) if info else []
        except Exception as e:
            print(f"[snapshot] Error scrapeando '{nombre}': {e}")
    return result


def build_catalog(clave: str, periodo: str) -> dict:
    """Scrape COMPLETO (abiertos=False) del universo de grupos ofrecidos.
    Es la parte cara: se hace una vez por periodo y se cachea."""
    print("[snapshot] Construyendo catálogo (scrape completo, abiertos=False)...")
    full = GraceScrapper(abiertos=False, verbose=False)
    classes = _scrape_groups(full, full.listaClases)
    catalog = {
        "clave": clave,
        "periodo": periodo,
        "scraped_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "classes": classes,
    }
    with open(_catalog_path(clave), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"[snapshot] Catálogo construido: {len(classes)} clases ofrecidas.")
    return catalog


def load_catalog(clave: str):
    """Lee el catálogo cacheado si existe y corresponde al periodo actual."""
    path = _catalog_path(clave)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            cat = json.load(f)
        return cat if cat.get("clave") == clave else None
    except Exception as e:
        print(f"[snapshot] No se pudo leer el catálogo: {e}")
        return None


def generate_snapshot():
    """Genera el snapshot diario de grupos abiertos/cerrados.
    Reutiliza el catálogo del periodo y solo lo reconstruye en periodo nuevo
    (o si detecta una clase abierta ausente del catálogo). Corre en un hilo
    aparte para no bloquear el arranque del servidor."""
    global snapshot_status
    if g is None:
        return
    try:
        snapshot_status = {"state": "running", "detail": "scrapeando grupos abiertos"}
        clave, periodo = g.clavePeriodo, g.periodo

        # 1. Universo de grupos ofrecidos (cacheado por periodo).
        catalog = load_catalog(clave) or build_catalog(clave, periodo)

        # 2. Grupos abiertos hoy: scrape ligero, solo clases con grupos abiertos.
        open_groups = _scrape_groups(g, g.listaClases)

        # 3. Stale-detect: si aparece una clase abierta ausente del catálogo, este
        #    quedó viejo (alta a mitad de periodo) -> reconstruir una sola vez.
        if any(n not in catalog["classes"] for n in open_groups):
            print("[snapshot] Clase abierta ausente del catálogo; reconstruyendo...")
            catalog = build_catalog(clave, periodo)

        # 4. Calcular abiertos/cerrados por grupo, totales y por depto.
        by_dept = defaultdict(
            lambda: {"offered_groups": 0, "open_groups": 0, "closed_groups": 0}
        )
        classes_out = {}
        tot = {
            "offered_groups": 0, "open_groups": 0, "closed_groups": 0,
            "offered_classes": 0, "open_classes": 0, "closed_classes": 0,
        }
        for nombre, all_g in catalog["classes"].items():
            abiertos_hoy = open_groups.get(nombre, [])
            opened = [grp for grp in all_g if grp in abiertos_hoy]
            closed = [grp for grp in all_g if grp not in opened]
            classes_out[nombre] = {"open": opened, "closed": closed}

            dept = _dept(nombre)
            by_dept[dept]["offered_groups"] += len(all_g)
            by_dept[dept]["open_groups"] += len(opened)
            by_dept[dept]["closed_groups"] += len(closed)

            tot["offered_groups"] += len(all_g)
            tot["open_groups"] += len(opened)
            tot["closed_groups"] += len(closed)
            tot["offered_classes"] += 1
            tot["open_classes" if opened else "closed_classes"] += 1

        snapshot = {
            "date": datetime.date.today().isoformat(),
            "clave": clave,
            "periodo": periodo,
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "totals": tot,
            "by_dept": dict(sorted(by_dept.items())),
            "classes": classes_out,
        }
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        out_path = os.path.join(SNAPSHOT_DIR, f"{snapshot['date']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        snapshot_status = {"state": "done", "detail": out_path}
        print(f"[snapshot] Snapshot guardado: {out_path}")
    except Exception as e:
        snapshot_status = {"state": "error", "detail": str(e)}
        print(f"[snapshot] ERROR generando snapshot: {e}")


def _available_dates():
    if not os.path.isdir(SNAPSHOT_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".json"))


def _load_snapshot(date=None):
    dates = _available_dates()
    if not dates:
        return None
    date = date or dates[-1]
    path = os.path.join(SNAPSHOT_DIR, f"{date}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.get("/stats")
async def stats(date: str | None = None):
    """Snapshot en JSON (por defecto el más reciente). ?date=YYYY-MM-DD para uno
    histórico. ?date=list para ver las fechas disponibles."""
    if date == "list":
        return JSONResponse(content={"dates": _available_dates()})
    snap = _load_snapshot(date)
    if snap is None:
        raise HTTPException(
            status_code=404,
            detail="No hay snapshot disponible todavía (aún generándose o fecha inexistente).",
        )
    return JSONResponse(content=snap)


_DASHBOARD_CSS = """
body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#222;background:#f5f5f5}
.head{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px;background:#006646;color:#fff;padding:18px 24px}
.head h1{margin:0;font-size:20px}
.sub{margin:4px 0 0;font-size:13px;opacity:.85}
.picker{display:flex;align-items:center;gap:6px;font-size:13px}
.picker select{padding:4px}
.cards{display:flex;flex-wrap:wrap;gap:12px;padding:16px 24px 0}
.card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:14px 18px;min-width:120px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.card .n{font-size:26px;font-weight:700;color:#006646}
.card .l{font-size:12px;color:#666;margin-top:2px}
h2{padding:0 24px;margin:24px 0 8px;color:#006646;font-size:16px}
table{border-collapse:collapse;margin:0 24px;background:#fff;min-width:420px}
th,td{border:1px solid #e0e0e0;padding:6px 12px;font-size:13px;text-align:right}
th:first-child,td:first-child{text-align:left}
thead th{background:#006646;color:#fff}
.foot{padding:16px 24px 28px;font-size:12px;color:#888}
.foot a{color:#006646}
"""


def _page(title, body):
    return (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{_esc(title)}</title><style>{_DASHBOARD_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(date: str | None = None):
    dates = _available_dates()
    snap = _load_snapshot(date)
    if snap is None:
        st = snapshot_status
        body = (
            "<div class='head'><div><h1>Grupos abiertos / cerrados</h1>"
            "<p class='sub'>Dashboard de horariosITAM</p></div></div>"
            "<div style='padding:24px'>"
            "<p>Aún no hay snapshots disponibles.</p>"
            f"<p>Estado de generación: <b>{_esc(st['state'])}</b> — {_esc(str(st['detail']))}</p>"
            "</div>"
        )
        return HTMLResponse(_page("Dashboard — horariosITAM", body))

    t = snap["totals"]

    def pct(o, total):
        return f"{(100 * o / total):.0f}%" if total else "—"

    opts = "".join(
        f"<option value='{_esc(d)}'{' selected' if d == snap['date'] else ''}>{_esc(d)}</option>"
        for d in reversed(dates)
    )
    selector = (
        "<form method='get' style='margin:0'>"
        f"<select name='date' onchange='this.form.submit()'>{opts}</select></form>"
    )

    def card(n, label):
        return f"<div class='card'><div class='n'>{n}</div><div class='l'>{label}</div></div>"

    cards = (
        "<div class='cards'>"
        + card(t["open_groups"], "grupos abiertos")
        + card(t["closed_groups"], "grupos cerrados")
        + card(t["offered_groups"], "grupos ofrecidos")
        + card(pct(t["open_groups"], t["offered_groups"]), "% abiertos")
        + "</div><div class='cards'>"
        + card(t["open_classes"], "clases con cupo")
        + card(t["closed_classes"], "clases llenas")
        + card(t["offered_classes"], "clases ofrecidas")
        + "</div>"
    )

    rows = "".join(
        "<tr>"
        f"<td>{_esc(dept)}</td>"
        f"<td>{d['open_groups']}</td>"
        f"<td>{d['closed_groups']}</td>"
        f"<td>{d['offered_groups']}</td>"
        f"<td>{pct(d['open_groups'], d['offered_groups'])}</td>"
        "</tr>"
        for dept, d in snap["by_dept"].items()
    )
    table = (
        "<table><thead><tr><th>Depto</th><th>Abiertos</th><th>Cerrados</th>"
        f"<th>Ofrecidos</th><th>% abiertos</th></tr></thead><tbody>{rows}</tbody></table>"
    )

    body = (
        "<div class='head'><div><h1>Grupos abiertos / cerrados</h1>"
        f"<p class='sub'>{_esc(snap['periodo'])} · snapshot {_esc(snap['date'])} "
        f"· generado {_esc(str(snap.get('generated_at', '')))}</p></div>"
        f"<div class='picker'><label>Fecha:</label>{selector}</div></div>"
        + cards
        + "<h2>Por departamento</h2>"
        + table
        + "<p class='foot'>Datos vía proxy de servicios.itam.mx · "
        f"<a href='/stats?date={_esc(snap['date'])}'>ver JSON</a></p>"
    )
    return HTMLResponse(_page("Dashboard — horariosITAM", body))


if __name__ == "__main__":
    # Para ejecutar la aplicación FastAPI, usa Uvicorn:
    # `uvicorn app:app --host 0.0.0.0 --port 5000 --reload`
    # --reload es para desarrollo (recarga automática al cambiar el código)
    uvicorn.run(app, host="0.0.0.0", port=6969)
