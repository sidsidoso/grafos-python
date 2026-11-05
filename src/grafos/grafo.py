"""Grafo genérico com lista de adjacência baseada em dicionários."""

from __future__ import annotations

import heapq
import itertools
import math
from collections import deque
from collections.abc import Hashable, Iterable, Iterator
from typing import Generic, TypeVar

V = TypeVar("V", bound=Hashable)

__all__ = [
    "ArestaInexistente",
    "CicloDetectado",
    "ErroGrafo",
    "Grafo",
    "PesoNegativo",
    "VerticeInexistente",
]


class ErroGrafo(Exception):
    """Erro base das operações de grafo."""


class VerticeInexistente(ErroGrafo, KeyError):
    """O vértice informado não existe no grafo."""


class ArestaInexistente(ErroGrafo, KeyError):
    """A aresta informada não existe no grafo."""


class PesoNegativo(ErroGrafo, ValueError):
    """Dijkstra não aceita arestas com peso negativo."""


class CicloDetectado(ErroGrafo):
    """Há ciclo no grafo dirigido; ``pendentes``: vértices no ciclo ou dependentes dele."""

    def __init__(self, pendentes: list[object]) -> None:
        super().__init__(
            f"o grafo possui ciclo: {len(pendentes)} vértice(s) ficaram sem ordenação"
        )
        self.pendentes = pendentes


class _UniaoBusca(Generic[V]):
    """Union-Find com compressão de caminho e união por tamanho."""

    __slots__ = ("_pai", "_tamanho")

    def __init__(self, elementos: Iterable[V]) -> None:
        self._pai: dict[V, V] = {e: e for e in elementos}
        self._tamanho: dict[V, int] = dict.fromkeys(self._pai, 1)

    def encontrar(self, x: V) -> V:
        """Retorna o representante do conjunto de ``x``."""
        raiz = x
        while self._pai[raiz] != raiz:
            raiz = self._pai[raiz]
        while self._pai[x] != raiz:  # compressão de caminho
            self._pai[x], x = raiz, self._pai[x]
        return raiz

    def unir(self, a: V, b: V) -> bool:
        """Une os conjuntos; retorna ``False`` se já estavam unidos."""
        ra, rb = self.encontrar(a), self.encontrar(b)
        if ra == rb:
            return False
        if self._tamanho[ra] < self._tamanho[rb]:
            ra, rb = rb, ra
        self._pai[rb] = ra
        self._tamanho[ra] += self._tamanho[rb]
        return True


class Grafo(Generic[V]):
    """Grafo dirigido ou não dirigido, com pesos opcionais.

    Internamente usa ``dict[vertice, dict[vizinho, peso]]``: inserção, remoção e
    consulta de aresta são O(1) em média, e a ordem de inserção é preservada
    (as travessias são determinísticas).
    """

    __slots__ = ("_adj", "_dirigido", "_num_arestas", "_ponderado")

    def __init__(self, dirigido: bool = False, ponderado: bool = False) -> None:
        self._adj: dict[V, dict[V, float]] = {}
        self._dirigido = dirigido
        self._ponderado = ponderado
        self._num_arestas = 0

    # ------------------------------------------------------------------ fábrica
    @classmethod
    def de_arestas(
        cls,
        arestas: Iterable[tuple[V, V] | tuple[V, V, float]],
        dirigido: bool = False,
        ponderado: bool = False,
    ) -> Grafo[V]:
        """Cria um grafo a partir de tuplas ``(u, v)`` ou ``(u, v, peso)``."""
        grafo: Grafo[V] = cls(dirigido=dirigido, ponderado=ponderado)
        for aresta in arestas:
            if len(aresta) == 2:
                grafo.adicionar_aresta(aresta[0], aresta[1])
            else:
                grafo.adicionar_aresta(aresta[0], aresta[1], aresta[2])  # type: ignore[misc]
        return grafo

    # ------------------------------------------------------------ propriedades
    @property
    def dirigido(self) -> bool:
        """Indica se as arestas têm sentido."""
        return self._dirigido

    @property
    def ponderado(self) -> bool:
        """Indica se as arestas aceitam pesos arbitrários."""
        return self._ponderado

    @property
    def num_vertices(self) -> int:
        """Quantidade de vértices."""
        return len(self._adj)

    @property
    def num_arestas(self) -> int:
        """Quantidade de arestas (no não dirigido, cada aresta conta uma vez)."""
        return self._num_arestas

    def __len__(self) -> int:
        return len(self._adj)

    def __contains__(self, vertice: object) -> bool:
        return vertice in self._adj

    def __iter__(self) -> Iterator[V]:
        return iter(self._adj)

    def __repr__(self) -> str:
        return (
            f"Grafo(dirigido={self._dirigido}, ponderado={self._ponderado}, "
            f"vertices={self.num_vertices}, arestas={self.num_arestas})"
        )

    # --------------------------------------------------------------- consultas
    def _exigir(self, vertice: V) -> dict[V, float]:
        try:
            return self._adj[vertice]
        except KeyError:
            raise VerticeInexistente(vertice) from None

    def tem_vertice(self, vertice: V) -> bool:
        """Retorna ``True`` se o vértice existe."""
        return vertice in self._adj

    def tem_aresta(self, origem: V, destino: V) -> bool:
        """Retorna ``True`` se existe a aresta ``origem -> destino``."""
        vizinhos = self._adj.get(origem)
        return vizinhos is not None and destino in vizinhos

    def peso(self, origem: V, destino: V) -> float:
        """Peso da aresta ``origem -> destino``."""
        try:
            return self._exigir(origem)[destino]
        except KeyError:
            raise ArestaInexistente((origem, destino)) from None

    def vertices(self) -> list[V]:
        """Lista de vértices na ordem de inserção."""
        return list(self._adj)

    def vizinhos(self, vertice: V) -> list[V]:
        """Vizinhos (sucessores, se dirigido) do vértice."""
        return list(self._exigir(vertice))

    def grau(self, vertice: V) -> int:
        """Grau do vértice (grau de saída, se dirigido)."""
        return len(self._exigir(vertice))

    def arestas(self) -> Iterator[tuple[V, V, float]]:
        """Itera ``(origem, destino, peso)``; no não dirigido, cada aresta aparece uma vez."""
        if self._dirigido:
            for u, vizinhos in self._adj.items():
                for v, p in vizinhos.items():
                    yield u, v, p
            return
        processados: set[V] = set()
        for u, vizinhos in self._adj.items():
            for v, p in vizinhos.items():
                if v not in processados:
                    yield u, v, p
            processados.add(u)

    # -------------------------------------------------------------- mutações
    def adicionar_vertice(self, vertice: V) -> bool:
        """Adiciona o vértice; retorna ``False`` se ele já existia."""
        if vertice in self._adj:
            return False
        self._adj[vertice] = {}
        return True

    def remover_vertice(self, vertice: V) -> None:
        """Remove o vértice e todas as arestas incidentes a ele."""
        vizinhos = self._exigir(vertice)
        removidas = len(vizinhos)
        if self._dirigido:
            for u, saida in self._adj.items():
                if u != vertice and vertice in saida:
                    del saida[vertice]
                    removidas += 1
        else:
            for w in vizinhos:
                if w != vertice:
                    del self._adj[w][vertice]
        del self._adj[vertice]
        self._num_arestas -= removidas

    def adicionar_aresta(self, origem: V, destino: V, peso: float = 1.0) -> None:
        """Adiciona (ou atualiza o peso de) uma aresta, criando os vértices se preciso."""
        if not self._ponderado and peso != 1.0:
            raise ValueError("grafo não ponderado: o peso deve ser 1")
        if math.isnan(peso):
            raise ValueError("peso não pode ser NaN")
        self.adicionar_vertice(origem)
        self.adicionar_vertice(destino)
        nova = destino not in self._adj[origem]
        self._adj[origem][destino] = peso
        if not self._dirigido:
            self._adj[destino][origem] = peso
        if nova:
            self._num_arestas += 1

    def remover_aresta(self, origem: V, destino: V) -> None:
        """Remove a aresta ``origem -> destino`` (e a recíproca, se não dirigido)."""
        if not self.tem_aresta(origem, destino):
            raise ArestaInexistente((origem, destino))
        del self._adj[origem][destino]
        if not self._dirigido and origem != destino:
            del self._adj[destino][origem]
        self._num_arestas -= 1

    # -------------------------------------------------------------- travessias
    def bfs(self, origem: V) -> list[V]:
        """Busca em largura; retorna os vértices na ordem de visita."""
        self._exigir(origem)
        visitados = {origem}
        ordem: list[V] = []
        fila: deque[V] = deque([origem])
        while fila:
            v = fila.popleft()
            ordem.append(v)
            for w in self._adj[v]:
                if w not in visitados:
                    visitados.add(w)
                    fila.append(w)
        return ordem

    def dfs(self, origem: V) -> list[V]:
        """Busca em profundidade iterativa (mesma ordem da versão recursiva)."""
        self._exigir(origem)
        visitados = {origem}
        ordem = [origem]
        pilha: list[Iterator[V]] = [iter(self._adj[origem])]
        while pilha:
            for w in pilha[-1]:
                if w not in visitados:
                    visitados.add(w)
                    ordem.append(w)
                    pilha.append(iter(self._adj[w]))
                    break
            else:
                pilha.pop()
        return ordem

    # --------------------------------------------------------- caminhos mínimos
    @staticmethod
    def _reconstruir(predecessor: dict[V, V], origem: V, destino: V) -> list[V]:
        caminho = [destino]
        while caminho[-1] != origem:
            caminho.append(predecessor[caminho[-1]])
        caminho.reverse()
        return caminho

    def caminho_mais_curto(self, origem: V, destino: V) -> list[V] | None:
        """Caminho com menos arestas (BFS, ignora pesos); ``None`` se inalcançável."""
        self._exigir(origem)
        self._exigir(destino)
        if origem == destino:
            return [origem]
        predecessor: dict[V, V] = {}
        visitados = {origem}
        fila: deque[V] = deque([origem])
        while fila:
            v = fila.popleft()
            for w in self._adj[v]:
                if w not in visitados:
                    visitados.add(w)
                    predecessor[w] = v
                    if w == destino:  # parada antecipada
                        return self._reconstruir(predecessor, origem, destino)
                    fila.append(w)
        return None

    def _verificar_pesos(self) -> None:
        for u, vizinhos in self._adj.items():
            for v, p in vizinhos.items():
                if p < 0:
                    raise PesoNegativo(f"aresta {u!r} -> {v!r} tem peso negativo ({p})")

    def _dijkstra(
        self, origem: V, destino: V | None = None
    ) -> tuple[dict[V, float], dict[V, V]]:
        self._exigir(origem)
        self._verificar_pesos()
        distancia: dict[V, float] = {origem: 0.0}
        predecessor: dict[V, V] = {}
        finalizados: set[V] = set()
        desempate = itertools.count()  # evita comparar vértices no heap
        heap: list[tuple[float, int, V]] = [(0.0, next(desempate), origem)]
        while heap:
            d, _, v = heapq.heappop(heap)
            if v in finalizados:  # entrada obsoleta (lazy deletion)
                continue
            finalizados.add(v)
            if v == destino:
                break
            for w, p in self._adj[v].items():
                nova = d + p
                if nova < distancia.get(w, math.inf):
                    distancia[w] = nova
                    predecessor[w] = v
                    heapq.heappush(heap, (nova, next(desempate), w))
        return distancia, predecessor

    def dijkstra(self, origem: V) -> tuple[dict[V, float], dict[V, V]]:
        """Distâncias mínimas a partir de ``origem`` e o mapa de predecessores.

        Vértices inalcançáveis não aparecem no dicionário de distâncias.
        """
        return self._dijkstra(origem)

    def menor_caminho(self, origem: V, destino: V) -> tuple[float, list[V]] | None:
        """Menor caminho ponderado (Dijkstra); retorna ``(custo, caminho)`` ou ``None``."""
        self._exigir(destino)
        distancia, predecessor = self._dijkstra(origem, destino)
        if destino not in distancia:
            return None
        return distancia[destino], self._reconstruir(predecessor, origem, destino)

    # ----------------------------------------------------------- estrutura
    def ordenacao_topologica(self) -> list[V]:
        """Ordenação topológica de Kahn; lança ``CicloDetectado`` se houver ciclo."""
        if not self._dirigido:
            raise ErroGrafo("ordenação topológica exige grafo dirigido")
        grau_entrada: dict[V, int] = dict.fromkeys(self._adj, 0)
        for vizinhos in self._adj.values():
            for w in vizinhos:
                grau_entrada[w] += 1
        fila: deque[V] = deque(v for v, g in grau_entrada.items() if g == 0)
        ordem: list[V] = []
        while fila:
            v = fila.popleft()
            ordem.append(v)
            for w in self._adj[v]:
                grau_entrada[w] -= 1
                if grau_entrada[w] == 0:
                    fila.append(w)
        if len(ordem) != len(self._adj):
            raise CicloDetectado([v for v, g in grau_entrada.items() if g > 0])
        return ordem

    def componentes_conexos(self) -> list[list[V]]:
        """Componentes conexos (fracamente conexos, se dirigido), em ordem de BFS."""
        vizinhanca: dict[V, list[V]] | dict[V, dict[V, float]]
        if self._dirigido:
            nao_dirigida: dict[V, list[V]] = {v: list(viz) for v, viz in self._adj.items()}
            for u, viz in self._adj.items():
                for w in viz:
                    nao_dirigida[w].append(u)
            vizinhanca = nao_dirigida
        else:
            vizinhanca = self._adj
        visitados: set[V] = set()
        componentes: list[list[V]] = []
        for inicio in self._adj:
            if inicio in visitados:
                continue
            visitados.add(inicio)
            componente: list[V] = []
            fila: deque[V] = deque([inicio])
            while fila:
                v = fila.popleft()
                componente.append(v)
                for w in vizinhanca[v]:
                    if w not in visitados:
                        visitados.add(w)
                        fila.append(w)
            componentes.append(componente)
        return componentes

    def eh_conexo(self) -> bool:
        """``True`` se o grafo tem no máximo um componente (fracamente) conexo."""
        return len(self.componentes_conexos()) <= 1

    def tem_ciclo(self) -> bool:
        """Detecta ciclo: DFS de três cores (dirigido) ou Union-Find (não dirigido)."""
        if not self._dirigido:
            conjuntos = _UniaoBusca(self._adj)
            return any(not conjuntos.unir(u, v) for u, v, _ in self.arestas())
        branco, cinza, preto = 0, 1, 2
        cor: dict[V, int] = dict.fromkeys(self._adj, branco)
        for inicio in self._adj:
            if cor[inicio] != branco:
                continue
            cor[inicio] = cinza
            pilha: list[tuple[V, Iterator[V]]] = [(inicio, iter(self._adj[inicio]))]
            while pilha:
                v, iterador = pilha[-1]
                for w in iterador:
                    if cor[w] == cinza:  # aresta de retorno
                        return True
                    if cor[w] == branco:
                        cor[w] = cinza
                        pilha.append((w, iter(self._adj[w])))
                        break
                else:
                    cor[v] = preto
                    pilha.pop()
        return False
