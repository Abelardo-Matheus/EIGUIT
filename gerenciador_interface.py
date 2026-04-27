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


def desenhar_escalas_ativas(tela, pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco, alpha, fonte):
    for chave, lista_modulos in dicionario_escalas.items():
        for modulo in lista_modulos:
            
            # Se a escala está grudada no braço ou sendo arrastada, desenha em qualquer aba!
            if modulo.estado in ['braco', 'mouse']:  
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, fonte, alpha)
                
            # Se ela está quietinha no menu, só mostra se estivermos na aba e sub-aba certas
            elif modulo.estado == 'painel' and aba_atual == modulo.aba and sub_aba_atual == modulo.sub_aba:
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, fonte, alpha)

def tratar_cliques_escalas(pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco):
    for chave, lista_modulos in dicionario_escalas.items():
        for modulo in lista_modulos:
            
            # Permite clicar para remover a escala do braço mesmo se você estiver na aba de IA
            if modulo.estado in ['braco', 'mouse']:
                if modulo.tratar_clique(pos_mouse, rect_braco):
                    return True
                    
            # Permite pegar novas escalas do menu apenas se a aba bater
            elif modulo.estado == 'painel' and aba_atual == modulo.aba and sub_aba_atual == modulo.sub_aba:
                if modulo.tratar_clique(pos_mouse, rect_braco):
                    return True
                    
    return False