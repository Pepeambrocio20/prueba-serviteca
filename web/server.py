# web/server.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from app.services import (
    StoreService, StockInsuficiente, DevolucionInvalida, LlantaNoEncontrada, VentaNoEncontrada
)

app = FastAPI(title="Serviteca (Web mínima)")

# Instancia única (persistencia en memoria por proceso)
store = StoreService()

# Semilla mínima para que haya datos básicos
def seed_minimo():
    if not store.llantas.list():
        ll = store.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
        store.ajustar_inventario(ll.id, delta=15, umbral_minimo=5)
    if not store.clientes.list():
        store.registrar_cliente("María López", "12345678")
    if not store.asesores.list():
        store.registrar_asesor("Carlos Pérez", "87654321")

seed_minimo()

templates = Jinja2Templates(directory="web/templates")


@app.get("/")
def root():
    return RedirectResponse(url="/inventario", status_code=status.HTTP_302_FOUND)


# -------- Panel único --------
@app.get("/inventario")
def inventario(request: Request, msg: str | None = None, error: str | None = None):
    filas = store.consultar_inventario()
    bajo = store.reporte_bajo_stock()
    clientes = store.clientes.list()
    asesores = store.asesores.list()
    llantas = store.llantas.list()
    ventas = store.listar_ventas()
    devoluciones = store.listar_devoluciones()
    return templates.TemplateResponse(
        "inventario.html",
        {
            "request": request,
            "filas": filas,
            "bajo": bajo,
            "clientes": clientes,
            "asesores": asesores,
            "llantas": llantas,
            "ventas": ventas,
            "devoluciones": devoluciones,
            "msg": msg,
            "error": error,
        },
    )


# -------- Llantas --------
@app.post("/llantas")
def crear_llanta(
    sku: str = Form(...),
    marca: str = Form(...),
    modelo: str = Form(...),
    medida: str = Form(...),
    precio: str = Form(...),
):
    store.registrar_llanta(sku, marca, modelo, medida, precio)
    return RedirectResponse("/inventario?msg=Llanta+creada", status_code=302)


@app.post("/llantas/precio")
def actualizar_precio(
    llanta_id: int = Form(...),
    nuevo_precio: str = Form(...),
):
    try:
        store.actualizar_precio_llanta(llanta_id, nuevo_precio)
        return RedirectResponse("/inventario?msg=Precio+actualizado", status_code=302)
    except LlantaNoEncontrada as e:
        return RedirectResponse(f"/inventario?error={str(e)}", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/inventario?error=Error:+{str(e)}", status_code=302)


# -------- Inventario --------
@app.post("/inventario/ajustar")
def ajustar_inventario(
    llanta_id: int = Form(...),
    delta: int = Form(...),
    umbral: str = Form(""),
):
    try:
        umbral_min = int(umbral) if umbral.strip() else None
        store.ajustar_inventario(llanta_id, delta=delta, umbral_minimo=umbral_min)
        return RedirectResponse("/inventario?msg=Inventario+actualizado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/inventario?error={str(e)}", status_code=302)


# -------- Personas --------
@app.post("/clientes")
def crear_cliente(
    nombre: str = Form(...),
    documento: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
):
    store.registrar_cliente(nombre, documento, telefono or None, email or None)
    return RedirectResponse("/inventario?msg=Cliente+creado", status_code=302)


@app.post("/asesores")
def crear_asesor(
    nombre: str = Form(...),
    documento: str = Form(...),
    email: str = Form(""),
):
    store.registrar_asesor(nombre, documento, email or None)
    return RedirectResponse("/inventario?msg=Asesor+creado", status_code=302)


# -------- Ventas --------
@app.post("/ventas")
def crear_venta(
    cliente_id: int = Form(...),
    asesor_id: int = Form(...),
    items_text: str = Form(...),
):
    """
    items_text formato: "1x2,3x1" -> [(1,2), (3,1)]
    """
    try:
        items = []
        raw = items_text.strip()
        if not raw:
            return RedirectResponse("/inventario?error=No+hay+items", status_code=302)
        for parte in raw.split(","):
            parte = parte.strip()
            if not parte:
                continue
            if "x" not in parte.lower():
                return RedirectResponse("/inventario?error=Formato+de+items+invalido", status_code=302)
            a, b = parte.lower().split("x", 1)
            ll_id = int(a.strip())
            cant = int(b.strip())
            items.append((ll_id, cant))

        store.registrar_venta(cliente_id, asesor_id, items)
        return RedirectResponse("/inventario?msg=Venta+registrada", status_code=302)

    except StockInsuficiente as e:
        return RedirectResponse(f"/inventario?error=Stock+insuficiente:+{str(e)}", status_code=302)
    except LlantaNoEncontrada as e:
        return RedirectResponse(f"/inventario?error={str(e)}", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/inventario?error=Error:+{str(e)}", status_code=302)


# -------- Devoluciones --------
@app.post("/devoluciones")
def crear_devolucion(
    venta_id: int = Form(...),
    items_text: str = Form(...),
    motivo: str = Form(...),
):
    """
    items_text formato: "1x2,3x1" -> [(1,2), (3,1)]
    """
    try:
        items = []
        raw = items_text.strip()
        if not raw:
            return RedirectResponse("/inventario?error=No+hay+items+en+devolucion", status_code=302)
        for parte in raw.split(","):
            parte = parte.strip()
            if not parte:
                continue
            if "x" not in parte.lower():
                return RedirectResponse("/inventario?error=Formato+de+items+invalido+(devolucion)", status_code=302)
            a, b = parte.lower().split("x", 1)
            ll_id = int(a.strip())
            cant = int(b.strip())
            items.append((ll_id, cant))

        store.registrar_devolucion(venta_id, items, motivo)
        return RedirectResponse("/inventario?msg=Devolucion+registrada", status_code=302)

    except (DevolucionInvalida, VentaNoEncontrada) as e:
        return RedirectResponse(f"/inventario?error={str(e)}", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/inventario?error=Error:+{str(e)}", status_code=302)
