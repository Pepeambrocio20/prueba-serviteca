import unittest
from decimal import Decimal
from app.services import StoreService as Store, StockInsuficiente
# Si usas el shim, podrías hacer: from store import Store, StockInsuficiente

class TestVentasBasicas(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        # Datos base
        self.ll1 = self.store.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
        self.store.ajustar_inventario(self.ll1.id, delta=15, umbral_minimo=5)
        self.cl = self.store.registrar_cliente("María López", "12345678")
        self.asr = self.store.registrar_asesor("Carlos Pérez", "87654321")

    def test_venta_con_stock(self):
        v = self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll1.id, 2)])
        self.assertEqual(v.total, Decimal("240.00"))
        inv = self.store.inventarios.get(self.ll1.id)  # o self.store.get_inventario_por_llanta(self.ll1.id)
        self.assertEqual(inv.cantidad_disponible, 13)

    def test_bloqueo_por_stock(self):
        with self.assertRaises(StockInsuficiente):
            self.store.registrar_venta(self.cl.id, self.asr.id, [(self.ll1.id, 999)])
        inv = self.store.inventarios.get(self.ll1.id)
        self.assertEqual(inv.cantidad_disponible, 15)  # no cambia
