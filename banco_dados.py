import firebase_admin
from firebase_admin import credentials, firestore, auth
from grafos import gerar_nome_vaga, criar_grafo_estacionamento, obter_vagas_vizinhas, obter_blocos_vizinhos  # Importando funções do grafos.py
import string
from networkx.readwrite import json_graph

# Inicializar o Firebase
cred = credentials.Certificate('StopFinder/stopfinder-8e536-firebase-adminsdk-xrdtc-ebc44ac9ac.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Variáveis global 
grafo_estacionamento = None  # Inicialmente None, pode ser criado quando necessário
posicoes_estacionamento = None  # Inicialmente None, pode ser criado quando necessário
letras = string.ascii_uppercase  # Letras para nomear blocos
admin_instance = None  # Inicialmente None

class Usuario:
    def __init__(self, email, user_id, role):
        self.email = email
        self.user_id = user_id
        self.role = role

    @staticmethod
    def criar_usuario(email, role):
        """Cria um novo usuário no Firebase Authentication e salva suas informações no Firestore."""
        global admin_instance  # Declara a variável global no início
        if role == 'admin' and admin_instance is not None:
            print("Já existe um Admin criado. Não é possível criar outro.")
            return None
        
        user = auth.create_user(email=email)
        user_ref = db.collection('Usuarios').document(user.uid)
        user_ref.set({
            'email': email,
            'role': role
        })
        
        if role == 'admin':
            admin_instance = Admin(email, user.uid)  # Atualiza a instância do admin

        print(f"Usuário criado com sucesso: {email}, Role: {role}")
        return user.uid

    @staticmethod
    def validar_usuario(user_id):
        """Valida o usuário no Firestore e retorna suas permissões."""
        # Verifica se é um email ou UID pelo formato
        if "@" in user_id:
            # Tenta buscar o usuário pelo email
            user_ref = db.collection('Usuarios').where('email', '==', user_id).get()
        else:
            # Busca pelo UID diretamente
            user_ref = db.collection('Usuarios').document(user_id).get()
            user_ref = [user_ref] if user_ref.exists else []

        # Verifica se encontrou o usuário e retorna o role
        if user_ref:
            dados = user_ref[0].to_dict()
            return dados.get('role')
        return None

    def solicitar_vaga_livre(estacionamento_nome, bloco_desejado):
        """Solicita ao Manager a obtenção de uma vaga livre."""
        return Manager.obter_vaga_livre(estacionamento_nome, bloco_desejado)

class Admin(Usuario):
    def __init__(self, email, user_id):
        super().__init__(email, user_id, 'admin')

    @staticmethod
    def salvar_estacionamento(estacionamento_nome, num_blocos, linhas_por_bloco, colunas_por_bloco):
        """Salva o estacionamento e suas vagas no Firestore."""
        global grafo_estacionamento, posicoes_estacionamento

        # Verifica se o estacionamento já existe
        if Admin.estacionamento_existe(estacionamento_nome):
            print(f"Estacionamento '{estacionamento_nome}' já existe. Atualizando...")
            # Atualiza o documento do estacionamento
            est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
            try:
                est_ref.update({
                    'num_blocos': num_blocos,
                    'linhas_por_bloco': linhas_por_bloco,
                    'colunas_por_bloco': colunas_por_bloco
                })
                print(f"Informações do estacionamento '{estacionamento_nome}' atualizadas com sucesso.")
            except Exception as e:
                print(f"Erro ao atualizar informações do estacionamento: {e}")
                return None
        else:
            # Cria o documento do estacionamento se ele não existir
            try:
                est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
                est_ref.set({
                    'nome': estacionamento_nome,
                    'num_blocos': num_blocos,
                    'linhas_por_bloco': linhas_por_bloco,
                    'colunas_por_bloco': colunas_por_bloco
                })
            except Exception as e:
                print(f"Erro ao criar o documento do estacionamento: {e}")
                return None

        # Verifica se a lista 'letras' está definida
        letras = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        # Cria o grafo do estacionamento
        grafo_estacionamento, posicoes_estacionamento = criar_grafo_estacionamento(num_blocos, linhas_por_bloco, colunas_por_bloco)

        # Atualiza ou recria os blocos e vagas
        try:
            for i in range(num_blocos):
                bloco_nome_atual = f"Bloco_{letras[i % len(letras)]}"
                blocos_vizinhos = obter_blocos_vizinhos(bloco_nome_atual, num_blocos)
                bloco_ref = est_ref.collection('blocos').document(bloco_nome_atual)
                bloco_ref.set({  # `set` substitui o documento se ele já existir
                    'nome': bloco_nome_atual,
                    'blocos_vizinhos': blocos_vizinhos
                })

                for linha in range(1, linhas_por_bloco + 1):
                    for coluna in range(1, colunas_por_bloco + 1):
                        vaga_nome_atual = gerar_nome_vaga(bloco_nome_atual, linha, coluna)
                        vagas_vizinhas = obter_vagas_vizinhas(grafo_estacionamento, vaga_nome_atual, linhas_por_bloco, colunas_por_bloco)

                        # Cria ou atualiza o documento da vaga
                        vaga_ref = bloco_ref.collection('vagas').document(vaga_nome_atual)
                        vaga_ref.set({
                            'ocupado': False,  # Reseta o status de ocupação ao recriar
                            'nome_vaga': vaga_nome_atual,
                            'linha': linha,
                            'coluna': coluna,
                            'vagas_vizinhas': vagas_vizinhas
                        })
        except Exception as e:
            print(f"Erro ao criar ou atualizar blocos e vagas: {e}")
            return None

        # Salvar ou atualizar o grafo e as posições no Firebase
        try:
            # Serializar o grafo
            grafo_serializado = json_graph.node_link_data(grafo_estacionamento)

            grafo_ref = est_ref.collection('dados').document('grafo')
            grafo_ref.set({  # `set` substitui o documento existente
                'grafo': grafo_serializado
            })

            posicoes_ref = est_ref.collection('dados').document('posicoes')
            posicoes_ref.set({
                'posicoes': posicoes_estacionamento
            })
            print("Grafo e posições salvo com sucesso no Firestore.")
        except Exception as e:
            print(f"Erro ao salvar ou atualizar grafo ou posições: {e}")
            return None

        print(f"Estacionamento '{estacionamento_nome}' foi salvo ou atualizado com sucesso.")

    @staticmethod
    def carregar_grafo(estacionamento_nome):
        """
        Carrega o grafo do estacionamento a partir do Firestore.
        """
        try:
            est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
            dados_ref = est_ref.collection('dados').document('grafo').get()
            
            if dados_ref.exists:
                grafo_data = dados_ref.to_dict().get('grafo')
                posicoes_data = dados_ref.to_dict().get('posicoes')

                # Converte o JSON para um grafo
                grafo = json_graph.node_link_graph(grafo_data)
                return grafo, posicoes_data
            else:
                print(f"Grafo não encontrado para o estacionamento '{estacionamento_nome}'.")
                return None, None
        except Exception as e:
            print(f"Erro ao carregar o grafo: {e}")
            return None, None

    @staticmethod
    def estacionamento_existe(estacionamento_nome):
        """Verifica se o estacionamento já existe no Firestore."""
        est_ref = db.collection('Estacionamentos').document(estacionamento_nome).get()
        if est_ref.exists:
            return True
        else:
            return False


class Manager(Usuario):
    def __init__(self, email, user_id):
        super().__init__(email, user_id, 'manager')

    @staticmethod
    def obter_resumo_vagas(estacionamento_nome, bloco_desejado=None):
        """Obtém um resumo das vagas de um estacionamento (ocupadas, livres e últimos lançamentos).
        Se um bloco for especificado, busca apenas no bloco.
        """
        est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
        
        if bloco_desejado:
            # Caso um bloco específico seja fornecido, busca apenas nesse bloco
            bloco_ref = est_ref.collection('blocos').document(bloco_desejado)
            vagas_ocupadas = bloco_ref.collection('vagas').where('ocupado', '==', True).stream()
            vagas_livres = bloco_ref.collection('vagas').where('ocupado', '==', False).stream()
        else:
            # Caso não seja fornecido um bloco específico, busca em todos os blocos
            vagas_ocupadas = est_ref.collection('blocos').where('ocupado', '==', True).stream()
            vagas_livres = est_ref.collection('blocos').where('ocupado', '==', False).stream()

        vagas_ocupadas = [vaga.id for vaga in vagas_ocupadas]
        vagas_livres = [vaga.id for vaga in vagas_livres]

        # Suponha que os lançamentos estejam em uma coleção 'ultimos_lancamentos'
        ultimos_lancamentos = db.collection('ultimos_lancamentos').order_by('data', direction=firestore.Query.DESCENDING).limit(10).stream()
        ultimos_lancamentos = [lancamento.to_dict()['nome_vaga'] for lancamento in ultimos_lancamentos]

        # Busca informações dos blocos e seus vizinhos
        blocos_vizinhos = {}
        blocos = est_ref.collection('blocos').stream()
        for bloco in blocos:
            bloco_data = bloco.to_dict()
            blocos_vizinhos[bloco.id] = bloco_data.get('blocos_vizinhos', [])

        return {
            'vagas_ocupadas': vagas_ocupadas,
            'vagas_livres': vagas_livres,
            'ultimos_lancamentos': ultimos_lancamentos,
            'blocos_vizinhos': blocos_vizinhos
        }

    def obter_vaga_livre(estacionamento_nome, bloco_desejado):
    #Obtém uma vaga livre no estacionamento e bloco desejado, ou em blocos vizinhos se necessário.
        # Função para buscar vagas livres num bloco específico
        def buscar_vaga_no_bloco(bloco_nome):
            est_ref = db.collection('Estacionamentos').document(estacionamento_nome) \
                .collection('blocos').document(bloco_nome).collection('vagas')
            vagas_livres = est_ref.where('ocupado', '==', False).stream()
            return [vaga.id for vaga in vagas_livres]

        # Função para atualizar o status de uma vaga
        def atualizar_status_vaga(estacionamento_nome, bloco_nome, vaga_nome, status_ocupado):
            vaga_ref = db.collection('Estacionamentos').document(estacionamento_nome) \
                .collection('blocos').document(bloco_nome).collection('vagas').document(vaga_nome)
            try:
                vaga_ref.update({'ocupado': status_ocupado})
                print(f"Status da vaga {vaga_nome} no bloco {bloco_nome} atualizado para {'ocupado' if status_ocupado else 'livre'}.")
            except Exception as e:
                print(f"Erro ao atualizar status da vaga {vaga_nome} no bloco {bloco_nome}: {e}")

        # Obtenha o resumo das vagas (ou você pode otimizar isso para usar a função buscar_vaga_no_bloco)
        vagas_livres = buscar_vaga_no_bloco(bloco_desejado)  # Busca as vagas livres no bloco desejado
        if vagas_livres:
            vaga_escolhida = vagas_livres[0]  # A primeira vaga livre
            atualizar_status_vaga(estacionamento_nome, bloco_desejado, vaga_escolhida, True)
            return vaga_escolhida
        else:
            # Caso não tenha vagas no bloco desejado, procurar nos blocos vizinhos
            print(f"Nenhuma vaga livre encontrada no bloco {bloco_desejado}, procurando nos blocos vizinhos...")
            
            # Aqui a função de buscar as vagas no bloco vizinho é repetida, mas ela também pode ser otimizada
            blocos_vizinhos = Manager.obter_resumo_vagas(estacionamento_nome)['blocos_vizinhos']  # Obtém blocos vizinhos
            for bloco_vizinho in blocos_vizinhos.get(bloco_desejado, []):
                vagas_no_vizinho = buscar_vaga_no_bloco(bloco_vizinho)  # Busca vagas livres no bloco vizinho
                if vagas_no_vizinho:
                    vaga_escolhida = vagas_no_vizinho[0]
                    atualizar_status_vaga(estacionamento_nome, bloco_vizinho, vaga_escolhida, True)
                    return vaga_escolhida

            print(f"Nenhuma vaga disponível nos blocos vizinhos.")
            return None
        
    @staticmethod
    def obter_resumo_estacionamento(estacionamento_nome):
        """
        Obtém um resumo geral do estacionamento, incluindo o número total de vagas,
        vagas livres, vagas ocupadas e outras informações úteis.
        """
        # Referência ao estacionamento
        est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
        
        # Inicializando contadores
        total_vagas = 0
        vagas_livres = 0
        vagas_ocupadas = 0
        blocos = 0

        # Busca informações sobre os blocos
        blocos_ref = est_ref.collection('blocos').stream()
        
        # Contando as vagas nos blocos
        for bloco in blocos_ref:
            blocos += 1  # Conta o número de blocos
            bloco_data = bloco.to_dict()

            # Busca as vagas dentro do bloco
            vagas_ref = est_ref.collection('blocos').document(bloco.id).collection('vagas').stream()

            for vaga in vagas_ref:
                total_vagas += 1  # Conta todas as vagas
                if vaga.to_dict().get('ocupado') is False:
                    vagas_livres += 1  # Conta as vagas livres
                else:
                    vagas_ocupadas += 1  # Conta as vagas ocupadas

        # Dados adicionais que poderiam ser úteis para o Manager
        resumo_estacionamento = {
            'total_vagas': total_vagas,
            'vagas_livres': vagas_livres,
            'vagas_ocupadas': vagas_ocupadas,
            'blocos_totais': blocos,
            'percentual_ocupacao': (vagas_ocupadas / total_vagas * 100) if total_vagas > 0 else 0
        }

        # Formata o percentual para 2 casas decimais
        percentual_ocupacao = f"{resumo_estacionamento['percentual_ocupacao']:.2f}%"
        
        # Retorna uma string formatada
        resultado = (
            f"Total de vagas: {resumo_estacionamento['total_vagas']}\n"
            f"Vagas livres: {resumo_estacionamento['vagas_livres']}\n"
            f"Vagas ocupadas: {resumo_estacionamento['vagas_ocupadas']}\n"
            f"Blocos totais: {resumo_estacionamento['blocos_totais']}\n"
            f"Percentual de ocupação: {percentual_ocupacao}"
        )
        
        return resultado

class Motorista(Usuario):
    def __init__(self, email, user_id):
        super().__init__(email, user_id, 'motorista')