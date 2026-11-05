# Grafos em Python

[![CI](https://github.com/sidsidoso/grafos-python/actions/workflows/ci.yml/badge.svg)](https://github.com/sidsidoso/grafos-python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)

Implementação didática e completa de um **grafo** em Python puro (somente biblioteca padrão),
com lista de adjacência baseada em `dict`, suporte a grafos **dirigidos ou não dirigidos** e
**ponderados opcionalmente**. Inclui os algoritmos clássicos da disciplina de Estrutura de Dados:
BFS, DFS iterativa, caminho mínimo sem peso, **Dijkstra** com `heapq`, **ordenação topológica**
(Kahn), componentes conexos e detecção de ciclo.

A demonstração monta um mapa rodoviário de cidades de **Goiás** e calcula o menor caminho
de **Trindade** até **Caldas Novas**.

## Sumário

- [Conceito](#conceito)
- [Operações e complexidade](#operações-e-complexidade)
- [Decisões de implementação e otimizações](#decisões-de-implementação-e-otimizações)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Como executar](#como-executar)
- [Como testar](#como-testar)
- [Exemplo de uso](#exemplo-de-uso)
- [Saída da demonstração](#saída-da-demonstração)
- [Referências](#referências)

## Conceito

Um grafo `G = (V, E)` é um conjunto de **vértices** ligados por **arestas**. Aqui ele é
representado por **lista de adjacência**: cada vértice guarda um dicionário
`{vizinho: peso}`. O mapa da demonstração (distâncias aproximadas, em km):

```text
                      Anápolis
                         |
                         | 55
                         |
   Trindade ---25--- Goiânia ---20--- Aparecida de Goiânia
                         |                 |
                         | 33              | 22
                         |                 |
                     Hidrolândia ----------+
                     /         \
                 58 /           \ 98
                   /             \
          Piracanjuba ----55---- Morrinhos ----76---- Itumbiara
                   \             /
                 85 \           / 57
                     \         /
                     Caldas Novas
```

Representação interna (trecho):

```text
_adj = {
    "Goiânia":     {"Trindade": 25, "Aparecida de Goiânia": 20, "Anápolis": 55, "Hidrolândia": 33},
    "Trindade":    {"Goiânia": 25},
    "Hidrolândia": {"Goiânia": 33, "Aparecida de Goiânia": 22, "Piracanjuba": 58, "Morrinhos": 98},
    ...
}
```

Em um grafo **não dirigido** cada aresta é gravada nos dois sentidos; em um **dirigido**,
apenas em `origem -> destino`.

**Dijkstra** expande sempre o vértice de menor distância provisória (fila de prioridade).
Para Trindade → Caldas Novas ele descobre que ir por Piracanjuba (201 km) é melhor que ir por
Morrinhos (213 km), embora os dois caminhos tenham 4 trechos.

## Operações e complexidade

`V` = número de vértices, `E` = número de arestas, `grau(v)` = quantidade de vizinhos de `v`.

| Operação / algoritmo | Método | Tempo | Espaço extra |
|---|---|---|---|
| Adicionar vértice | `adicionar_vertice(v)` | O(1) | — |
| Remover vértice (não dirigido) | `remover_vertice(v)` | O(grau(v)) | — |
| Remover vértice (dirigido) | `remover_vertice(v)` | O(V) | — |
| Adicionar / atualizar aresta | `adicionar_aresta(u, v, peso)` | O(1) | — |
| Remover aresta | `remover_aresta(u, v)` | O(1) | — |
| Consultar aresta / peso | `tem_aresta`, `peso` | O(1) | — |
| Listar vizinhos | `vizinhos(v)` | O(grau(v)) | O(grau(v)) |
| Busca em largura | `bfs(origem)` | O(V + E) | O(V) |
| Busca em profundidade (iterativa) | `dfs(origem)` | O(V + E) | O(V) |
| Caminho com menos arestas | `caminho_mais_curto(u, v)` | O(V + E) | O(V) |
| Dijkstra (todas as distâncias) | `dijkstra(origem)` | O((V + E) log V) | O(V + E) |
| Menor caminho ponderado | `menor_caminho(u, v)` | O((V + E) log V) | O(V + E) |
| Ordenação topológica (Kahn) | `ordenacao_topologica()` | O(V + E) | O(V) |
| Componentes conexos | `componentes_conexos()` | O(V + E) | O(V) (+ O(E) se dirigido) |
| Detecção de ciclo (dirigido) | `tem_ciclo()` | O(V + E) | O(V) |
| Detecção de ciclo (não dirigido) | `tem_ciclo()` | O(E · α(V)) | O(V) |

As complexidades O(1) são médias (tabela hash). `α` é a inversa da função de Ackermann
(praticamente constante).

## Decisões de implementação e otimizações

- **`dict` de `dict` em vez de lista de listas**: inserção, remoção e consulta de aresta em
  O(1) médio, vértices de qualquer tipo *hashable* (strings, tuplas, inteiros) e ordem de inserção
  preservada, o que deixa BFS/DFS **determinísticas** e os testes reproduzíveis.
- **DFS iterativa com pilha de iteradores**: em vez de empilhar todos os vizinhos de uma vez,
  cada nível guarda um `iter()` dos vizinhos. Isso reproduz *exatamente* a ordem da DFS
  recursiva, usa O(V) de memória e não estoura o limite de recursão do Python (testado com uma
  cadeia de 200 000 vértices).
- **Dijkstra com *lazy deletion***: o `heapq` não tem *decrease-key*; quando uma distância
  melhora, uma nova entrada é inserida e as entradas obsoletas são descartadas ao sair do heap
  (conjunto `finalizados`).
- **Desempate no heap**: as entradas são `(distância, contador, vértice)`. O contador evita que
  o Python tente comparar dois vértices (o que falharia para tipos não ordenáveis).
- **Parada antecipada**: `menor_caminho` interrompe o Dijkstra quando o destino é finalizado, e
  `caminho_mais_curto` interrompe a BFS quando o destino é descoberto.
- **Pesos negativos são rejeitados** com `PesoNegativo` antes de rodar o Dijkstra (a verificação é
  O(E) e não altera a complexidade total).
- **Kahn com detecção de ciclo**: se sobrarem vértices com grau de entrada positivo, é lançada
  `CicloDetectado`, cujo atributo `pendentes` lista os vértices que ficaram de fora (no ciclo ou
  dependentes dele).
- **Detecção de ciclo**: DFS de três cores (branco/cinza/preto) para grafos dirigidos, também
  iterativa; **Union-Find** com compressão de caminho e união por tamanho para não dirigidos.
- **Grafo não ponderado protege o peso**: passar peso diferente de 1 em grafo não ponderado
  lança `ValueError`, evitando resultados confusos. `NaN` é sempre rejeitado.
- **Exceções específicas** (`VerticeInexistente`, `ArestaInexistente`, `PesoNegativo`,
  `CicloDetectado`) herdam de `ErroGrafo`; as de busca também herdam de `KeyError`.
- `__slots__` na classe e *type hints* genéricos (`Grafo[str]`, `Grafo[int]`).

## Estrutura de pastas

```text
grafos-python/
├── .github/workflows/ci.yml   # testes + demo em Python 3.11, 3.12 e 3.13
├── src/grafos/
│   ├── __init__.py            # API pública
│   ├── __main__.py            # python -m grafos
│   ├── demo.py                # mapa de Goiás e grade de disciplinas
│   └── grafo.py               # classe Grafo, exceções e Union-Find
├── tests/
│   └── test_grafo.py          # unittest: bordas + testes aleatórios contra oráculos
├── main.py                    # demonstração (não exige instalação)
├── pyproject.toml
├── LICENSE
└── README.md
```

## Como executar

Requisito: **Python 3.11+**. Não há dependências externas.

**Linux / macOS**

```bash
git clone https://github.com/sidsidoso/grafos-python.git
cd grafos-python
python3 main.py
# ou, como módulo:
PYTHONPATH=src python3 -m grafos
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/sidsidoso/grafos-python.git
cd grafos-python
py main.py
# ou, como módulo:
$env:PYTHONPATH = "src"; py -m grafos
```

Opcionalmente, instale o pacote em modo editável: `pip install -e .`.

## Como testar

```bash
# Linux / macOS
python3 -m unittest discover -s tests -v
```

```powershell
# Windows
py -m unittest discover -s tests -v
```

A suíte cobre casos de borda (grafo vazio, laços, vértice isolado, vértice/aresta inexistente,
peso negativo ou NaN) e **testes aleatórios contra oráculos**:

- Dijkstra comparado com **Bellman-Ford** em 300 grafos aleatórios (distâncias e soma dos
  pesos do caminho reconstruído);
- caminho sem peso (BFS) comparado com Bellman-Ford de pesos unitários;
- DFS iterativa comparada com uma **DFS recursiva** de referência;
- ordenação topológica validada aresta por aresta e detecção de ciclo comparada com força bruta;
- componentes conexos e ciclo não dirigido validados pela propriedade `|E| = |V| - C` das
  florestas.

Resultado local:

```text
Ran 37 tests in 0.468s

OK
```

## Exemplo de uso

```python
from grafos import Grafo

mapa = Grafo.de_arestas(
    [("Goiânia", "Trindade", 25), ("Goiânia", "Hidrolândia", 33),
     ("Hidrolândia", "Piracanjuba", 58), ("Piracanjuba", "Caldas Novas", 85)],
    ponderado=True,
)
custo, caminho = mapa.menor_caminho("Trindade", "Caldas Novas")
print(custo, caminho)
# 201.0 ['Trindade', 'Goiânia', 'Hidrolândia', 'Piracanjuba', 'Caldas Novas']

grade = Grafo.de_arestas([("Algoritmos I", "Estrutura de Dados"),
                          ("Estrutura de Dados", "Teoria dos Grafos")], dirigido=True)
print(grade.ordenacao_topologica())
# ['Algoritmos I', 'Estrutura de Dados', 'Teoria dos Grafos']
```

## Saída da demonstração

Saída real de `python main.py`:

```text
=== Grafos em Python: mapa de Goiás ===
Grafo(dirigido=False, ponderado=True, vertices=9, arestas=11)

Trechos (km)
------------
  Goiânia                <-> Trindade                  25
  Goiânia                <-> Aparecida de Goiânia      20
  Goiânia                <-> Anápolis                  55
  Goiânia                <-> Hidrolândia               33
  Aparecida de Goiânia   <-> Hidrolândia               22
  Hidrolândia            <-> Piracanjuba               58
  Hidrolândia            <-> Morrinhos                 98
  Piracanjuba            <-> Morrinhos                 55
  Piracanjuba            <-> Caldas Novas              85
  Morrinhos              <-> Caldas Novas              57
  Morrinhos              <-> Itumbiara                 76

Travessias a partir de Goiânia
------------------------------
  BFS: Goiânia -> Trindade -> Aparecida de Goiânia -> Anápolis -> Hidrolândia -> Piracanjuba -> Morrinhos -> Caldas Novas -> Itumbiara
  DFS: Goiânia -> Trindade -> Aparecida de Goiânia -> Hidrolândia -> Piracanjuba -> Morrinhos -> Caldas Novas -> Itumbiara -> Anápolis

Menos trechos: Trindade -> Caldas Novas (BFS, ignora km)
--------------------------------------------------------
  Trindade -> Goiânia -> Hidrolândia -> Piracanjuba -> Caldas Novas  (4 trechos)

Menor distância: Trindade -> Caldas Novas (Dijkstra)
----------------------------------------------------
  Trindade               -> Goiânia                   25 km  (acumulado    25 km)
  Goiânia                -> Hidrolândia               33 km  (acumulado    58 km)
  Hidrolândia            -> Piracanjuba               58 km  (acumulado   116 km)
  Piracanjuba            -> Caldas Novas              85 km  (acumulado   201 km)
  Total: 201 km

Distâncias mínimas a partir de Trindade
---------------------------------------
  Trindade                   0 km
  Goiânia                   25 km
  Aparecida de Goiânia      45 km
  Hidrolândia               58 km
  Anápolis                  80 km
  Piracanjuba              116 km
  Morrinhos                156 km
  Caldas Novas             201 km
  Itumbiara                232 km

Estrutura do mapa
-----------------
  Componentes conexos: 1
  Possui ciclo? sim

Grade de disciplinas (ordenação topológica de Kahn)
---------------------------------------------------
  1. Algoritmos I
  2. Matemática Discreta
  3. Cálculo I
  4. Algoritmos II
  5. Cálculo II
  6. Estrutura de Dados
  7. Teoria dos Grafos
  8. Banco de Dados
  Possui ciclo? não
  + aresta 'Teoria dos Grafos' -> 'Algoritmos I'
  CicloDetectado: o grafo possui ciclo: 5 vértice(s) ficaram sem ordenação
  Pendentes (ciclo e dependentes): Algoritmos I, Algoritmos II, Estrutura de Dados, Teoria dos Grafos, Banco de Dados
```

## Referências

- CORMEN, T. H.; LEISERSON, C. E.; RIVEST, R. L.; STEIN, C. *Algoritmos: Teoria e Prática*.
  3. ed. Elsevier, 2012. Capítulos 22 (Algoritmos Elementares em Grafos) e 24 (Caminhos Mínimos
  de Fonte Única).
- SEDGEWICK, R.; WAYNE, K. *Algorithms*. 4. ed. Addison-Wesley, 2011. Capítulo 4 (Graphs).
- DIJKSTRA, E. W. A note on two problems in connexion with graphs. *Numerische Mathematik*,
  v. 1, p. 269–271, 1959.
- KAHN, A. B. Topological sorting of large networks. *Communications of the ACM*, v. 5, n. 11,
  p. 558–562, 1962.
- Documentação do Python: [`heapq`](https://docs.python.org/pt-br/3/library/heapq.html) e
  [`collections.deque`](https://docs.python.org/pt-br/3/library/collections.html#collections.deque).

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
