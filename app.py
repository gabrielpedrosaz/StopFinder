from grafos import criar_grafo_estacionamento, obter_vagas_vizinhas
from banco_dados import Usuario, Admin, Manager, Motorista

# Verificar se o admin existe e criar se necessário
def verificar_admin():
    admin_identificador = input("Informe o UID ou email do admin: ").strip()
    role_admin = Admin.validar_usuario(admin_identificador)

    if not role_admin:
        print("Admin não encontrado. Vamos criar um novo admin.")
        email_admin = input("Informe o email do novo admin: ").strip()
        Admin.criar_usuario(email_admin, "admin")
        print(f"Admin {email_admin} criado com sucesso.")
    else:
        print("Admin já existe.")

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
        buscar_vaga_livre(estacionamento_nome)
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
def buscar_vaga_livre(estacionamento_nome):
    bloco_desejado = input("Informe o bloco desejado (ex: 'Bloco_A'): ").strip()
    vagas_disponiveis = Usuario.solicitar_vaga(estacionamento_nome, bloco_desejado)

    if vagas_disponiveis:
        print(f"Vagas disponíveis: {vagas_disponiveis}")
    else:
        bloco_vizinho = obter_blocos_vizinhos(bloco_desejado)
        vaga_vizinha_disponivel = Usuario.solicitar_vaga(estacionamento_nome, bloco_vizinho)
        if vaga_vizinha_disponivel:
            print(f"Vagas no bloco vizinho: {vaga_vizinha_disponivel}")
            ocupar_vaga(vaga_vizinha_disponivel[0])
        else:
            print("Não há vagas disponíveis no bloco desejado ou nos blocos vizinhos.")

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
        buscar_vaga_livre(estacionamento_nome)
    elif opcao == "2":
        status = Manager.obter_resumo_vagas(estacionamento_nome)
        print(f"Status do estacionamento '{estacionamento_nome}': {status}")

# Ações do motorista
def acoes_motorista(estacionamento_nome):
    bloco_desejado = input("Informe o bloco desejado (ex: 'Bloco_A'): ").strip()
    vagas_disponiveis = obter_vagas_disponiveis(estacionamento_nome, bloco_desejado)

    if vagas_disponiveis:
        ocupar_vaga(vagas_disponiveis[0])
    else:
        print(f"Todas as vagas do bloco '{bloco_desejado}' estão ocupadas.")

# Fluxo principal
def fluxo_principal():
    verificar_admin()

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
