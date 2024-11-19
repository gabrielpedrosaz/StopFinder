from grafos import criar_grafo_estacionamento, obter_vagas_vizinhas, obter_blocos_vizinhos, desenhar_grafo
from banco_dados import db, Usuario, Admin, Manager, Motorista

usuario = None

# Verificar se o admin existe e criar se necessário
def verificar_admin():
    identificador_admin = input("Informe o UID ou email do admin: ").strip()
    
    # Verifica se é um email ou UID pelo formato
    if "@" in identificador_admin:
        # Tenta buscar o usuário pelo email
        user_ref = db.collection('Usuarios').where('email', '==', identificador_admin).get()
    else:
        # Busca pelo UID diretamente
        user_ref = db.collection('Usuarios').document(identificador_admin).get()
        user_ref = [user_ref] if user_ref.exists else []

    if user_ref:
        user_data = user_ref[0].to_dict()
        user_id = user_ref[0].id
        role = user_data.get("role")
        
        if role == "admin":
            print("Admin encontrado.")
            admin_instance = Admin(identificador_admin, user_id)
            return admin_instance
        else:
            print("O usuário encontrado não é um admin.")
            return None
    else:
        print("Admin não encontrado. Vamos criar um novo admin.")
        email = input("Informe o email do novo admin: ")
        senha = input("Informe a senha para o novo admin: ")
        return Admin.criar_usuario(email, senha, "admin")

# Ações do admin
def acoes_admin(usuario, estacionamento_nome):
    while True:
        print("\nAções do Admin:")
        print("Escolha uma ação:")
        print("1. Criar ou Editar Estacionamento")
        print("2. Buscar uma vaga livre")
        print("3. Desenhar grafo do estacionamento")
        print("4. Sair")
        opcao = input("Informe a opção desejada (1, 2, 3 ou 4): ").strip()

        if opcao == "1":
            criar_editar_estacionamento(estacionamento_nome)
        elif opcao == "2":
            buscar_vaga_livre(estacionamento_nome, bloco_desejado=None)
        elif opcao == "3":
            try:
                # Carregar o grafo e as posições do banco de dados
                grafo, posicoes = Admin.carregar_grafo(estacionamento_nome)
                if grafo is not None and posicoes is not None:
                    desenhar_grafo(grafo, posicoes)  # Função que desenha o grafo
                else:
                    print("Falha ao carregar o grafo. Verifique se o estacionamento foi configurado corretamente.")
            except Exception as e:
                print(f"Erro ao desenhar o grafo: {e}")
        elif opcao == "4":
            break
        else:
            print("Opção inválida. Tente novamente.")

# Criar ou editar estacionamento
def criar_editar_estacionamento(estacionamento_nome):
    # Se o estacionamento já existir, você pode avisar o admin ou apenas editar
    if usuario.estacionamento_existe(estacionamento_nome):
        print(f"Estacionamento '{estacionamento_nome}' já existe. Atualizando as informações.")
    
    quantidade_blocos = int(input("Informe o número de blocos: "))
    linhas_por_bloco = int(input("Informe o número de linhas por bloco: "))
    colunas_por_bloco = int(input("Informe o número de colunas por bloco: "))

    # Salvar o estacionamento no banco (essa função cuida de criar grafo e salvar as vagas)
    usuario.salvar_estacionamento(estacionamento_nome, quantidade_blocos, linhas_por_bloco, colunas_por_bloco)
    print(f"Estacionamento '{estacionamento_nome}' salvo/atualizado com sucesso.")

# Buscar vaga livre
def buscar_vaga_livre(estacionamento_nome, bloco_desejado):
    if bloco_desejado == None:
        bloco_desejado = input("Informe o bloco desejado (ex: 'A'): ").strip()
        bloco_desejado = f"Bloco_{bloco_desejado.upper()}"
    # Tenta obter uma vaga livre no bloco desejado
    vaga_escolhida = Usuario.solicitar_vaga_livre(estacionamento_nome, bloco_desejado)

    if vaga_escolhida:
        print(f"Vaga {vaga_escolhida} no bloco {bloco_desejado} foi ocupada com sucesso.")
    else:
        print(f"Nenhuma vaga livre encontrada.")


# Criar novo usuário
def criar_usuario():
    email_novo_usuario = input("Informe o email do novo usuário: ").strip()
    role_novo_usuario = input("Informe o role do novo usuário (admin/manager/motorista): ").strip()
    usuario.criar_usuario(email_novo_usuario, role_novo_usuario)
    print(f"Usuário {email_novo_usuario} criado com sucesso.")

# Ações do manager
def acoes_manager(usuario, estacionamento_nome):
    while True:
        print("\nAções do Manager:")
        print("Escolha uma ação:")
        print("1. Buscar uma vaga livre")
        print("2. Ver status do estacionamento")
        print("3. Desenhar grafo do estacionamento")
        print("4. Sair")
        opcao = input("Informe a opção desejada (1, 2, 3 ou 4): ").strip()

        if opcao == "1":
            buscar_vaga_livre(estacionamento_nome, bloco_desejado=None)
        elif opcao == "2":
            status = usuario.obter_resumo_estacionamento(estacionamento_nome)
            print(f"Status do estacionamento '{estacionamento_nome}': {status}")
        elif opcao == "3":
            try:
                # Carregar o grafo e as posições do banco de dados
                grafo, posicoes = Admin.carregar_grafo(estacionamento_nome)
                if grafo is not None and posicoes is not None:
                    desenhar_grafo(grafo, posicoes)  # Função que desenha o grafo
                else:
                    print("Falha ao carregar o grafo. Verifique se o estacionamento foi configurado corretamente.")
            except Exception as e:
                print(f"Erro ao desenhar o grafo: {e}")
        elif opcao == "4":
            break
        else:
            print("Opção inválida. Tente novamente.")

# Ações do motorista
def acoes_motorista(usuario, estacionamento_nome):
    buscar_vaga_livre(estacionamento_nome, bloco_desejado=None)
        

# Fluxo principal
def fluxo_principal():
    global usuario
    login = input("Você ja tem conta no aplicativo? (s/n) ").strip()

    if login == "s":
        identificador_usuario = input("Informe o email ou UID do usuário: ").strip().lower()
        role = Admin.validar_usuario(identificador_usuario)

        while not role:
            print("Usuário não encontrado ou sem permissões.")
            identificador_usuario = input("Tente novamente, informando um email ou um UID de usuário válido: ").strip().lower()
            role = Admin.validar_usuario(identificador_usuario)

            if role:
                print(f"Usuário logado com role: {role}")
    elif login == "n":
        criar_usuario()
    else:
        print("Opção inválida. Tente novamente.")

        # Atribui a instância correta para a variável `usuario` com base no papel
    if role == "admin":
        usuario = Admin(identificador_usuario, identificador_usuario)
    elif role == "manager":
        usuario = Manager(identificador_usuario, identificador_usuario)
    elif role == "motorista":
        usuario = Motorista(identificador_usuario, identificador_usuario)
    else:
        print("ERRO: Papel do usuário não reconhecido")
        return

    estacionamento_nome = input("Informe o nome do estacionamento: ").strip()        

    # Chama as funções de acordo com o papel do usuário
    if role == "admin":
        
        acoes_admin(usuario, estacionamento_nome) 
    elif (role == 'manager' or role == 'motorista') and not Admin.estacionamento_existe(estacionamento_nome):
        print ("Estacionamento não existe!")
    elif role == "manager" :
        acoes_manager(usuario, estacionamento_nome)
    elif role == "motorista":
        acoes_motorista(usuario, estacionamento_nome)
    else:
        print("Permissão negada.")

# Iniciar o fluxo principal
fluxo_principal()
