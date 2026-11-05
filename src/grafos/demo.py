"""Demonstração: mapa rodoviário (aproximado) de cidades de Goiás e grade de disciplinas."""

from __future__ import annotations

from .grafo import CicloDetectado, Grafo

# Distâncias rodoviárias aproximadas, em km (valores didáticos).
TRECHOS_GOIAS: list[tuple[str, str, float]] = [
    ("Goiânia", "Trindade", 25),
    ("Goiânia", "Aparecida de Goiânia", 20),
    ("Goiânia", "Anápolis", 55),
    ("Goiânia", "Hidrolândia", 33),
    ("Aparecida de Goiânia", "Hidrolândia", 22),
    ("Hidrolândia", "Piracanjuba", 58),
    ("Hidrolândia", "Morrinhos", 98),
    ("Piracanjuba", "Morrinhos", 55),
    ("Piracanjuba", "Caldas Novas", 85),
    ("Morrinhos", "Caldas Novas", 57),
    ("Morrinhos", "Itumbiara", 76),
]

PRE_REQUISITOS: list[tuple[str, str]] = [
    ("Algoritmos I", "Algoritmos II"),
    ("Algoritmos II", "Estrutura de Dados"),
    ("Matemática Discreta", "Estrutura de Dados"),
    ("Estrutura de Dados", "Teoria dos Grafos"),
    ("Matemática Discreta", "Teoria dos Grafos"),
    ("Estrutura de Dados", "Banco de Dados"),
    ("Cálculo I", "Cálculo II"),
]


def montar_mapa_goias() -> Grafo[str]:
    """Grafo não dirigido e ponderado com as cidades do mapa."""
    return Grafo.de_arestas(TRECHOS_GOIAS, dirigido=False, ponderado=True)


def montar_grade() -> Grafo[str]:
    """Grafo dirigido de pré-requisitos (aresta A -> B: cursar A antes de B)."""
    return Grafo.de_arestas(PRE_REQUISITOS, dirigido=True)


def _titulo(texto: str) -> None:
    print()
    print(texto)
    print("-" * len(texto))


def executar() -> None:
    """Executa a demonstração completa no terminal."""
    mapa = montar_mapa_goias()
    print("=== Grafos em Python: mapa de Goiás ===")
    print(mapa)

    _titulo("Trechos (km)")
    for u, v, km in mapa.arestas():
        print(f"  {u:<22} <-> {v:<22} {km:>5.0f}")

    _titulo("Travessias a partir de Goiânia")
    print("  BFS:", " -> ".join(mapa.bfs("Goiânia")))
    print("  DFS:", " -> ".join(mapa.dfs("Goiânia")))

    _titulo("Menos trechos: Trindade -> Caldas Novas (BFS, ignora km)")
    trechos = mapa.caminho_mais_curto("Trindade", "Caldas Novas")
    assert trechos is not None
    print(f"  {' -> '.join(trechos)}  ({len(trechos) - 1} trechos)")

    _titulo("Menor distância: Trindade -> Caldas Novas (Dijkstra)")
    resultado = mapa.menor_caminho("Trindade", "Caldas Novas")
    assert resultado is not None
    total, caminho = resultado
    acumulado = 0.0
    for u, v in zip(caminho, caminho[1:]):
        km = mapa.peso(u, v)
        acumulado += km
        print(f"  {u:<22} -> {v:<22} {km:>5.0f} km  (acumulado {acumulado:>5.0f} km)")
    print(f"  Total: {total:.0f} km")

    _titulo("Distâncias mínimas a partir de Trindade")
    distancias, _ = mapa.dijkstra("Trindade")
    for cidade, km in sorted(distancias.items(), key=lambda item: item[1]):
        print(f"  {cidade:<22} {km:>5.0f} km")

    _titulo("Estrutura do mapa")
    print(f"  Componentes conexos: {len(mapa.componentes_conexos())}")
    print(f"  Possui ciclo? {'sim' if mapa.tem_ciclo() else 'não'}")

    grade = montar_grade()
    _titulo("Grade de disciplinas (ordenação topológica de Kahn)")
    for i, disciplina in enumerate(grade.ordenacao_topologica(), start=1):
        print(f"  {i}. {disciplina}")
    print(f"  Possui ciclo? {'sim' if grade.tem_ciclo() else 'não'}")

    grade.adicionar_aresta("Teoria dos Grafos", "Algoritmos I")
    print("  + aresta 'Teoria dos Grafos' -> 'Algoritmos I'")
    try:
        grade.ordenacao_topologica()
    except CicloDetectado as erro:
        print(f"  CicloDetectado: {erro}")
        print(f"  Pendentes (ciclo e dependentes): {', '.join(map(str, erro.pendentes))}")
