import string
import networkx as nx

# Variável global para letras dos blocos
letras = string.ascii_uppercase

def gerar_nome_vaga(bloco, linha, coluna):
    """Gera o nome da vaga baseado no bloco, linha e coluna."""
    return f"{bloco}_Vaga_{linha:02d}_{coluna:02d}"

def criar_grafo_estacionamento(num_blocos, linhas_por_bloco, colunas_por_bloco):
    """Cria o grafo de um estacionamento com entrada, blocos e vagas."""
    grafo = nx.Graph()  # Cria um grafo não-direcionado
    pos = {}  # Dicionário para armazenar as posições dos nós

    # Adiciona o nó de entrada
    grafo.add_node("Entrada")
    pos["Entrada"] = (0, num_blocos + 1)  # Posiciona a entrada acima dos blocos

    for i in range(num_blocos):
        bloco_nome = f"Bloco_{letras[i % len(letras)]}"
        
        # Conecta a entrada ao bloco
        grafo.add_node(bloco_nome)  # Adiciona o bloco como um nó
        grafo.add_edge("Entrada", bloco_nome)  # Conecta a entrada ao bloco

        # Posiciona os blocos de forma espaçada horizontalmente
        pos[bloco_nome] = (i * (colunas_por_bloco + 1), num_blocos)

        # Adiciona as vagas e conecta ao bloco
        for linha in range(1, linhas_por_bloco + 1):
            for coluna in range(1, colunas_por_bloco + 1):
                vaga_nome = gerar_nome_vaga(bloco_nome, linha, coluna)
                grafo.add_node(vaga_nome, ocupado=False, bloco=bloco_nome)  # Adiciona cada vaga como nó
                
                # Conecta a vaga ao bloco
                grafo.add_edge(bloco_nome, vaga_nome)

                # Define a posição da vaga com base na linha e coluna
                pos[vaga_nome] = (i * (colunas_por_bloco + 1) + coluna, -linha)

                # Conecta a vaga com a anterior na mesma linha (vagas adjacentes na horizontal)
                if coluna > 1:
                    vaga_anterior = gerar_nome_vaga(bloco_nome, linha, coluna - 1)
                    grafo.add_edge(vaga_nome, vaga_anterior)

                # Conecta a vaga com a da linha anterior na mesma coluna (vagas adjacentes na vertical)
                if linha > 1:
                    vaga_acima = gerar_nome_vaga(bloco_nome, linha - 1, coluna)
                    grafo.add_edge(vaga_nome, vaga_acima)

    # Conectar blocos adjacentes entre si
    for i in range(len(letras) - 1):
        grafo.add_edge(f"Bloco_{letras[i]}", f"Bloco_{letras[i + 1]}")

    return grafo, pos

def obter_vagas_vizinhas(grafo, vaga, linhas_por_bloco, colunas_por_bloco):
    """Obtém as vagas vizinhas de uma vaga específica, considerando vizinhos em linha e coluna."""
    partes = vaga.split("_")
    bloco = partes[0]
    linha = int(partes[2])  # Extraindo linha
    coluna = int(partes[3])  # Extraindo coluna

    vizinhas = []

    # Verificando vizinhos em linha
    for delta in [-1, 1]:  # Para cima e para baixo
        nova_linha = linha + delta
        if 1 <= nova_linha <= linhas_por_bloco:
            vizinha = gerar_nome_vaga(bloco, nova_linha, coluna)
            vizinhas.append(vizinha)

    # Verificando vizinhos em coluna
    for delta in [-1, 1]:  # Para esquerda e direita
        nova_coluna = coluna + delta
        if 1 <= nova_coluna <= colunas_por_bloco:
            vizinha = gerar_nome_vaga(bloco, linha, nova_coluna)
            vizinhas.append(vizinha)

    return vizinhas