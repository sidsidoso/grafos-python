"""Pacote ``grafos``: grafo com lista de adjacência e algoritmos clássicos."""

from .grafo import (
    ArestaInexistente,
    CicloDetectado,
    ErroGrafo,
    Grafo,
    PesoNegativo,
    VerticeInexistente,
)

__all__ = [
    "ArestaInexistente",
    "CicloDetectado",
    "ErroGrafo",
    "Grafo",
    "PesoNegativo",
    "VerticeInexistente",
]
__version__ = "1.0.0"
