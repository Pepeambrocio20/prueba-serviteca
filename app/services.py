# app/services.py
from typing import List, Tuple
from decimal import Decimal

# Modelos (las dataclasses viven aquí)
from .models import (
    Llanta, Inventario, Cliente, Asesor,
    Venta, VentaDetalle,
    Devolucion, DevolucionDetalle
)

# Repos (persistencia simple en memoria)
from .repositories import (
    RepoLlantas, RepoClientes, RepoAsesores, RepoInventarios,
    RepoVentas, RepoDevoluciones
)

# Utilidades
from .utils import to_money, now_ts


# ==========================
# Excepciones de negocio
# ==========================
class StockInsuficiente(Exception):
    """Se intenta vender más de lo disponible en inventario."""
    pass

class LlantaNoEncontrada(Exception):
    """Llanta no registrada."""
    pass

class VentaNoEncontrada(Exception):
    """Venta no registrada."""
    pass

class DevolucionInvalida(Exception):
    """Reglas incumplidas en devolución (sin motivo, cantidades inválidas, etc.)."""
    pass


# ==========================
# Servicio principal
# ==========================
class StoreService:
    """
    Orquesta la lógica de negocio y usa repos in-memory como persistencia simple.
    Compatible con la interfaz anterior (se añade get_inventario_por_llanta).
    """

    def __init__(self):
        self.llantas = RepoLlantas()
        self.clientes = RepoClientes()
        self.asesores = RepoAsesores()
        self.inventarios = RepoInventarios()
        self.ventas = RepoVentas()
        self.devoluciones = RepoDevoluciones()

    # --------- Altas ---------
    def registrar_llanta(self, sku, marca, modelo, medida, precio_venta) -> Llanta:
        ll = Llanta(
            id=0,
            sku=sku,
            marca=marca,
            modelo=modelo,
            medida=medida,
            precio_venta=to_money(precio_venta),
            precio_historial=[]
        )
        return self.llantas.add(ll)

    def registrar_cliente(self, nombre, documento, telefono=None, email=None) -> Cliente:
        return self.clientes.add(Cliente(0, nombre, documento, telefono, email))

    def registrar_asesor(self, nombre, documento, email=None) -> Asesor:
        return self.asesores.add(Asesor(0, nombre, documento, email))

    # --------- Inventario ---------
    def ajustar_inventario(self, llanta_id: int, delta: int, umbral_minimo: int | None = None) -> Inventario:
        ll = self.llantas.get(llanta_id)
        if not ll:
            raise LlantaNoEncontrada(f"Llanta {llanta_id} no existe")

        inv = self.inventarios.get(llanta_id)
        if inv is None:
            # Crear inventario nuevo: requiere delta>0 y umbral_minimo
            if delta <= 0 or umbral_minimo is None:
                raise ValueError("Para crear inventario: delta > 0 y umbral_minimo requerido.")
            inv = Inventario(llanta_id=llanta_id, cantidad_disponible=delta, umbral_minimo=umbral_minimo)
        else:
            nueva = inv.cantidad_disponible + delta
            if nueva < 0:
                raise ValueError("No puede quedar negativo.")
            inv.cantidad_disponible = nueva
            if umbral_minimo is not None:
                inv.umbral_minimo = umbral_minimo

        return self.inventarios.create_or_update(inv)

    def consultar_inventario(self) -> List[dict]:
        filas: List[dict] = []
        for inv in self.inventarios.list():
            ll = self.llantas.get(inv.llanta_id)
            filas.append({
                "llanta_id": ll.id,
                "sku": ll.sku,
                "marca": ll.marca,
                "modelo": ll.modelo,
                "medida": ll.medida,
                "cantidad": inv.cantidad_disponible,
                "umbral_minimo": inv.umbral_minimo,
                "alerta": inv.cantidad_disponible <= inv.umbral_minimo
            })
        return filas

    # Reporte: bajo stock (cantidad ≤ umbral)
    def reporte_bajo_stock(self) -> List[dict]:
        return [f for f in self.consultar_inventario() if f["cantidad"] <= f["umbral_minimo"]]

    # --------- Compatibilidad con tests antiguos ---------
    def get_inventario_por_llanta(self, llanta_id: int) -> Inventario | None:
        """Helper de compatibilidad: algunos tests viejos llamaban a este nombre."""
        return self.inventarios.get(llanta_id)

    # --------- Ventas ---------
    def registrar_venta(self, cliente_id: int, asesor_id: int, items: List[tuple[int, int]]) -> Venta:
        if not self.clientes.get(cliente_id):
            raise ValueError("Cliente inválido")
        if not self.asesores.get(asesor_id):
            raise ValueError("Asesor inválido")

        # Validación previa: stock suficiente para todos los ítems (transaccional)
        for ll_id, cant in items:
            inv = self.inventarios.get(ll_id)
            if inv is None or inv.cantidad_disponible < cant:
                raise StockInsuficiente(f"Llanta {ll_id} sin stock para {cant} uds")

        # Descuentos y armado de detalles
        detalles: List[VentaDetalle] = []
        total = Decimal("0.00")

        for ll_id, cant in items:
            ll = self.llantas.get(ll_id)
            inv = self.inventarios.get(ll_id)
            inv.cantidad_disponible -= cant
            self.inventarios.create_or_update(inv)

            # subtotal = cantidad * precio
            subtotal = to_money(Decimal(cant) * ll.precio_venta)
            detalles.append(VentaDetalle(
                llanta_id=ll_id,
                cantidad=cant,
                precio_unitario=ll.precio_venta,
                subtotal=subtotal
            ))
            total += subtotal

        venta = Venta(
            id=0,
            cliente_id=cliente_id,
            asesor_id=asesor_id,
            fecha=now_ts(),
            total=to_money(total)
        )
        venta = self.ventas.add(venta)
        # Guardamos detalles adheridos en memoria (no hay BD)
        venta._detalles = detalles  # atributo auxiliar

        return venta

    def listar_ventas(self) -> List[Tuple[Venta, List[VentaDetalle]]]:
        out: List[Tuple[Venta, List[VentaDetalle]]] = []
        for v in self.ventas.list():
            dets = getattr(v, "_detalles", [])
            out.append((v, dets))
        return out

    # --------- Devoluciones ---------
    def registrar_devolucion(self, venta_id: int, items: List[tuple[int, int]], motivo: str) -> Devolucion:
        v = self.ventas.get(venta_id)
        if not v:
            raise VentaNoEncontrada(f"Venta {venta_id} no existe")
        if not motivo or not motivo.strip():
            raise DevolucionInvalida("Debe indicar un motivo de devolución.")

        # No se puede devolver más de lo vendido por ítem
        vendidos: dict[int, int] = {}
        for d in getattr(v, "_detalles", []):
            vendidos[d.llanta_id] = vendidos.get(d.llanta_id, 0) + d.cantidad

        for ll_id, cant_dev in items:
            if cant_dev <= 0:
                raise DevolucionInvalida("Cantidad a devolver debe ser > 0")
            if vendidos.get(ll_id, 0) < cant_dev:
                raise DevolucionInvalida(
                    f"No puede devolver {cant_dev} si solo se vendió {vendidos.get(ll_id,0)} (llanta {ll_id})"
                )

        # Reingresar stock + armar detalles de devolución
        detalles: List[DevolucionDetalle] = []
        for ll_id, cant in items:
            ll = self.llantas.get(ll_id)
            inv = self.inventarios.get(ll_id)
            if inv is None:
                # si no había inventario registrado, créalo con umbral 0
                inv = Inventario(llanta_id=ll_id, cantidad_disponible=0, umbral_minimo=0)

            inv.cantidad_disponible += cant
            self.inventarios.create_or_update(inv)

            subtotal = to_money(Decimal(cant) * ll.precio_venta)
            detalles.append(DevolucionDetalle(
                llanta_id=ll_id,
                cantidad=cant,
                precio_unitario=ll.precio_venta,
                subtotal=subtotal
            ))

        dev = Devolucion(
            id=0,
            venta_id=v.id,
            fecha=now_ts(),
            motivo=motivo.strip(),
            detalles=detalles
        )
        return self.devoluciones.add(dev)

    def listar_devoluciones(self) -> List[Devolucion]:
        return self.devoluciones.list()

    # --------- Precio ---------
    def actualizar_precio_llanta(self, llanta_id: int, nuevo_precio) -> Llanta:
        ll = self.llantas.get(llanta_id)
        if not ll:
            raise LlantaNoEncontrada(f"Llanta {llanta_id} no existe")
        anterior = ll.precio_venta
        ll.precio_venta = to_money(nuevo_precio)
        ll.precio_historial.append({
            "fecha": now_ts(),
            "anterior": anterior,
            "nuevo": ll.precio_venta
        })
        self.llantas.set(ll.id, ll)
        return ll

    def historial_precios(self, llanta_id: int) -> List[dict]:
        ll = self.llantas.get(llanta_id)
        if not ll:
            raise LlantaNoEncontrada(f"Llanta {llanta_id} no existe")
        return ll.precio_historial
