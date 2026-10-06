# -*- coding: utf-8 -*-
"""
Teclas de atalho configuraveis (Configuracoes > Teclas de atalho).

Uma combinacao e guardada como texto: 'ctrl+shift+s', 'f12', 'alt+1'. O nome
da tecla e o de pygame.key.name(), entao volta para o codigo com
pygame.key.key_code(). Cada funcao pode ter mais de uma combinacao; a mesma
combinacao nunca fica em duas funcoes ao mesmo tempo.

As combinacoes do usuario sao guardadas no perfil.
"""
import pygame

# (grupo, id, rotulo, combinacoes padrao)
ACOES = [
    ('Arquivo', 'novo_projeto', 'Novo projeto', ['ctrl+n']),
    ('Arquivo', 'abrir_projeto', 'Abrir projeto', ['ctrl+o']),
    ('Arquivo', 'salvar_projeto', 'Salvar', ['ctrl+s']),
    ('Arquivo', 'salvar_como', 'Salvar como', ['ctrl+shift+s']),
    ('Arquivo', 'exportar_txt', 'Exportar tablatura (.txt)', ['ctrl+e']),
    ('Arquivo', 'exportar_midi', 'Exportar MIDI (.mid)', ['ctrl+shift+e']),
    ('Arquivo', 'capturar_tela', 'Capturar tela (PNG)', ['f12']),
    ('Arquivo', 'abrir_pasta', 'Abrir pasta do EIGUIT', []),
    ('Arquivo', 'sair', 'Sair', ['ctrl+q']),
    ('Exibir', 'modo_edicao', 'Modo de edição do layout', ['f2']),
    ('Exibir', 'tema_escuro', 'Alternar tema claro/escuro', ['f3']),
    ('Exibir', 'zoom_mais', 'Aumentar zoom', ['ctrl+=', 'ctrl+shift+=', 'ctrl+[+]']),
    ('Exibir', 'zoom_menos', 'Diminuir zoom', ['ctrl+-', 'ctrl+[-]']),
    ('Exibir', 'zoom_padrao', 'Zoom 100% / centralizar', ['ctrl+0', 'ctrl+[0]']),
    ('Exibir', 'restaurar_layout', 'Restaurar layout dos blocos', []),
    ('Exibir', 'tela_cheia', 'Tela cheia', ['f11']),
    ('Exibir', 'voltar', 'Voltar ao workspace', ['alt+left']),
    ('Workspace', 'secao_escalas', 'Abrir/fechar Escalas', ['alt+1']),
    ('Workspace', 'secao_acordes', 'Abrir/fechar Acordes', ['alt+2']),
    ('Workspace', 'secao_analise_ia', 'Abrir/fechar Análise de IA', ['alt+3']),
    ('Workspace', 'secao_estudos', 'Abrir/fechar Estudos', ['alt+4']),
    ('Workspace', 'secao_musicas', 'Abrir/fechar Músicas', ['alt+5']),
    ('Workspace', 'secao_configuracao', 'Abrir/fechar Configuração', ['alt+6']),
    ('Workspace', 'metronomo', 'Metrônomo: tocar / parar', ['ctrl+m']),
    ('Workspace', 'bpm_mais', 'Metrônomo: +5 BPM', ['ctrl+up']),
    ('Workspace', 'bpm_menos', 'Metrônomo: -5 BPM', ['ctrl+down']),
    ('Perfil', 'conta', 'Minha conta (Cloud)', []),
    ('Perfil', 'perfil_salvar', 'Salvar perfil', ['ctrl+shift+p']),
    ('Perfil', 'perfil_carregar', 'Carregar perfil', []),
    ('Perfil', 'perfil_excluir', 'Excluir perfil atual', []),
    ('Perfil', 'perfil_padrao', 'Voltar para o padrão', []),
    ('Perfil', 'trocar_conta', 'Trocar de conta', []),
    ('Configurações', 'pref_gerais', 'Preferências gerais', ['ctrl+,']),
    ('Configurações', 'pref_cores', 'Cores da interface', []),
    ('Configurações', 'teclas', 'Teclas de atalho', ['ctrl+k']),
    ('Configurações', 'desempenho', 'Desempenho', []),
    ('Configurações', 'audio', 'Entrada de áudio', []),
    ('Configurações', 'tela', 'Tela e resolução', []),
    ('Configurações', 'idioma', 'Idioma', []),
    ('Ajuda', 'suporte', 'Central de suporte e tutoriais', ['f1']),
    ('Ajuda', 'atalhos', 'Lista de atalhos', ['ctrl+/']),
    ('Ajuda', 'sobre', 'Sobre o EIGUIT', []),
]

PADROES = {acao: list(combos) for _g, acao, _r, combos in ACOES}
ROTULOS = {acao: rotulo for _g, acao, rotulo, _c in ACOES}
GRUPOS = []
for _grupo, _acao, _rot, _c in ACOES:
    if _grupo not in GRUPOS:
        GRUPOS.append(_grupo)

# Teclas que sozinhas sao so modificadores (nao viram atalho)
_MODIFICADORES = {pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LSHIFT, pygame.K_RSHIFT,
                  pygame.K_LALT, pygame.K_RALT, pygame.K_LGUI, pygame.K_RGUI,
                  pygame.K_CAPSLOCK, pygame.K_NUMLOCK, pygame.K_MODE}

_NOMES_BONITOS = {
    'space': 'Espaço', 'return': 'Enter', 'escape': 'Esc', 'backspace': 'Backspace',
    'delete': 'Del', 'insert': 'Ins', 'tab': 'Tab', 'home': 'Home', 'end': 'End',
    'page up': 'PgUp', 'page down': 'PgDn', 'left': '←', 'right': '→', 'up': '↑',
    'down': '↓', 'enter': 'Num Enter',
}


# ---------------------------------------------------------------------------
# Combinacoes
# ---------------------------------------------------------------------------

def combo_do_evento(evento):
    """'ctrl+shift+s' para um KEYDOWN, ou None se for so um modificador."""
    if evento.key in _MODIFICADORES:
        return None
    nome = pygame.key.name(evento.key)
    if not nome or nome == 'unknown key':
        return None
    mods = getattr(evento, 'mod', 0) or 0
    partes = []
    if mods & pygame.KMOD_CTRL:
        partes.append('ctrl')
    if mods & pygame.KMOD_SHIFT:
        partes.append('shift')
    if mods & pygame.KMOD_ALT:
        partes.append('alt')
    partes.append(nome.lower())
    return '+'.join(partes)


def _separar(combo):
    """'ctrl+shift+=' -> ({'ctrl','shift'}, '='). Aceita '+' e '[+]' como tecla."""
    combo = (combo or '').strip().lower()
    mods = set()
    while True:
        for m in ('ctrl+', 'shift+', 'alt+'):
            if combo.startswith(m) and len(combo) > len(m):
                mods.add(m[:-1])
                combo = combo[len(m):]
                break
        else:
            break
    return mods, combo


def valido(combo):
    mods, tecla = _separar(combo)
    if not tecla:
        return False
    try:
        return pygame.key.key_code(tecla) != pygame.K_UNKNOWN
    except (ValueError, pygame.error):
        return False


def texto(combo):
    """Como mostrar: 'Ctrl+Shift+S', 'F12', 'Alt+1', 'Num +'."""
    if not combo:
        return ''
    mods, tecla = _separar(combo)
    partes = [m.capitalize() for m in ('ctrl', 'shift', 'alt') if m in mods]
    if tecla.startswith('[') and tecla.endswith(']'):
        bonito = 'Num ' + tecla[1:-1]
    elif tecla in _NOMES_BONITOS:
        bonito = _NOMES_BONITOS[tecla]
    elif len(tecla) <= 3 and tecla[:1] == 'f' and tecla[1:].isdigit():
        bonito = tecla.upper()
    elif len(tecla) == 1:
        bonito = tecla.upper()
    else:
        bonito = tecla.title()
    return '+'.join(partes + [bonito])


def precisa_modificador(combo):
    """Letras, numeros e espaco sozinhos atrapalhariam a digitacao."""
    mods, tecla = _separar(combo)
    if mods & {'ctrl', 'alt'}:
        return False
    return len(tecla) == 1 or tecla == 'space'


# ---------------------------------------------------------------------------
# Tabela do usuario (guardada no estado e no perfil)
# ---------------------------------------------------------------------------

def normalizar(dados):
    """Padroes + o que veio do perfil, so com acoes e combinacoes validas."""
    final = {acao: list(combos) for acao, combos in PADROES.items()}
    if isinstance(dados, dict):
        usados = {}
        for acao, combos in dados.items():
            if acao not in final or not isinstance(combos, (list, tuple)):
                continue
            final[acao] = [c for c in combos if isinstance(c, str) and valido(c)][:3]
        # Se o perfil repetiu uma combinacao, fica so na primeira acao
        for acao in list(final):
            limpos = []
            for c in final[acao]:
                if c in usados:
                    continue
                usados[c] = acao
                limpos.append(c)
            final[acao] = limpos
    return final


def obter(estado):
    tabela = getattr(estado, 'atalhos', None)
    if not isinstance(tabela, dict):
        tabela = normalizar(None)
        estado.atalhos = tabela
    return tabela


def _indice(estado):
    indice = getattr(estado, '_indice_atalhos', None)
    if indice is None:
        indice = {}
        for acao, combos in obter(estado).items():
            for c in combos:
                indice[c] = acao
        estado._indice_atalhos = indice
    return indice


def acao_do_evento(estado, evento):
    combo = combo_do_evento(evento)
    if combo is None:
        return None
    return _indice(estado).get(combo)


def acao_do_combo(estado, combo):
    return _indice(estado).get(combo)


def texto_da_acao(estado, acao):
    combos = obter(estado).get(acao) or []
    return texto(combos[0]) if combos else ''


def _mudou(estado):
    estado._indice_atalhos = None
    estado.perfil_alterado = True


def definir(estado, acao, combo):
    """
    Liga 'combo' a 'acao' (substitui as combinacoes dela). Se outra acao usava
    a combinacao, ela perde essa tecla. Devolve a acao que perdeu, ou None.
    """
    tabela = obter(estado)
    perdeu = None
    for outra, combos in tabela.items():
        if outra != acao and combo in combos:
            combos.remove(combo)
            perdeu = outra
    tabela[acao] = [combo]
    _mudou(estado)
    return perdeu


def limpar(estado, acao):
    obter(estado)[acao] = []
    _mudou(estado)


def restaurar(estado, acao=None):
    """Volta uma acao (ou todas) ao padrao, sem deixar combinacao repetida."""
    tabela = obter(estado)
    if acao is None:
        estado.atalhos = normalizar(None)
    else:
        for combo in PADROES.get(acao, []):
            for outra, combos in tabela.items():
                if outra != acao and combo in combos:
                    combos.remove(combo)
        tabela[acao] = list(PADROES.get(acao, []))
    _mudou(estado)


def diferentes_do_padrao(estado):
    """So o que o usuario mudou (e o que vai para o perfil)."""
    return {acao: list(combos) for acao, combos in obter(estado).items()
            if combos != PADROES.get(acao, [])}
