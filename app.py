from grafos import criar_grafo_estacionamento, obter_vagas_vizinhas, obter_blocos_vizinhos, desenhar_grafo
from banco_dados import db, Usuario, Admin, Manager, Motorista

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
def acoes_admin(estacionamento_nome):
    print("Escolha uma ação:")
    print("1. Criar ou Editar Estacionamento")
    print("2. Buscar uma vaga livre")
    print("3. Criar um novo usuário")
    opcao = input("Informe a opção desejada (1, 2 ou 3): ").strip()

    if opcao == "1":
        criar_editar_estacionamento(estacionamento_nome)
    elif opcao == "2":
        buscar_vaga_livre(estacionamento_nome, bloco_desejado=None)
    elif opcao == "3":
        criar_usuario()

# Criar ou editar estacionamento
def criar_editar_estacionamento(estacionamento_nome):
    quantidade_blocos = int(input("Informe o número de blocos: "))
    linhas_por_bloco = int(input("Informe o número de linhas por bloco: "))
    colunas_por_bloco = int(input("Informe o número de colunas por bloco: "))

    # Se o estacionamento já existir, você pode avisar o admin ou apenas editar
    if Admin.estacionamento_existe(estacionamento_nome):
        print(f"Estacionamento '{estacionamento_nome}' já existe. Atualizando as informações.")
    
    # Salvar o estacionamento no banco (essa função cuida de criar grafo e salvar as vagas)
    Admin.salvar_estacionamento(estacionamento_nome, quantidade_blocos, linhas_por_bloco, colunas_por_bloco)
    print(f"Estacionamento '{estacionamento_nome}' salvo/atualizado com sucesso.")

# Buscar vaga livre
def buscar_vaga_livre(estacionamento_nome, bloco_desejado):
    if bloco_desejado == None:
        bloco_desejado = input("Informe o bloco desejado (ex: 'A'): ").strip()
    # Tenta obter uma vaga livre no bloco desejado
    vaga_escolhida = Usuario.solicitar_vaga_livre(estacionamento_nome, bloco_desejado)

    if vaga_escolhida:
        print(f"Vaga {vaga_escolhida} no bloco {bloco_desejado} foi ocupada com sucesso.")
    else:
        print(f"Nenhuma vaga livre encontrada no bloco {bloco_desejado}. Buscando em blocos vizinhos...")

        # Busca em blocos vizinhos se não houver vagas no bloco desejado
        for bloco_vizinho in obter_blocos_vizinhos(bloco_desejado):
            vaga_escolhida = Usuario.obter_vaga_livre(estacionamento_nome, bloco_vizinho)
            if vaga_escolhida:
                print(f"Vaga {vaga_escolhida} no bloco vizinho {bloco_vizinho} foi ocupada com sucesso.")
                break
        else:
            print("Não há vagas disponíveis no bloco desejado nem nos blocos vizinhos.")


# Criar novo usuário
def criar_usuario():
    email_novo_usuario = input("Informe o email do novo usuário: ").strip()
    role_novo_usuario = input("Informe o role do novo usuário (admin/manager/motorista): ").strip()
    Usuario.criar_usuario(email_novo_usuario, role_novo_usuario)
    print(f"Usuário {email_novo_usuario} criado com sucesso.")

# Ações do manager
def acoes_manager(estacionamento_nome):
    print("Escolha uma ação:")
    print("1. Buscar uma vaga livre")
    print("2. Ver status do estacionamento")
    opcao = input("Informe a opção desejada (1 ou 2): ").strip()

    if opcao == "1":
        bloco_desejado = input("Informe o bloco desejado (ex: 'A'): ").strip()
        buscar_vaga_livre(estacionamento_nome, bloco_desejado)
    elif opcao == "2":
        status = Manager.obter_resumo_vagas(estacionamento_nome)
        print(f"Status do estacionamento '{estacionamento_nome}': {status}")

# Ações do motorista
def acoes_motorista(estacionamento_nome):
    bloco_desejado = input("Informe o bloco desejado (ex: 'A'): ").strip()

    # Tenta obter uma vaga livre no bloco desejado
    vaga_escolhida = Usuario.solicitar_vaga_livre(estacionamento_nome, bloco_desejado)

    if vaga_escolhida:
        print(f"Vaga {vaga_escolhida} no bloco {bloco_desejado} foi ocupada com sucesso.")
    else:
        print(f"Todas as vagas do bloco '{bloco_desejado}' estão ocupadas.")
        
        # Tenta buscar vaga em blocos vizinhos
        for bloco_vizinho in Usuario.obter_blocos_vizinhos(bloco_desejado):
            vaga_escolhida = Usuario.obter_vaga_livre(estacionamento_nome, bloco_vizinho)
            if vaga_escolhida:
                print(f"Vaga {vaga_escolhida} no bloco vizinho {bloco_vizinho} foi ocupada com sucesso.")
                break
        else:
            print("Não há vagas disponíveis no bloco desejado nem nos blocos vizinhos.")


# Fluxo principal
def fluxo_principal():
    

    identificador_usuario = input("Informe o email ou UID do usuário: ").strip()
    role = Admin.validar_usuario(identificador_usuario)

    if not role:
        print("Usuário não encontrado ou sem permissões.")
    else:
        print(f"Usuário logado com role: {role}")

        estacionamento_nome = input("Informe o nome do estacionamento: ").strip()

        if role == "admin":
            acoes_admin(estacionamento_nome)
        elif role == "manager":
            acoes_manager(estacionamento_nome)
        elif role == "motorista":
            acoes_motorista(estacionamento_nome)
        else:
            print("Permissão negada.")

# Iniciar o fluxo principal
fluxo_principal()
