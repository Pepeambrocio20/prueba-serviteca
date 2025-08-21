# Proyecto Serviteca – Gestión básica de Inventario y Ventas

## Descripción
Este proyecto implementa un sistema simple de **gestión de inventario y ventas para una serviteca (llantas)**.  
Permite registrar productos, clientes y asesores, controlar inventario con umbral mínimo, y realizar ventas que descuentan stock.  

El sistema está desarrollado en **Python**, funciona totalmente en memoria (sin base de datos externa) y cumple con los **requerimientos de la prueba técnica**:

- Modelado con **clases y relaciones**.
- Control de **stock disponible**.
- Cálculo correcto de **totales**.
- Datos de prueba incluidos.
- **Tests unitarios básicos** para validar la lógica.

---

## Requisitos
- Python **3.10+**
- Entorno virtual (`venv`) recomendado.

---

## Cómo ejecutar

### 1. Crear el entorno virtual
```bash
python -m venv .venv

Activar entorno virtual
.venv\Scripts\Activate

Desactivar entorno virtual
deactivate

### 2. Ejecucion del sistema
## Demo Automatica
python main.py

## Demo Manual
python main.py --cli
se vera un menu con todas las funciones como se muestra a continuacion
0) Salir
1) Ver inventario
2) Registrar llanta
3) Ajustar inventario (+/-)
4) Registrar cliente
5) Registrar asesor
6) Registrar venta
7) Listar ventas

## tests automaticos unitarios
python main.py --run-tests


## Selftests
pruebas automaticas y visibles para cada una de las funciones
python main.py --selftest
