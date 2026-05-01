"""Punto de entrada de la aplicacion.

Mantenido por compatibilidad con ``uvicorn app:app`` y para ejecucion directa
con ``python app.py``. La logica vive en el paquete ``src``.
"""

from __future__ import annotations

import uvicorn

from src.main import app

__all__ = ["app"]


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
