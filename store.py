from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

# ------------------ Utilidad de dinero ------------------
def money(value) -> Decimal:
    """Normaliza a Decimal con 2 decimales (evita errores de flotantes)."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# ------------------ Modelos (OBJETOS) ------------------
@dataclass
class Llanta:
    id: int
    sku: str
    marca: str
    modelo: str
    medida: str
    precio_venta: Decimal
    activa: bool = True

@dataclass
class Inventario:
    id: int
    llanta_id: int
    cantidad_disponible: int
    umbral_minimo: int

@dataclass
class Cliente:
    id: int
    nombre: str
    documento: str
    telefono: Optional[str] = None
    email: Optional[str] = None

@dataclass
class Asesor:
    id: int
    nombre: str
    documento: str
    email: Optional[str] = None

@dataclass
class DetalleVenta:
    id: int
    venta_id: int
    llanta_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

@dataclass
class Venta:
    id: int
    fecha: datetime
    cliente_id: int
    asesor_id: int
    total: Decimal = Decimal("0.00")

# ------------------ Errores de dominio ------------------
class StockInsuficiente(Exception):
    """Se lanza cuando no hay stock suficiente para confirmar una venta."""
    pass

# ------------------ Repositorio en memoria ------------------
class Repo:
    """Repositorio genérico en memoria con autoincremento simple."""
    def __init__(self):
        self.data: Dict[int, object] = {}
        self.next_id = 1

    def add(self, obj):
        obj.id = self.next_id
        self.data[self.next_id] = obj
        self.next_id += 1
        return obj

    def get(self, id_: int):
        return self.data.get(id_)

    def list(self):
        return list(self.data.values())

    def update(self, id_: int, obj):
        if id_ not in self.data:
            raise KeyError("ID no encontrado")
        self.data[id_] = obj
        return obj

# ------------------ Servicio principal (Tienda) ------------------
class Store:
    """
    Orquesta los casos de uso:
    - Registrar llanta, cliente, asesor
    - Cargar/ajustar inventario
    - Registrar venta (con control de stock y cálculo de totales)
    - Consultar inventario y listar ventas
    """
    def __init__(self):
        self.llantas = Repo()
        self.inventarios = Repo()
        self.clientes = Repo()
        self.asesores = Repo()
        self.ventas = Repo()
        self.detalles = Repo()

    # ---- Altas básicas ----
    def registrar_llanta(self, sku: str, marca: str, modelo: str, medida: str, precio_venta, activa: bool = True) -> Llanta:
        l = Llanta(id=0, sku=sku, marca=marca, modelo=modelo, medida=medida, precio_venta=money(precio_venta), activa=activa)
        return self.llantas.add(l)

    def registrar_cliente(self, nombre: str, documento: str, telefono: Optional[str] = None, email: Optional[str] = None) -> Cliente:
        c = Cliente(id=0, nombre=nombre, documento=documento, telefono=telefono, email=email)
        return self.clientes.add(c)

    def registrar_asesor(self, nombre: str, documento: str, email: Optional[str] = None) -> Asesor:
        a = Asesor(id=0, nombre=nombre, documento=documento, email=email)
        return self.asesores.add(a)

    # ---- Inventario ----
    def get_inventario_por_llanta(self, llanta_id: int) -> Optional[Inventario]:
        for inv in self.inventarios.list():
            if inv.llanta_id == llanta_id:
                return inv
        return None

    def ajustar_inventario(self, llanta_id: int, delta: int, umbral_minimo: Optional[int] = None) -> Inventario:
        """
        Aumenta/disminuye existencias. Si el inventario no existe y delta>0, lo crea (requiere umbral_minimo).
        """
        inv = self.get_inventario_por_llanta(llanta_id)
        if inv:
            inv.cantidad_disponible += delta
            if umbral_minimo is not None:
                inv.umbral_minimo = umbral_minimo
            return self.inventarios.update(inv.id, inv)
        else:
            if delta < 0:
                raise ValueError("No hay inventario inicial para disminuir")
            if umbral_minimo is None:
                raise ValueError("Debe especificar umbral_minimo al crear inventario por primera vez")
            inv = Inventario(id=0, llanta_id=llanta_id, cantidad_disponible=delta, umbral_minimo=umbral_minimo)
            return self.inventarios.add(inv)

    def consultar_inventario(self) -> List[dict]:
        """
        Retorna lista de dicts con datos de llanta + existencias + alerta (True si <= umbral).
        """
        salida = []
        for inv in self.inventarios.list():
            ll = self.llantas.get(inv.llanta_id)
            alerta = inv.cantidad_disponible <= inv.umbral_minimo
            salida.append({
                "llanta_id": ll.id,
                "sku": ll.sku,
                "marca": ll.marca,
                "modelo": ll.modelo,
                "medida": ll.medida,
                "cantidad": inv.cantidad_disponible,
                "umbral_minimo": inv.umbral_minimo,
                "alerta": alerta,
            })
        return salida

    # ---- Ventas ----
    def registrar_venta(self, cliente_id: int, asesor_id: int, items: List[Tuple[int, int]]) -> Venta:
        """
        items = [(llanta_id, cantidad), ...]
        Valida stock de todas las llantas antes de confirmar.
        """
        # 1) Validar stock
        for llanta_id, cantidad in items:
            inv = self.get_inventario_por_llanta(llanta_id)
            if inv is None or inv.cantidad_disponible < cantidad:
                ll = self.llantas.get(llanta_id)
                ref = ll.sku if ll else f"ID {llanta_id}"
                disp = inv.cantidad_disponible if inv else 0
                raise StockInsuficiente(f"Stock insuficiente para LLANTA {ref} (disp: {disp}, req: {cantidad})")

        # 2) Crear venta
        venta = Venta(id=0, fecha=datetime.now(), cliente_id=cliente_id, asesor_id=asesor_id, total=money(0))
        venta = self.ventas.add(venta)

        # 3) Crear detalles y descontar inventario
        total = Decimal("0.00")
        for llanta_id, cantidad in items:
            ll = self.llantas.get(llanta_id)
            inv = self.get_inventario_por_llanta(llanta_id)
            precio_u = ll.precio_venta
            subtotal = money(precio_u * cantidad)

            det = DetalleVenta(
                id=0, venta_id=venta.id, llanta_id=llanta_id,
                cantidad=cantidad, precio_unitario=precio_u, subtotal=subtotal
            )
            self.detalles.add(det)

            inv.cantidad_disponible -= cantidad
            self.inventarios.update(inv.id, inv)

            total += subtotal

        # 4) Guardar total
        venta.total = money(total)
        self.ventas.update(venta.id, venta)
        return venta

    def listar_ventas(self):
        """Retorna lista de tuplas (Venta, [DetalleVenta]) para inspección."""
        salida = []
        for v in self.ventas.list():
            dets = [d for d in self.detalles.list() if d.venta_id == v.id]
            salida.append((v, dets))
        return salida
