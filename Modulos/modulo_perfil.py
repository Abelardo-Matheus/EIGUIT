# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Todos os direitos reservados. Uso comercial proibido.
# =============================================================================

import pygame
import os
import json

class GerenciadorPerfil:
    def __init__(self):
        self.pasta_padrao = "Perfis"
        self.arquivo_config_global = "config_eiguit.json"
        
        self.ativo = False
        self.modo = None 
        self.texto_input = ""
        
        self.lista_perfis = []
        self.indice_selecionado = 0
        
        if not os.path.exists(self.pasta_padrao):
            os.makedirs(self.pasta_padrao)

        self.BRANCO = (255, 255, 255)
        self.FUNDO = (30, 30, 30)
        self.AZUL_BOTAO = (0, 120, 215)
        self.CINZA = (100, 100, 100)
        self.VERMELHO = (200, 50, 50)

    def abrir_modal_novo(self):
        self.ativo = True
        self.modo = 'salvar'
        self.texto_input = "Meu_Setup" 

    def abrir_modal_carregar(self):
        self.ativo = True
        self.modo = 'carregar'
        self.lista_perfis = [f for f in os.listdir(self.pasta_padrao) if f.endswith('.json')]
        self.indice_selecionado = 0

    def fechar_modal(self):
        self.ativo = False
        self.modo = None
        self.texto_input = ""

    def restaurar_padrao(self, estado, configs=None, campo=None):
        import pygame
        import json
        
        # Volta a centralizar usando a tela real do monitor do usuário
        tela = pygame.display.get_surface()
        if tela:
            largura_tela = tela.get_width()
            altura_tela = tela.get_height()
        else:
            largura_tela = getattr(estado, 'LARGURA_BRACO', 1000) + 350
            altura_tela = getattr(estado, 'ALTURA_TELA', 768)
       
        largura_braco = getattr(estado, 'LARGURA_BRACO', largura_tela - 350)
        altura_braco = getattr(estado, 'ALTURA_BRACO', 300)
        largura_acordes = getattr(estado, 'LARGURA_ACORDES', 580)
        altura_acordes = getattr(estado, 'ALTURA_ACORDES', 110)
        largura_metronomo = getattr(estado, 'LARGURA_METRONOMO', 250)
        largura_topo = 480

        centro_x_braco = (largura_tela - largura_braco) // 2
        centro_x_acordes = (largura_tela - largura_acordes) // 2
        centro_x_metronomo = (largura_tela - largura_metronomo) // 2
        centro_x_topo = (largura_tela - largura_topo) // 2

        padroes = {
            'dragger_controles_topo': {'x': centro_x_topo, 'y': 30},
            'dragger_guitarra': {'x': centro_x_braco, 'y': 100},
            'dragger_acordes': {'x': centro_x_acordes, 'y': 480},
            'dragger_metronomo': {'x': centro_x_metronomo, 'y': 480 + altura_acordes + 90},
            'dragger_painel_inferior': {'x': centro_x_braco, 'y': altura_tela - 60},
            'dragger_cores': {'x': 20, 'y': altura_tela - 270} 
        }
        
        for nome, coords in padroes.items():
            if hasattr(estado, nome):
                obj = getattr(estado, nome)
                obj.x = coords["x"]
                obj.y = coords["y"]
                if hasattr(obj, 'rect_caixa'):
                    obj.rect_caixa.x = coords["x"]
                    obj.rect_caixa.y = coords["y"]

        # Reseta as variáveis que influenciam as cores e interface
        if configs:
            configs.transparencia = 100
            configs.cor_braco = (80, 40, 15)
            configs.cor_notas = (255, 255, 255)
            configs.indice_modo = 0
            configs.indice_fonte = 0
            
        if estado:
            estado.instrumento = 'guitarra'
            estado.NUM_CASAS = 18
            estado.tom_atual = 'C'
            estado.indice_afinacao = 0
            estado.indice_cor_tonica = 0
            estado.indice_cor_terca = 0
            estado.indice_cor_quinta = 0
            estado.afinador_suavizacao = 5
            estado.afinador_sensibilidade = 0.5
            if hasattr(estado, 'atualizar_medidas'): estado.atualizar_medidas()
            
        if campo:
            campo.tonica_campo = 'C'
            campo.indice_escala_campo = 0
            campo.tonica = 'C'
            campo.tipo_escala = "Maior (Jônio)"
            campo.indice_acorde_selecionado = -1
            
        try:
            with open(self.arquivo_config_global, 'w', encoding='utf-8') as f:
                json.dump({"ultimo_perfil": ""}, f)
        except: pass
            
        print("[PERFIL] Layout restaurado para o centro e as cores padrão!")

    # =========================================================================
    # NOVO: AGORA SALVA TUDO (ESTADO, CORES, MIC, CAMPO HARMÔNICO)
    # =========================================================================
    def salvar_perfil(self, estado, configs, campo, gravador):
        nome_arquivo = self.texto_input.strip()
        if not nome_arquivo: return
        if not nome_arquivo.endswith(".json"): nome_arquivo += ".json"
            
        caminho = os.path.join(self.pasta_padrao, nome_arquivo)

        dados = {
            "posicoes_draggers": {},
            "estado": {
                "instrumento": getattr(estado, 'instrumento', 'guitarra'),
                "NUM_CASAS": getattr(estado, 'NUM_CASAS', 18),
                "tom_atual": getattr(estado, 'tom_atual', 'C'),
                "indice_afinacao": getattr(estado, 'indice_afinacao', 0),
                "indice_cor_tonica": getattr(estado, 'indice_cor_tonica', 0),
                "indice_cor_terca": getattr(estado, 'indice_cor_terca', 0),
                "indice_cor_quinta": getattr(estado, 'indice_cor_quinta', 0),
                "afinador_suavizacao": getattr(estado, 'afinador_suavizacao', 5),
                "afinador_sensibilidade": getattr(estado, 'afinador_sensibilidade', 0.5)
            },
            "configs": {
                "transparencia": getattr(configs, 'transparencia', 100),
                "cor_braco": getattr(configs, 'cor_braco', (80, 40, 15)),
                "cor_notas": getattr(configs, 'cor_notas', (255, 255, 255)),
                "indice_modo": getattr(configs, 'indice_modo', 0),
                "indice_fonte": getattr(configs, 'indice_fonte', 0)
            },
            "campo_harmonico": {
                "tonica_campo": getattr(campo, 'tonica_campo', 'C'),
                "indice_escala_campo": getattr(campo, 'indice_escala_campo', 0)
            },
            "gravador": {
                "device_id": getattr(gravador, 'device_id', None)
            }
        }

        lista_draggers = ['dragger_guitarra', 'dragger_acordes', 'dragger_controles_topo', 
                          'dragger_painel_inferior', 'dragger_metronomo', 'dragger_cores']
        for nome in lista_draggers:
            if hasattr(estado, nome):
                obj = getattr(estado, nome)
                dados["posicoes_draggers"][nome] = {"x": obj.x, "y": obj.y}

        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4)

        self.salvar_ultimo_perfil_config(caminho)
        print(f"[PERFIL] Perfil completo salvo em: {caminho}")
        self.fechar_modal()

    # =========================================================================
    # NOVO: AGORA CARREGA TUDO DE VOLTA PROS COMPONENTES DO PROGRAMA
    # =========================================================================
    def carregar_perfil(self, caminho, estado, configs, campo, gravador):
        if not os.path.exists(caminho): return
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
            if "posicoes_draggers" in dados:
                for nome, coords in dados["posicoes_draggers"].items():
                    if hasattr(estado, nome):
                        obj = getattr(estado, nome)
                        obj.x = coords["x"]
                        obj.y = coords["y"]
                        if hasattr(obj, 'rect_caixa'):
                            obj.rect_caixa.x = coords["x"]
                            obj.rect_caixa.y = coords["y"]
                            
            if "estado" in dados:
                d_est = dados["estado"]
                estado.instrumento = d_est.get("instrumento", 'guitarra')
                estado.NUM_CASAS = d_est.get("NUM_CASAS", 18)
                estado.tom_atual = d_est.get("tom_atual", 'C')
                estado.indice_afinacao = d_est.get("indice_afinacao", 0)
                estado.indice_cor_tonica = d_est.get("indice_cor_tonica", 0)
                estado.indice_cor_terca = d_est.get("indice_cor_terca", 0)
                estado.indice_cor_quinta = d_est.get("indice_cor_quinta", 0)
                estado.afinador_suavizacao = d_est.get("afinador_suavizacao", 5)
                estado.afinador_sensibilidade = d_est.get("afinador_sensibilidade", 0.5)

            if "configs" in dados:
                d_cfg = dados["configs"]
                configs.transparencia = d_cfg.get("transparencia", 100)
                configs.cor_braco = tuple(d_cfg.get("cor_braco", (80, 40, 15)))
                configs.cor_notas = tuple(d_cfg.get("cor_notas", (255, 255, 255)))
                configs.indice_modo = d_cfg.get("indice_modo", 0)
                configs.indice_fonte = d_cfg.get("indice_fonte", 0)

            if "campo_harmonico" in dados:
                d_ch = dados["campo_harmonico"]
                campo.tonica_campo = d_ch.get("tonica_campo", "C")
                campo.indice_escala_campo = d_ch.get("indice_escala_campo", 0)
                campo.tonica = campo.tonica_campo 
                campo.tipo_escala = campo.escalas_campo[campo.indice_escala_campo]["nome"]
                campo.indice_acorde_selecionado = -1

            if "gravador" in dados and gravador:
                novo_id = dados["gravador"].get("device_id", None)
                if novo_id is not None and hasattr(gravador, 'mudar_dispositivo'):
                    try: gravador.mudar_dispositivo(novo_id)
                    except: pass

            if hasattr(estado, 'atualizar_medidas'):
                estado.atualizar_medidas()
                
            print(f"[PERFIL] Setup global carregado: {caminho}")
            self.salvar_ultimo_perfil_config(caminho)
            
        except Exception as e: print(f"[PERFIL] Erro ao carregar perfil: {e}")

    def deletar_perfil_atual(self):
        if os.path.exists(self.arquivo_config_global):
            try:
                with open(self.arquivo_config_global, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                ultimo = config.get("ultimo_perfil", "")
                if ultimo and os.path.exists(ultimo):
                    os.remove(ultimo)
                    print(f"[PERFIL] Perfil deletado: {ultimo}")
                    with open(self.arquivo_config_global, 'w', encoding='utf-8') as f:
                        json.dump({"ultimo_perfil": ""}, f)
            except: pass

    def salvar_ultimo_perfil_config(self, caminho):
        config = {"ultimo_perfil": caminho}
        with open(self.arquivo_config_global, 'w', encoding='utf-8') as f:
            json.dump(config, f)

    def carregar_ultimo_perfil(self, estado, configs, campo, gravador):
        if os.path.exists(self.arquivo_config_global):
            try:
                with open(self.arquivo_config_global, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    ultimo = config.get("ultimo_perfil", "")
                    if ultimo and os.path.exists(ultimo):
                        self.carregar_perfil(ultimo, estado, configs, campo, gravador)
            except: pass

    def tratar_eventos(self, eventos, estado, configs, campo, gravador):
        if not self.ativo: return False

        for evento in eventos:
            if evento.type == pygame.QUIT:
                estado.solicitou_saida = True
                
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.fechar_modal()
                
                elif self.modo == 'salvar':
                    if evento.key == pygame.K_RETURN:
                        self.salvar_perfil(estado, configs, campo, gravador)
                    elif evento.key == pygame.K_BACKSPACE:
                        self.texto_input = self.texto_input[:-1]
                    else:
                        if len(self.texto_input) < 20 and evento.unicode.isprintable():
                            self.texto_input += evento.unicode
                            
                elif self.modo == 'carregar' and evento.key == pygame.K_RETURN:
                    if len(self.lista_perfis) > 0:
                        caminho = os.path.join(self.pasta_padrao, self.lista_perfis[self.indice_selecionado])
                        self.carregar_perfil(caminho, estado, configs, campo, gravador)
                        self.fechar_modal()

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos_mouse = pygame.mouse.get_pos()
                
                if hasattr(self, 'btn_cancelar') and self.btn_cancelar.collidepoint(pos_mouse):
                    self.fechar_modal()
                    
                if self.modo == 'salvar':
                    if hasattr(self, 'btn_acao') and self.btn_acao.collidepoint(pos_mouse):
                        self.salvar_perfil(estado, configs, campo, gravador)
                        
                elif self.modo == 'carregar':
                    if hasattr(self, 'btn_esq') and self.btn_esq.collidepoint(pos_mouse) and len(self.lista_perfis) > 0:
                        self.indice_selecionado = (self.indice_selecionado - 1) % len(self.lista_perfis)
                    elif hasattr(self, 'btn_dir') and self.btn_dir.collidepoint(pos_mouse) and len(self.lista_perfis) > 0:
                        self.indice_selecionado = (self.indice_selecionado + 1) % len(self.lista_perfis)
                    elif hasattr(self, 'btn_acao') and self.btn_acao.collidepoint(pos_mouse) and len(self.lista_perfis) > 0:
                        caminho = os.path.join(self.pasta_padrao, self.lista_perfis[self.indice_selecionado])
                        self.carregar_perfil(caminho, estado, configs, campo, gravador)
                        self.fechar_modal()

        return True 

    def desenhar(self, tela, fonte_titulo, fonte_ui):
        if not self.ativo: return

        overlay = pygame.Surface((tela.get_width(), tela.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        largura_modal = 450
        altura_modal = 250
        cx = tela.get_width() // 2 - largura_modal // 2
        cy = tela.get_height() // 2 - altura_modal // 2
        rect_modal = pygame.Rect(cx, cy, largura_modal, altura_modal)

        pygame.draw.rect(tela, self.FUNDO, rect_modal, border_radius=10)
        pygame.draw.rect(tela, self.CINZA, rect_modal, width=2, border_radius=10)

        if self.modo == 'salvar':
            txt_tit = fonte_titulo.render("Salvar Novo Perfil", True, self.BRANCO)
            tela.blit(txt_tit, (cx + 20, cy + 20))

            tela.blit(fonte_ui.render("Nome do Perfil:", True, self.CINZA), (cx + 20, cy + 70))
            rect_input = pygame.Rect(cx + 20, cy + 95, largura_modal - 40, 40)
            pygame.draw.rect(tela, (20, 20, 20), rect_input, border_radius=5)
            pygame.draw.rect(tela, self.AZUL_BOTAO, rect_input, width=2, border_radius=5)
            
            txt_digitado = fonte_titulo.render(self.texto_input + "_", True, self.BRANCO)
            tela.blit(txt_digitado, (rect_input.x + 10, rect_input.y + 10))
            
            texto_btn_acao = "Salvar Setup"
            cor_acao = self.AZUL_BOTAO if len(self.texto_input) > 0 else self.CINZA

        elif self.modo == 'carregar':
            txt_tit = fonte_titulo.render("Carregar Perfil Existente", True, self.BRANCO)
            tela.blit(txt_tit, (cx + 20, cy + 20))

            tela.blit(fonte_ui.render("Selecione o arquivo salvo:", True, self.CINZA), (cx + 20, cy + 70))
            
            self.btn_esq = pygame.Rect(cx + 20, cy + 95, 40, 40)
            self.btn_dir = pygame.Rect(cx + largura_modal - 60, cy + 95, 40, 40)
            rect_meio = pygame.Rect(cx + 70, cy + 95, largura_modal - 140, 40)

            pygame.draw.rect(tela, self.AZUL_BOTAO, self.btn_esq, border_radius=5)
            pygame.draw.rect(tela, self.AZUL_BOTAO, self.btn_dir, border_radius=5)
            tela.blit(fonte_titulo.render("<", True, self.BRANCO), (self.btn_esq.centerx - 6, self.btn_esq.centery - 12))
            tela.blit(fonte_titulo.render(">", True, self.BRANCO), (self.btn_dir.centerx - 6, self.btn_dir.centery - 12))

            pygame.draw.rect(tela, (20, 20, 20), rect_meio, border_radius=5)
            pygame.draw.rect(tela, self.CINZA, rect_meio, width=2, border_radius=5)

            if len(self.lista_perfis) > 0:
                nome_exibir = self.lista_perfis[self.indice_selecionado]
            else:
                nome_exibir = "Nenhum Perfil Encontrado"

            txt_nome = fonte_titulo.render(nome_exibir, True, self.BRANCO)
            tela.blit(txt_nome, (rect_meio.centerx - txt_nome.get_width()//2, rect_meio.centery - txt_nome.get_height()//2))

            texto_btn_acao = "Carregar"
            cor_acao = self.AZUL_BOTAO if len(self.lista_perfis) > 0 else self.CINZA

        txt_dir = fonte_ui.render(f"Pasta Base: ./EIGUIT/{self.pasta_padrao}/", True, (150, 150, 150))
        tela.blit(txt_dir, (cx + 20, cy + 150))

        self.btn_cancelar = pygame.Rect(cx + 20, cy + 190, 150, 40)
        self.btn_acao = pygame.Rect(cx + largura_modal - 170, cy + 190, 150, 40)

        pygame.draw.rect(tela, self.VERMELHO, self.btn_cancelar, border_radius=5)
        txt_canc = fonte_ui.render("Cancelar", True, self.BRANCO)
        tela.blit(txt_canc, (self.btn_cancelar.centerx - txt_canc.get_width()//2, self.btn_cancelar.centery - txt_canc.get_height()//2))

        pygame.draw.rect(tela, cor_acao, self.btn_acao, border_radius=5)
        txt_acao_render = fonte_ui.render(texto_btn_acao, True, self.BRANCO)
        tela.blit(txt_acao_render, (self.btn_acao.centerx - txt_acao_render.get_width()//2, self.btn_acao.centery - txt_acao_render.get_height()//2))