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


def desenhar_escalas_ativas(tela, pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco, alpha, fonte, scroll_y=0):
    for chave, lista_modulos in dicionario_escalas.items():
        for modulo in lista_modulos:
            if modulo.estado in ['braco', 'mouse']:  
                modulo.scroll_offset = 0 # Sem scroll no braço
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, fonte, alpha)
                
            elif modulo.estado == 'painel' and aba_atual == modulo.aba and sub_aba_atual == modulo.sub_aba:
                # Apenas avisa a escala do valor do scroll. A própria escala vai lidar com a matemática!
                modulo.scroll_offset = scroll_y 
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, fonte, alpha)

def tratar_cliques_escalas(pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco, scroll_y=0):
    for chave, lista_modulos in dicionario_escalas.items():
        for modulo in lista_modulos:
            if modulo.estado in ['braco', 'mouse']:
                modulo.scroll_offset = 0
                if modulo.tratar_clique(pos_mouse, rect_braco):
                    return True
                    
            elif modulo.estado == 'painel' and aba_atual == modulo.aba and sub_aba_atual == modulo.sub_aba:
                modulo.scroll_offset = scroll_y
                if modulo.tratar_clique(pos_mouse, rect_braco):
                    return True
    return False