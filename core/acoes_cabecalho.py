# -*- coding: utf-8 -*-
"""
Acoes do cabecalho (menus Arquivo, Exibir, Perfil, Configuracoes e Ajuda).

Cada acao recebe o mesmo contexto (estado, configs, campo, gravador) e da
retorno ao usuario por notificacao, nunca so pelo console. O menu superior
so decide QUAL acao chamar; o que ela faz mora aqui.
"""
import json
import os
import sys
import threading
import time
import webbrowser

import pygame

from core.i18n import _t
from ui.components.notificacoes import notificar

EXTENSAO_PROJETO = '.eiguit'
URL_REPOSITORIO = 'https://github.com/Abelardo-Matheus/EIGUIT'
EMAIL_CONTATO = 'matheusabelardo12@gmail.com'

MODOS_TELA = [
    ('cheia', 'Tela cheia'),
    ('janela', 'Janela redimensionável'),
    ((1280, 720), 'Janela 1280 × 720 (HD)'),
    ((1600, 900), 'Janela 1600 × 900 (HD+)'),
    ((1920, 1080), 'Janela 1920 × 1080 (Full HD)'),
]

PASSO_ZOOM = 0.1
ZOOM_MIN, ZOOM_MAX = 0.4, 2.5


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def pasta_documentos(sub=''):
    """Documentos/EIGUIT[/sub], criada se preciso (cai na pasta do projeto)."""
    for base in (os.path.join(os.path.expanduser('~'), 'Documents'),
                 os.path.join(os.path.expanduser('~'), 'Documentos'),
                 os.path.expanduser('~')):
        if os.path.isdir(base):
            pasta = os.path.join(base, 'EIGUIT', sub) if sub else os.path.join(base, 'EIGUIT')
            try:
                os.makedirs(pasta, exist_ok=True)
                return pasta
            except OSError:
                continue
    return os.getcwd()


def _janela_arquivo(salvar, titulo, tipos, extensao='', inicial='', pasta=''):
    """Dialogo nativo de arquivo. Devolve '' se o usuario cancelar."""
    if os.environ.get('SDL_VIDEODRIVER') == 'dummy':
        return ''            # testes sem janela: nunca abre dialogo
    try:
        import tkinter as tk
        from tkinter import filedialog
        raiz = tk.Tk()
        raiz.withdraw()
        raiz.attributes('-topmost', True)
        if salvar:
            caminho = filedialog.asksaveasfilename(
                title=titulo, filetypes=tipos, defaultextension=extensao,
                initialfile=inicial, initialdir=pasta or None)
        else:
            caminho = filedialog.askopenfilename(title=titulo, filetypes=tipos,
                                                 initialdir=pasta or None)
        raiz.destroy()
        return caminho or ''
    except Exception as erro:
        print(f'[ARQUIVO] Dialogo indisponivel: {erro}')
        return ''


def _nome_arquivo_seguro(texto):
    proibidos = '<>:"/\\|?*'
    limpo = ''.join('_' if c in proibidos else c for c in (texto or '').strip())
    return limpo or 'Projeto'


def obter_editor(criar=False):
    """O editor de tablatura/partitura (criado sob demanda)."""
    import ui.renderizador_ui as render_ui
    if render_ui.render_tab_maker is None and criar:
        from ui.editor_musical import EditorMusical
        render_ui.render_tab_maker = EditorMusical()
    return render_ui.render_tab_maker


def fechar_telas(estado):
    """Fecha estudos, jogos e tablatura em tela cheia, voltando ao workspace."""
    estado.tela_criacao_tab_ativa = False
    estado.tab_tela_cheia_ativa = False
    estado.tela_jogo_ativa = False
    if getattr(estado, 'tela_estudo_ativa', False):
        estado.tela_estudo_ativa = False
        if hasattr(estado, 'gerenciador_estudos'):
            try:
                estado.gerenciador_estudos._limpar_modulos()
            except Exception:
                pass
    jogos = getattr(estado, 'gerenciador_jogos', None)
    if jogos is not None:
        jogos.jogo_instancia = None


def ha_tela_aberta(estado):
    return any(getattr(estado, nome, False) for nome in
               ('tela_criacao_tab_ativa', 'tab_tela_cheia_ativa',
                'tela_estudo_ativa', 'tela_jogo_ativa'))


def nome_contexto(estado):
    """Onde o usuario esta agora, para o centro da barra."""
    if getattr(estado, 'tela_criacao_tab_ativa', False):
        editor = obter_editor()
        nome = editor.dados.nome_musica if editor else _t('Nova Música')
        return f"{_t('Criação musical')} · {nome}", projeto_modificado(estado)
    if getattr(estado, 'tab_tela_cheia_ativa', False):
        tab = getattr(estado, 'tab_focada', None)
        return f"{_t('Tablatura')} · {getattr(tab, 'titulo', '')}".rstrip(' ·'), False
    if getattr(estado, 'tela_estudo_ativa', False):
        return f"{_t('Estudo')} · {_t(getattr(estado, 'estudo_ativo', '') or '')}".rstrip(' ·'), False
    if getattr(estado, 'tela_jogo_ativa', False):
        jogos = getattr(estado, 'gerenciador_jogos', None)
        nome = ''
        if jogos is not None:
            for jogo in getattr(jogos, 'jogos', []):
                if jogo.get('id') == getattr(jogos, 'jogo_id_ativo', None):
                    nome = jogo.get('nome', '')
        return f"{_t('Jogo')} · {_t(nome)}".rstrip(' ·'), False
    return _t('Workspace'), False


# ---------------------------------------------------------------------------
# Arquivo: projetos (tablatura / partitura)
# ---------------------------------------------------------------------------

def projeto_modificado(estado):
    editor = obter_editor()
    if editor is None:
        return False
    salva = getattr(estado, 'projeto_assinatura_salva', None)
    if salva is None:
        return editor.tem_notas()
    return editor.assinatura() != salva


def tem_projeto(estado):
    return obter_editor() is not None


def _abrir_editor(estado):
    fechar_telas(estado)
    estado.tela_criacao_tab_ativa = True


def novo_projeto(estado):
    from ui.editor_musical import EditorMusical
    import ui.renderizador_ui as render_ui
    antigo = render_ui.render_tab_maker
    if antigo is not None:
        antigo.parar()
    render_ui.render_tab_maker = EditorMusical()
    estado.projeto_caminho = None
    estado.projeto_assinatura_salva = render_ui.render_tab_maker.assinatura()
    _abrir_editor(estado)
    notificar(estado, _t('Novo projeto criado'), 'sucesso')


def abrir_projeto(estado, caminho=None):
    caminho = caminho or _janela_arquivo(
        False, _t('Abrir projeto'),
        [(_t('Projeto EIGUIT'), f'*{EXTENSAO_PROJETO} *.json'), (_t('Todos'), '*.*')],
        pasta=pasta_documentos('Projetos'))
    if not caminho:
        return False
    try:
        with open(caminho, 'r', encoding='utf-8') as arq:
            dados = json.load(arq)
        editor = obter_editor(criar=True)
        editor.carregar_dict(dados)
    except Exception as erro:
        notificar(estado, f"{_t('Não foi possível abrir')}: {erro}", 'erro', 4.5)
        return False
    estado.projeto_caminho = caminho
    estado.projeto_assinatura_salva = editor.assinatura()
    _abrir_editor(estado)
    notificar(estado, f"{_t('Projeto aberto')}: {os.path.basename(caminho)}", 'sucesso')
    return True


def _sincronizar_nuvem(estado, editor):
    """Envia o projeto para a conta em segundo plano (nao trava a tela)."""
    db = getattr(estado, 'db', None)
    usuario = getattr(estado, 'usuario_id_logado', None)
    if not (db and usuario):
        return
    nome = editor.dados.nome_musica
    conteudo = json.dumps(editor.para_dict())

    def _enviar():
        try:
            ok = db.salvar_projeto(usuario, nome, 'tablatura', conteudo)
        except Exception:
            ok = False
        if ok:
            notificar(estado, _t('Projeto sincronizado com a nuvem'), 'sucesso')
        else:
            notificar(estado, _t('Salvo no computador (nuvem indisponível)'), 'aviso')

    threading.Thread(target=_enviar, daemon=True).start()


def salvar_projeto(estado, como=False):
    editor = obter_editor()
    if editor is None:
        notificar(estado, _t('Nenhum projeto aberto. Use Arquivo › Novo projeto.'), 'aviso')
        return False
    caminho = getattr(estado, 'projeto_caminho', None)
    if como or not caminho:
        caminho = _janela_arquivo(
            True, _t('Salvar projeto como'),
            [(_t('Projeto EIGUIT'), f'*{EXTENSAO_PROJETO}'), (_t('Todos'), '*.*')],
            EXTENSAO_PROJETO, _nome_arquivo_seguro(editor.dados.nome_musica) + EXTENSAO_PROJETO,
            pasta_documentos('Projetos'))
        if not caminho:
            return False
    try:
        with open(caminho, 'w', encoding='utf-8') as arq:
            json.dump(editor.para_dict(), arq, ensure_ascii=False, indent=1)
    except Exception as erro:
        notificar(estado, f"{_t('Erro ao salvar')}: {erro}", 'erro', 4.5)
        return False
    estado.projeto_caminho = caminho
    estado.projeto_assinatura_salva = editor.assinatura()
    notificar(estado, f"{_t('Projeto salvo')}: {os.path.basename(caminho)}", 'sucesso')
    _sincronizar_nuvem(estado, editor)
    return True


def exportar_txt(estado):
    editor = obter_editor()
    if editor is None:
        notificar(estado, _t('Abra ou crie um projeto para exportar.'), 'aviso')
        return None
    caminho = _janela_arquivo(
        True, _t('Exportar tablatura'), [(_t('Texto'), '*.txt')], '.txt',
        _nome_arquivo_seguro(editor.dados.nome_musica) + '.txt', pasta_documentos('Exportados'))
    if not caminho:
        return None
    if editor.exportar(caminho):
        notificar(estado, f"{_t('Tablatura exportada')}: {os.path.basename(caminho)}", 'sucesso')
        return caminho
    notificar(estado, _t('Erro ao exportar a tablatura'), 'erro')
    return None


# Instrumento General MIDI de cada trilha (a bateria fica de fora: a grade dela
# e de cordas, nao de pecas do kit)
_PROGRAMA_MIDI = {'Guitarra': 27, 'Baixo': 33, 'Voz': 53}


def gerar_midi(editor, caminho):
    """Converte as trilhas com notas em um arquivo .mid (uma faixa cada)."""
    import mido
    from config.instrumentos import NOTAS
    from ui.editor_musical import altura_da_casa, valor_da_celula

    ticks_por_seminima = 480
    passo = ticks_por_seminima // 4          # cada coluna e uma semicolcheia
    arquivo = mido.MidiFile(ticks_per_beat=ticks_por_seminima)
    tempo_meta = mido.MidiTrack()
    tempo_meta.append(mido.MetaMessage('track_name', name=editor.dados.nome_musica))
    tempo_meta.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(editor.dados.bpm)))
    tempo_meta.append(mido.MetaMessage('time_signature', numerator=4, denominator=4))
    arquivo.tracks.append(tempo_meta)

    faixas = 0
    for canal, (nome, grade) in enumerate(editor.dados.trilhas.items()):
        if nome not in _PROGRAMA_MIDI:
            continue
        eventos = []
        for corda, linha in enumerate(grade):
            colunas = [i for i, c in enumerate(linha) if valor_da_celula(c) is not None]
            for n, coluna in enumerate(colunas):
                casa = valor_da_celula(linha[coluna])
                nota, oitava = altura_da_casa(nome, corda, casa)
                if nota is None:
                    continue
                numero = max(0, min(127, 12 * (oitava + 1) + NOTAS.index(nota)))
                proxima = colunas[n + 1] if n + 1 < len(colunas) else coluna + 4
                duracao = max(1, min(8, proxima - coluna)) * passo
                inicio = coluna * passo
                eventos.append((inicio, 1, numero))
                eventos.append((inicio + duracao, 0, numero))
        if not eventos:
            continue
        faixa = mido.MidiTrack()
        faixa.append(mido.MetaMessage('track_name', name=nome))
        faixa.append(mido.Message('program_change', channel=canal, program=_PROGRAMA_MIDI[nome]))
        eventos.sort(key=lambda e: (e[0], e[1]))
        agora = 0
        for instante, liga, numero in eventos:
            tipo = 'note_on' if liga else 'note_off'
            faixa.append(mido.Message(tipo, channel=canal, note=numero,
                                      velocity=96 if liga else 0, time=instante - agora))
            agora = instante
        arquivo.tracks.append(faixa)
        faixas += 1
    if not faixas:
        raise ValueError(_t('o projeto ainda não tem notas'))
    arquivo.save(caminho)
    return faixas


def exportar_midi(estado):
    editor = obter_editor()
    if editor is None:
        notificar(estado, _t('Abra ou crie um projeto para exportar.'), 'aviso')
        return None
    caminho = _janela_arquivo(
        True, _t('Exportar MIDI'), [('MIDI', '*.mid')], '.mid',
        _nome_arquivo_seguro(editor.dados.nome_musica) + '.mid', pasta_documentos('Exportados'))
    if not caminho:
        return None
    try:
        faixas = gerar_midi(editor, caminho)
    except Exception as erro:
        notificar(estado, f"{_t('Erro ao exportar MIDI')}: {erro}", 'erro', 4.5)
        return None
    notificar(estado, f"{_t('MIDI exportado')} ({faixas} {_t('faixa(s)')}): "
                      f"{os.path.basename(caminho)}", 'sucesso')
    return caminho


# ---------------------------------------------------------------------------
# Arquivo: captura de tela (substitui o antigo "Imprimir", que nao fazia nada)
# ---------------------------------------------------------------------------

def pedir_captura(estado):
    """A captura sai no proximo quadro, ja sem o menu aberto por cima."""
    estado.captura_pendente = 1


def executar_captura_se_pendente(estado, tela):
    pendente = getattr(estado, 'captura_pendente', 0)
    if not pendente:
        return None
    estado.captura_pendente = 0
    pasta = pasta_documentos('Capturas')
    caminho = os.path.join(pasta, time.strftime('EIGUIT_%Y-%m-%d_%H-%M-%S.png'))
    try:
        pygame.image.save(tela, caminho)
    except Exception as erro:
        notificar(estado, f"{_t('Erro ao capturar a tela')}: {erro}", 'erro')
        return None
    estado.ultima_captura = caminho
    notificar(estado, f"{_t('Captura salva em')} {caminho}", 'sucesso', 4.0)
    return caminho


def abrir_pasta(caminho):
    try:
        if os.name == 'nt':
            os.startfile(caminho)                         # noqa: S606
        else:
            webbrowser.open('file://' + os.path.abspath(caminho))
    except Exception as erro:
        print(f'[ARQUIVO] Nao abriu a pasta: {erro}')


# ---------------------------------------------------------------------------
# Exibir: edicao, tema, zoom, tela
# ---------------------------------------------------------------------------

def alternar_modo_edicao(estado):
    estado.drag_ativado = not estado.drag_ativado
    if not estado.drag_ativado:
        try:
            from core.controlador_eventos import obter_draggers_ativos
            for dragger in obter_draggers_ativos(estado):
                dragger.arrastando = False
        except Exception:
            pass
    notificar(estado, _t('Modo de edição ligado: arraste e redimensione os blocos')
              if estado.drag_ativado else _t('Layout travado'), 'info', 2.2)


def alternar_tema(estado):
    from config.design_system import TEMA
    import config.theme as tema_legado
    TEMA.alternar()
    tema_legado.sincronizar_tema()


def _tamanho_tela():
    superficie = pygame.display.get_surface()
    if superficie is None:
        return 1280, 720
    return superficie.get_size()


def mudar_zoom(estado, delta=None, valor=None):
    camera = getattr(estado, 'camera', None)
    if camera is None:
        return
    largura, altura = _tamanho_tela()
    # Mantem fixo o ponto que esta no centro da tela
    cx, cy = largura / 2, altura / 2
    vx = cx / camera.zoom + camera.offset_x
    vy = cy / camera.zoom + camera.offset_y
    novo = valor if valor is not None else camera.zoom + (delta or 0)
    camera.zoom = round(max(ZOOM_MIN, min(ZOOM_MAX, novo)), 2)
    camera.offset_x = vx - cx / camera.zoom
    camera.offset_y = vy - cy / camera.zoom
    notificar(estado, f"{_t('Zoom')}: {int(round(camera.zoom * 100))}%", 'info', 1.2)


def zoom_padrao(estado):
    camera = getattr(estado, 'camera', None)
    if camera is None:
        return
    camera.zoom = 1.0
    camera.offset_x = camera.offset_y = 0
    notificar(estado, _t('Zoom 100% e visão centralizada'), 'info', 1.4)


def em_tela_cheia(estado):
    superficie = pygame.display.get_surface()
    if superficie is not None and hasattr(superficie, 'get_flags'):
        try:
            return bool(superficie.get_flags() & pygame.FULLSCREEN)
        except pygame.error:
            pass
    return bool(getattr(estado, 'em_tela_cheia', True))


def aplicar_modo_tela(estado, modo):
    """'cheia', 'janela' (redimensionavel) ou (largura, altura)."""
    if os.environ.get('SDL_VIDEODRIVER') == 'dummy':
        estado.em_tela_cheia = modo == 'cheia'
        estado.modo_tela = modo
        return
    try:
        if modo == 'cheia':
            tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        elif modo == 'janela':
            info = pygame.display.Info()
            largura = max(1024, int(getattr(info, 'current_w', 1600) * 0.85))
            altura = max(640, int(getattr(info, 'current_h', 900) * 0.85))
            tela = pygame.display.set_mode((largura, altura), pygame.RESIZABLE)
        else:
            tela = pygame.display.set_mode(tuple(modo), pygame.RESIZABLE)
    except pygame.error as erro:
        notificar(estado, f"{_t('Não foi possível mudar a tela')}: {erro}", 'erro')
        return
    estado.em_tela_cheia = modo == 'cheia'
    estado.modo_tela = modo
    atualizar_tamanho_tela(estado, tela.get_width(), tela.get_height())
    rotulo = dict((m if isinstance(m, str) else tuple(m), r) for m, r in MODOS_TELA)
    notificar(estado, _t(rotulo.get(modo if isinstance(modo, str) else tuple(modo),
                                    'Tela ajustada')), 'info', 1.8)


def alternar_tela_cheia(estado):
    if em_tela_cheia(estado):
        aplicar_modo_tela(estado, 'janela')
    else:
        aplicar_modo_tela(estado, 'cheia')


def atualizar_tamanho_tela(estado, largura, altura):
    """Chamado quando a janela muda de tamanho (troca de modo ou arrasto da borda)."""
    estado.LARGURA_TELA = largura
    estado.ALTURA_TELA = altura


def restaurar_layout(estado):
    perfil = getattr(estado, 'gerenciador_perfil', None)
    if perfil is not None and hasattr(perfil, 'restaurar_layout'):
        perfil.restaurar_layout(estado)
    zoom_padrao(estado)
    notificar(estado, _t('Layout restaurado para o padrão'), 'sucesso')


# ---------------------------------------------------------------------------
# Perfil e conta
# ---------------------------------------------------------------------------

def nome_perfil_atual(estado):
    perfil = getattr(estado, 'gerenciador_perfil', None)
    if perfil is not None and hasattr(perfil, 'nome_perfil_atual'):
        return perfil.nome_perfil_atual()
    return ''


def excluir_perfil(estado):
    perfil = getattr(estado, 'gerenciador_perfil', None)
    if perfil is None:
        return
    nome = perfil.deletar_perfil_atual()
    if nome:
        notificar(estado, f"{_t('Perfil excluído')}: {nome}", 'sucesso')
    else:
        notificar(estado, _t('Nenhum perfil salvo para excluir'), 'aviso')


def restaurar_padrao(estado, configs, campo):
    perfil = getattr(estado, 'gerenciador_perfil', None)
    if perfil is not None:
        perfil.restaurar_padrao(estado, configs, campo)
    notificar(estado, _t('Configurações de fábrica restauradas'), 'sucesso')


def trocar_conta(estado):
    """Esquece a sessao salva e reabre o programa na tela de login."""
    try:
        from ui.tela_login import FILE_CACHE
    except Exception:
        FILE_CACHE = 'sessao_cache.json'
    if os.path.exists(FILE_CACHE):
        try:
            os.remove(FILE_CACHE)
        except OSError:
            pass
    estado.reiniciar_apos_sair = True
    estado.solicitou_saida = True


def reiniciar_programa():
    """Abre uma nova instancia do programa (usado ao trocar de conta)."""
    import subprocess
    try:
        subprocess.Popen([sys.executable] + sys.argv, cwd=os.getcwd())
    except Exception as erro:
        print(f'[CONTA] Nao consegui reabrir o programa: {erro}')


# ---------------------------------------------------------------------------
# Configuracoes
# ---------------------------------------------------------------------------

def abrir_secao(estado, conteudo, sub_aba=0):
    """Abre uma aba do painel inferior (ex.: configuracao)."""
    fechar_telas(estado)
    for i, secao in enumerate(getattr(estado, 'secoes_inferiores', [])):
        abrir = secao.get('conteudo') == conteudo
        secao['expandido'] = abrir
        if abrir:
            secao['memoria_sub_aba'] = sub_aba
            try:
                estado.scroll_y[i] = 0
            except Exception:
                pass


def listar_entradas_audio(gravador):
    if gravador is None or not hasattr(gravador, 'obter_lista_entradas'):
        return []
    try:
        return gravador.obter_lista_entradas()
    except Exception:
        return []


def escolher_entrada_audio(estado, gravador, entrada):
    if gravador is None:
        return
    try:
        gravador.mudar_dispositivo(entrada['id'])
    except Exception as erro:
        notificar(estado, f"{_t('Erro ao trocar a entrada')}: {erro}", 'erro')
        return
    if getattr(gravador, 'ativo', False):
        notificar(estado, f"{_t('Entrada de áudio')}: {entrada['nome']}", 'sucesso')
    else:
        notificar(estado, _t('Não foi possível abrir essa entrada de áudio'), 'erro')


def escolher_idioma(estado, configs, indice):
    if configs is None or not hasattr(configs, 'idiomas'):
        return
    configs.indice_idioma = indice
    codigo = configs.idiomas[indice]['code']
    try:
        from core.i18n import sistema_traducao
        sistema_traducao.atualizar_configuracao(codigo)
    except Exception:
        pass
    estado.idioma = codigo
    notificar(estado, f"{_t('Idioma')}: {configs.idiomas[indice]['nome']}", 'sucesso')


# ---------------------------------------------------------------------------
# Ajuda
# ---------------------------------------------------------------------------

def abrir_link(url):
    try:
        webbrowser.open(url)
    except Exception as erro:
        print(f'[LINK] {erro}')


def versao_programa():
    try:
        import tomllib
        with open('pyproject.toml', 'rb') as arq:
            return tomllib.load(arq).get('project', {}).get('version', '')
    except Exception:
        return ''


# ---------------------------------------------------------------------------
# Workspace (atalhos configuraveis)
# ---------------------------------------------------------------------------

def alternar_secao(estado, conteudo):
    """Abre a aba do painel inferior; se ja estava aberta, fecha."""
    for i, secao in enumerate(getattr(estado, 'secoes_inferiores', [])):
        if secao.get('conteudo') == conteudo:
            abrir = not secao.get('expandido')
            for outra in estado.secoes_inferiores:
                outra['expandido'] = False
            secao['expandido'] = abrir
            if abrir:
                try:
                    estado.scroll_y[i] = 0
                except Exception:
                    pass
            return


def alternar_metronomo(estado):
    metronomo = getattr(estado, 'metronomo', None)
    if metronomo is None:
        return
    if getattr(metronomo, 'tocando', False):
        metronomo.tocando = False
        notificar(estado, _t('Metrônomo parado'), 'info', 1.2)
    else:
        metronomo.ativado = True
        metronomo._iniciar()
        notificar(estado, f"{_t('Metrônomo')}: {metronomo.bpm} BPM", 'info', 1.2)


def mudar_bpm(estado, delta):
    metronomo = getattr(estado, 'metronomo', None)
    if metronomo is None:
        return
    metronomo.definir_bpm(metronomo.bpm + delta)
    notificar(estado, f"{_t('Metrônomo')}: {metronomo.bpm} BPM", 'info', 1.0)
