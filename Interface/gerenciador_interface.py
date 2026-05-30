def obter_lista_ativa(aba_atual, sub_aba_atual, dicionario_escalas):
    """
        Como funciona: Acessa e formata dados internos ou de configuração.
        Para que serve: Retorna as informações solicitadas sobre 'lista ativa'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_interface'.
    """
    if aba_atual == 0:
        if sub_aba_atual == 0:
            return dicionario_escalas.get('maior', [])
        if sub_aba_atual == 1:
            return dicionario_escalas.get('menor', [])
        if sub_aba_atual == 2:
            return dicionario_escalas.get('penta', [])
        if sub_aba_atual == 3:
            return dicionario_escalas.get('blues', [])
        if sub_aba_atual == 4:
            return dicionario_escalas.get('modos', [])
    elif aba_atual == 1:
        if sub_aba_atual == 0:
            return dicionario_escalas.get('triades_maior', [])
        if sub_aba_atual == 1:
            return dicionario_escalas.get('triades_menor', [])
    return []

def desenhar_escalas_ativas(tela, pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco, alpha, fonte, scroll_y=0):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'escalas ativas' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_interface'.
    """
    for chave, lista_modulos in dicionario_escalas.items():
        for modulo in lista_modulos:
            if modulo.estado in ['braco', 'mouse']:
                modulo.scroll_offset = 0
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, fonte, alpha)
            elif modulo.estado == 'painel' and aba_atual == modulo.aba and (sub_aba_atual == modulo.sub_aba):
                modulo.scroll_offset = scroll_y
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, fonte, alpha)

def tratar_cliques_escalas(pos_mouse, aba_atual, sub_aba_atual, dicionario_escalas, rect_braco, scroll_y=0):
    """
        Como funciona: Verifica colisões e processa inputs do mouse/teclado.
        Para que serve: Mapeia ações do usuário para atualizações de estado.
        Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_interface'.
    """
    for chave, lista_modulos in dicionario_escalas.items():
        for modulo in lista_modulos:
            if modulo.estado in ['braco', 'mouse']:
                modulo.scroll_offset = 0
                if modulo.tratar_clique(pos_mouse, rect_braco):
                    return True
            elif modulo.estado == 'painel' and aba_atual == modulo.aba and (sub_aba_atual == modulo.sub_aba):
                modulo.scroll_offset = scroll_y
                if modulo.tratar_clique(pos_mouse, rect_braco):
                    return True
    return False