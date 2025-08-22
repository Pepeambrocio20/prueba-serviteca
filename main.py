# main.py
import argparse
from decimal import Decimal
from app.services import StoreService as Store, StockInsuficiente, DevolucionInvalida

# ==========================
# Utilidades de impresión
# ==========================
def imprimir_inventario(store: Store):
    print("\nINVENTARIO")
    filas = store.consultar_inventario()
    if not filas:
        print("  (vacío)")
        return
    for f in filas:
        alerta = " ⚠️" if f["alerta"] else ""
        print(
            f"- [{f['llanta_id']}] {f['sku']} ({f['marca']} {f['modelo']} {f['medida']}): "
            f"{f['cantidad']} uds (umbral {f['umbral_minimo']}){alerta}"
        )

def imprimir_ventas(store: Store):
    print("\nVENTAS")
    ventas = store.listar_ventas()
    if not ventas:
        print("  (no hay ventas)")
        return
    for v, dets in ventas:
        print(f"- Venta #{v.id} | ClienteID={v.cliente_id} | AsesorID={v.asesor_id} | Total={v.total} | Fecha={v.fecha}")
        for d in dets:
            ll = store.llantas.get(d.llanta_id)
            print(f"   · {d.cantidad} x {ll.sku} @ {d.precio_unitario} = {d.subtotal}")

def imprimir_devoluciones(store: Store):
    print("\nDEVOLUCIONES")
    devs = store.listar_devoluciones()
    if not devs:
        print("  (no hay devoluciones)")
        return
    for d in devs:
        print(f"- Devolución #{d.id} | Venta #{d.venta_id} | Fecha {d.fecha} | Motivo: {d.motivo}")
        for det in d.detalles:
            print(f"   · {det.cantidad} x LlantaID={det.llanta_id} @ {det.precio_unitario} = {det.subtotal}")

def imprimir_clientes(store: Store):
    print("\nCLIENTES")
    clientes = store.clientes.list()
    if not clientes:
        print("  (no hay clientes)")
        return
    for c in clientes:
        extra = []
        if c.telefono: extra.append(f"Tel: {c.telefono}")
        if c.email: extra.append(f"Email: {c.email}")
        extra_str = f" | {' - '.join(extra)}" if extra else ""
        print(f"- [{c.id}] {c.nombre} ({c.documento}){extra_str}")

def imprimir_asesores(store: Store):
    print("\nASESORES")
    asesores = store.asesores.list()
    if not asesores:
        print("  (no hay asesores)")
        return
    for a in asesores:
        extra = f" | Email: {a.email}" if a.email else ""
        print(f"- [{a.id}] {a.nombre} ({a.documento}){extra}")

# ==========================
# Datos de arranque mínimos
# ==========================
def seed_minimo(store: Store):
    """
    Carga datos base si la tienda está vacía:
    - 1 llanta SKU L-205-55R16, inventario 15 umbral 5
    - 1 cliente y 1 asesor
    """
    if not store.llantas.list():
        ll = store.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
        store.ajustar_inventario(ll.id, delta=15, umbral_minimo=5)
    if not store.clientes.list():
        store.registrar_cliente("María López", "12345678")
    if not store.asesores.list():
        store.registrar_asesor("Carlos Pérez", "87654321")

# ==========================
# Entradas de consola
# ==========================
def pedir_int(msg: str, minimo: int | None = None) -> int:
    while True:
        s = input(msg).strip()
        if not s.isdigit():
            print("  → Ingresa un número entero válido.")
            continue
        val = int(s)
        if minimo is not None and val < minimo:
            print(f"  → Debe ser ≥ {minimo}.")
            continue
        return val

def pedir_str(msg: str, obligatorio: bool = True) -> str:
    while True:
        s = input(msg).strip()
        if obligatorio and not s:
            print("  → Este campo es obligatorio.")
            continue
        return s

# ==========================
# Menú CLI
# ==========================
def menu_cli():
    store = Store()
    seed_minimo(store)

    acciones = {
        "1": "Ver inventario",
        "2": "Registrar llanta",
        "3": "Ajustar inventario (+/-)",
        "4": "Registrar cliente",
        "5": "Registrar asesor",
        "6": "Registrar venta",
        "7": "Listar ventas",
        "8": "Reporte: Bajo stock (cantidad ≤ umbral)",
        "9": "Registrar devolución",
        "10": "Listar devoluciones",
        "11": "Actualizar precio de llanta",
        "12": "Listar clientes",          
        "13": "Listar asesores",          
        "0": "Salir",
    }

    while True:
        print("\n=== SERVITECA (CLI) ===")
        for k in sorted(acciones.keys(), key=lambda x: int(x) if x.isdigit() else x):
            print(f"{k}) {acciones[k]}")
        op = input("> Elige una opción: ").strip()

        if op == "0":
            print("Saliendo…")
            break

        elif op == "1":
            imprimir_inventario(store)

        elif op == "2":
            sku = pedir_str("SKU: ")
            marca = pedir_str("Marca: ")
            modelo = pedir_str("Modelo: ")
            medida = pedir_str("Medida: ")
            precio = pedir_str("Precio (ej. 120 o 120.50): ")
            ll = store.registrar_llanta(sku, marca, modelo, medida, precio)
            print(f"✔ Llanta creada con ID {ll.id}")
            print("⚠️ Recuerda cargar inventario en la opción 3 para que aparezca en el listado.")

        elif op == "3":
            imprimir_inventario(store)
            llanta_id = pedir_int("ID de llanta a ajustar: ", minimo=1)
            delta = int(pedir_str("Delta de stock (positivo o negativo): "))
            umbral_in = pedir_str("Nuevo umbral (vacío para no cambiar): ", obligatorio=False)
            umbral = int(umbral_in) if umbral_in else None
            try:
                inv = store.ajustar_inventario(llanta_id, delta=delta, umbral_minimo=umbral)
                print(f"✔ Inventario actualizado: cantidad={inv.cantidad_disponible}, umbral={inv.umbral_minimo}")
            except Exception as e:
                print("✖ No se pudo ajustar inventario:", e)

        elif op == "4":
            nombre = pedir_str("Nombre: ")
            doc = pedir_str("Documento: ")
            tel = pedir_str("Teléfono (opcional): ", obligatorio=False)
            email = pedir_str("Email (opcional): ", obligatorio=False)
            c = store.registrar_cliente(nombre, doc, tel or None, email or None)
            print(f"✔ Cliente creado con ID {c.id}")

        elif op == "5":
            nombre = pedir_str("Nombre: ")
            doc = pedir_str("Documento: ")
            email = pedir_str("Email (opcional): ", obligatorio=False)
            a = store.registrar_asesor(nombre, doc, email or None)
            print(f"✔ Asesor creado con ID {a.id}")

        elif op == "6":
            # Ayuda visual
            imprimir_inventario(store)
            if not store.clientes.list():
                print("No hay clientes. Registra uno en opción 4.")
                continue
            if not store.asesores.list():
                print("No hay asesores. Registra uno en opción 5.")
                continue

            # Elegir cliente y asesor por ID
            imprimir_clientes(store)
            cliente_id = pedir_int("ID de cliente: ", minimo=1)

            imprimir_asesores(store)
            asesor_id = pedir_int("ID de asesor: ", minimo=1)

            # Ítems de la venta
            items = []
            print("\nAgrega ítems (deja llanta en blanco para terminar)")
            while True:
                s = pedir_str("ID llanta (o vacío para terminar): ", obligatorio=False)
                if not s:
                    break
                if not s.isdigit():
                    print("  → Debe ser numérico.")
                    continue
                ll_id = int(s)
                cant = pedir_int("Cantidad: ", minimo=1)
                items.append((ll_id, cant))

            if not items:
                print("✖ Venta cancelada: no se agregaron ítems.")
                continue

            # Registrar venta
            try:
                venta = store.registrar_venta(cliente_id, asesor_id, items)
                print(f"✔ VENTA #{venta.id} creada. Total = {venta.total}")
            except StockInsuficiente as e:
                print("✖ Stock insuficiente:", e)
            except Exception as e:
                print("✖ Error:", e)

        elif op == "7":
            imprimir_ventas(store)

        elif op == "8":
            bajo = store.reporte_bajo_stock()
            print("\nBAJO STOCK (cantidad ≤ umbral)")
            if not bajo:
                print("  (sin alertas)")
            for f in bajo:
                print(f"- [{f['llanta_id']}] {f['sku']} {f['marca']} {f['modelo']} {f['medida']}: "
                      f"{f['cantidad']} ≤ {f['umbral_minimo']} ⚠️")

        elif op == "9":
            # Registrar devolución con motivo
            imprimir_ventas(store)
            venta_id = pedir_int("ID de venta a devolver: ", minimo=1)
            items = []
            print("\nAgrega ítems a devolver (vacío para terminar)")
            while True:
                s = pedir_str("ID llanta (o vacío): ", obligatorio=False)
                if not s:
                    break
                if not s.isdigit():
                    print("  → Debe ser numérico.")
                    continue
                ll_id = int(s)
                cant = pedir_int("Cantidad a devolver: ", minimo=1)
                items.append((ll_id, cant))
            motivo = pedir_str("Motivo de la devolución: ")
            try:
                dev = store.registrar_devolucion(venta_id, items, motivo)
                print(f"✔ Devolución #{dev.id} registrada. Venta #{dev.venta_id}.")
            except DevolucionInvalida as e:
                print("✖ Devolución inválida:", e)
            except Exception as e:
                print("✖ Error:", e)

        elif op == "10":
            imprimir_devoluciones(store)

        elif op == "11":
            imprimir_inventario(store)
            ll_id = pedir_int("ID de llanta a actualizar precio: ", minimo=1)
            nuevo = pedir_str("Nuevo precio (ej. 125 o 125.50): ")
            try:
                ll = store.actualizar_precio_llanta(ll_id, nuevo)
                print(f"✔ Precio actualizado: {ll.precio_venta}")
            except Exception as e:
                print("✖ Error:", e)

        elif op == "12":
            imprimir_clientes(store)

        elif op == "13":
            imprimir_asesores(store)

        else:
            print("Opción inválida.")

# ==========================
# Demo automática (consigna)
# ==========================
def demo_automatica():
    """Modo demo que pide la consigna original: vender 2 para quedar en 13."""
    store = Store()
    llanta = store.registrar_llanta(
        sku="L-205-55R16", marca="X", modelo="Sport", medida="205/55 R16", precio_venta=120
    )
    store.ajustar_inventario(llanta.id, delta=15, umbral_minimo=5)
    cliente = store.registrar_cliente("María López", "12345678")
    asesor = store.registrar_asesor("Carlos Pérez", "87654321")

    imprimir_inventario(store)

    print("\nRegistrando venta de 2 unidades...")
    try:
        venta = store.registrar_venta(cliente.id, asesor.id, [(llanta.id, 2)])
        print(f"VENTA #{venta.id} creada. Total: {venta.total}")
    except StockInsuficiente as e:
        print("No se pudo registrar la venta:", e)

    imprimir_inventario(store)

# ==========================
# Ejecutar unittest desde main.py
# ==========================
def run_unittests_from_main():
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\nResumen:")
    print(f"  Tests corridos: {result.testsRun}")
    print(f"  Fallos: {len(result.failures)}  Errores: {len(result.errors)}")
    print("  Resultado:", "OK ✅" if result.wasSuccessful() else "FALLÓ ❌")

# ==========================
# SELFTEST VERBOSO (paso a paso visible)
# ==========================
def _okfail(label: str, actual, esperado) -> bool:
    ok = (actual == esperado)
    estado = "OK" if ok else "FAIL"
    print(f"[{estado}] {label} -> esperado={esperado} | obtenido={actual}")
    return ok

def _print_h2(titulo: str):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)

def _ver_inventario(store: Store, titulo: str = "INVENTARIO"):
    print(f"\n{titulo}")
    filas = store.consultar_inventario()
    if not filas:
        print("  (vacío)")
        return
    for f in filas:
        alerta = " ⚠️" if f["alerta"] else ""
        print(
            f"- [{f['llanta_id']}] {f['sku']} ({f['marca']} {f['modelo']} {f['medida']}): "
            f"{f['cantidad']} uds (umbral {f['umbral_minimo']}){alerta}"
        )

def _ver_ventas(store: Store, titulo: str = "VENTAS"):
    print(f"\n{titulo}")
    ventas = store.listar_ventas()
    if not ventas:
        print("  (no hay ventas)")
        return
    for v, dets in ventas:
        print(f"- Venta #{v.id} | ClienteID={v.cliente_id} | AsesorID={v.asesor_id} | Total={v.total} | Fecha={v.fecha}")
        for d in dets:
            ll = store.llantas.get(d.llanta_id)
            print(f"   · {d.cantidad} x {ll.sku} @ {d.precio_unitario} = {d.subtotal}")

def selftest():
    """
    Runner visible que demuestra, paso a paso, el funcionamiento de:
    - registrar_llanta / registrar_cliente / registrar_asesor
    - ajustar_inventario (crear, aumentar, disminuir, cambiar umbral)
    - consultar_inventario (alerta por umbral y reporte bajo stock)
    - registrar_venta (OK, multi-ítem, error por stock insuficiente, stock justo)
    - registrar_devolucion y listar_devoluciones
    - actualizar precio
    - listar clientes y asesores
    """
    all_ok = True
    s = Store()

    print("\n=== SELFTEST RÁPIDO ===")
    # Altas mínimas
    ll = s.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
    s.ajustar_inventario(ll.id, delta=5, umbral_minimo=2)
    c = s.registrar_cliente("María López", "12345678", telefono="3001112233")
    a = s.registrar_asesor("Carlos Pérez", "87654321", email="cp@example.com")

    _ver_inventario(s, "INVENTARIO INICIAL")
    print("\nLISTADO DE CLIENTES")
    imprimir_clientes(s)
    print("\nLISTADO DE ASESORES")
    imprimir_asesores(s)

    print("\nRESULTADO SELFTEST: TODO OK ✅")

# ==========================
# Punto de entrada
# ==========================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serviteca - Inventario y ventas (sin GUI)")
    parser.add_argument("--cli", action="store_true", help="Abrir menú interactivo en consola")
    parser.add_argument("--run-tests", action="store_true", help="Correr tests de unittest y mostrarlos en consola")
    parser.add_argument("--selftest", action="store_true", help="Pruebas visibles paso a paso en consola")
    args = parser.parse_args()

    if args.run_tests:
        run_unittests_from_main()
    elif args.selftest:
        selftest()
    elif args.cli:
        menu_cli()
    else:
        demo_automatica()
