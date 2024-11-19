import firebase_admin
from firebase_admin import credentials, firestore
from grafos import criar_grafo_estacionamento, dijkstra

cred = credentials.Certificate("C:/Users/gabri/OneDrive/Área de Trabalho/StopFinder/stopfinder-8e536-firebase-adminsdk-xrdtc-ebc44ac9ac.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class Admin:
    @staticmethod
    def carregar_grafo(estacionamento_nome):
        """Carrega o grafo do Firebase."""
        try:
            est_ref = db.collection('Estacionamentos').document(estacionamento_nome)
            dados_ref = est_ref.collection('dados').document('grafo').get()

            if dados_ref.exists:
                grafo = dados_ref.to_dict().get('grafo')
                return grafo
            else:
                return None
        except Exception as e:
            print(f"Erro ao carregar o grafo: {e}")
            return None

    @staticmethod
    def calcular_menor_caminho(estacionamento_nome, origem, destino):
        """Calcula o menor caminho no grafo do Firebase."""
        grafo = Admin.carregar_grafo(estacionamento_nome)
        if grafo:
            distancia, caminho = dijkstra(grafo, origem, destino)
            return distancia, caminho
        else:
            return None, None
