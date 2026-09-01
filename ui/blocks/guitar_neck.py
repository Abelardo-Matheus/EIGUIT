import pygame
import core.modulos.escalas as escalas
from config.theme import *
from config.ui_metrics import *
from config.app_settings import *
from ui.components.utils import obter_grau, equivalencia_notas
from ui.components.config_componentes import GUITAR_RAIO_NOTA, GUITAR_RAIO_DETECTADA, GUITAR_ALPHA_NORMAL, GUITAR_ALPHA_INATIVO

def desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico, dragger_obj=None):
    """
        Como funciona: Utiliza funções de renderização do Pygame para desenhar na tela.
        Para que serve: Apresenta o elemento visual 'guitarra' na interface gráfica.
        Onde é usada: Chamado a partir do módulo ou classe base de 'guitar_neck'.
    """
    try:
        notas_abertas = lista_afinacoes[estado.indice_afinacao]['notas']
    except:
        notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
    cor_madeira = configs.get_cor_braco() if configs else MADEIRA
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas_desenho = 4 if instrumento == 'baixo' else estado.NUM_CORDAS
    alvo = dragger_obj if dragger_obj else estado.dragger_guitarra if hasattr(estado, 'dragger_guitarra') else None
    if alvo is None:
        return
    pos_x_base = alvo.x
    pos_y_base = alvo.y
    largura_braco_atual = alvo.largura
    altura_braco_atual = alvo.altura - 2 * estado.ESPACO_CORDAS if instrumento == 'baixo' else alvo.altura
    offset_y_atual = pos_y_base + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_base
    
    # Cálculo dinâmico do espaço entre casas para garantir precisão visual
    espaco_casas_dinamico = largura_braco_atual / estado.NUM_CASAS
    
    pygame.draw.rect(tela, (10, 10, 10), (pos_x_base + 3, offset_y_atual + 3, largura_braco_atual, altura_braco_atual), border_radius=4)
    pygame.draw.rect(tela, cor_madeira, (pos_x_base, offset_y_atual, largura_braco_atual, altura_braco_atual), border_radius=4)
    for casa in range(estado.NUM_CASAS + 1):
        x = pos_x_base + casa * espaco_casas_dinamico
        largura_traste = 4 if casa == 0 else 2
        pygame.draw.line(tela, COR_TRASTE, (x, offset_y_atual), (x, offset_y_atual + altura_braco_atual), largura_traste)
        if casa > 0:
            x_centro_casa = x - espaco_casas_dinamico / 2
            txt_casa = fontes['pequena'].render(str(casa), True, (130, 130, 130))
            tela.blit(txt_casa, (x_centro_casa - txt_casa.get_width() // 2, offset_y_atual + altura_braco_atual + 35))
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else BRANCO
    tom_global = getattr(meu_campo_harmonico, 'tom', getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
    estado.tom_atual = tom_global
    nome_escala = getattr(meu_campo_harmonico, 'tipo_escala', getattr(meu_campo_harmonico, 'tipo', '')).lower()
    escala_menor = any((x in nome_escala for x in ['menor', 'eólia', 'dórico', 'frígio', 'lócrio']))
    terca_global = escalas.obter_terca(tom_global, menor=escala_menor)
    quinta_global = escalas.obter_quinta(tom_global)
    tom_ref_global = meu_campo_harmonico.notas_acorde_selecionado[0] if meu_campo_harmonico.indice_acorde_selecionado != -1 else tom_global
    nota_microfone = estado.nota_atual_detectada
    for i in range(num_cordas_desenho):
        y = offset_y_atual + altura_braco_atual - i * estado.ESPACO_CORDAS if instrumento != 'baixo' else offset_y_atual + altura_braco_atual - 15 - i * estado.ESPACO_CORDAS
        pygame.draw.line(tela, COR_CORDA, (pos_x_base, y), (pos_x_base + largura_braco_atual, y), 1 + i // 3)
        nota_aberta_atual = notas_abertas[i if instrumento != 'baixo' else i + 2]
        for casa in range(estado.NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            esta_no_acorde = True
            alpha_nota, raio_atual = (GUITAR_ALPHA_NORMAL, GUITAR_RAIO_NOTA)
            if meu_campo_harmonico.indice_acorde_selecionado != -1:
                if nota_calculada not in meu_campo_harmonico.notas_acorde_selecionado:
                    esta_no_acorde = False
                    alpha_nota, raio_atual = (GUITAR_ALPHA_INATIVO, 12)
            x_nota = pos_x_base - 35 if casa == 0 else pos_x_base + casa * espaco_casas_dinamico - espaco_casas_dinamico / 2
            cor_fundo = cor_base_escala
            if esta_no_acorde:
                if nota_calculada == (meu_campo_harmonico.notas_acorde_selecionado[0] if meu_campo_harmonico.indice_acorde_selecionado != -1 else tom_global):
                    cor_fundo = CORES_TONICA[estado.indice_cor_tonica]
                elif nota_calculada == (meu_campo_harmonico.notas_acorde_selecionado[1] if meu_campo_harmonico.indice_acorde_selecionado != -1 and len(meu_campo_harmonico.notas_acorde_selecionado) > 1 else terca_global):
                    cor_fundo = CORES_TONICA[estado.indice_cor_terca]
                elif nota_calculada == (meu_campo_harmonico.notas_acorde_selecionado[2] if meu_campo_harmonico.indice_acorde_selecionado != -1 and len(meu_campo_harmonico.notas_acorde_selecionado) > 2 else quinta_global):
                    cor_fundo = CORES_TONICA[estado.indice_cor_quinta]
            tocando_agora = False
            if nota_microfone and equivalencia_notas(nota_microfone, nota_calculada):
                cor_fundo = (255, 255, 0)
                raio_atual = GUITAR_RAIO_DETECTADA
                alpha_nota = GUITAR_ALPHA_NORMAL
                tocando_agora = True
            s = pygame.Surface((raio_atual * 2, raio_atual * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cor_fundo, alpha_nota), (raio_atual, raio_atual), raio_atual)
            if tocando_agora:
                pygame.draw.circle(s, (255, 100, 0), (raio_atual, raio_atual), raio_atual, 3)
            else:
                pygame.draw.circle(s, (0, 0, 0, alpha_nota // 2), (raio_atual, raio_atual), raio_atual, 1)
            tela.blit(s, (int(x_nota - raio_atual), int(y - raio_atual)))
            if modo_texto != 'vazio':
                texto_str = nota_calculada if modo_texto == 'letras' else obter_grau(tom_ref_global, nota_calculada)
                txt_surf = fontes['pequena' if raio_atual < 15 else 'notas'].render(texto_str, True, (30, 30, 30))
                txt_surf.set_alpha(alpha_nota)
                tela.blit(txt_surf, (x_nota - txt_surf.get_width() / 2, y - txt_surf.get_height() / 2))
    if estado.drag_ativado and alvo:
        alvo.desenhar_caixa_selecao(tela, margem=15)