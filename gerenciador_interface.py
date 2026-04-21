import pygame

def tratar_cliques_escalas(pos_clique, aba_atual, sub_aba_atual, listas, rect_braco):
    lista_alvo = []

    # Aba de ESCALAS (0)
    if aba_atual == 0:
        if sub_aba_atual == 0: lista_alvo = listas.get('maior', [])
        elif sub_aba_atual == 1: lista_alvo = listas.get('menor', [])
        elif sub_aba_atual == 2: lista_alvo = listas.get('penta', [])
        elif sub_aba_atual == 3: lista_alvo = listas.get('blues', [])
        elif sub_aba_atual == 4: lista_alvo = listas.get('modos', [])

    # Aba de ACORDES (1)
    elif aba_atual == 1:
        if sub_aba_atual == 0: lista_alvo = listas.get('triades_maior', [])
        elif sub_aba_atual == 1: lista_alvo = listas.get('triades_menor', [])
        elif sub_aba_atual == 2: lista_alvo = listas.get('tetrades', [])

    for modulo in lista_alvo:
        if modulo.tratar_clique(pos_clique, rect_braco):
            return True
    return False

def desenhar_escalas_ativas(tela, pos_mouse, aba_atual, sub_aba_atual, listas, rect_braco):
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
        modulo.atualizar_e_desenhar(tela, pos_mouse, rect_braco)