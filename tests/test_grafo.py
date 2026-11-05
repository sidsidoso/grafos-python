"""Testes da classe Grafo: operações básicas, travessias e algoritmos."""

import itertools
import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grafos import (  # noqa: E402
    ArestaInexistente,
    CicloDetectado,
    ErroGrafo,
    Grafo,
    PesoNegativo,
    VerticeInexistente,
)
from grafos.demo import montar_grade, montar_mapa_goias  # noqa: E402

# ----------------------------------------------------------------- oráculos


def bellman_ford(grafo: Grafo[int], origem: int) -> dict[int, float]:
    """Oráculo simples de caminho mínimo (relaxa todas as arestas V-1 vezes)."""
    dist = {v: math.inf for v in grafo.vertices()}
    dist[origem] = 0.0
    arestas = list(grafo.arestas())
    if not grafo.dirigido:
        arestas += [(v, u, p) for u, v, p in arestas]
    for _ in range(len(dist) - 1):
        for u, v, p in arestas:
            if dist[u] + p < dist[v]:
                dist[v] = dist[u] + p
    return {v: d for v, d in dist.items() if d != math.inf}


def dfs_recursiva(grafo: Grafo[int], v: int, visitados: set[int], ordem: list[int]) -> None:
    visitados.add(v)
    ordem.append(v)
    for w in grafo.vizinhos(v):
        if w not in visitados:
            dfs_recursiva(grafo, w, visitados, ordem)


def tem_ciclo_forca_bruta(grafo: Grafo[int]) -> bool:
    """Dirigido: existe ciclo se algum vértice alcança a si mesmo."""
    for s in grafo.vertices():
        pilha = list(grafo.vizinhos(s))
        vistos: set[int] = set()
        while pilha:
            v = pilha.pop()
            if v == s:
                return True
            if v not in vistos:
                vistos.add(v)
                pilha.extend(grafo.vizinhos(v))
    return False


def grafo_aleatorio(
    rng: random.Random, n: int, prob: float, dirigido: bool, ponderado: bool = False
) -> Grafo[int]:
    g: Grafo[int] = Grafo(dirigido=dirigido, ponderado=ponderado)
    for v in range(n):
        g.adicionar_vertice(v)
    for u, v in itertools.product(range(n), repeat=2):
        if u != v and rng.random() < prob:
            g.adicionar_aresta(u, v, rng.randint(0, 20) if ponderado else 1.0)
    return g


# -------------------------------------------------------------------- testes


class TestOperacoesBasicas(unittest.TestCase):
    def test_grafo_vazio(self) -> None:
        g: Grafo[str] = Grafo()
        self.assertEqual(len(g), 0)
        self.assertEqual(g.num_arestas, 0)
        self.assertEqual(g.componentes_conexos(), [])
        self.assertFalse(g.tem_ciclo())
        self.assertTrue(g.eh_conexo())
        self.assertEqual(list(g.arestas()), [])

    def test_adicionar_vertice_repetido(self) -> None:
        g: Grafo[str] = Grafo()
        self.assertTrue(g.adicionar_vertice("A"))
        self.assertFalse(g.adicionar_vertice("A"))
        self.assertEqual(g.num_vertices, 1)
        self.assertIn("A", g)

    def test_aresta_nao_dirigida_e_simetrica(self) -> None:
        g: Grafo[str] = Grafo()
        g.adicionar_aresta("A", "B")
        self.assertTrue(g.tem_aresta("A", "B"))
        self.assertTrue(g.tem_aresta("B", "A"))
        self.assertEqual(g.num_arestas, 1)
        self.assertEqual(list(g.arestas()), [("A", "B", 1.0)])

    def test_aresta_dirigida_nao_e_simetrica(self) -> None:
        g: Grafo[str] = Grafo(dirigido=True)
        g.adicionar_aresta("A", "B")
        self.assertTrue(g.tem_aresta("A", "B"))
        self.assertFalse(g.tem_aresta("B", "A"))
        self.assertEqual(g.grau("A"), 1)
        self.assertEqual(g.grau("B"), 0)

    def test_aresta_repetida_atualiza_peso(self) -> None:
        g: Grafo[str] = Grafo(ponderado=True)
        g.adicionar_aresta("A", "B", 5)
        g.adicionar_aresta("B", "A", 7)
        self.assertEqual(g.num_arestas, 1)
        self.assertEqual(g.peso("A", "B"), 7)

    def test_peso_em_grafo_nao_ponderado(self) -> None:
        g: Grafo[str] = Grafo()
        with self.assertRaises(ValueError):
            g.adicionar_aresta("A", "B", 3)

    def test_peso_nan(self) -> None:
        g: Grafo[str] = Grafo(ponderado=True)
        with self.assertRaises(ValueError):
            g.adicionar_aresta("A", "B", math.nan)

    def test_remover_aresta(self) -> None:
        g: Grafo[str] = Grafo()
        g.adicionar_aresta("A", "B")
        g.remover_aresta("B", "A")
        self.assertFalse(g.tem_aresta("A", "B"))
        self.assertEqual(g.num_arestas, 0)
        with self.assertRaises(ArestaInexistente):
            g.remover_aresta("A", "B")

    def test_remover_vertice_nao_dirigido(self) -> None:
        g = Grafo.de_arestas([("A", "B"), ("A", "C"), ("B", "C"), ("C", "C")])
        self.assertEqual(g.num_arestas, 4)
        g.remover_vertice("C")
        self.assertEqual(g.vertices(), ["A", "B"])
        self.assertEqual(g.num_arestas, 1)
        self.assertEqual(g.vizinhos("A"), ["B"])

    def test_remover_vertice_dirigido(self) -> None:
        g = Grafo.de_arestas([("A", "B"), ("C", "B"), ("B", "D"), ("B", "B")], dirigido=True)
        g.remover_vertice("B")
        self.assertEqual(g.num_arestas, 0)
        self.assertEqual(g.vizinhos("A"), [])
        self.assertEqual(g.vizinhos("C"), [])

    def test_vertice_inexistente(self) -> None:
        g: Grafo[str] = Grafo()
        for operacao in (g.bfs, g.dfs, g.vizinhos, g.grau, g.remover_vertice, g.dijkstra):
            with self.assertRaises(VerticeInexistente):
                operacao("X")
        self.assertIsInstance(VerticeInexistente("X"), KeyError)

    def test_peso_aresta_inexistente(self) -> None:
        g = Grafo.de_arestas([("A", "B")])
        with self.assertRaises(ArestaInexistente):
            g.peso("A", "Z")

    def test_laco_conta_uma_vez(self) -> None:
        g: Grafo[str] = Grafo()
        g.adicionar_aresta("A", "A")
        self.assertEqual(g.num_arestas, 1)
        self.assertEqual(list(g.arestas()), [("A", "A", 1.0)])
        g.remover_aresta("A", "A")
        self.assertEqual(g.num_arestas, 0)

    def test_repr(self) -> None:
        g = Grafo.de_arestas([(1, 2)])
        self.assertIn("vertices=2", repr(g))


class TestTravessias(unittest.TestCase):
    def setUp(self) -> None:
        #   1 - 2 - 4
        #   |   |
        #   3 - 5   6 (isolado)
        self.g = Grafo.de_arestas([(1, 2), (1, 3), (2, 4), (2, 5), (3, 5)])
        self.g.adicionar_vertice(6)

    def test_bfs(self) -> None:
        self.assertEqual(self.g.bfs(1), [1, 2, 3, 4, 5])

    def test_dfs(self) -> None:
        self.assertEqual(self.g.dfs(1), [1, 2, 4, 5, 3])

    def test_vertice_isolado(self) -> None:
        self.assertEqual(self.g.bfs(6), [6])
        self.assertEqual(self.g.dfs(6), [6])

    def test_dfs_profunda_nao_estoura_recursao(self) -> None:
        n = 200_000
        g: Grafo[int] = Grafo(dirigido=True)
        for i in range(n - 1):
            g.adicionar_aresta(i, i + 1)
        self.assertEqual(len(g.dfs(0)), n)
        self.assertFalse(g.tem_ciclo())
        self.assertEqual(len(g.ordenacao_topologica()), n)

    def test_dfs_igual_recursiva_aleatorio(self) -> None:
        rng = random.Random(7)
        for _ in range(200):
            g = grafo_aleatorio(rng, rng.randint(1, 12), 0.25, rng.random() < 0.5)
            s = rng.randrange(len(g))
            ordem: list[int] = []
            dfs_recursiva(g, s, set(), ordem)
            self.assertEqual(g.dfs(s), ordem)
            self.assertEqual(set(g.bfs(s)), set(ordem))


class TestCaminhos(unittest.TestCase):
    def test_caminho_bfs(self) -> None:
        g = Grafo.de_arestas([("A", "B"), ("B", "C"), ("C", "D"), ("A", "D")])
        self.assertEqual(g.caminho_mais_curto("A", "D"), ["A", "D"])
        self.assertEqual(g.caminho_mais_curto("A", "A"), ["A"])

    def test_caminho_inalcancavel(self) -> None:
        g = Grafo.de_arestas([("A", "B")], dirigido=True)
        g.adicionar_vertice("C")
        self.assertIsNone(g.caminho_mais_curto("B", "A"))
        self.assertIsNone(g.menor_caminho("A", "C"))
        with self.assertRaises(VerticeInexistente):
            g.menor_caminho("A", "Z")

    def test_dijkstra_prefere_caminho_mais_leve(self) -> None:
        g = Grafo.de_arestas(
            [("A", "B", 10), ("A", "C", 1), ("C", "D", 1), ("D", "B", 1)], ponderado=True
        )
        self.assertEqual(g.menor_caminho("A", "B"), (3.0, ["A", "C", "D", "B"]))

    def test_dijkstra_peso_negativo(self) -> None:
        g = Grafo.de_arestas([("A", "B", -1)], dirigido=True, ponderado=True)
        with self.assertRaises(PesoNegativo):
            g.dijkstra("A")

    def test_dijkstra_peso_zero(self) -> None:
        g = Grafo.de_arestas([("A", "B", 0), ("B", "C", 0)], ponderado=True)
        self.assertEqual(g.menor_caminho("A", "C"), (0.0, ["A", "B", "C"]))

    def test_dijkstra_vs_bellman_ford(self) -> None:
        rng = random.Random(2026)
        for _ in range(300):
            g = grafo_aleatorio(rng, rng.randint(1, 10), 0.3, rng.random() < 0.5, ponderado=True)
            s = rng.randrange(len(g))
            distancias, predecessor = g.dijkstra(s)
            self.assertEqual(distancias, bellman_ford(g, s))
            for destino, custo in distancias.items():
                resultado = g.menor_caminho(s, destino)
                assert resultado is not None
                total, caminho = resultado
                self.assertEqual(total, custo)
                self.assertEqual((caminho[0], caminho[-1]), (s, destino))
                soma = sum(g.peso(u, v) for u, v in zip(caminho, caminho[1:]))
                self.assertEqual(soma, custo)

    def test_bfs_vs_bellman_ford_sem_peso(self) -> None:
        rng = random.Random(99)
        for _ in range(300):
            g = grafo_aleatorio(rng, rng.randint(1, 10), 0.25, rng.random() < 0.5)
            s, t = rng.randrange(len(g)), rng.randrange(len(g))
            esperado = bellman_ford(g, s).get(t)
            caminho = g.caminho_mais_curto(s, t)
            if esperado is None:
                self.assertIsNone(caminho)
            else:
                assert caminho is not None
                self.assertEqual(len(caminho) - 1, esperado)
                for u, v in zip(caminho, caminho[1:]):
                    self.assertTrue(g.tem_aresta(u, v))


class TestEstrutura(unittest.TestCase):
    def test_topologica_simples(self) -> None:
        g = Grafo.de_arestas([("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")], dirigido=True)
        self.assertEqual(g.ordenacao_topologica(), ["a", "b", "c", "d"])

    def test_topologica_exige_dirigido(self) -> None:
        with self.assertRaises(ErroGrafo):
            Grafo.de_arestas([(1, 2)]).ordenacao_topologica()

    def test_topologica_com_ciclo(self) -> None:
        g = Grafo.de_arestas([(0, 1), (1, 2), (2, 3), (3, 1)], dirigido=True)
        with self.assertRaises(CicloDetectado) as ctx:
            g.ordenacao_topologica()
        self.assertEqual(sorted(ctx.exception.pendentes), [1, 2, 3])

    def test_topologica_aleatoria(self) -> None:
        rng = random.Random(11)
        for _ in range(300):
            g = grafo_aleatorio(rng, rng.randint(1, 9), 0.2, dirigido=True)
            esperado_ciclo = tem_ciclo_forca_bruta(g)
            self.assertEqual(g.tem_ciclo(), esperado_ciclo)
            if esperado_ciclo:
                with self.assertRaises(CicloDetectado):
                    g.ordenacao_topologica()
            else:
                ordem = g.ordenacao_topologica()
                posicao = {v: i for i, v in enumerate(ordem)}
                self.assertEqual(len(ordem), len(g))
                for u, v, _ in g.arestas():
                    self.assertLess(posicao[u], posicao[v])

    def test_ciclo_nao_dirigido(self) -> None:
        arvore = Grafo.de_arestas([(1, 2), (1, 3), (3, 4)])
        self.assertFalse(arvore.tem_ciclo())
        arvore.adicionar_aresta(4, 2)
        self.assertTrue(arvore.tem_ciclo())
        self.assertTrue(Grafo.de_arestas([(1, 1)]).tem_ciclo())

    def test_ciclo_nao_dirigido_aleatorio(self) -> None:
        # Uma floresta tem exatamente V - C arestas; mais que isso implica ciclo.
        rng = random.Random(5)
        for _ in range(300):
            g = grafo_aleatorio(rng, rng.randint(1, 10), 0.15, dirigido=False)
            floresta = g.num_arestas == len(g) - len(g.componentes_conexos())
            self.assertEqual(g.tem_ciclo(), not floresta)

    def test_componentes(self) -> None:
        g = Grafo.de_arestas([(1, 2), (3, 4), (4, 5)])
        g.adicionar_vertice(6)
        self.assertEqual(g.componentes_conexos(), [[1, 2], [3, 4, 5], [6]])
        self.assertFalse(g.eh_conexo())

    def test_componentes_fracos_dirigido(self) -> None:
        g = Grafo.de_arestas([(1, 2), (3, 2), (4, 5)], dirigido=True)
        self.assertEqual(sorted(map(sorted, g.componentes_conexos())), [[1, 2, 3], [4, 5]])

    def test_componentes_aleatorio(self) -> None:
        rng = random.Random(3)
        for _ in range(200):
            g = grafo_aleatorio(rng, rng.randint(1, 12), 0.1, rng.random() < 0.5)
            componentes = g.componentes_conexos()
            todos = [v for c in componentes for v in c]
            self.assertEqual(sorted(todos), sorted(g.vertices()))
            indice = {v: i for i, c in enumerate(componentes) for v in c}
            for u, v, _ in g.arestas():
                self.assertEqual(indice[u], indice[v])


class TestDemo(unittest.TestCase):
    def test_trindade_caldas_novas(self) -> None:
        mapa = montar_mapa_goias()
        self.assertEqual(
            mapa.menor_caminho("Trindade", "Caldas Novas"),
            (201.0, ["Trindade", "Goiânia", "Hidrolândia", "Piracanjuba", "Caldas Novas"]),
        )
        self.assertEqual(len(mapa), 9)
        self.assertTrue(mapa.eh_conexo())

    def test_grade_sem_ciclo(self) -> None:
        grade = montar_grade()
        self.assertFalse(grade.tem_ciclo())
        ordem = grade.ordenacao_topologica()
        self.assertLess(ordem.index("Algoritmos I"), ordem.index("Teoria dos Grafos"))


if __name__ == "__main__":
    unittest.main()
