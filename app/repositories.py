# app/repositories.py
from typing import Dict, List, Optional
from .models import Llanta, Inventario, Cliente, Asesor, Venta, VentaDetalle, Devolucion

class InMemoryRepo:
    def __init__(self):
        self._data: Dict[int, object] = {}
        self._auto = 1

    def add(self, obj):
        obj.id = self._auto
        self._data[self._auto] = obj
        self._auto += 1
        return obj

    def get(self, _id: int):
        return self._data.get(_id)

    def list(self):
        return list(self._data.values())

    def set(self, _id: int, obj):
        self._data[_id] = obj

class RepoLlantas(InMemoryRepo): ...
class RepoClientes(InMemoryRepo): ...
class RepoAsesores(InMemoryRepo): ...
class RepoVentas(InMemoryRepo): ...
class RepoDevoluciones(InMemoryRepo): ...

class RepoInventarios:
    def __init__(self):
        self._by_llanta: Dict[int, Inventario] = {}

    def get(self, llanta_id: int) -> Optional[Inventario]:
        return self._by_llanta.get(llanta_id)

    def create_or_update(self, inv: Inventario):
        self._by_llanta[inv.llanta_id] = inv
        return inv

    def list(self) -> List[Inventario]:
        return list(self._by_llanta.values())
