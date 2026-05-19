# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# All rights reserved. Commercial use prohibited.
# =============================================================================
import pygame
import math 
import Modulos.escalas as escalas
from Interface import gerenciador_interface
from Core.constantes_ui import *
from Jogos.Jogos_interativos import GerenciadorJogos
import Modulos.modulos_estudos as modulo_estudos

_NOTAS_IDX = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}

def obter_grau(tonica, nota):
    graus = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    try:
        return graus[(_NOTAS_IDX[nota] - _NOTAS_IDX[tonica]) % 12]
    except (KeyError, ValueError): return ""

def equivalencia_notas(nota1, nota2):
    if nota1 == nota2: return True
    enarmonicas = {"C#": "Db", "Db": "C#", "D#": "Eb", "Eb": "D#", "F#": "Gb", "Gb": "F#", "G#": "Ab", "Ab": "G#", "A#": "Bb", "Bb": "A#"}
    return enarmonicas.get(nota1) == nota2 or enarmonicas.get(nota2) == nota1

def desenhar_painel_superior(tela, estado, fontes):
    if hasattr(estado, 'dragger_controles_topo') and estado.dragger_controles_topo.largura < 650:
        estado.dragger_controles_topo.largura = 650
        
    dx = estado.dragger_controles_topo.x if hasattr(estado, 'dragger_controles_topo') else 100
    dy = estado.dragger_controles_topo.y if hasattr(estado, 'dragger_controles_topo') else 30
    largura_caixa = estado.dragger_controles_topo.largura if hasattr(estado, 'dragger_controles_topo') else 650
    
    largura_tela_real = getattr(estado, 'LARGURA_TELA', 1280)
    estado.rect_btn_pin = pygame.Rect(largura_tela_real - 70, 25, 45, 45)
    cor_pin_bg = AZUL_PRIMARIO if estado.drag_ativado else (45, 45, 45)
    pygame.draw.rect(tela, cor_pin_bg, estado.rect_btn_pin, border_radius=10)
    pygame.draw.rect(tela, COR_BORDA, estado.rect_btn_pin, width=1, border_radius=10)
    
    cx, cy = estado.rect_btn_pin.center
    if estado.drag_ativado:
        pygame.draw.circle(tela, BRANCO, (cx, cy), 5)
        pygame.draw.line(tela, BRANCO, (cx-12, cy), (cx+12, cy), 3)
        pygame.draw.line(tela, BRANCO, (cx, cy-12), (cx, cy+12), 3)
    else:
        pygame.draw.circle(tela, (200, 200, 200), (cx, cy - 4), 6) 
        pygame.draw.line(tela, BRANCO, (cx - 6, cy + 2), (cx + 6, cy + 2), 2) 
        pygame.draw.line(tela, BRANCO, (cx, cy + 2), (cx, cy + 12), 2) 

    centro_col1 = dx + (largura_caixa / 6)
    centro_col2 = dx + (largura_caixa / 2)
    centro_col3 = dx + (largura_caixa * 5 / 6)
    
    # Bloco 1: Casas
    x_casas_inicio = centro_col1 - 95 
    btn_menos_casa = pygame.Rect(x_casas_inicio, dy, 40, 35)
    btn_mais_casa = pygame.Rect(x_casas_inicio + 150, dy, 40, 35)
    
    pygame.draw.rect(tela, AZUL_PRIMARIO, btn_menos_casa, border_radius=6)
    tela.blit(fontes['titulo'].render("-", True, BRANCO), (btn_menos_casa.centerx - 5, btn_menos_casa.centery - 15))
    
    txt_casas = fontes['pequena'].render(f"{_t('Casas')}: {estado.NUM_CASAS}", True, BRANCO)
    meio_casas = btn_menos_casa.right + ((btn_mais_casa.left - btn_menos_casa.right) // 2)
    tela.blit(txt_casas, (meio_casas - txt_casas.get_width()//2, dy + 5))
    
    pygame.draw.rect(tela, AZUL_PRIMARIO, btn_mais_casa, border_radius=6)
    tela.blit(fontes['titulo'].render("+", True, BRANCO), (btn_mais_casa.centerx - 7, btn_mais_casa.centery - 15))

    # Bloco 2: Instrumento
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    x_inst_inicio = centro_col2 - 105
    estado.btn_guit = pygame.Rect(x_inst_inicio, dy, 100, 35)
    estado.btn_baixo = pygame.Rect(x_inst_inicio + 110, dy, 100, 35)

    pygame.draw.rect(tela, AZUL_PRIMARIO if instrumento == 'guitarra' else (60, 60, 60), estado.btn_guit, border_radius=6)
    txt_g = fontes['pequena'].render(_t("Guitarra"), True, BRANCO)
    tela.blit(txt_g, (estado.btn_guit.centerx - txt_g.get_width()//2, estado.btn_guit.centery - txt_g.get_height()//2))

    pygame.draw.rect(tela, AZUL_PRIMARIO if instrumento == 'baixo' else (60, 60, 60), estado.btn_baixo, border_radius=6)
    txt_b = fontes['pequena'].render(_t("Baixo"), True, BRANCO)
    tela.blit(txt_b, (estado.btn_baixo.centerx - txt_b.get_width()//2, estado.btn_baixo.centery - txt_b.get_height()//2))

    # Bloco 3: Afinação
    try: nome_afinacao = _t(lista_afinacoes[estado.indice_afinacao]["nome"])
    except: nome_afinacao = _t("Standard")

    x_af_inicio = centro_col3 - 75
    estado.btn_menos_afinacao = pygame.Rect(x_af_inicio, dy, 35, 35)
    estado.btn_mais_afinacao = pygame.Rect(x_af_inicio + 115, dy, 35, 35)

    pygame.draw.rect(tela, AZUL_PRIMARIO, estado.btn_menos_afinacao, border_radius=6)
    tela.blit(fontes['titulo'].render("<", True, BRANCO), (estado.btn_menos_afinacao.centerx - 7, estado.btn_menos_afinacao.centery - 15))

    pygame.draw.rect(tela, AZUL_PRIMARIO, estado.btn_mais_afinacao, border_radius=6)
    tela.blit(fontes['titulo'].render(">", True, BRANCO), (estado.btn_mais_afinacao.centerx - 7, estado.btn_mais_afinacao.centery - 15))

    txt_af = fontes['pequena'].render(nome_afinacao, True, BRANCO)
    meio_setas = estado.btn_menos_afinacao.right + ((estado.btn_mais_afinacao.left - estado.btn_menos_afinacao.right) // 2)
    tela.blit(txt_af, (meio_setas - (txt_af.get_width() // 2), dy + 8))

    if estado.drag_ativado and hasattr(estado, 'dragger_controles_topo'):
        estado.dragger_controles_topo.desenhar_caixa_selecao(tela, margem=10)
        
def desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico, dragger_obj=None):
    try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
    except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']

    cor_madeira = configs.get_cor_braco() if configs else MADEIRA
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    num_cordas_desenho = 4 if instrumento == 'baixo' else estado.NUM_CORDAS
    
    alvo = dragger_obj if dragger_obj else (estado.dragger_guitarra if hasattr(estado, 'dragger_guitarra') else None)
    if alvo is None: return 
    
    pos_x_base = alvo.x
    pos_y_base = alvo.y
    largura_braco_atual = alvo.largura
    altura_braco_atual = alvo.altura - (2 * estado.ESPACO_CORDAS) if instrumento == 'baixo' else alvo.altura
    offset_y_atual = pos_y_base + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_base

    # Braço com sombra sutil
    pygame.draw.rect(tela, (10, 10, 10), (pos_x_base + 3, offset_y_atual + 3, largura_braco_atual, altura_braco_atual), border_radius=4)
    pygame.draw.rect(tela, cor_madeira, (pos_x_base, offset_y_atual, largura_braco_atual, altura_braco_atual), border_radius=4)

    for casa in range(estado.NUM_CASAS + 1):
        x = pos_x_base + (casa * estado.ESPACO_CASAS)
        largura_traste = 4 if casa == 0 else 2
        pygame.draw.line(tela, COR_TRASTE, (x, offset_y_atual), (x, offset_y_atual + altura_braco_atual), largura_traste)
        
        if casa > 0:
            x_centro_casa = x - (estado.ESPACO_CASAS / 2) 
            txt_casa = fontes['pequena'].render(str(casa), True, (130, 130, 130)) 
            tela.blit(txt_casa, (x_centro_casa - txt_casa.get_width()//2, offset_y_atual + altura_braco_atual + 12))
            
    modo_texto = configs.get_modo_texto() if configs else 'letras'
    cor_base_escala = configs.get_cor_notas() if configs else BRANCO
    tom_global = getattr(meu_campo_harmonico, 'tom', getattr(meu_campo_harmonico, 'tonica', estado.tom_atual))
    estado.tom_atual = tom_global 
    
    nome_escala = getattr(meu_campo_harmonico, 'tipo_escala', getattr(meu_campo_harmonico, 'tipo', '')).lower()
    escala_menor = any(x in nome_escala for x in ['menor', 'eólia', 'dórico', 'frígio', 'lócrio'])

    terca_global = escalas.obter_terca(tom_global, menor=escala_menor)
    quinta_global = escalas.obter_quinta(tom_global)
    tom_ref_global = meu_campo_harmonico.notas_acorde_selecionado[0] if meu_campo_harmonico.indice_acorde_selecionado != -1 else tom_global

    nota_microfone = estado.nota_atual_detectada

    for i in range(num_cordas_desenho):
        y = (offset_y_atual + altura_braco_atual - (i * estado.ESPACO_CORDAS)) if instrumento != 'baixo' else (offset_y_atual + altura_braco_atual - 15 - (i * estado.ESPACO_CORDAS))
        pygame.draw.line(tela, COR_CORDA, (pos_x_base, y), (pos_x_base + largura_braco_atual, y), 1 + (i//3))
        nota_aberta_atual = notas_abertas[i if instrumento != 'baixo' else i + 2]

        for casa in range(estado.NUM_CASAS + 1):
            nota_calculada = escalas.obter_nota(nota_aberta_atual, casa)
            
            esta_no_acorde = True
            alpha_nota, raio_atual = 255, 16

            if meu_campo_harmonico.indice_acorde_selecionado != -1:
                if nota_calculada not in meu_campo_harmonico.notas_acorde_selecionado:
                    esta_no_acorde = False
                    alpha_nota, raio_atual = 90, 12  

            x_nota = pos_x_base - 35 if casa == 0 else pos_x_base + (casa * estado.ESPACO_CASAS) - (estado.ESPACO_CASAS / 2)
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
                raio_atual = 20
                alpha_nota = 255
                tocando_agora = True

            s = pygame.Surface((raio_atual*2, raio_atual*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cor_fundo, alpha_nota), (raio_atual, raio_atual), raio_atual)
            
            if tocando_agora: pygame.draw.circle(s, (255, 100, 0), (raio_atual, raio_atual), raio_atual, 3) 
            else: pygame.draw.circle(s, (0, 0, 0, alpha_nota // 2), (raio_atual, raio_atual), raio_atual, 1) 
            
            tela.blit(s, (int(x_nota - raio_atual), int(y - raio_atual)))

            if modo_texto != 'vazio':
                texto_str = nota_calculada if modo_texto == 'letras' else obter_grau(tom_ref_global, nota_calculada)
                txt_surf = fontes['pequena' if raio_atual < 15 else 'notas'].render(texto_str, True, (30, 30, 30))
                txt_surf.set_alpha(alpha_nota) 
                tela.blit(txt_surf, (x_nota - (txt_surf.get_width()/2), y - (txt_surf.get_height()/2)))
    
    if estado.drag_ativado and alvo:
        alvo.desenhar_caixa_selecao(tela, margem=15)

def desenhar_painel_cores(tela, estado, fontes):
    if not hasattr(estado, 'dragger_cores'):
        return

    x_base = estado.dragger_cores.x
    y_base = estado.dragger_cores.y
    largura = estado.dragger_cores.largura
    altura = estado.dragger_cores.altura

    pygame.draw.rect(tela, FUNDO_PAINEL, (x_base, y_base, largura, altura), border_radius=RADIUS_PADRAO)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, altura), width=1, border_radius=RADIUS_PADRAO)

    txt_tit = fontes['pequena'].render(_t("Cores (Graus)"), True, BRANCO)
    tela.blit(txt_tit, (x_base + largura//2 - txt_tit.get_width()//2, y_base + 12))

    itens = [
        (_t("Tônica (1)"), estado.indice_cor_tonica, 'rect_cor_tonica'),
        (_t("Terça (3)"), estado.indice_cor_terca, 'rect_cor_terca'),
        (_t("Quinta (5)"), estado.indice_cor_quinta, 'rect_cor_quinta')
    ]

    y_item = y_base + 45
    for texto, indice_cor, nome_rect in itens:
        txt = fontes['pequena'].render(texto, True, BRANCO)
        tela.blit(txt, (x_base + 10, y_item + 5))
        
        rect_cor = pygame.Rect(x_base + largura - 40, y_item, 25, 25)
        cor_atual = CORES_TONICA[indice_cor % len(CORES_TONICA)]
        
        pygame.draw.rect(tela, cor_atual, rect_cor, border_radius=5)
        pygame.draw.rect(tela, BRANCO, rect_cor, width=2, border_radius=5)
        setattr(estado, nome_rect, rect_cor)
        y_item += 35

    if estado.drag_ativado:
        estado.dragger_cores.desenhar_caixa_selecao(tela, margem=5)

def desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes):
    if not hasattr(estado, 'dragger_acordes'): return
    x_base = estado.dragger_acordes.x
    y_base = estado.dragger_acordes.y
    largura = estado.dragger_acordes.largura

    # Fundo moderno para o campo harmônico
    pygame.draw.rect(tela, FUNDO_PAINEL, (x_base, y_base, largura, estado.ALTURA_ACORDES), border_radius=RADIUS_PADRAO)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, estado.ALTURA_ACORDES), width=1, border_radius=RADIUS_PADRAO)

    meu_campo_harmonico.desenhar(tela, x_base, y_base + 10, largura, fontes['titulo'], fontes['ui'], fontes['pequena'])

    if estado.drag_ativado:
        estado.dragger_acordes.desenhar_caixa_selecao(tela, margem=8)

def _desenhar_aba_ia(tela, dx, y_start, estado, fontes, meu_processador, meu_gravador, meu_gerenciador_jogos, memoria_sub_aba):
    if memoria_sub_aba == 0:
        try: notas_abertas = lista_afinacoes[estado.indice_afinacao]["notas"]
        except: notas_abertas = ['E', 'A', 'D', 'G', 'B', 'E', 'B']
        meu_processador.desenhar_aba_ia(tela, dx, y_start, meu_gravador, fontes['ui'], fontes['titulo'], notas_abertas, estado)
    elif memoria_sub_aba == 1:
        meu_gerenciador_jogos.desenhar_aba_jogos(tela, dx, y_start, fontes['ui'])

def _desenhar_aba_configuracao(tela, dx, y_start, estado, fontes, configs, meu_metronomo, memoria_sub_aba):
    if memoria_sub_aba == 0:
        configs.y = y_start + 10 
        configs.x = dx + 20 
        configs.desenhar(tela, fontes, 0) 
    else:
        meu_metronomo.y = y_start + 10
        meu_metronomo.x = dx + 20 
        if hasattr(meu_metronomo, 'x_config'): meu_metronomo.x_config = dx + 20 
        meu_metronomo.desenhar_config(tela, fontes['ui'], 0)

def _desenhar_aba_estudos(tela, dx, y_start, largura_conteudo, estado, fontes, memoria_sub_aba):
    AZUL_PRIMARIO = (0, 163, 255)
    BRANCO = (255, 255, 255)
    estado.botoes_estudo.clear()
    
    if memoria_sub_aba == 0:
        textos = [
            (_t("Acerte a Nota"), _t("Treine seu mapeamento visual: Descubra qual nota está escondida em uma casa específica do braço.")),
            (_t("Acerte o Som"), _t("Treinamento de percepção absoluta: Escute a frequência gerada e identifique a nota pelo som.")),
            (_t("Acerte a Próxima"), _t("Domine os intervalos calculando saltos de distância (Uníssono, 2ª, 3ª, 4ª, 5ª, 6ª e 7ª)."))
        ]
        y_btn = y_start + 20
        for titulo_btn, descricao in textos:
            rect_btn = pygame.Rect(dx + 20, y_btn, 170, 45)
            pygame.draw.rect(tela, AZUL_PRIMARIO, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width()//2, rect_btn.centery - txt_btn.get_height()//2))
            estado.botoes_estudo[titulo_btn] = rect_btn 
            txt_desc = fontes['pequena'].render(descricao, True, (200, 200, 200))
            tela.blit(txt_desc, (dx + 210, rect_btn.centery - txt_desc.get_height()//2))
            y_btn += 65 
            
    elif memoria_sub_aba == 1:
        textos_escalas = [
            (_t("Acerte a Escala"), _t("Pratique shapes e digitações: Encontre todas as notas que pertencem à escala solicitada."))
        ]
        y_btn = y_start + 20
        for titulo_btn, descricao in textos_escalas:
            rect_btn = pygame.Rect(dx + 20, y_btn, 170, 45)
            pygame.draw.rect(tela, AZUL_PRIMARIO, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width()//2, rect_btn.centery - txt_btn.get_height()//2))
            estado.botoes_estudo[titulo_btn] = rect_btn 
            txt_desc = fontes['pequena'].render(descricao, True, (200, 200, 200))
            tela.blit(txt_desc, (dx + 210, rect_btn.centery - txt_desc.get_height()//2))
            y_btn += 65

    elif memoria_sub_aba == 2:
        textos_acordes = [
            (_t("Prática de Acordes"), _t("IA Real-Time: Toque o acorde completo em sua guitarra e a IA validará se as notas estão certas."))
        ]
        y_btn = y_start + 20
        for titulo_btn, descricao in textos_acordes:
            rect_btn = pygame.Rect(dx + 20, y_btn, 170, 45)
            pygame.draw.rect(tela, AZUL_PRIMARIO, rect_btn, border_radius=6)
            txt_btn = fontes['ui'].render(titulo_btn, True, BRANCO)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width()//2, rect_btn.centery - txt_btn.get_height()//2))
            estado.botoes_estudo[titulo_btn] = rect_btn 
            txt_desc = fontes['pequena'].render(descricao, True, (200, 200, 200))
            tela.blit(txt_desc, (dx + 210, rect_btn.centery - txt_desc.get_height()//2))
            y_btn += 65

    elif memoria_sub_aba == 3:
        txt = fontes['titulo'].render(_t("Módulo: Estudo de Teoria (Em Breve)"), True, (180, 180, 180))
        tela.blit(txt, (dx + (largura_conteudo // 2) - (txt.get_width() // 2), y_start + 100))

def desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos):
    alpha_atual = configs.get_alpha() if configs else 255
    
    dx = estado.dragger_painel_inferior.x if hasattr(estado, 'dragger_painel_inferior') else 100
    dy = estado.dragger_painel_inferior.y if hasattr(estado, 'dragger_painel_inferior') else estado.ALTURA_TELA - 50
    
    altura_caixa_total = 360
    largura_conteudo = estado.dragger_painel_inferior.largura if hasattr(estado, 'dragger_painel_inferior') else estado.LARGURA_BRACO
    
    espacamento = 8
    num_secoes = len(estado.secoes_inferiores)
    largura_botao = (largura_conteudo - (espacamento * (num_secoes - 1))) / num_secoes 
    
    pos_x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
    pos_y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 90
    instrumento = getattr(estado, 'instrumento', 'guitarra')
    offset_y_guit = pos_y_guit + estado.ESPACO_CORDAS if instrumento == 'baixo' else pos_y_guit
    altura_guit_atual = estado.ALTURA_BRACO - (2 * estado.ESPACO_CORDAS) if instrumento == 'baixo' else estado.ALTURA_BRACO
    rect_braco_real = pygame.Rect(pos_x_guit, offset_y_guit, estado.LARGURA_BRACO, altura_guit_atual)
    
    tela.set_clip(None) 
    
    for chave_escala, lista_modulos_gerais in dicionario_escalas.items():
        for modulo in lista_modulos_gerais:
            if modulo.estado != 'painel': 
                modulo.x_braco = pos_x_guit
                modulo.y_braco = offset_y_guit
                modulo.atualizar_e_desenhar(tela, pygame.mouse.get_pos(), rect_braco_real, fontes['pequena'], alpha_atual)
    
    # Barra de Ferramentas Inferior (Estilo Dock Moderno)
    for i, secao in enumerate(estado.secoes_inferiores):
        x_botao = dx + (i * (largura_botao + espacamento))
        rect_cabecalho = pygame.Rect(x_botao, dy, largura_botao, 45)
        secao["rect_cabecalho"] = rect_cabecalho 
        
        cor_fundo = AZUL_PRIMARIO if secao["expandido"] else (40, 40, 40)
        pygame.draw.rect(tela, cor_fundo, rect_cabecalho, border_radius=RADIUS_PADRAO)
        if not secao["expandido"]:
            pygame.draw.rect(tela, COR_BORDA, rect_cabecalho, width=1, border_radius=RADIUS_PADRAO)
        
        # Tradução dinâmica do título para refletir troca de idioma em tempo real
        txt_traduzido = _t(secao["titulo"])
        txt = fontes['pequena'].render(txt_traduzido, True, BRANCO)
        tela.blit(txt, (rect_cabecalho.centerx - txt.get_width()//2, rect_cabecalho.centery - txt.get_height()//2))

        if secao["expandido"]:
            # Painel de Conteúdo
            y_conteudo = dy - altura_caixa_total - 15 
            rect_fundo_conteudo = pygame.Rect(dx, y_conteudo, largura_conteudo, altura_caixa_total)
            pygame.draw.rect(tela, (25, 25, 25), rect_fundo_conteudo, border_radius=RADIUS_PADRAO)
            pygame.draw.rect(tela, COR_BORDA, rect_fundo_conteudo, width=2, border_radius=RADIUS_PADRAO)

            # Sub-abas
            y_sub_abas = y_conteudo + 12
            altura_sub = 32
            if secao["sub_abas"]:
                largura_sub = (largura_conteudo - 40) / len(secao["sub_abas"])
                for j, nome_sub in enumerate(secao["sub_abas"]):
                    rect_sub = pygame.Rect(dx + 20 + (j * largura_sub), y_sub_abas, largura_sub - 5, altura_sub)
                    secao[f"rect_sub_{j}"] = rect_sub 
                    cor_sub = AZUL_PRIMARIO if secao["memoria_sub_aba"] == j else (40, 40, 40)
                    pygame.draw.rect(tela, cor_sub, rect_sub, border_radius=6)
                    
                    # Tradução dinâmica da sub-aba
                    txt_sub_trad = _t(nome_sub)
                    txt_sub = fontes['pequena'].render(txt_sub_trad, True, BRANCO)
                    tela.blit(txt_sub, (rect_sub.centerx - txt_sub.get_width()//2, rect_sub.centery - txt_sub.get_height()//2))

            y_area_desenho = y_conteudo + 55
            altura_util = altura_caixa_total - 70 
            
            rect_clipping = pygame.Rect(dx + 5, y_area_desenho, largura_conteudo - 10, altura_util)
            tela.set_clip(rect_clipping)
            scroll_atual = estado.scroll_y.get(i, 0)
            y_start = y_area_desenho - scroll_atual

            if secao["conteudo"] in ["escalas", "acordes"]:
                chaves = []
                if secao["conteudo"] == "escalas": chaves = ['maior', 'menor', 'penta_maior', 'penta_menor', 'blues', 'modos', 'harmonica', 'melodica', 'exoticas']
                elif secao["conteudo"] == "acordes": chaves = ['caged', 'triades_maior', 'triades_menor', 'setimas', 'power']
                
                if secao["memoria_sub_aba"] < len(chaves):
                    chave_atual = chaves[secao["memoria_sub_aba"]]
                    lista_ativa = dicionario_escalas.get(chave_atual, [])
                    for modulo in lista_ativa:
                        if modulo.estado == 'painel':
                            modulo.x_braco = pos_x_guit
                            modulo.y_braco = offset_y_guit
                            y_rel = getattr(modulo, 'y_relativo', 0)
                            modulo.rect_painel.y = y_start + 20 + y_rel
                            modulo.scroll_offset = 0 
                            modulo.atualizar_e_desenhar(tela, pygame.mouse.get_pos(), rect_braco_real, fontes['pequena'], alpha_atual)
                    tela.set_clip(rect_clipping)

            elif secao["conteudo"] == "analise_ia":
                _desenhar_aba_ia(tela, dx, y_start, estado, fontes, meu_processador, meu_gravador, meu_gerenciador_jogos, secao["memoria_sub_aba"])

            elif secao["conteudo"] == "configuracao":
                _desenhar_aba_configuracao(tela, dx, y_start, estado, fontes, configs, meu_metronomo, secao["memoria_sub_aba"])

            elif secao["conteudo"] == "estudos":
                _desenhar_aba_estudos(tela, dx, y_start, largura_conteudo, estado, fontes, secao["memoria_sub_aba"])

            tela.set_clip(None)

            if estado.max_scroll.get(i, 0) > 0:
                x_scroll = dx + largura_conteudo - 12
                tamanho_alca = max(30, altura_util * (altura_util / (altura_util + estado.max_scroll[i])))
                y_alca = y_area_desenho + (scroll_atual / estado.max_scroll[i]) * (altura_util - tamanho_alca)
                pygame.draw.rect(tela, (45, 45, 45), (x_scroll, y_area_desenho, 8, altura_util), border_radius=4)
                pygame.draw.rect(tela, (120, 120, 120), (x_scroll, y_alca, 8, tamanho_alca), border_radius=4)

    if estado.drag_ativado and hasattr(estado, 'dragger_painel_inferior'):
        estado.dragger_painel_inferior.desenhar_caixa_selecao(tela, margem=8)

def desenhar_bloco_nota_atual(tela, estado, fontes):
    if not hasattr(estado, 'dragger_nota_atual'): return
    
    x_base = estado.dragger_nota_atual.x
    y_base = estado.dragger_nota_atual.y
    largura = estado.dragger_nota_atual.largura
    altura = estado.dragger_nota_atual.altura

    # Bloco Nota Atual Profissional
    pygame.draw.rect(tela, FUNDO_PAINEL, (x_base, y_base, largura, altura), border_radius=RADIUS_PADRAO)
    pygame.draw.rect(tela, COR_BORDA, (x_base, y_base, largura, altura), width=1, border_radius=RADIUS_PADRAO)

    nota_microfone = estado.nota_atual_detectada

    # Nota Grande Centralizada
    cor_nota_grande = VERDE_SUCCESS if nota_microfone != "--" else (100, 100, 100)
    txt_nota = fontes['titulo'].render(nota_microfone, True, cor_nota_grande)
    tela.blit(txt_nota, (x_base + 25, y_base + 15))
    
    txt_label = fontes['pequena'].render(_t("Entrada de Áudio"), True, (150, 150, 150))
    tela.blit(txt_label, (x_base + 25, y_base + 55))

    # Seleção de Notas (Grid Moderno)
    y_selecao = y_base + 85
    espacamento = (largura - 40) / 12
    estado.rects_notas_selecao.clear()

    notas_base = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    for i, n in enumerate(notas_base):
        rect_n = pygame.Rect(x_base + 20 + (i * espacamento), y_selecao, espacamento - 3, 35)
        estado.rects_notas_selecao.append((rect_n, n))
        
        cor_bg = AZUL_PRIMARIO if estado.nota_selecionada_bloco == n else (40, 40, 40)
        pygame.draw.rect(tela, cor_bg, rect_n, border_radius=5)
        if estado.nota_selecionada_bloco != n:
            pygame.draw.rect(tela, COR_BORDA, rect_n, width=1, border_radius=5)
        
        txt_n = fontes['pequena'].render(n, True, BRANCO)
        tela.blit(txt_n, (rect_n.centerx - txt_n.get_width()//2, rect_n.centery - txt_n.get_height()//2))

    # Sliders de Calibração
    y_ctrl = y_selecao + 50
    
    # Persistência
    txt_pers = fontes['pequena'].render(f"{_t('Persistência')}: {estado.afinador_persistencia}ms", True, (180, 180, 180))
    tela.blit(txt_pers, (x_base + 20, y_ctrl))
    
    barra_pers = pygame.Rect(x_base + 20, y_ctrl + 22, largura - 40, 6)
    pygame.draw.rect(tela, (40, 40, 40), barra_pers, border_radius=3)
    pct_pers = (estado.afinador_persistencia - 100) / 2900
    pos_alca = barra_pers.x + (pct_pers * barra_pers.width)
    estado.rect_alca_persistencia = pygame.Rect(pos_alca - 7, barra_pers.y - 5, 14, 16)
    pygame.draw.rect(tela, AZUL_PRIMARIO, estado.rect_alca_persistencia, border_radius=4)
    estado.rect_barra_persistencia = barra_pers

    # Threshold
    y_ctrl += 42
    txt_thresh = fontes['pequena'].render(f"{_t('Sensibilidade')}: {estado.afinador_threshold:.2f}", True, (180, 180, 180))
    tela.blit(txt_thresh, (x_base + 20, y_ctrl))
    
    barra_thresh = pygame.Rect(x_base + 20, y_ctrl + 22, largura - 40, 6)
    pygame.draw.rect(tela, (40, 40, 40), barra_thresh, border_radius=3)
    pct_thresh = (estado.afinador_threshold - 0.1) / 0.7
    pos_alca_t = barra_thresh.x + (pct_thresh * barra_thresh.width)
    estado.rect_alca_threshold = pygame.Rect(pos_alca_t - 7, barra_thresh.y - 5, 14, 16)
    pygame.draw.rect(tela, AZUL_PRIMARIO, estado.rect_alca_threshold, border_radius=4)
    estado.rect_barra_threshold = barra_thresh

    if estado.drag_ativado:
        estado.dragger_nota_atual.desenhar_caixa_selecao(tela, margem=8)

def desenhar_tudo(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_campo_harmonico, meu_gerenciador_jogos):
    tela.fill(FUNDO_ESCURO)
    
    # 1. Desenho do Workspace Físico
    desenhar_painel_superior(tela, estado, fontes)
    if hasattr(estado, 'lista_guitarras'):
        for guit in estado.lista_guitarras:
            desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico, dragger_obj=guit)
    else:
        # Fallback se não houver lista, desenha a padrão
        desenhar_guitarra(tela, estado, configs, fontes, meu_processador, meu_campo_harmonico)

    desenhar_acordes_arrastaveis(tela, estado, meu_campo_harmonico, fontes)
    desenhar_painel_cores(tela, estado, fontes)
    desenhar_bloco_nota_atual(tela, estado, fontes)
    meu_metronomo.desenhar_mini_metronomo(tela, estado, fontes['ui'])
    desenhar_secoes_inferiores_expansiveis(tela, estado, configs, dicionario_escalas, fontes, meu_metronomo, meu_processador, meu_gravador, meu_gerenciador_jogos)
    
    # 2. Desenho de Telas Cheias (Cobre o Workspace)
    largura_real = getattr(estado, 'LARGURA_TELA', 1280)
    altura_real = getattr(estado, 'ALTURA_TELA', 720)

    if getattr(estado, 'tela_estudo_ativa', False):
        if not hasattr(estado, 'gerenciador_estudos'):
            estado.gerenciador_estudos = modulo_estudos.GerenciadorEstudos()
        estado.gerenciador_estudos.desenhar_tela_estudo(tela, largura_real, altura_real, estado, fontes)
    elif estado.tela_jogo_ativa: 
        meu_gerenciador_jogos.desenhar_tela_jogo(tela, largura_real, altura_real, estado, meu_gravador, configs)

    # 3. Desenho de Menus Flutuantes (UI Suprema)
    if hasattr(estado, 'menu_superior'):
        estado.menu_superior.desenhar(tela, fontes['ui'], estado)
    if hasattr(estado, 'gerenciador_perfil'):
        estado.gerenciador_perfil.desenhar(tela, fontes['titulo'], fontes['ui'], estado) 
    if hasattr(estado, 'menu_contexto'):
        estado.menu_contexto.desenhar(tela, fontes['ui'])

    # 4. Impressão Fotográfica (Roda escondido no final)
    if getattr(estado, 'solicitou_impressao', False):
        import os
        try:
            tela_w, tela_h = tela.get_size()
            x_guit = estado.dragger_guitarra.x if hasattr(estado, 'dragger_guitarra') else 100
            y_guit = estado.dragger_guitarra.y if hasattr(estado, 'dragger_guitarra') else 100
            largura = estado.LARGURA_BRACO
            altura = estado.ALTURA_BRACO
            
            x_captura = max(0, x_guit - 80)
            y_captura = max(0, y_guit - 80)
            largura_captura = min(tela_w - x_captura, largura + 160)
            altura_captura = min(tela_h - y_captura, altura + 160)
            
            rect_captura = pygame.Rect(x_captura, y_captura, largura_captura, altura_captura)
            imagem_recortada = tela.subsurface(rect_captura)
            caminho_imagem = os.path.join(os.getcwd(), "impressao_eiguit.png")
            pygame.image.save(imagem_recortada, caminho_imagem)
            
            if os.name == 'nt':
                os.startfile(caminho_imagem, "print")
                print(f"[IMPRESSÃO] Imagem salva e enviada para o Windows: {caminho_imagem}")
        except Exception as e:
            print(f"[ERRO IMPRESSÃO] Não foi possível gerar a impressão: {e}")
            
        estado.solicitou_impressao = False
