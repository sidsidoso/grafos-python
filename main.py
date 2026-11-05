"""Ponto de entrada da demonstração (funciona sem instalar o pacote)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from grafos.demo import executar  # noqa: E402

if __name__ == "__main__":
    executar()
