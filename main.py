# main.py
import argparse
from decimal import Decimal
from store import Store, StockInsuficiente

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
# Menú CLI (opcional)
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
        "0": "Salir",
    }

    while True:
        print("\n=== SERVITECA (CLI) ===")
        for k in sorted(acciones.keys()):
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
            print("\nCLIENTES:")
            for c in store.clientes.list():
                print(f"  [{c.id}] {c.nombre} ({c.documento})")
            cliente_id = pedir_int("ID de cliente: ", minimo=1)

            print("\nASESORES:")
            for a in store.asesores.list():
                print(f"  [{a.id}] {a.nombre} ({a.documento})")
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

        elif op == "7":
            imprimir_ventas(store)

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
# Opción A: ejecutar unittest desde main.py
# ==========================
def run_unittests_from_main():
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')  # descubre todos tus test_*.py
    runner = unittest.TextTestRunner(verbosity=2)          # muestra cada test en consola
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
    - consultar_inventario (alerta por umbral)
    - registrar_venta (OK, multi-ítem, error por stock insuficiente, stock justo)
    - listar_ventas
    """
    all_ok = True
    s = Store()

    _print_h2("1) ALTAS BÁSICAS")
    ll1 = s.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
    print(f"✔ Llanta creada: id={ll1.id}, precio={ll1.precio_venta}")
    ll2 = s.registrar_llanta("L-195-65R15", "Y", "City", "195/65 R15", 19.999)  # -> 20.00
    print(f"✔ Llanta creada: id={ll2.id}, precio={ll2.precio_venta}")
    all_ok &= _okfail("Redondeo precio ll2", ll2.precio_venta, Decimal("20.00"))

    c1 = s.registrar_cliente("María López", "12345678")
    a1 = s.registrar_asesor("Carlos Pérez", "87654321")
    print(f"✔ Cliente id={c1.id} | Asesor id={a1.id}")

    _print_h2("2) INVENTARIO: CREAR Y AJUSTAR")
    inv1 = s.ajustar_inventario(ll1.id, delta=15, umbral_minimo=5)  # crea inventario
    print(f"✔ Inventario ll1 creado: cant={inv1.cantidad_disponible}, umbral={inv1.umbral_minimo}")
    inv2 = s.ajustar_inventario(ll2.id, delta=5, umbral_minimo=2)
    print(f"✔ Inventario ll2 creado: cant={inv2.cantidad_disponible}, umbral={inv2.umbral_minimo}")

    _ver_inventario(s, "INVENTARIO INICIAL")

    # Disminuir y cambiar umbral
    inv1_b = s.ajustar_inventario(ll1.id, delta=-3, umbral_minimo=4)
    print(f"✔ Ajuste ll1: cant={inv1_b.cantidad_disponible}, umbral={inv1_b.umbral_minimo}")
    all_ok &= _okfail("ll1 cantidad tras -3", inv1_b.cantidad_disponible, 12)
    all_ok &= _okfail("ll1 umbral actualizado", inv1_b.umbral_minimo, 4)

    _print_h2("3) INVENTARIO: ALERTA POR UMBRAL")
    s.ajustar_inventario(ll2.id, delta=-2)         # 5 -> 3
    s.ajustar_inventario(ll2.id, delta=0, umbral_minimo=3)
    fila_ll2 = [f for f in s.consultar_inventario() if f["llanta_id"] == ll2.id][0]
    all_ok &= _okfail("Alerta ll2 (3 <= 3)", fila_ll2["alerta"], True)
    _ver_inventario(s, "INVENTARIO CON ALERTA")

    _print_h2("4) VENTAS: ESCENARIO FELIZ (1 ÍTEM)")
    v1 = s.registrar_venta(c1.id, a1.id, [(ll1.id, 2)])  # 2 * 120 = 240
    all_ok &= _okfail("Total v1", v1.total, Decimal("240.00"))
    all_ok &= _okfail("Stock ll1 tras v1", s.get_inventario_por_llanta(ll1.id).cantidad_disponible, 10)
    _ver_inventario(s, "INVENTARIO TRAS V1")
    _ver_ventas(s, "VENTAS TRAS V1")

    _print_h2("5) VENTAS: MULTI-ÍTEM")
    v2 = s.registrar_venta(c1.id, a1.id, [(ll1.id, 1), (ll2.id, 2)])  # 1*120 + 2*20 = 160
    all_ok &= _okfail("Total v2", v2.total, Decimal("160.00"))
    all_ok &= _okfail("Stock ll1 tras v2", s.get_inventario_por_llanta(ll1.id).cantidad_disponible, 9)
    all_ok &= _okfail("Stock ll2 tras v2", s.get_inventario_por_llanta(ll2.id).cantidad_disponible, 1)
    _ver_inventario(s, "INVENTARIO TRAS V2")
    _ver_ventas(s, "VENTAS TRAS V2")

    _print_h2("6) VENTAS: BLOQUEO POR FALTA DE STOCK (TRANSACCIONALIDAD)")
    inv1_before = s.get_inventario_por_llanta(ll1.id).cantidad_disponible
    inv2_before = s.get_inventario_por_llanta(ll2.id).cantidad_disponible
    try:
        s.registrar_venta(c1.id, a1.id, [(ll1.id, 2), (ll2.id, 999)])  # ll2 insuficiente
        print("[FAIL] Se esperaba StockInsuficiente y no ocurrió.")
        all_ok = False
    except StockInsuficiente:
        print("[OK] Lanzó StockInsuficiente (no se confirma la venta)")
    all_ok &= _okfail("ll1 intacto tras fallo", s.get_inventario_por_llanta(ll1.id).cantidad_disponible, inv1_before)
    all_ok &= _okfail("ll2 intacto tras fallo", s.get_inventario_por_llanta(ll2.id).cantidad_disponible, inv2_before)
    _ver_ventas(s, "VENTAS (DEBE SER IGUAL QUE TRAS V2)")

    _print_h2("7) VENTAS: STOCK JUSTO")
    v3 = s.registrar_venta(c1.id, a1.id, [(ll2.id, 1)])  # 1 * 20 = 20
    all_ok &= _okfail("Total v3", v3.total, Decimal("20.00"))
    all_ok &= _okfail("Stock ll2 tras v3 (debe 0)", s.get_inventario_por_llanta(ll2.id).cantidad_disponible, 0)
    _ver_inventario(s, "INVENTARIO FINAL")
    _ver_ventas(s, "VENTAS FINALES")

    print("\nRESULTADO SELFTEST:", "TODO OK ✅" if all_ok else "HAY FALLAS ❌")

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
