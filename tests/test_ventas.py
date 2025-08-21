import unittest
from store import Store, StockInsuficiente
from decimal import Decimal

class TestVentas(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.llanta = self.store.registrar_llanta("L-205-55R16", "X", "Sport", "205/55 R16", 120)
        self.store.ajustar_inventario(self.llanta.id, delta=10, umbral_minimo=2)
        self.cliente = self.store.registrar_cliente("María López", "12345678")
        self.asesor = self.store.registrar_asesor("Carlos Pérez", "87654321")

    def test_venta_con_stock(self):
        venta = self.store.registrar_venta(self.cliente.id, self.asesor.id, [(self.llanta.id, 3)])
        self.assertEqual(self.store.get_inventario_por_llanta(self.llanta.id).cantidad_disponible, 7)
        self.assertEqual(venta.total, Decimal("360.00"))

    def test_bloqueo_por_stock(self):
        with self.assertRaises(StockInsuficiente):
            self.store.registrar_venta(self.cliente.id, self.asesor.id, [(self.llanta.id, 11)])

if __name__ == "__main__":
    unittest.main()
