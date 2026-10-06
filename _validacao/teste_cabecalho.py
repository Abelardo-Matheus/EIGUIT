# -*- coding: utf-8 -*-
"""
Cabecalho (barra superior): todo item de menu faz alguma coisa, os atalhos
funcionam, os modais abrem centrados na tela real e fecham, e os botoes da
barra respondem. Os eventos passam pelo controlador de verdade, com o mouse
real, como no main.py.
"""
import json
import os
import tempfile

import pygame

import harness
from harness import Contexto, Suite
import core.acoes_cabecalho as acoes
import core.controlador_eventos as controlador
import core.modulos.modulo_menu_superior as mms
from config.ui_metrics import ALTURA_TOPBAR
from core.modulos.modulo_perfil import GerenciadorPerfil
from ui import renderizador_ui
from ui.components import desenhar_painel_superior

s = Suite('teste_cabecalho')
LARG, ALT = 1920, 1080


class GravadorFalso:
    """Motor de audio sem placa de som, com duas entradas."""
    def __init__(self):
        self.device_id = 0
        self.ativo = False
        self.trocas = []

    def obter_lista_entradas(self):
        return [{'id': 0, 'nome': 'Microfone'}, {'id': 3, 'nome': 'MK-300 USB'}]

    def mudar_dispositivo(self, novo):
        self.device_id = novo
        self.ativo = True
        self.trocas.append(novo)


def montar(largura=LARG, altura=ALT, tema='escuro'):
    ctx = Contexto(largura, altura, tema)
    e = ctx.estado
    e.menu_superior = mms.MenuSuperior()
    e.gerenciador_perfil = GerenciadorPerfil()
    e.email_usuario = 'teste@eiguit.app'
    e.usuario_id_logado = None
    e.pos_mouse_real = (5, 600)
    ctx.gravador = GravadorFalso()
    e.motor_audio = ctx.gravador
    ctx.tela = pygame.Surface((largura, altura))
    quadro(ctx)
    return ctx


def quadro(ctx):
    tela = ctx.tela
    vp = tela.subsurface(pygame.Rect(0, ALTURA_TOPBAR, tela.get_width(), tela.get_height() - ALTURA_TOPBAR))
    renderizador_ui.desenhar_workspace(vp, ctx.estado, ctx.configs, ctx.escalas, ctx.fontes,
                                       ctx.metronomo, ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    renderizador_ui.desenhar_ui_fixa(vp, ctx.estado, ctx.fontes, ctx.gravador, ctx.configs, ctx.jogos, ctx.campo)
    desenhar_painel_superior(tela, ctx.estado, ctx.fontes, ctx.configs)


def enviar(ctx, *eventos):
    controlador.processar(list(eventos), ctx.estado, ctx.configs, ctx.escalas, ctx.metronomo,
                          ctx.processador, ctx.gravador, ctx.campo, ctx.jogos)
    quadro(ctx)


def clicar(ctx, pos, botao=1):
    ctx.estado.pos_mouse_real = pos
    enviar(ctx, pygame.event.Event(pygame.MOUSEMOTION, {'pos': pos, 'rel': (0, 0), 'buttons': (0, 0, 0)}))
    enviar(ctx, pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': botao}))
    enviar(ctx, pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': pos, 'button': botao}))


def tecla(ctx, key, ctrl=False, shift=False, unicode=''):
    mod = (pygame.KMOD_LCTRL if ctrl else 0) | (pygame.KMOD_LSHIFT if shift else 0)
    enviar(ctx, pygame.event.Event(pygame.KEYDOWN, {'key': key, 'mod': mod, 'unicode': unicode,
                                                    'scancode': 0}))


def clicar_item(ctx, menu, acao):
    m = ctx.estado.menu_superior
    if menu == 'Perfil':
        # O Perfil fica so no botao da conta (canto superior direito)
        chip = {a: r for r, a in ctx.estado.botoes_cabecalho}['menu_conta']
        clicar(ctx, chip.center)
    else:
        clicar(ctx, m.rects_principais[menu].center)
    s.checar(m.menu_aberto == menu, f'o menu {menu} nao abriu')
    alvo = dict(m.rects_dropdown).get(acao)
    s.checar(alvo is not None, f'{acao} nao aparece no menu {menu}')
    clicar(ctx, alvo.center)


def todos_os_itens_tem_acao():
    """Nenhum item pode cair no vazio: cada id tem um ramo em executar_acao."""
    import inspect
    fonte = inspect.getsource(mms.MenuSuperior.executar_acao)
    for menu, itens in mms.MENUS:
        for item in itens:
            if item == mms.SEP:
                continue
            s.checar(f"'{item[0]}'" in fonte, f'item {item[0]} do menu {menu} sem acao')
    import core.atalhos as atalhos
    for _g, acao, _r, _p in atalhos.ACOES:
        s.checar(f"'{acao}'" in fonte or acao.startswith('secao_'),
                 f'funcao {acao} da lista de teclas sem acao')


def perfil_so_no_canto_direito():
    ctx = montar()
    m = ctx.estado.menu_superior
    s.checar('Perfil' not in m.rects_principais, 'Perfil ainda aparece na barra de menus')
    chip = {a: r for r, a in ctx.estado.botoes_cabecalho}['menu_conta']
    s.checar(chip.right > LARG - 300, f'botao da conta fora do canto direito: {chip}')


def menus_cabem_sem_cortar():
    for largura in (1280, 1600, 1920, 2560):
        ctx = montar(largura, 900)
        m = ctx.estado.menu_superior
        barra = pygame.Rect(0, 0, largura, ALTURA_TOPBAR)
        for nome, r in m.rects_principais.items():
            s.checar(barra.contains(r), f'{largura}px: menu {nome} fora da barra')
            texto = ctx.fontes['pequena'].size(nome)[0]
            s.checar(r.width >= texto, f'{largura}px: menu {nome} cortado')
        for r, acao in ctx.estado.botoes_cabecalho:
            s.checar(barra.contains(r), f'{largura}px: botao {acao} fora da barra')
            s.checar(r.left >= m.largura_total_menu, f'{largura}px: botao {acao} em cima dos menus')


def abrir_e_fechar_menu():
    ctx = montar()
    m = ctx.estado.menu_superior
    clicar(ctx, m.rects_principais['Arquivo'].center)
    s.checar(m.menu_aberto == 'Arquivo', 'Arquivo nao abriu')
    # passar o mouse por outro titulo troca o menu
    pos = m.rects_principais['Ajuda'].center
    ctx.estado.pos_mouse_real = pos
    enviar(ctx, pygame.event.Event(pygame.MOUSEMOTION, {'pos': pos, 'rel': (0, 0), 'buttons': (0, 0, 0)}))
    s.checar(m.menu_aberto == 'Ajuda', 'hover nao trocou para Ajuda')
    tecla(ctx, pygame.K_ESCAPE)
    s.checar(m.menu_aberto is None, 'ESC nao fechou o menu')
    s.checar(not ctx.estado.solicitou_saida, 'ESC com menu aberto fechou o programa')
    # clique fora fecha sem atravessar para o workspace
    clicar(ctx, m.rects_principais['Exibir'].center)
    clicar(ctx, (LARG // 2, ALT // 2))
    s.checar(m.menu_aberto is None, 'clique fora nao fechou')


def navegacao_por_teclado():
    ctx = montar()
    m = ctx.estado.menu_superior
    tecla(ctx, pygame.K_LALT)
    enviar(ctx, pygame.event.Event(pygame.KEYUP, {'key': pygame.K_LALT, 'mod': 0, 'unicode': '',
                                                  'scancode': 0}))
    s.checar(m.menu_aberto == 'Arquivo', 'Alt nao abriu o primeiro menu')
    tecla(ctx, pygame.K_RIGHT)
    s.checar(m.menu_aberto == 'Exibir', 'seta direita nao foi para Exibir')
    antes = ctx.estado.drag_ativado
    tecla(ctx, pygame.K_RETURN)      # primeiro item de Exibir = modo de edicao
    s.checar(ctx.estado.drag_ativado != antes, 'Enter nao executou o item')


def itens_desabilitados_sem_projeto():
    ctx = montar()
    import ui.renderizador_ui as r
    r.render_tab_maker = None
    m = ctx.estado.menu_superior
    for acao in ('salvar_projeto', 'exportar_txt', 'exportar_midi'):
        s.checar(not m.item_habilitado(acao, ctx.estado), f'{acao} habilitado sem projeto')
    clicar_item(ctx, 'Arquivo', 'salvar_projeto')
    s.checar(m.menu_aberto == 'Arquivo', 'clique em item desabilitado fechou o menu')
    # Pelo atalho avisa em vez de nao fazer nada
    tecla(ctx, pygame.K_ESCAPE)
    tecla(ctx, pygame.K_s, ctrl=True)
    s.checar(any('Nenhum projeto' in a['texto'] for a in ctx.estado.notificacoes),
             'Ctrl+S sem projeto nao avisou')


def projeto_novo_salvar_abrir():
    ctx = montar()
    pasta = tempfile.mkdtemp()
    clicar_item(ctx, 'Arquivo', 'novo_projeto')
    s.checar(ctx.estado.tela_criacao_tab_ativa, 'Novo projeto nao abriu o editor')
    editor = acoes.obter_editor()
    editor.dados.nome_musica = 'Riff de teste'
    editor.cursor = [0, 0]
    editor.escrever(3)
    editor.cursor = [1, 4]
    editor.escrever(5)
    s.checar(acoes.projeto_modificado(ctx.estado), 'nota nova nao marcou o projeto como modificado')
    caminho = os.path.join(pasta, 'riff.eiguit')
    ctx.estado.projeto_caminho = caminho
    tecla(ctx, pygame.K_s, ctrl=True)
    s.checar(os.path.exists(caminho), 'Ctrl+S nao gravou o arquivo')
    s.checar(not acoes.projeto_modificado(ctx.estado), 'depois de salvar continua "nao salvo"')
    dados = json.load(open(caminho, encoding='utf-8'))
    s.checar(dados['nome'] == 'Riff de teste' and dados['formato'] == 'eiguit-projeto',
             'conteudo do arquivo errado')
    # Novo com alteracoes pede confirmacao
    editor.cursor = [2, 8]
    editor.escrever(7)
    clicar_item(ctx, 'Arquivo', 'novo_projeto')
    s.checar(ctx.estado.menu_superior.modal is not None, 'Novo com alteracoes nao confirmou')
    tecla(ctx, pygame.K_ESCAPE)
    # Reabre
    acoes.novo_projeto(ctx.estado)
    s.checar(acoes.abrir_projeto(ctx.estado, caminho), 'abrir_projeto falhou')
    editor = acoes.obter_editor()
    s.checar(editor.dados.nome_musica == 'Riff de teste', 'nome nao voltou')
    s.checar(editor.dados.trilhas['Guitarra'][0][0].startswith('3'), 'nota nao voltou')
    # JSON antigo ({'bpm','grade'}) tambem abre
    antigo = os.path.join(pasta, 'antigo.json')
    json.dump({'bpm': 90, 'grade': [['-'] * 16 for _ in range(6)]}, open(antigo, 'w'))
    s.checar(acoes.abrir_projeto(ctx.estado, antigo), 'formato antigo nao abriu')
    s.checar(acoes.obter_editor().dados.bpm == 90, 'bpm do formato antigo')
    # Arquivo ruim avisa, nao quebra
    ruim = os.path.join(pasta, 'ruim.eiguit')
    open(ruim, 'w').write('nao e json')
    s.checar(not acoes.abrir_projeto(ctx.estado, ruim), 'arquivo invalido "abriu"')
    s.checar(any(a['tipo'] == 'erro' for a in ctx.estado.notificacoes), 'erro sem aviso')


def exportar_txt_e_midi():
    import mido
    ctx = montar()
    acoes.novo_projeto(ctx.estado)
    editor = acoes.obter_editor()
    editor.cursor = [0, 0]
    editor.escrever(0)       # E2
    editor.cursor = [5, 4]
    editor.escrever(12)      # E5
    pasta = tempfile.mkdtemp()
    txt = editor.exportar(os.path.join(pasta, 't.txt'))
    s.checar(txt and 'E|' in open(txt, encoding='utf-8').read(), 'txt sem a tablatura')
    mid = os.path.join(pasta, 't.mid')
    faixas = acoes.gerar_midi(editor, mid)
    s.checar(faixas == 1, f'esperava 1 faixa, veio {faixas}')
    notas = [m.note for t in mido.MidiFile(mid).tracks for m in t if m.type == 'note_on' and m.velocity]
    s.checar(sorted(notas) == [40, 76], f'notas MIDI erradas: {notas}')
    vazio = acoes.obter_editor()
    vazio.carregar_dict({'bpm': 100, 'trilhas': {'Guitarra': [['-'] * 16 for _ in range(6)]}})
    try:
        acoes.gerar_midi(vazio, mid)
        s.checar(False, 'projeto vazio exportou MIDI')
    except ValueError:
        pass


def captura_de_tela():
    ctx = montar()
    pasta = tempfile.mkdtemp()
    original = acoes.pasta_documentos
    acoes.pasta_documentos = lambda sub='': pasta
    try:
        clicar_item(ctx, 'Arquivo', 'capturar_tela')
        s.checar(not getattr(ctx.estado, 'captura_pendente', 0), 'captura ficou pendente')
        arquivos = [f for f in os.listdir(pasta) if f.endswith('.png')]
        s.checar(len(arquivos) == 1, f'esperava 1 PNG, achei {arquivos}')
        tecla(ctx, pygame.K_F12)
        quadro(ctx)
        s.checar(len(os.listdir(pasta)) >= 1, 'F12 nao capturou')
    finally:
        acoes.pasta_documentos = original


def exibir_zoom_tema_edicao():
    ctx = montar()
    cam = ctx.estado.camera
    tecla(ctx, pygame.K_EQUALS, ctrl=True)
    s.checar(abs(cam.zoom - 1.1) < 1e-6, f'Ctrl+= deu zoom {cam.zoom}')
    clicar_item(ctx, 'Exibir', 'zoom_menos')
    clicar_item(ctx, 'Exibir', 'zoom_menos')
    s.checar(abs(cam.zoom - 0.9) < 1e-6, f'zoom_menos deu {cam.zoom}')
    tecla(ctx, pygame.K_0, ctrl=True)
    s.checar(cam.zoom == 1.0 and cam.offset_x == 0, 'Ctrl+0 nao voltou ao 100%')
    from config.design_system import TEMA
    antes = TEMA.modo
    tecla(ctx, pygame.K_F3)
    s.checar(TEMA.modo != antes, 'F3 nao trocou o tema')
    harness.definir_tema(antes)
    tecla(ctx, pygame.K_F2)
    s.checar(ctx.estado.drag_ativado, 'F2 nao ligou o modo de edicao')
    # Zoom nao age dentro de uma tela aberta
    ctx.estado.tela_criacao_tab_ativa = True
    s.checar(not ctx.estado.menu_superior.item_habilitado('zoom_mais', ctx.estado),
             'zoom habilitado com tela aberta')
    ctx.estado.tela_criacao_tab_ativa = False


def botoes_da_barra():
    ctx = montar()
    alvos = {acao: r for r, acao in ctx.estado.botoes_cabecalho}
    for acao in ('modo_edicao', 'tema_escuro', 'tela_cheia', 'menu_conta', 'audio'):
        s.checar(acao in alvos, f'botao {acao} nao registrado')
    clicar(ctx, alvos['modo_edicao'].center)
    s.checar(ctx.estado.drag_ativado, 'botao de edicao nao ligou')
    clicar(ctx, alvos['menu_conta'].center)
    m = ctx.estado.menu_superior
    s.checar(m.menu_aberto == 'Perfil' and m.ancora_dropdown is not None, 'chip da conta nao abriu o menu')
    s.checar(m.rect_dropdown.right <= LARG, 'menu da conta saiu da tela')
    tecla(ctx, pygame.K_ESCAPE)
    clicar(ctx, alvos['audio'].center)
    s.checar(m.modal and m.modal['id'] == 'audio', 'medidor nao abriu a escolha da entrada')
    # escolhe a segunda entrada clicando nela
    i, r = m.modal['rects_opcoes'][1]
    clicar(ctx, r.center)
    s.checar(ctx.gravador.device_id == 3, 'entrada de audio nao trocou')
    s.checar(m.modal is None, 'modal de audio nao fechou depois da escolha')
    # Voltar aparece com uma tela aberta e fecha a tela
    ctx.estado.tela_jogo_ativa = True
    quadro(ctx)
    alvos = {acao: r for r, acao in ctx.estado.botoes_cabecalho}
    s.checar('voltar' in alvos, 'sem botao Voltar com jogo aberto')
    clicar(ctx, alvos['voltar'].center)
    s.checar(not ctx.estado.tela_jogo_ativa, 'Voltar nao fechou o jogo')


def modais_centrados_e_fecham():
    ctx = montar()
    m = ctx.estado.menu_superior
    # Camera longe da origem: os modais tem de continuar no meio da tela
    ctx.estado.camera.offset_x, ctx.estado.camera.offset_y, ctx.estado.camera.zoom = 900, 700, 1.6
    for menu, acao in (('Ajuda', 'sobre'), ('Ajuda', 'atalhos'), ('Ajuda', 'ideias'),
                       ('Ajuda', 'patrocine'), ('Ajuda', 'motivacao'),
                       ('Configurações', 'tela'), ('Configurações', 'idioma'),
                       ('Configurações', 'audio'), ('Perfil', 'perfil_padrao'),
                       ('Perfil', 'trocar_conta')):
        clicar_item(ctx, menu, acao)
        s.checar(m.modal is not None, f'{acao} nao abriu modal')
        r = m.modal['rect']
        s.checar(pygame.Rect(0, 0, LARG, ALT).contains(r), f'{acao}: modal fora da tela')
        s.checar(abs(r.centerx - LARG // 2) <= 1 and abs(r.centery - ALT // 2) <= 1,
                 f'{acao}: modal fora do centro {r.center}')
        clicar(ctx, m.modal['rect_fechar'].center)
        s.checar(m.modal is None, f'{acao}: X nao fechou')
    clicar_item(ctx, 'Ajuda', 'suporte')
    s.checar(m.gerenciador_suporte.aberto, 'suporte nao abriu')
    tecla(ctx, pygame.K_ESCAPE)
    s.checar(not m.gerenciador_suporte.aberto, 'ESC nao fechou o suporte')
    s.checar(not ctx.estado.solicitou_saida, 'ESC no suporte fechou o programa')


def idioma_e_tela():
    ctx = montar()
    m = ctx.estado.menu_superior
    m.executar_acao('idioma', ctx.estado, ctx.configs, ctx.campo, ctx.gravador)
    original = ctx.configs.indice_idioma
    try:
        tecla(ctx, pygame.K_DOWN)
        tecla(ctx, pygame.K_RETURN)
        s.checar(ctx.configs.indice_idioma == (original + 1) % len(ctx.configs.idiomas),
                 'idioma nao mudou pelo teclado')
    finally:
        acoes.escolher_idioma(ctx.estado, ctx.configs, original)
    m.executar_acao('tela', ctx.estado, ctx.configs, ctx.campo, ctx.gravador)
    quadro(ctx)
    i, r = m.modal['rects_opcoes'][2]
    clicar(ctx, r.center)
    s.checar(ctx.estado.modo_tela == (1280, 720), 'modo de tela nao aplicado')


def perfil_salvar_carregar_excluir():
    ctx = montar()
    e = ctx.estado
    perfil = e.gerenciador_perfil
    original_pasta = perfil.pasta_padrao
    perfil.pasta_padrao = tempfile.mkdtemp()
    try:
        clicar_item(ctx, 'Perfil', 'perfil_salvar')
        s.checar(perfil.ativo and perfil.modo == 'salvar', 'Salvar perfil nao abriu o modal')
        perfil.texto_input = 'Teste_Cabecalho'
        # Clique no botao do modal com a camera deslocada (antes errava o alvo)
        e.camera.offset_x, e.camera.zoom = 500, 1.5
        quadro(ctx)
        alvo = perfil.btn_acao.move(0, ALTURA_TOPBAR).center
        clicar(ctx, alvo)
        s.checar(not perfil.ativo, 'botao Salvar do modal nao respondeu')
        s.checar(perfil.nome_perfil_atual() == 'Teste_Cabecalho', 'perfil nao virou o atual')
        s.checar(e.menu_superior.item_habilitado('perfil_excluir', e), 'Excluir desabilitado com perfil')
        clicar_item(ctx, 'Perfil', 'perfil_excluir')
        botoes = e.menu_superior.modal['rects_botoes']
        clicar(ctx, botoes[-1][0].center)       # confirmar
        s.checar(perfil.nome_perfil_atual() == '', 'perfil nao foi excluido')
        # Conta: o botao Ok fecha (antes nao fazia nada)
        e.usuario_id_logado = 1
        clicar_item(ctx, 'Perfil', 'conta')
        s.checar(perfil.ativo and perfil.modo == 'conta', 'Minha conta nao abriu')
        clicar(ctx, perfil.btn_acao.move(0, ALTURA_TOPBAR).center)
        s.checar(not perfil.ativo, 'Ok da conta nao fechou')
    finally:
        perfil.pasta_padrao = original_pasta


def trocar_conta_e_sair():
    try:
        from ui.tela_login import FILE_CACHE
    except Exception:
        FILE_CACHE = 'sessao_cache.json'
    # A sessao salva do usuario nao pode sumir por causa do teste
    guardada = open(FILE_CACHE, 'rb').read() if os.path.exists(FILE_CACHE) else None
    ctx = montar()
    m = ctx.estado.menu_superior
    clicar_item(ctx, 'Perfil', 'trocar_conta')
    clicar(ctx, m.modal['rects_botoes'][-1][0].center)
    if guardada is not None:
        open(FILE_CACHE, 'wb').write(guardada)
    s.checar(ctx.estado.reiniciar_apos_sair and ctx.estado.solicitou_saida,
             'trocar de conta nao pediu o reinicio')
    ctx = montar()
    tecla(ctx, pygame.K_q, ctrl=True)
    s.checar(ctx.estado.solicitou_saida, 'Ctrl+Q nao saiu')


def preferencias_abrem_a_aba():
    ctx = montar()
    clicar_item(ctx, 'Configurações', 'pref_cores')
    secao = next(x for x in ctx.estado.secoes_inferiores if x['conteudo'] == 'configuracao')
    s.checar(secao['expandido'] and secao['memoria_sub_aba'] == 0, 'Cores da interface nao abriu')
    tecla(ctx, pygame.K_COMMA, ctrl=True)
    s.checar(secao['expandido'] and secao['memoria_sub_aba'] == 1, 'Ctrl+, nao abriu as preferencias')


def desenha_em_resolucoes_e_temas():
    for tema in harness.TEMAS:
        for largura, altura in ((1280, 720), (1366, 768), (1920, 1080), (2560, 1440)):
            ctx = montar(largura, altura, tema)
            m = ctx.estado.menu_superior
            for menu in m.ordem_menus:
                m.abrir_menu(menu)
                quadro(ctx)
                s.checar(m.rect_dropdown.right <= largura, f'dropdown {menu} saiu da tela')
            m.fechar_menu()
            ctx.estado.tela_estudo_ativa = True
            ctx.estado.estudo_ativo = 'Tempo'
            quadro(ctx)
    harness.definir_tema('escuro')


if __name__ == '__main__':
    for nome, funcao in [
        ('todo item de menu tem acao', todos_os_itens_tem_acao),
        ('menus e botoes cabem na barra (4 larguras)', menus_cabem_sem_cortar),
        ('perfil so no botao da conta, no canto direito', perfil_so_no_canto_direito),
        ('abrir, trocar por hover e fechar menus', abrir_e_fechar_menu),
        ('navegacao pelo teclado (Alt, setas, Enter)', navegacao_por_teclado),
        ('itens de projeto desabilitados sem projeto', itens_desabilitados_sem_projeto),
        ('projeto: novo, salvar, abrir, formato antigo, erro', projeto_novo_salvar_abrir),
        ('exportar txt e MIDI', exportar_txt_e_midi),
        ('captura de tela pelo menu e F12', captura_de_tela),
        ('Exibir: zoom, tema e modo de edicao', exibir_zoom_tema_edicao),
        ('botoes da barra: edicao, conta, audio, voltar', botoes_da_barra),
        ('modais centrados na tela mesmo com a camera longe', modais_centrados_e_fecham),
        ('idioma e modo de tela', idioma_e_tela),
        ('perfil: salvar, excluir com confirmacao, conta', perfil_salvar_carregar_excluir),
        ('trocar de conta e Ctrl+Q', trocar_conta_e_sair),
        ('preferencias abrem a aba de configuracao', preferencias_abrem_a_aba),
        ('desenho em 4 resolucoes x 2 temas', desenha_em_resolucoes_e_temas),
    ]:
        s.teste(nome, funcao)

    s.encerrar()
