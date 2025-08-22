# app/models.py
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

@dataclass
class Llanta:
    id: int
    sku: str
    marca: str
    modelo: str
    medida: str
    precio_venta: Decimal
    precio_historial: List[dict] = field(default_factory=list)  # [{fecha, anterior, nuevo}]

@dataclass
class Inventario:
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
class VentaDetalle:
    llanta_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

@dataclass
class Venta:
    id: int
    cliente_id: int
    asesor_id: int
    fecha: datetime
    total: Decimal

@dataclass
class DevolucionDetalle:
    llanta_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

@dataclass
class Devolucion:
    id: int
    venta_id: int
    fecha: datetime
    motivo: str
    detalles: List[DevolucionDetalle] = field(default_factory=list)
