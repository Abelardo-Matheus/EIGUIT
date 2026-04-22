import pygame

def tratar_cliques_escalas(pos_clique, aba_atual, sub_aba_atual, listas, rect_braco):
    # 1. GLOBAL: Primeiro checa se clicou em alguma escala que JÁ ESTÁ NO BRAÇO ou no MOUSE
    for chave, lista in listas.items():
        for modulo in lista:
            if modulo.estado in ['braco', 'mouse']:
                if modulo.tratar_clique(pos_clique, rect_braco):
                    return True # Se clicou e arrastou, sai da função

    # 2. LOCAL: Depois checa as miniaturas APENAS da aba atual do painel
    lista_alvo = []
    if aba_atual == 0:
        if sub_aba_atual == 0: lista_alvo = listas.get('maior', [])
        elif sub_aba_atual == 1: lista_alvo = listas.get('menor', [])
        elif sub_aba_atual == 2: lista_alvo = listas.get('penta', [])
        elif sub_aba_atual == 3: lista_alvo = listas.get('blues', [])
        elif sub_aba_atual == 4: lista_alvo = listas.get('modos', [])
    elif aba_atual == 1:
        if sub_aba_atual == 0: lista_alvo = listas.get('triades_maior', [])
        elif sub_aba_atual == 1: lista_alvo = listas.get('triades_menor', [])
        elif sub_aba_atual == 2: lista_alvo = listas.get('tetrades', [])

    for modulo in lista_alvo:
        if modulo.estado == 'painel':
            if modulo.tratar_clique(pos_clique, rect_braco):
                return True
                
    return False

def desenhar_escalas_ativas(tela, pos_mouse, aba_atual, sub_aba_atual, listas, rect_braco, nivel_alpha=255):
    # 1. GLOBAL: SEMPRE desenha as escalas que estão coladas no braço, independente da aba!
    for chave, lista in listas.items():
        for modulo in lista:
            if modulo.estado in ['braco', 'mouse']:
                modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, nivel_alpha)

    # 2. LOCAL: Desenha as miniaturas do painel inferior APENAS se estiver na aba correta (0 ou 1)
    lista_alvo = []
    if aba_atual == 0:
        if sub_aba_atual == 0: lista_alvo = listas.get('maior', [])
        elif sub_aba_atual == 1: lista_alvo = listas.get('menor', [])
        elif sub_aba_atual == 2: lista_alvo = listas.get('penta', [])
        elif sub_aba_atual == 3: lista_alvo = listas.get('blues', [])
        elif sub_aba_atual == 4: lista_alvo = listas.get('modos', [])
    elif aba_atual == 1:
        if sub_aba_atual == 0: lista_alvo = listas.get('triades_maior', [])
        elif sub_aba_atual == 1: lista_alvo = listas.get('triades_menor', [])
        elif sub_aba_atual == 2: lista_alvo = listas.get('tetrades', [])

    for modulo in lista_alvo:
        if modulo.estado == 'painel':
            modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco, nivel_alpha)