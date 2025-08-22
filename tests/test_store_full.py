import unittest
from decimal import Decimal
from app.services import StoreService as Store, StockInsuficiente, DevolucionInvalida

class TestStoreFull(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        # Llantas + inventario
        self.ll1 = self.store.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
        self.store.ajustar_inventario(self.ll1.id, delta=15, umbral_minimo=5)
        self.ll2 = self.store.registrar_llanta("L-195-65R15", "Y", "City", "195/65 R15", 19.999)  # -> 20.00
        self.store.ajustar_inventario(self.ll2.id, delta=5, umbral_minimo=1)
        # Personas
        self.cl = self.store.registrar_cliente("María López", "12345678")
        self.asr = self.store.registrar_asesor("Carlos Pérez", "87654321")

    def test_crear_inventario_sin_umbral_falla(self):
        ll3 = self.store.registrar_llanta("SKU-NEW", "Z", "Pro", "225/45 R17", 100)
        with self.assertRaises(ValueError):
            self.store.ajustar_inventario(ll3.id, delta=10)  # falta umbral

    def test_disminuir_sin_inventario_falla(self):
        ll3 = self.store.registrar_llanta("SKU-EMPTY", "Z", "Eco", "185/65 R14", 80)
        with self.assertRaises(ValueError):
            self.store.ajustar_inventario(ll3.id, delta=-1)

    def test_disminuir_existente_ok_y_actualiza_umbral(self):
        antes = self.store.inventarios.get(self.ll1.id).cantidad_disponible
        inv = self.store.ajustar_inventario(self.ll1.id, delta=-3, umbral_minimo=4)
        self.assertEqual(inv.cantidad_disponible, antes - 3)
        self.assertEqual(inv.umbral_minimo, 4)

    def test_alerta_igual_a_umbral(self):
        self.store.ajustar_inventario(self.ll2.id, delta=0, umbral_minimo=3)
        self.store.ajustar_inventario(self.ll2.id, delta=-2)  # deja 3
        fila = [f for f in self.store.consultar_inventario() if f["llanta_id"] == self.ll2.id][0]
        self.assertTrue(fila["alerta"])  # 3 <= 3

    def test_reporte_bajo_stock(self):
        # dejar ll2 en alerta: cantidad 1, umbral 3
        inv2 = self.store.inventarios.get(self.ll2.id)
        self.store.ajustar_inventario(self.ll2.id, delta=-(inv2.cantidad_disponible - 1))  # deja 1
        self.store.ajustar_inventario(self.ll2.id, delta=0, umbral_minimo=3)
        bajo = self.store.reporte_bajo_stock()
        ids = [f["llanta_id"] for f in bajo]
        self.assertIn(self.ll2.id, ids)

    def test_precio_redondeado(self):
        self.assertEqual(self.store.llantas.get(self.ll2.id).precio_venta, Decimal("20.00"))

    def test_actualizar_precio_con_historial(self):
        prev = self.store.llantas.get(self.ll1.id).precio_venta
        ll = self.store.actualizar_precio_llanta(self.ll1.id, 130.123)  # -> 130.12
        self.assertEqual(ll.precio_venta, Decimal("130.12"))
        self.assertGreaterEqual(len(ll.precio_historial), 1)
        self.assertEqual(ll.precio_historial[-1]["anterior"], prev)

    def test_venta_un_item(self):
        v = self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll1.id, 2)])
        self.assertEqual(v.total, Decimal("240.00"))
        self.assertEqual(self.store.inventarios.get(self.ll1.id).cantidad_disponible, 13)

    def test_venta_multiple_items(self):
        v = self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll1.id, 2), (self.ll2.id, 3)])
        self.assertEqual(v.total, Decimal("300.00"))  # 2*120 + 3*20
        self.assertEqual(self.store.inventarios.get(self.ll1.id).cantidad_disponible, 13)
        self.assertEqual(self.store.inventarios.get(self.ll2.id).cantidad_disponible, 2)

    def test_bloqueo_sin_stock_no_altera(self):
        inv1 = self.store.inventarios.get(self.ll1.id).cantidad_disponible
        inv2 = self.store.inventarios.get(self.ll2.id).cantidad_disponible
        with self.assertRaises(StockInsuficiente):
            self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll1.id, 2), (self.ll2.id, 999)])
        self.assertEqual(self.store.inventarios.get(self.ll1.id).cantidad_disponible, inv1)
        self.assertEqual(self.store.inventarios.get(self.ll2.id).cantidad_disponible, inv2)
        self.assertEqual(len(self.store.ventas.list()), 0)

    def test_venta_stock_justo(self):
        inv = self.store.inventarios.get(self.ll2.id)
        self.store.ajustar_inventario(self.ll2.id, delta=-(inv.cantidad_disponible - 2))  # dejar 2
        v = self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll2.id, 2)])
        self.assertEqual(self.store.inventarios.get(self.ll2.id).cantidad_disponible, 0)
        self.assertEqual(v.total, Decimal("40.00"))

    def test_devolucion_reingresa_y_guarda_motivo(self):
        v = self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll1.id, 2)])
        inv_antes = self.store.inventarios.get(self.ll1.id).cantidad_disponible
        dev = self.store.registrar_devolucion(v.id, [(self.ll1.id, 1)], "Cliente se arrepintió")
        self.assertEqual(dev.motivo, "Cliente se arrepintió")
        inv_despues = self.store.inventarios.get(self.ll1.id).cantidad_disponible
        self.assertEqual(inv_despues, inv_antes + 1)

    def test_devolucion_invalida_mayor_a_vendido(self):
        v = self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll2.id, 1)])
        with self.assertRaises(DevolucionInvalida):
            self.store.registrar_devolucion(v.id, [(self.ll2.id, 5)], "Error de captura")
