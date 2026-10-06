# -*- coding: utf-8 -*-
"""
Menu superior do EIGUIT: barra de menus, atalhos de teclado e modais.

Estrutura:
- MENUS descreve cada menu (id da acao, rotulo, atalho, marcador e quando fica
  habilitado). O desenho e o clique leem a mesma lista.
- executar_acao() traduz o id em uma chamada de core/acoes_cabecalho.py.
- Os modais (confirmacao, lista de opcoes, texto informativo) sao genericos e
  sempre centrados na tela real, fora da camera do workspace.
"""
import pygame

import core.acoes_cabecalho as acoes
import core.atalhos as atalhos
import core.modulos.modulo_suporte as modulo_suporte
from config.design_system import TEMA, ds
from core.i18n import _t
from core.modulos.modulos_config import *  # noqa: F401,F403  (MENU_SUPERIOR_ALTURA_BARRA)

SEP = '-'

# (id, rotulo). A tecla mostrada ao lado vem de core/atalhos.py (o usuario
# troca em Configuracoes > Teclas de atalho).
MENUS = [
    ('Arquivo', [
        ('novo_projeto', 'Novo projeto'),
        ('abrir_projeto', 'Abrir projeto...'),
        SEP,
        ('salvar_projeto', 'Salvar'),
        ('salvar_como', 'Salvar como...'),
        SEP,
        ('exportar_txt', 'Exportar tablatura (.txt)'),
        ('exportar_midi', 'Exportar MIDI (.mid)'),
        SEP,
        ('capturar_tela', 'Capturar tela (PNG)'),
        ('abrir_pasta', 'Abrir pasta do EIGUIT'),
        SEP,
        ('sair', 'Sair'),
    ]),
    ('Exibir', [
        ('modo_edicao', 'Modo de edição do layout'),
        ('tema_escuro', 'Tema escuro'),
        SEP,
        ('zoom_mais', 'Aumentar zoom'),
        ('zoom_menos', 'Diminuir zoom'),
        ('zoom_padrao', 'Zoom 100% / centralizar'),
        SEP,
        ('restaurar_layout', 'Restaurar layout dos blocos'),
        ('tela_cheia', 'Tela cheia'),
    ]),
    # O Perfil nao fica na barra de menus: abre pelo botao da conta, no canto
    # superior direito (ancora_dropdown).
    ('Perfil', [
        ('conta', 'Minha conta (Cloud)'),
        SEP,
        ('perfil_salvar', 'Salvar perfil...'),
        ('perfil_carregar', 'Carregar perfil...'),
        ('perfil_excluir', 'Excluir perfil atual'),
        ('perfil_padrao', 'Voltar para o padrão'),
        SEP,
        ('trocar_conta', 'Trocar de conta'),
    ]),
    ('Configurações', [
        ('pref_gerais', 'Preferências gerais'),
        ('pref_cores', 'Cores da interface'),
        ('teclas', 'Teclas de atalho'),
        ('desempenho', 'Desempenho'),
        SEP,
        ('audio', 'Entrada de áudio...'),
        ('tela', 'Tela e resolução...'),
        ('idioma', 'Idioma...'),
    ]),
    ('Ajuda', [
        ('suporte', 'Central de suporte e tutoriais'),
        ('atalhos', 'Atalhos do teclado'),
        SEP,
        ('ideias', 'Envie ideias'),
        ('patrocine', 'Apoie o projeto'),
        ('motivacao', 'A história do EIGUIT'),
        ('repositorio', 'Repositório no GitHub'),
        SEP,
        ('sobre', 'Sobre o EIGUIT'),
    ]),
]
MENUS_DA_BARRA = ['Arquivo', 'Exibir', 'Configurações', 'Ajuda']

# Dentro das telas de estudo estes atalhos ja tem outro uso (abrir partitura,
# zoom da partitura): la eles ficam com a tela.
ATALHOS_DA_TELA_DE_ESTUDO = {'abrir_projeto', 'zoom_mais', 'zoom_menos', 'zoom_padrao'}
# O zoom so faz sentido na mesa de trabalho
ACOES_SO_NO_WORKSPACE = {'zoom_mais', 'zoom_menos', 'zoom_padrao', 'secao_escalas',
                         'secao_acordes', 'secao_analise_ia', 'secao_estudos',
                         'secao_musicas', 'secao_configuracao'}
# Teclas fixas do sistema (nao configuraveis), so para a lista de atalhos
ATALHOS_FIXOS = [('Ctrl + roda', 'Zoom no ponteiro'), ('Botão do meio', 'Mover a visão'),
                 ('Alt + arrastar', 'Mover a visão'), ('Esc', 'Fechar menu ou janela'),
                 ('Alt', 'Abrir os menus (setas para navegar)')]

ALTURA_ITEM = 32
ALTURA_SEP = 9


def _ctrl_shift(evento):
    mods = getattr(evento, 'mod', 0) or 0
    return bool(mods & pygame.KMOD_CTRL), bool(mods & pygame.KMOD_SHIFT)


class MenuSuperior:
    """
        Como funciona: Guarda o estado da barra de menus (menu aberto, item em
        destaque, modal ativo), trata mouse/teclado e desenha menus e modais.
        Para que serve: Navegacao global do programa.
        Onde é usada: Criado em controlador_eventos.processar e desenhado por
        ui/components/top_bar.py.
    """

    def __init__(self):
        self.altura_barra = MENU_SUPERIOR_ALTURA_BARRA  # noqa: F405
        self.menu_aberto = None
        self.item_hover = None
        self.sub_item_hover = None
        self.gerenciador_suporte = modulo_suporte.TutorialSuporte()
        self.ordem_menus = list(MENUS_DA_BARRA)
        self.estrutura = {nome: itens for nome, itens in MENUS}
        self.rects_principais = {}
        self.rects_dropdown = []          # [(id, rect)] so dos itens clicaveis
        self.rect_dropdown = pygame.Rect(0, 0, 0, 0)
        self.largura_dropdown = 260
        self.ancora_dropdown = None       # rect alternativo (chip da conta)
        self.offset_x = 0
        self.largura_disponivel = 0
        self.largura_total_menu = 0
        self.fonte_menu = None
        self.modal = None
        self.pedir_regeneracao = False    # avisa o controlador para refazer escalas
        self._ctx = {}
        self._overlay = None

    # Compatibilidade com quem lia estes atributos
    @property
    def modal_ideias_aberto(self):
        return bool(self.modal and self.modal.get('id') == 'ideias')

    @property
    def modal_patrocine_aberto(self):
        return bool(self.modal and self.modal.get('id') == 'patrocine')

    @property
    def modal_motivacao_aberto(self):
        return bool(self.modal and self.modal.get('id') == 'motivacao')

    @property
    def ocupado(self):
        """Ha menu, modal ou suporte aberto por cima de tudo."""
        return bool(self.menu_aberto or self.modal or self.gerenciador_suporte.aberto)

    def consumir_regeneracao(self):
        pedir, self.pedir_regeneracao = self.pedir_regeneracao, False
        return pedir

    # ----------------------------------------------------------- estado ----
    def item_marcado(self, acao, estado):
        if acao == 'modo_edicao':
            return bool(getattr(estado, 'drag_ativado', False))
        if acao == 'tema_escuro':
            return bool(TEMA.escuro)
        if acao == 'tela_cheia':
            return acoes.em_tela_cheia(estado)
        return None

    def item_habilitado(self, acao, estado):
        if acao in ('salvar_projeto', 'salvar_como', 'exportar_txt', 'exportar_midi'):
            return acoes.tem_projeto(estado)
        if acao == 'perfil_excluir':
            return bool(acoes.nome_perfil_atual(estado))
        if acao in ACOES_SO_NO_WORKSPACE:
            return not acoes.ha_tela_aberta(estado)
        if acao == 'conta':
            return bool(getattr(estado, 'usuario_id_logado', None))
        return True

    # ---------------------------------------------------------- layout -----
    def recalcular_posicoes(self, largura_total=0, fonte=None):
        """Cada menu ocupa a largura do proprio texto (nada de cortar rotulos)."""
        largura_total = largura_total or self.largura_disponivel
        fonte = fonte or self.fonte_menu
        self.rects_principais.clear()
        x = self.offset_x + ds.ESPACO_SM
        if fonte is None:
            for menu in self.ordem_menus:
                self.rects_principais[menu] = pygame.Rect(x, 0, 110, self.altura_barra)
                x += 110
        else:
            larguras = [fonte.size(_t(m))[0] + 24 for m in self.ordem_menus]
            espaco = max(0, (largura_total or 1920) - self.offset_x - 420)
            if sum(larguras) > espaco > 0:
                fator = max(0.6, espaco / sum(larguras))
                larguras = [max(48, int(l * fator)) for l in larguras]
            for menu, larg in zip(self.ordem_menus, larguras):
                self.rects_principais[menu] = pygame.Rect(x, 0, larg, self.altura_barra)
                x += larg
        self.largura_total_menu = x

    def _medir_dropdown(self, menu, fonte):
        largura = 220
        for item in self.estrutura[menu]:
            if item == SEP:
                continue
            _id, rotulo = item
            atalho = self._texto_atalho(_id)
            larg = fonte.size(_t(rotulo))[0] + 44
            if atalho:
                larg += fonte.size(atalho)[0] + 36
            largura = max(largura, larg)
        return min(largura, 420)

    # ---------------------------------------------------------- eventos ----
    def abrir_menu(self, menu, ancora=None):
        self.menu_aberto = menu
        self.ancora_dropdown = ancora
        self.sub_item_hover = None

    def fechar_menu(self):
        self.menu_aberto = None
        self.ancora_dropdown = None
        self.sub_item_hover = None

    def _itens_clicaveis(self, menu, estado):
        return [item[0] for item in self.estrutura.get(menu, [])
                if item != SEP and self.item_habilitado(item[0], estado)]

    def _mover_destaque(self, passo, estado):
        ids = [item[0] if item != SEP else None for item in self.estrutura[self.menu_aberto]]
        if not ids:
            return
        i = self.sub_item_hover if self.sub_item_hover is not None else (-1 if passo > 0 else 0)
        for _ in range(len(ids)):
            i = (i + passo) % len(ids)
            if ids[i] is not None and self.item_habilitado(ids[i], estado):
                self.sub_item_hover = i
                return

    def tratar_eventos(self, evento, pos_mouse, estado, configs=None, campo=None, gravador=None):
        """
            Como funciona: Recebe UM evento (com o mouse em coordenadas reais) e
            devolve True quando ele pertence ao cabecalho (menu, modal, atalho ou
            botao da barra), para o controlador nao repassar adiante.
        """
        self._ctx = {'estado': estado, 'configs': configs, 'campo': campo, 'gravador': gravador}

        if evento.type == pygame.VIDEORESIZE:
            acoes.atualizar_tamanho_tela(estado, evento.w, evento.h)
            return False

        # O modal de perfil (salvar/carregar/conta) e dono da tela enquanto aberto
        perfil = getattr(estado, 'gerenciador_perfil', None)
        if perfil is not None and getattr(perfil, 'ativo', False):
            self.fechar_menu()
            return False

        # 1. Suporte e modais ficam com todos os eventos enquanto abertos
        if self.gerenciador_suporte.aberto:
            self.gerenciador_suporte.tratar_eventos([evento], pos_mouse)
            return True
        if self.modal:
            self._tratar_modal(evento, pos_mouse, estado)
            return True

        # 2. Gravando uma tecla nova (Configuracoes > Teclas de atalho)
        if getattr(estado, 'capturando_atalho', None):
            if evento.type == pygame.KEYDOWN:
                self._capturar_tecla(evento, estado)
                return True
            if evento.type == pygame.KEYUP:
                return True

        # 3. Atalhos globais
        if evento.type == pygame.KEYDOWN:
            # Alt sozinho (apertar e soltar) abre os menus; Alt+tecla e atalho
            self._alt_sozinho = evento.key in (pygame.K_LALT, pygame.K_RALT)
            if self.menu_aberto and self._tratar_teclado_menu(evento, estado):
                return True
            acao = self._acao_do_atalho(evento, estado)
            if acao:
                self.fechar_menu()
                self.executar_acao(acao, estado, configs, campo, gravador)
                return True
            return False
        if evento.type == pygame.KEYUP and evento.key in (pygame.K_LALT, pygame.K_RALT):
            if getattr(self, '_alt_sozinho', False):
                self._alt_sozinho = False
                if self.menu_aberto:
                    self.fechar_menu()
                else:
                    self.abrir_menu(self.ordem_menus[0])
                    self._mover_destaque(1, estado)
                return True
            return False

        # 4. Mouse sobre a barra e o dropdown
        if evento.type == pygame.MOUSEMOTION:
            self.item_hover = None
            for menu, rect in self.rects_principais.items():
                if rect.collidepoint(pos_mouse):
                    self.item_hover = menu
                    # Com um menu aberto, passar por cima de outro troca o menu
                    if self.menu_aberto and self.menu_aberto != menu:
                        self.abrir_menu(menu)
            if self.menu_aberto:
                self.sub_item_hover = None
                for acao, rect in self.rects_dropdown:
                    if rect.collidepoint(pos_mouse):
                        ids = [i[0] if i != SEP else None for i in self.estrutura[self.menu_aberto]]
                        self.sub_item_hover = ids.index(acao)
                return self.rect_dropdown.collidepoint(pos_mouse)
            return False

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button != 1:
                if self.menu_aberto:
                    self.fechar_menu()
                    return True
                return False
            for menu, rect in self.rects_principais.items():
                if rect.collidepoint(pos_mouse):
                    if self.menu_aberto == menu and self.ancora_dropdown is None:
                        self.fechar_menu()
                    else:
                        self.abrir_menu(menu)
                    return True
            if self.menu_aberto:
                for acao, rect in self.rects_dropdown:
                    if rect.collidepoint(pos_mouse):
                        if self.item_habilitado(acao, estado):
                            self.fechar_menu()
                            self.executar_acao(acao, estado, configs, campo, gravador)
                        return True
                if self.rect_dropdown.collidepoint(pos_mouse):
                    return True        # separador ou item desabilitado
                self.fechar_menu()
                return True            # clique fora so fecha o menu
            return self._tratar_botoes_barra(pos_mouse, estado, configs, campo, gravador)

        if evento.type == pygame.MOUSEBUTTONUP and self.menu_aberto:
            return True
        if evento.type == pygame.MOUSEWHEEL and self.menu_aberto:
            return True
        return False

    def _texto_atalho(self, acao, estado=None):
        estado = estado or self._ctx.get('estado')
        if estado is None:
            return atalhos.texto((atalhos.PADROES.get(acao) or [''])[0])
        return atalhos.texto_da_acao(estado, acao)

    def _acao_do_atalho(self, evento, estado):
        acao = atalhos.acao_do_evento(estado, evento)
        if not acao:
            return None
        if getattr(estado, 'tela_estudo_ativa', False) and acao in ATALHOS_DA_TELA_DE_ESTUDO:
            return None
        if acao in ACOES_SO_NO_WORKSPACE and acoes.ha_tela_aberta(estado):
            return None
        return acao

    def _tratar_teclado_menu(self, evento, estado):
        if evento.key == pygame.K_ESCAPE:
            self.fechar_menu()
        elif evento.key == pygame.K_DOWN:
            self._mover_destaque(1, estado)
        elif evento.key == pygame.K_UP:
            self._mover_destaque(-1, estado)
        elif evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
            i = (self.ordem_menus.index(self.menu_aberto)
                 if self.menu_aberto in self.ordem_menus else -1)
            i = (i + (1 if evento.key == pygame.K_RIGHT else -1)) % len(self.ordem_menus)
            self.abrir_menu(self.ordem_menus[i])
            self._mover_destaque(1, estado)
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.sub_item_hover is not None:
                item = self.estrutura[self.menu_aberto][self.sub_item_hover]
                if item != SEP and self.item_habilitado(item[0], estado):
                    self.fechar_menu()
                    c = self._ctx
                    self.executar_acao(item[0], estado, c.get('configs'), c.get('campo'),
                                       c.get('gravador'))
        else:
            return False
        return True

    def _tratar_botoes_barra(self, pos, estado, configs, campo, gravador):
        """Botoes desenhados pela barra (tema, edicao, tela cheia, conta...)."""
        for rect, acao in getattr(estado, 'botoes_cabecalho', []):
            if rect.collidepoint(pos):
                if acao == 'menu_conta':
                    if self.menu_aberto == 'Perfil' and self.ancora_dropdown is not None:
                        self.fechar_menu()
                    else:
                        self.abrir_menu('Perfil', ancora=rect)
                else:
                    self.executar_acao(acao, estado, configs, campo, gravador)
                return True
        return False

    def _capturar_tecla(self, evento, estado):
        """Primeira tecla (com modificadores) depois de clicar em 'Alterar'."""
        from ui.components.notificacoes import notificar
        acao = estado.capturando_atalho
        if evento.key == pygame.K_ESCAPE and not (evento.mod & (pygame.KMOD_CTRL | pygame.KMOD_ALT)):
            estado.capturando_atalho = None
            notificar(estado, _t('Alteração cancelada'), 'info', 1.5)
            return
        if evento.key in (pygame.K_BACKSPACE, pygame.K_DELETE) and not evento.mod & (
                pygame.KMOD_CTRL | pygame.KMOD_ALT | pygame.KMOD_SHIFT):
            atalhos.limpar(estado, acao)
            estado.capturando_atalho = None
            notificar(estado, f"{_t(atalhos.ROTULOS[acao])}: {_t('sem atalho')}", 'info')
            return
        combo = atalhos.combo_do_evento(evento)
        if combo is None:
            return                      # so apertou Ctrl/Shift/Alt: continua esperando
        if atalhos.precisa_modificador(combo):
            notificar(estado, _t('Letras, números e espaço precisam de Ctrl ou Alt '
                                 '(senão atrapalham a digitação).'), 'aviso', 3.5)
            return
        perdeu = atalhos.definir(estado, acao, combo)
        estado.capturando_atalho = None
        msg = f"{_t(atalhos.ROTULOS[acao])}: {atalhos.texto(combo)}"
        if perdeu:
            msg += f"  ({_t('removido de')} {_t(atalhos.ROTULOS[perdeu])})"
        notificar(estado, msg, 'sucesso', 3.0)

    # ----------------------------------------------------------- acoes -----
    def executar_acao(self, acao, estado, configs=None, campo=None, gravador=None):
        """Traduz o id de um item de menu (ou de um atalho) na acao certa."""
        if not self.item_habilitado(acao, estado) and acao not in ('salvar_projeto', 'exportar_txt',
                                                                 'exportar_midi', 'salvar_como'):
            return
        a = acoes
        perfil = getattr(estado, 'gerenciador_perfil', None)
        # --- Arquivo
        if acao == 'novo_projeto':
            if a.projeto_modificado(estado):
                self.confirmar('Descartar alterações?',
                               ['O projeto aberto tem alterações que não foram salvas.',
                                'Criar um novo projeto vai descartá-las.'],
                               'Criar novo', lambda: a.novo_projeto(estado), perigo=True,
                               extra=('Salvar antes', lambda: a.salvar_projeto(estado)
                                      and a.novo_projeto(estado)))
            else:
                a.novo_projeto(estado)
        elif acao == 'abrir_projeto':
            if a.projeto_modificado(estado):
                self.confirmar('Descartar alterações?',
                               ['O projeto aberto tem alterações que não foram salvas.'],
                               'Abrir mesmo assim', lambda: a.abrir_projeto(estado), perigo=True)
            else:
                a.abrir_projeto(estado)
        elif acao == 'salvar_projeto':
            a.salvar_projeto(estado)
        elif acao == 'salvar_como':
            a.salvar_projeto(estado, como=True)
        elif acao == 'exportar_txt':
            a.exportar_txt(estado)
        elif acao == 'exportar_midi':
            a.exportar_midi(estado)
        elif acao in ('capturar_tela', 'Imprimir'):
            a.pedir_captura(estado)
        elif acao == 'abrir_pasta':
            a.abrir_pasta(a.pasta_documentos())
        elif acao in ('sair', 'Sair'):
            if a.projeto_modificado(estado):
                self.confirmar('Sair do EIGUIT?',
                               ['O projeto aberto tem alterações que não foram salvas.'],
                               'Sair sem salvar', lambda: setattr(estado, 'solicitou_saida', True),
                               perigo=True,
                               extra=('Salvar e sair', lambda: a.salvar_projeto(estado)
                                      and setattr(estado, 'solicitou_saida', True)))
            else:
                estado.solicitou_saida = True
        # --- Exibir
        elif acao == 'modo_edicao':
            a.alternar_modo_edicao(estado)
        elif acao == 'tema_escuro':
            a.alternar_tema(estado)
        elif acao == 'zoom_mais':
            a.mudar_zoom(estado, a.PASSO_ZOOM)
        elif acao == 'zoom_menos':
            a.mudar_zoom(estado, -a.PASSO_ZOOM)
        elif acao == 'zoom_padrao':
            a.zoom_padrao(estado)
        elif acao == 'restaurar_layout':
            a.restaurar_layout(estado)
        elif acao in ('tela_cheia', 'Tela Cheia / Janela'):
            a.alternar_tela_cheia(estado)
        elif acao == 'voltar':
            a.fechar_telas(estado)
        # --- Perfil
        elif acao == 'conta' and perfil is not None:
            perfil.abrir_modal_conta(estado)
        elif acao == 'perfil_salvar' and perfil is not None:
            perfil.abrir_modal_novo()
        elif acao == 'perfil_carregar' and perfil is not None:
            perfil.abrir_modal_carregar()
            self.pedir_regeneracao = True
        elif acao == 'perfil_excluir':
            nome = a.nome_perfil_atual(estado)
            self.confirmar('Excluir perfil?',
                           [f"{_t('O perfil')} \"{nome}\" {_t('será apagado deste computador.')}",
                            'Esta ação não pode ser desfeita.'],
                           'Excluir', lambda: a.excluir_perfil(estado), perigo=True)
        elif acao == 'perfil_padrao':
            def _padrao():
                a.restaurar_padrao(estado, configs, campo)
                self.pedir_regeneracao = True
            self.confirmar('Voltar para o padrão?',
                           ['Layout, instrumento, tom, cores e afinador voltam',
                            'à configuração de fábrica.'],
                           'Restaurar', _padrao, perigo=True)
        elif acao == 'trocar_conta':
            self.confirmar('Trocar de conta?',
                           ['O EIGUIT será reaberto na tela de login.'],
                           'Trocar de conta', lambda: a.trocar_conta(estado))
        # --- Configuracoes
        elif acao == 'pref_gerais':
            a.abrir_secao(estado, 'configuracao', 1)
        elif acao == 'pref_cores':
            a.abrir_secao(estado, 'configuracao', 0)
        elif acao == 'audio':
            self.abrir_modal_audio(estado, gravador)
        elif acao == 'tela':
            self.abrir_modal_tela(estado)
        elif acao == 'idioma':
            self.abrir_modal_idioma(estado, configs)
        elif acao == 'teclas':
            a.abrir_secao(estado, 'configuracao', 2)
        elif acao == 'desempenho':
            a.abrir_secao(estado, 'configuracao', 3)
        # --- Workspace
        elif acao.startswith('secao_'):
            a.alternar_secao(estado, acao[len('secao_'):])
        elif acao == 'metronomo':
            a.alternar_metronomo(estado)
        elif acao in ('bpm_mais', 'bpm_menos'):
            a.mudar_bpm(estado, 5 if acao == 'bpm_mais' else -5)
        # --- Ajuda
        elif acao == 'suporte':
            self.gerenciador_suporte.aberto = True
        elif acao == 'atalhos':
            self.modal = {'id': 'atalhos', 'tipo': 'atalhos', 'titulo': 'Atalhos do teclado',
                          'largura': 980}
        elif acao == 'ideias':
            self.abrir_modal_ideias()
        elif acao == 'patrocine':
            self.abrir_modal_patrocine()
        elif acao == 'motivacao':
            self.abrir_modal_motivacao()
        elif acao == 'repositorio':
            a.abrir_link(a.URL_REPOSITORIO)
        elif acao == 'sobre':
            self.abrir_modal_sobre()

    # ---------------------------------------------------------- modais -----
    def confirmar(self, titulo, linhas, rotulo_ok, ao_confirmar, perigo=False, extra=None):
        botoes = [('Cancelar', 'secundario', None)]
        if extra:
            botoes.append((extra[0], 'suave', extra[1]))
        botoes.append((rotulo_ok, 'perigo' if perigo else 'primario', ao_confirmar))
        self.modal = {'id': 'confirmar', 'tipo': 'info', 'titulo': titulo,
                      'linhas': linhas, 'botoes': botoes, 'largura': 560}

    def abrir_modal_lista(self, id_modal, titulo, descricao, opcoes, selecionado, ao_escolher,
                          vazio='Nenhuma opção disponível.'):
        self.modal = {'id': id_modal, 'tipo': 'lista', 'titulo': titulo,
                      'linhas': [descricao] if descricao else [], 'opcoes': opcoes,
                      'selecionado': selecionado, 'ao_escolher': ao_escolher,
                      'vazio': vazio, 'scroll': 0, 'largura': 620,
                      'botoes': [('Fechar', 'secundario', None)]}

    def abrir_modal_audio(self, estado, gravador):
        entradas = acoes.listar_entradas_audio(gravador)
        atual = getattr(gravador, 'device_id', None)
        selecionado = next((i for i, e in enumerate(entradas) if e['id'] == atual), -1)
        if gravador is None or not hasattr(gravador, 'mudar_dispositivo'):
            vazio = 'O motor de áudio não está disponível nesta sessão.'
        else:
            vazio = 'Nenhuma entrada de áudio encontrada. Conecte a interface/pedaleira e reabra.'
        status = ('Captura ativa' if getattr(gravador, 'ativo', False) else 'Sem captura no momento')
        self.abrir_modal_lista(
            'audio', 'Entrada de áudio',
            f"{_t('Escolha o dispositivo usado pelo afinador, jogos e análises.')}  "
            f"({_t(status)})",
            [(e['nome'], f"ID {e['id']}") for e in entradas], selecionado,
            lambda i: acoes.escolher_entrada_audio(estado, gravador, entradas[i]), vazio)

    def abrir_modal_tela(self, estado):
        modo = getattr(estado, 'modo_tela', None)
        if modo is None:
            modo = 'cheia' if acoes.em_tela_cheia(estado) else 'janela'

        def _igual(a, b):
            if isinstance(a, str) or isinstance(b, str):
                return a == b
            return tuple(a) == tuple(b)

        selecionado = next((i for i, (m, _r) in enumerate(acoes.MODOS_TELA) if _igual(m, modo)), -1)
        atual = f"{estado.LARGURA_TELA} × {estado.ALTURA_TELA}" if hasattr(estado, 'LARGURA_TELA') else ''
        self.abrir_modal_lista(
            'tela', 'Tela e resolução',
            f"{_t('Tamanho atual')}: {atual}. {_t('O layout dos blocos é mantido.')}",
            [(r, '') for _m, r in acoes.MODOS_TELA], selecionado,
            lambda i: acoes.aplicar_modo_tela(estado, acoes.MODOS_TELA[i][0]))

    def abrir_modal_idioma(self, estado, configs):
        if configs is None or not hasattr(configs, 'idiomas'):
            return
        self.abrir_modal_lista(
            'idioma', 'Idioma da interface',
            'A tradução é feita automaticamente e guardada para as próximas vezes.',
            [(i['nome'], i['code'].upper()) for i in configs.idiomas],
            getattr(configs, 'indice_idioma', 0),
            lambda i: self._escolher_idioma(estado, configs, i))

    def _escolher_idioma(self, estado, configs, i):
        acoes.escolher_idioma(estado, configs, i)
        self.pedir_regeneracao = True

    def abrir_modal_ideias(self):
        self.modal = {'id': 'ideias', 'tipo': 'info', 'largura': 680,
                      'titulo': 'Colabore com o ecossistema open-source',
                      'linhas': ['Grandes ferramentas não nascem no isolamento; elas ganham vida através',
                                 'do diálogo direto com quem as utiliza. Se você vislumbrou um recurso,',
                                 'identificou falhas ou quer sugerir refinamentos técnicos, sua visão é crucial.',
                                 'O EIGUIT pertence à comunidade, e Pull Requests são muito bem-vindos.'],
                      'links': [('Compartilhe suas ideias', acoes.EMAIL_CONTATO,
                                 'mailto:' + acoes.EMAIL_CONTATO),
                                ('Repositório oficial', 'github.com/Abelardo-Matheus/EIGUIT',
                                 acoes.URL_REPOSITORIO)],
                      'botoes': [('Fechar', 'primario', None)]}

    def abrir_modal_patrocine(self):
        self.modal = {'id': 'patrocine', 'tipo': 'info', 'largura': 780,
                      'titulo': 'Apoie o desenvolvimento do projeto',
                      'linhas': ['Manter uma plataforma de código aberto exige dedicação, estudo e infraestrutura.',
                                 'Se o Guitar Studio IA trouxe clareza ou impulsionou sua rotina de estudos,',
                                 'saiba que seu incentivo é o que viabiliza a evolução contínua do sistema.',
                                 'Por enquanto, o suporte ao projeto é centralizado de forma direta via PIX.'],
                      'destaque': ('Chave PIX / Celular', '31983410907'),
                      'rodape': ['Este número também é meu canal direto no WhatsApp pessoal.',
                                 'Sinta-se à vontade para mandar feedbacks, dúvidas ou apenas conversar sobre música!'],
                      'botoes': [('Copiar chave PIX', 'suave', lambda: self._copiar('31983410907')),
                                 ('Fechar', 'primario', None)]}

    def abrir_modal_motivacao(self):
        self.modal = {'id': 'motivacao', 'tipo': 'info', 'largura': 860,
                      'titulo': 'A gênese do Guitar Studio IA',
                      'linhas': ['O EIGUIT nasceu de uma profunda inquietação pessoal. Diante dos labirintos',
                                 'teóricos e da fragmentação de materiais que frequentemente frustram o estudo',
                                 'da guitarra, idealizei este projeto, inicialmente, como um utilitário de uso restrito',
                                 '— um porto seguro para mapear escalas e visualizar intervalos de forma ágil.',
                                 'Contudo, à medida que as linhas de código se fundiam com as necessidades musicais,',
                                 'o software expandiu-se a ponto de se tornar um ambiente completo de prática.',
                                 'Compreendi, então, que reter essa ferramenta seria privar outros músicos do mesmo amparo.',
                                 'É uma honra abrir este ecossistema para que novos entusiastas aprimorem sua técnica',
                                 'através de uma metodologia visual, simples e unificada.'],
                      'botoes': [('Fechar', 'primario', None)]}

    def abrir_modal_sobre(self):
        versao = acoes.versao_programa()
        self.modal = {'id': 'sobre', 'tipo': 'info', 'largura': 600, 'logo': True,
                      'titulo': 'EIGUIT Studio',
                      'linhas': [f"{_t('Versão')} {versao}" if versao else '',
                                 'Estúdio completo para guitarristas: braço interativo, campo harmônico,',
                                 'afinador, estudos, criação musical, jogos e análise de timbre.',
                                 f'pygame {pygame.version.ver}',
                                 '© Abelardo Matheus — uso educacional, não comercial.'],
                      'links': [('Código-fonte', 'github.com/Abelardo-Matheus/EIGUIT',
                                 acoes.URL_REPOSITORIO)],
                      'botoes': [('Fechar', 'primario', None)]}

    def _copiar(self, texto):
        estado = self._ctx.get('estado')
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put_text(texto)
            ok = True
        except Exception:
            try:
                import tkinter as tk
                raiz = tk.Tk()
                raiz.withdraw()
                raiz.clipboard_clear()
                raiz.clipboard_append(texto)
                raiz.update()
                raiz.destroy()
                ok = True
            except Exception:
                ok = False
        from ui.components.notificacoes import notificar
        notificar(estado, _t('Copiado para a área de transferência') if ok
                  else _t('Não foi possível copiar'), 'sucesso' if ok else 'erro')
        return False      # mantem o modal aberto

    def _fechar_modal(self):
        self.modal = None

    def _acionar_botao(self, callback):
        if callback is None:
            self._fechar_modal()
            return
        modal = self.modal
        resultado = callback()
        # Callbacks que devolvem False (ex.: copiar) mantem o modal aberto
        if resultado is False and self.modal is modal and modal.get('id') == 'patrocine':
            return
        if self.modal is modal:
            self._fechar_modal()

    def _tratar_modal(self, evento, pos, estado):
        modal = self.modal
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self._fechar_modal()
            elif modal['tipo'] == 'lista' and modal['opcoes']:
                n = len(modal['opcoes'])
                if evento.key in (pygame.K_DOWN, pygame.K_UP):
                    passo = 1 if evento.key == pygame.K_DOWN else -1
                    modal['selecionado'] = (max(0, modal['selecionado']) + passo) % n
                    self._garantir_visivel(modal)
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and modal['selecionado'] >= 0:
                    self._escolher_da_lista(modal['selecionado'])
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                botoes = modal.get('rects_botoes', [])
                if botoes:
                    self._acionar_botao(botoes[-1][1])
            return
        if evento.type == pygame.MOUSEWHEEL and modal['tipo'] == 'lista':
            modal['scroll'] = max(0, min(modal.get('scroll_max', 0),
                                         modal['scroll'] - evento.y * ALTURA_ITEM))
            return
        if evento.type == pygame.MOUSEMOTION:
            modal['hover'] = pos
            return
        if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
            return
        if modal.get('rect_fechar') and modal['rect_fechar'].collidepoint(pos):
            self._fechar_modal()
            return
        for rect, callback in modal.get('rects_botoes', []):
            if rect.collidepoint(pos):
                self._acionar_botao(callback)
                return
        for rect, url in modal.get('rects_links', []):
            if rect.collidepoint(pos):
                acoes.abrir_link(url)
                return
        if modal['tipo'] == 'lista':
            area = modal.get('rect_area')
            for i, rect in modal.get('rects_opcoes', []):
                if rect.collidepoint(pos) and (area is None or area.collidepoint(pos)):
                    self._escolher_da_lista(i)
                    return
        if modal.get('rect') and not modal['rect'].collidepoint(pos):
            self._fechar_modal()      # clique fora fecha

    def _garantir_visivel(self, modal):
        area = modal.get('altura_area', 0)
        if not area:
            return
        y = modal['selecionado'] * ALTURA_ITEM
        if y < modal['scroll']:
            modal['scroll'] = y
        elif y + ALTURA_ITEM > modal['scroll'] + area:
            modal['scroll'] = y + ALTURA_ITEM - area

    def _escolher_da_lista(self, i):
        modal = self.modal
        modal['selecionado'] = i
        self._fechar_modal()
        try:
            modal['ao_escolher'](i)
        except Exception as erro:
            from ui.components.notificacoes import notificar
            notificar(self._ctx.get('estado'), f'{erro}', 'erro')

    # ---------------------------------------------------------- desenho ----
    def desenhar(self, tela, fonte_ui, estado=None, fonte_pequena=None, fonte_titulo=None):
        """Titulos dos menus (sobre a barra ja pintada), dropdown e modais."""
        fonte_pequena = fonte_pequena or fonte_ui
        fonte_titulo = fonte_titulo or fonte_ui
        self.fonte_menu = fonte_ui
        for menu, rect in self.rects_principais.items():
            aberto = self.menu_aberto == menu and self.ancora_dropdown is None
            hover = self.item_hover == menu
            pilula = rect.inflate(-4, -12)
            if aberto:
                ds.superficie_translucida(tela, pilula,
                                          ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.30),
                                          240, ds.RAIO_MD, TEMA.acento, 1)
            elif hover:
                ds.superficie_translucida(tela, pilula, TEMA.superficie_alt, 200, ds.RAIO_MD)
            ds.texto_centralizado(tela, _t(menu), fonte_ui, rect,
                                  TEMA.texto if (aberto or hover) else TEMA.texto_suave)
        self.rects_dropdown = []
        self.rect_dropdown = pygame.Rect(0, 0, 0, 0)
        if self.menu_aberto:
            self._desenhar_dropdown(tela, fonte_ui, fonte_pequena, estado)

    def desenhar_sobreposicoes(self, tela, fontes, fontes_modal=None):
        """Modais e suporte: desenhados por ultimo, por cima de tudo."""
        if self.modal:
            self._desenhar_modal(tela, fontes_modal or fontes)
        elif self.gerenciador_suporte.aberto:
            self.gerenciador_suporte.desenhar(tela, fontes['ui'], fontes['titulo'],
                                              self._ctx.get('estado'))

    def _desenhar_dropdown(self, tela, fonte, fonte_pequena, estado):
        menu = self.menu_aberto
        itens = self.estrutura[menu]
        self.largura_dropdown = self._medir_dropdown(menu, fonte)
        altura = sum(ALTURA_SEP if i == SEP else ALTURA_ITEM for i in itens) + 10
        if self.ancora_dropdown is not None:
            x = self.ancora_dropdown.right - self.largura_dropdown
        else:
            x = self.rects_principais[menu].x
        x = max(4, min(x, tela.get_width() - self.largura_dropdown - 4))
        rect = pygame.Rect(x, self.altura_barra - 2, self.largura_dropdown, altura)
        self.rect_dropdown = rect
        ds.sombra(tela, rect, ds.RAIO_LG, forca=130, deslocamento=5)
        ds.superficie_translucida(tela, rect, TEMA.superficie_alt, 252, ds.RAIO_LG, TEMA.borda, 1)
        y = rect.y + 5
        for indice, item in enumerate(itens):
            if item == SEP:
                ds.divisor(tela, rect.x + 10, y + ALTURA_SEP // 2, rect.width - 20)
                y += ALTURA_SEP
                continue
            acao, rotulo = item
            atalho = self._texto_atalho(acao, estado)
            r = pygame.Rect(rect.x + 5, y, rect.width - 10, ALTURA_ITEM)
            self.rects_dropdown.append((acao, r))
            habilitado = self.item_habilitado(acao, estado)
            destacado = habilitado and self.sub_item_hover == indice
            if destacado:
                pygame.draw.rect(tela, ds.rgb(TEMA.acento), r, border_radius=ds.RAIO_MD)
            cor = (TEMA.texto_sobre_cor if destacado else
                   TEMA.texto if habilitado else TEMA.texto_apagado)
            marcado = self.item_marcado(acao, estado)
            if marcado:
                cx, cy = r.x + 14, r.centery
                pygame.draw.lines(tela, ds.rgb(cor if destacado else TEMA.acento), False,
                                  [(cx - 5, cy), (cx - 1, cy + 4), (cx + 6, cy - 5)], 2)
            ds.texto_em(tela, _t(rotulo), fonte, (r.x + 30, r.centery), cor, ancora='midleft',
                        largura_max=r.width - 40 - (fonte_pequena.size(atalho)[0] + 20 if atalho else 0))
            if atalho:
                ds.texto_em(tela, atalho, fonte_pequena, (r.right - 12, r.centery),
                            TEMA.texto_sobre_cor if destacado else TEMA.texto_apagado,
                            ancora='midright')
            y += ALTURA_ITEM

    def _cartao_modal(self, tela, largura, altura, titulo, fonte_titulo, logo=False):
        """Fundo escurecido + cartao centrado. Devolve o rect do cartao."""
        tam = tela.get_size()
        if self._overlay is None or self._overlay.get_size() != tam or \
                getattr(self, '_overlay_tema', None) != TEMA.modo:
            self._overlay = pygame.Surface(tam, pygame.SRCALPHA)
            self._overlay.fill(ds.com_alpha(TEMA.overlay, 200))
            self._overlay_tema = TEMA.modo
        tela.blit(self._overlay, (0, 0))
        largura = min(largura, tam[0] - 40)
        altura = min(altura, tam[1] - 40)
        rect = pygame.Rect((tam[0] - largura) // 2, (tam[1] - altura) // 2, largura, altura)
        ds.sombra(tela, rect, ds.RAIO_LG, forca=150, deslocamento=8)
        pygame.draw.rect(tela, ds.rgb(TEMA.superficie), rect, border_radius=ds.RAIO_LG)
        pygame.draw.rect(tela, ds.rgb(TEMA.borda), rect, width=1, border_radius=ds.RAIO_LG)
        pygame.draw.rect(tela, ds.rgb(TEMA.acento), (rect.x + 1, rect.y + 1, rect.width - 2, 3),
                         border_top_left_radius=ds.RAIO_LG, border_top_right_radius=ds.RAIO_LG)
        x_titulo = rect.x + 24
        if logo:
            r_logo = pygame.Rect(rect.x + 24, rect.y + 20, 30, 30)
            ds.gradiente_vertical(tela, r_logo, TEMA.primaria_clara, TEMA.primaria, ds.RAIO_MD)
            ds.texto_centralizado(tela, 'E', fonte_titulo, r_logo, TEMA.texto_sobre_cor)
            x_titulo = r_logo.right + 12
        ds.texto_em(tela, _t(titulo), fonte_titulo, (x_titulo, rect.y + 35), TEMA.texto,
                    ancora='midleft', largura_max=rect.width - 100)
        # Botao X
        r_x = pygame.Rect(rect.right - 46, rect.y + 18, 30, 30)
        self.modal['rect_fechar'] = r_x
        hover = r_x.collidepoint(self.modal.get('hover', (-1, -1)))
        if hover:
            pygame.draw.rect(tela, ds.rgb(ds.misturar(TEMA.superficie, TEMA.alerta, 0.25)), r_x,
                             border_radius=ds.RAIO_MD)
        c = ds.rgb(TEMA.alerta if hover else TEMA.texto_suave)
        pygame.draw.line(tela, c, (r_x.centerx - 6, r_x.centery - 6), (r_x.centerx + 6, r_x.centery + 6), 2)
        pygame.draw.line(tela, c, (r_x.centerx + 6, r_x.centery - 6), (r_x.centerx - 6, r_x.centery + 6), 2)
        ds.divisor(tela, rect.x + 1, rect.y + 64, rect.width - 2)
        self.modal['rect'] = rect
        return rect

    def _desenhar_botoes_modal(self, tela, rect, fonte):
        botoes = self.modal.get('botoes', [])
        self.modal['rects_botoes'] = []
        x = rect.right - 24
        hover = self.modal.get('hover', (-1, -1))
        for rotulo, variante, callback in reversed(botoes):
            texto = _t(rotulo)
            largura = max(110, fonte.size(texto)[0] + 32)
            r = pygame.Rect(x - largura, rect.bottom - 24 - 38, largura, 38)
            ds.botao(tela, r, texto, fonte, variante=variante, hover=r.collidepoint(hover))
            self.modal['rects_botoes'].insert(0, (r, callback))
            x = r.x - 10

    def _desenhar_modal(self, tela, fontes):
        modal = self.modal
        fonte, fonte_p, fonte_t = fontes['ui'], fontes['pequena'], fontes['titulo']
        linhas = [l for l in modal.get('linhas', []) if l]
        if modal['tipo'] == 'atalhos':
            self._desenhar_atalhos(tela, fontes)
            return
        if modal['tipo'] == 'lista':
            self._desenhar_lista(tela, fontes, linhas)
            return
        altura_linha = 26
        altura = 64 + 22 + len(linhas) * altura_linha + 24
        if modal.get('destaque'):
            altura += 56
        altura += len(modal.get('links', [])) * 32 + (12 if modal.get('links') else 0)
        altura += len(modal.get('rodape', [])) * 22 + (10 if modal.get('rodape') else 0)
        altura += 38 + 24 + 8
        rect = self._cartao_modal(tela, modal.get('largura', 640), altura, modal['titulo'],
                                  fonte_t, modal.get('logo', False))
        y = rect.y + 64 + 22
        for linha in linhas:
            ds.texto_em(tela, _t(linha), fonte, (rect.x + 24, y), TEMA.texto_suave,
                        largura_max=rect.width - 48)
            y += altura_linha
        y += 12
        if modal.get('destaque'):
            rotulo, valor = modal['destaque']
            caixa = pygame.Rect(rect.x + 24, y, rect.width - 48, 44)
            ds.superficie_translucida(tela, caixa, ds.misturar(TEMA.superficie, TEMA.aviso, 0.12),
                                      255, ds.RAIO_MD, ds.misturar(TEMA.borda, TEMA.aviso, 0.5), 1)
            ds.texto_em(tela, _t(rotulo), fonte, (caixa.x + 16, caixa.centery), TEMA.texto_suave,
                        ancora='midleft')
            ds.texto_em(tela, valor, fonte_t, (caixa.right - 16, caixa.centery), TEMA.aviso,
                        ancora='midright')
            y += 56
        modal['rects_links'] = []
        hover = modal.get('hover', (-1, -1))
        for rotulo, texto, url in modal.get('links', []):
            r_rot = ds.texto_em(tela, _t(rotulo) + ':', fonte, (rect.x + 24, y + 4), TEMA.texto_suave)
            r_link = ds.texto_em(tela, texto, fonte, (r_rot.right + 8, y + 4),
                                 TEMA.primaria_clara)
            sublinhado = r_link.collidepoint(hover)
            pygame.draw.line(tela, ds.rgb(TEMA.primaria_clara), (r_link.x, r_link.bottom - 1),
                             (r_link.right, r_link.bottom - 1), 2 if sublinhado else 1)
            modal['rects_links'].append((r_link.inflate(6, 6), url))
            y += 32
        if modal.get('links'):
            y += 12
        for linha in modal.get('rodape', []):
            ds.texto_em(tela, _t(linha), fonte_p, (rect.x + 24, y), TEMA.texto_apagado,
                        largura_max=rect.width - 48)
            y += 22
        self._desenhar_botoes_modal(tela, rect, fontes.get('botao', fonte))

    def _desenhar_lista(self, tela, fontes, linhas):
        modal = self.modal
        fonte, fonte_p, fonte_t = fontes['ui'], fontes['pequena'], fontes['titulo']
        visiveis = min(8, max(1, len(modal['opcoes'])))
        area_h = visiveis * ALTURA_ITEM
        altura = 64 + 20 + len(linhas) * 24 + 12 + area_h + 20 + 38 + 24
        rect = self._cartao_modal(tela, modal.get('largura', 620), altura, modal['titulo'], fonte_t)
        y = rect.y + 64 + 20
        for linha in linhas:
            ds.texto_em(tela, _t(linha), fonte_p, (rect.x + 24, y), TEMA.texto_suave,
                        largura_max=rect.width - 48)
            y += 24
        y += 12
        area = pygame.Rect(rect.x + 20, y, rect.width - 40, area_h)
        modal['rect_area'] = area
        modal['altura_area'] = area_h
        pygame.draw.rect(tela, ds.rgb(TEMA.fundo_alt), area, border_radius=ds.RAIO_MD)
        modal['rects_opcoes'] = []
        if not modal['opcoes']:
            ds.texto_centralizado(tela, _t(modal['vazio']), fonte_p, area, TEMA.texto_apagado)
        else:
            total = len(modal['opcoes']) * ALTURA_ITEM
            modal['scroll_max'] = max(0, total - area_h)
            modal['scroll'] = max(0, min(modal['scroll'], modal['scroll_max']))
            hover = modal.get('hover', (-1, -1))
            tela.set_clip(area)
            for i, (rotulo, detalhe) in enumerate(modal['opcoes']):
                r = pygame.Rect(area.x + 4, area.y + i * ALTURA_ITEM - modal['scroll'],
                                area.width - 8 - (10 if modal['scroll_max'] else 0), ALTURA_ITEM)
                if r.bottom < area.y or r.y > area.bottom:
                    continue
                modal['rects_opcoes'].append((i, r))
                sel = i == modal['selecionado']
                if sel:
                    pygame.draw.rect(tela, ds.rgb(TEMA.acento), r.inflate(0, -4),
                                     border_radius=ds.RAIO_MD)
                elif r.collidepoint(hover) and area.collidepoint(hover):
                    pygame.draw.rect(tela, ds.rgb(TEMA.superficie_alt), r.inflate(0, -4),
                                     border_radius=ds.RAIO_MD)
                cor = TEMA.texto_sobre_cor if sel else TEMA.texto
                # Radio
                cx, cy = r.x + 16, r.centery
                pygame.draw.circle(tela, ds.rgb(cor if sel else TEMA.texto_apagado), (cx, cy), 7, 2)
                if sel:
                    pygame.draw.circle(tela, ds.rgb(cor), (cx, cy), 3)
                larg_det = fonte_p.size(detalhe)[0] + 16 if detalhe else 0
                ds.texto_em(tela, _t(rotulo), fonte, (r.x + 32, cy), cor, ancora='midleft',
                            largura_max=r.width - 44 - larg_det)
                if detalhe:
                    ds.texto_em(tela, detalhe, fonte_p, (r.right - 10, cy),
                                TEMA.texto_sobre_cor if sel else TEMA.texto_apagado,
                                ancora='midright')
            tela.set_clip(None)
            if modal['scroll_max']:
                ds.barra_rolagem(tela, area.right - 10, area.y + 4, area.height - 8,
                                 area_h / total, modal['scroll'] / modal['scroll_max'], 6)
        self._desenhar_botoes_modal(tela, rect, fontes.get('botao', fonte))

    def _grupos_lista_atalhos(self):
        """Atalhos atuais do usuario (so as funcoes com tecla) + os fixos."""
        estado = self._ctx.get('estado')
        tabela = atalhos.obter(estado) if estado is not None else atalhos.PADROES
        grupos = []
        for grupo in atalhos.GRUPOS:
            itens = [(' / '.join(atalhos.texto(c) for c in tabela.get(acao, [])[:2]), rotulo)
                     for g, acao, rotulo, _p in atalhos.ACOES if g == grupo and tabela.get(acao)]
            if itens:
                grupos.append((grupo, itens))
        grupos.append(('Sistema', ATALHOS_FIXOS))
        return grupos

    def _desenhar_atalhos(self, tela, fontes):
        fonte, fonte_p, fonte_t = fontes['ui'], fontes['pequena'], fontes['titulo']
        grupos = self._grupos_lista_atalhos()
        colunas = 3
        # distribui os grupos nas colunas equilibrando a altura
        alturas = [0] * colunas
        distribuicao = [[] for _ in range(colunas)]
        for grupo, itens in grupos:
            c = alturas.index(min(alturas))
            distribuicao[c].append((grupo, itens))
            alturas[c] += 34 + len(itens) * 28 + 10
        altura = 64 + 20 + max(alturas) + 24 + 38 + 24
        estado = self._ctx.get('estado')
        self.modal['botoes'] = [
            ('Personalizar teclas', 'suave',
             lambda: (acoes.abrir_secao(estado, 'configuracao', 2) if estado is not None else None)),
            ('Fechar', 'primario', None)]
        rect = self._cartao_modal(tela, self.modal.get('largura', 980), altura,
                                  self.modal['titulo'], fonte_t)
        largura_col = (rect.width - 48) // colunas
        for c, col in enumerate(distribuicao):
            x = rect.x + 24 + c * largura_col
            y = rect.y + 64 + 20
            for grupo, itens in col:
                ds.texto_em(tela, _t(grupo).upper(), fonte_p, (x, y), TEMA.acento)
                y += 26
                for tecla, descricao in itens:
                    larg = min(int(largura_col * 0.48), fonte_p.size(tecla)[0] + 16)
                    caixa = pygame.Rect(x, y, larg, 22)
                    ds.superficie_translucida(tela, caixa, TEMA.superficie_alt, 255, ds.RAIO_SM,
                                              TEMA.borda, 1)
                    ds.texto_centralizado(tela, tecla, fonte_p, caixa, TEMA.texto)
                    ds.texto_em(tela, _t(descricao), fonte_p, (caixa.right + 10, caixa.centery),
                                TEMA.texto_suave, ancora='midleft',
                                largura_max=largura_col - larg - 24)
                    y += 28
                y += 10
        self._desenhar_botoes_modal(tela, rect, fontes.get('botao', fonte))
