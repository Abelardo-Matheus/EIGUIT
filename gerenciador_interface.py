# gerenciador_interface.py

def obter_lista_ativa(aba_atual, sub_aba_atual, dicionario_escalas):
    """
    Função auxiliar inteligente (Roteador).
    Mapeia a aba selecionada na interface para a lista de dados correspondente.
    """
    # ABA 0: ESCALAS
    if aba_atual == 0:  
        if sub_aba_atual == 0: return dicionario_escalas.get('maior', [])
        if sub_aba_atual == 1: return dicionario_escalas.get('menor', [])
        if sub_aba_atual == 2: return dicionario_escalas.get('penta', [])
        if sub_aba_atual == 3: return dicionario_escalas.get('blues', [])
        if sub_aba_atual == 4: return dicionario_escalas.get('modos', [])
        
    # ABA 1: ACORDES
    elif aba_atual == 1: 
        if sub_aba_atual == 0: return dicionario_escalas.get('triades_maior', [])
        if sub_aba_atual == 1: return dicionario_escalas.get('triades_menor', [])
        # Você pode mapear as próximas sub-abas aqui futuramente (Tétrades, etc)

    # Se estiver na aba de IA (2) ou Configurações (3), retorna vazio para esconder os blocos
    return []


def desenhar_escalas_ativas(tela, pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco_colisao, nivel_alpha, fonte_pequena):
    """
    Pega a lista correta do roteador e manda desenhar cada bloquinho.
    """
    lista_ativa = obter_lista_ativa(aba_atual, sub_aba_atual, dicionario_escalas)
    
    for modulo in lista_ativa:
        modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco_colisao, fonte_pequena, nivel_alpha)


def tratar_cliques_escalas(pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco_colisao):
    """
    Pega a lista correta do roteador e verifica se o usuário arrastou/clicou em algum bloco.
    """
    lista_ativa = obter_lista_ativa(aba_atual, sub_aba_atual, dicionario_escalas)
    
    for modulo in lista_ativa:
        if modulo.tratar_clique(pos_mouse, rect_braco_colisao):
            return True # Retorna True assim que achar um clique, para evitar conflitos
            
    return False