import networkx as nx
import matplotlib.pyplot as plt
from grafos import dijkstra
from banco_dados import Admin

grafo = {
    'ENTRADA': {'estA': 230, 'estE': 300},
    'estA': {'ENTRADA': 230, 'estBC': 120, 'blocoA': 100, 'ADM': 100},
    'estBC': {'estA': 120, 'estD': 120, 'blocoB': 100, 'blocoC': 110},
    'estD': {'estBC': 120, 'blocoD': 100},
    'estE': {'ENTRADA': 300, 'blocoE': 85, 'blocoF': 200},
    'blocoE': {'estE': 85, 'ADM': 180, 'blocoF': 200},
    'ADM': {'estA': 100, 'blocoE': 180, 'blocoA': 120},
    'blocoF': {'estE': 200, 'blocoE': 200},
    'blocoA': {'estA': 100, 'ADM': 120, 'blocoB': 60},
    'blocoB': {'estBC': 100, 'blocoA': 60, 'blocoC': 60},
    'blocoC': {'estBC': 110, 'blocoB': 60, 'blocoD': 60},
    'blocoD': {'estD': 100, 'blocoC': 60},
}

def visualizar_grafo():
    G = nx.Graph()

    # Adiciona os nós e arestas
    for origem, destinos in grafo.items():
        for destino, peso in destinos.items():
            G.add_edge(origem, destino, weight=peso)

    # Desenhando o grafo
    pos = nx.spring_layout(G)  # Layout do grafo
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_weight='bold')
    
    # Exibe os pesos das arestas
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    plt.show()

def calcular_menor_caminho():
    print("Nós disponíveis:", ", ".join(grafo.keys()))
    origem = input("Escolha o nó de origem: ").strip()
    destino = input("Escolha o nó de destino: ").strip()

    if origem in grafo and destino in grafo:
        distancia, caminho = dijkstra(grafo, origem, destino)
        print(f"\nMenor distância: {distancia}")
        print("Caminho:", " -> ".join(caminho))
    else:
        print("Nó inválido.")

if __name__ == "__main__":
    visualizar_grafo()  # Chama a função para visualizar o grafo
    calcular_menor_caminho()  # Calcula o menor caminho
