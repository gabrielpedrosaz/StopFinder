import firebase_admin
from firebase_admin import credentials, firestore, auth
from grafos import gerar_nome_vaga, criar_grafo_estacionamento, obter_vagas_vizinhas  # Importando funções do grafos.py
import string

# Inicializar o Firebase
cred = credentials.Certificate('C:/Users/gabri/OneDrive/Área de Trabalho/StopFinder/stopfinder-8e536-firebase-adminsdk-xrdtc-ebc44ac9ac.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Variáveis global 
grafo_estacionamento = None  # Inicialmente None, pode ser criado quando necessário
letras = string.ascii_uppercase  # Letras para nomear blocos
admin_instance = None  # Inicialmente None

class Usuario:
    def __init__(self, email, user_id, role):
        self.email = email
        self.user_id = user_id
        self.role = role

    @staticmethod
    def criar_usuario(email, senha, role):
        """Cria um novo usuário no Firebase Authentication e salva suas informações no Firestore."""
        global admin_instance  # Declara a variável global no início
        if role == 'admin' and admin_instance is not None:
            print("Já existe um Admin criado. Não é possível criar outro.")
            return None
        
        user = auth.create_user(email=email, password=senha)
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
        usuario = db.collection('Usuarios').document(user_id).get()
        if usuario.exists:
            dados = usuario.to_dict()
            return dados.get('role')
        return None

    def solicitar_vaga_livre(self, estacionamento_nome, bloco_desejado, manager):
        """Solicita ao Manager a obtenção de uma vaga livre."""
        return manager.obter_vaga_livre(estacionamento_nome, bloco_desejado)

class Admin(Usuario):
    def __init__(self, email, user_id):
        super().__init__(email, user_id, 'admin')

    @staticmethod
    def salvar_estacionamento(estacionamento_nome, num_blocos, linhas_por_bloco, colunas_por_bloco):
        """Salva o estacionamento e suas vagas no Firestore."""
        global grafo_estacionamento  # Usar a variável global
        if Admin.estacionamento_existe(estacionamento_nome):
            print(f"Estacionamento '{estacionamento_nome}' já existe.")
            return None

        est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
        est_ref.set({
            'nome': estacionamento_nome,
            'num_blocos': num_blocos,
            'linhas_por_bloco': linhas_por_bloco,
            'colunas_por_bloco': colunas_por_bloco
        })

        # Criar o grafo do estacionamento se ainda não existir
        if grafo_estacionamento is None:
            grafo_estacionamento = criar_grafo_estacionamento(num_blocos, linhas_por_bloco, colunas_por_bloco)

        # Adicionar as vagas no Firestore
        for i in range(num_blocos):
            bloco_nome_atual = f"Bloco_{letras[i % len(letras)]}"
            bloco_ref = est_ref.collection('blocos').document(bloco_nome_atual)

            for linha in range(1, linhas_por_bloco + 1):
                for coluna in range(1, colunas_por_bloco + 1):
                    vaga_nome_atual = gerar_nome_vaga(bloco_nome_atual, linha, coluna)
                    vagas_vizinhas = obter_vagas_vizinhas(grafo_estacionamento, vaga_nome_atual, linhas_por_bloco, colunas_por_bloco)

                    bloco_ref.collection('vagas').document(vaga_nome_atual).set({
                        'ocupado': False,
                        'nome_vaga': vaga_nome_atual,
                        'linha': linha,
                        'coluna': coluna,
                        'vagas_vizinhas': vagas_vizinhas
                    })

    @staticmethod
    def estacionamento_existe(estacionamento_nome):
        """Verifica se o estacionamento já existe no Firestore."""
        est_ref = db.collection('Estacionamentos').document(estacionamento_nome).get()
        return est_ref.exists


class Manager(Usuario):
    def __init__(self, email, user_id):
        super().__init__(email, user_id, 'manager')

    @staticmethod
    def obter_resumo_vagas(estacionamento_nome):
        """Obtém um resumo das vagas de um estacionamento (ocupadas, livres e últimos lançamentos)."""
        est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
        vagas_ocupadas = est_ref.collection('blocos').where('ocupado', '==', True).stream()
        vagas_livres = est_ref.collection('blocos').where('ocupado', '==', False).stream()

        vagas_ocupadas = [vaga.id for vaga in vagas_ocupadas]
        vagas_livres = [vaga.id for vaga in vagas_livres]

        # Suponha que os lançamentos estejam em uma coleção 'ultimos_lancamentos'
        ultimos_lancamentos = db.collection('ultimos_lancamentos').order_by('data', direction=firestore.Query.DESCENDING).limit(3).stream()
        ultimos_lancamentos = [lancamento.to_dict()['nome_vaga'] for lancamento in ultimos_lancamentos]

        return {
            'vagas_ocupadas': vagas_ocupadas,
            'vagas_livres': vagas_livres,
            'ultimos_lancamentos': ultimos_lancamentos
        }

    def obter_vaga_livre(self, estacionamento_nome, bloco_desejado):
    #Obtém uma vaga livre no estacionamento e bloco desejado, ou em blocos vizinhos se necessário.
        def buscar_vaga_no_bloco(bloco):
            """Função auxiliar para buscar uma vaga livre em um bloco específico."""
            est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
            vagas_livres = est_ref.collection('blocos').document(bloco).collection('vagas').where('ocupado', '==', False).stream()
            return [vaga.id for vaga in vagas_livres]

        def atualizar_status_vaga(estacionamento_nome, bloco_nome, vaga_nome, status_ocupado):
            """Atualiza o status de uma vaga específica no Firestore."""
            est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
            vaga_ref = est_ref.collection('blocos').document(bloco_nome).collection('vagas').document(vaga_nome)
            vaga_ref.update({'ocupado': status_ocupado})
            print(f"Status da vaga {vaga_nome} no bloco {bloco_nome} atualizado para {'ocupado' if status_ocupado else 'livre'}.")


        resumo = self.obter_resumo_vagas(estacionamento_nome)  # Obtenha o resumo das vagas
        vagas_livres = resumo['vagas_livres']  # Pegue a lista de vagas livres
        ultimos_lancamentos = resumo['ultimos_lancamentos']  # Pegue a lista de últimos lançamentos

        # Filtra as vagas livres pelo bloco desejado, excluindo as vagas que estão nos últimos lançamentos
        vagas_no_bloco = [
            vaga for vaga in vagas_livres 
            if bloco_desejado in vaga and vaga not in ultimos_lancamentos
        ]

        if vagas_no_bloco:
            vaga_escolhida = vagas_no_bloco[0]  # Retorna a primeira vaga livre encontrada

            # Usa a função auxiliar para atualizar o status da vaga escolhida
            atualizar_status_vaga(estacionamento_nome, bloco_desejado, vaga_escolhida, True)

            return vaga_escolhida
        else:
            # Caso não encontre vagas no bloco desejado, buscar em blocos vizinhos
            print(f"Nenhuma vaga livre encontrada no bloco {bloco_desejado}, procurando em blocos vizinhos...")
            for bloco_vizinho in self.obter_blocos_vizinhos(bloco_desejado):
                vagas_no_vizinho = [
                    vaga for vaga in vagas_livres 
                    if bloco_vizinho in vaga and vaga not in ultimos_lancamentos
                ]
                if vagas_no_vizinho:
                    vaga_escolhida = vagas_no_vizinho[0]
                    atualizar_status_vaga(estacionamento_nome, bloco_vizinho, vaga_escolhida, True)
                    return vaga_escolhida

            print(f"Nenhuma vaga disponível nos blocos vizinhos.")
            return None

class Motorista(Usuario):
    def __init__(self, email, user_id):
        super().__init__(email, user_id, 'motorista')
