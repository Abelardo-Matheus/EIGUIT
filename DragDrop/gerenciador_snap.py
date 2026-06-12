import pygame

def calcular_snap_e_guias(bloco_alvo, outros_blocos, largura_tela, altura_tela, limite_snap=15):
    """
    Calcula o encaixe magnético (snap) e retorna as coordenadas para as guias inteligentes.
    """
    snap_x = None
    snap_y = None
    guias_x = [] # Linhas verticais (alinhamento em X)
    guias_y = [] # Linhas horizontais (alinhamento em Y)

    # Pontos de interesse do bloco sendo arrastado
    alvo_pontos_x = {
        'esq': bloco_alvo.x,
        'centro': bloco_alvo.x + bloco_alvo.largura // 2,
        'dir': bloco_alvo.x + bloco_alvo.largura
    }
    alvo_pontos_y = {
        'topo': bloco_alvo.y,
        'centro': bloco_alvo.y + bloco_alvo.altura // 2,
        'base': bloco_alvo.y + bloco_alvo.altura
    }

    # 1. Snap com o Centro da Tela
    centro_tela_x = largura_tela // 2
    centro_tela_y = altura_tela // 2

    # Snap X (Vertical)
    if abs(alvo_pontos_x['centro'] - centro_tela_x) < limite_snap:
        snap_x = centro_tela_x - (bloco_alvo.largura // 2)
        guias_x.append(centro_tela_x)

    # Snap Y (Horizontal)
    if abs(alvo_pontos_y['centro'] - centro_tela_y) < limite_snap:
        snap_y = centro_tela_y - (bloco_alvo.altura // 2)
        guias_y.append(centro_tela_y)

    # 2. Snap com outros blocos
    for outro in outros_blocos:
        if outro == bloco_alvo:
            continue
        
        # Pontos de interesse do outro bloco
        outro_x = {
            'esq': outro.x,
            'centro': outro.x + outro.largura // 2,
            'dir': outro.x + outro.largura
        }
        outro_y = {
            'topo': outro.y,
            'centro': outro.y + outro.altura // 2,
            'base': outro.y + outro.altura
        }

        # Verificar Snap X
        for label_alvo, val_alvo in alvo_pontos_x.items():
            for label_outro, val_outro in outro_x.items():
                if abs(val_alvo - val_outro) < limite_snap:
                    if label_alvo == 'esq': snap_x = val_outro
                    elif label_alvo == 'centro': snap_x = val_outro - (bloco_alvo.largura // 2)
                    elif label_alvo == 'dir': snap_x = val_outro - bloco_alvo.largura
                    guias_x.append(val_outro)
                    break
            if snap_x is not None: break

        # Verificar Snap Y
        for label_alvo, val_alvo in alvo_pontos_y.items():
            for label_outro, val_outro in outro_y.items():
                if abs(val_alvo - val_outro) < limite_snap:
                    if label_alvo == 'topo': snap_y = val_outro
                    elif label_alvo == 'centro': snap_y = val_outro - (bloco_alvo.altura // 2)
                    elif label_alvo == 'base': snap_y = val_outro - bloco_alvo.altura
                    guias_y.append(val_outro)
                    break
            if snap_y is not None: break

    return snap_x, snap_y, guias_x, guias_y

def desenhar_guias_inteligentes(tela, guias_x, guias_y, largura_tela, altura_tela):
    """
    Desenha as linhas de guia na tela.
    """
    COR_GUIA = (255, 0, 255, 100) # Rosa transparente
    superficie_guias = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    
    for x in guias_x:
        pygame.draw.line(superficie_guias, COR_GUIA, (x, 0), (x, altura_tela), 1)
        
    for y in guias_y:
        pygame.draw.line(superficie_guias, COR_GUIA, (0, y), (largura_tela, y), 1)
        
    tela.blit(superficie_guias, (0, 0))
