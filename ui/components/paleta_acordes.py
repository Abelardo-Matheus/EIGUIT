# -*- coding: utf-8 -*-
"""
Paleta de acordes: estudar acordes no braco sem abrir a aba ACORDES.

Um bloco do gaveteiro ('Acordes') que fica na tela junto do braco:

- Linha de tonicas: as doze notas; clicar troca a tonica dos cartoes.
- Cartoes de acorde: C, Cm, C7, Cmaj7... Clicar liga o acorde no braco
  inteiro; clicar de novo tira. Arrastar o cartao e soltar no braco poe o
  acorde so naquela regiao, encaixado na forma CAGED mais perto de onde foi
  solto (C solto na casa 3 vira "C (A)", casas 3 a 7).
- Faixa "No braco": um chip por acorde ligado, na cor dele. Passar o mouse
  destaca so aquele acorde no braco; clicar tira; arrastar o chip e soltar
  em outro ponto do braco muda a regiao.

Varios acordes ficam ligados ao mesmo tempo (ate MAX_NO_BRACO), cada um com
a sua cor; nota que pertence a mais de um acorde ganha um anel na cor do
outro, o que mostra as notas em comum.

Os cartoes da aba ACORDES e o mini-braco dela tambem podem ser arrastados
para o braco: o arrasto e o mesmo deste modulo.

Tudo vive em estado.acordes_fixados, a mesma lista que o botao Fixar da aba,
as progressoes rapidas e o braco ja usam. As regras dos blocos valem aqui:
desenho recortado no bloco e retangulos guardados no desenho.
"""
import pygame

from config.design_system import TEMA, ds
from core.i18n import _t

# Ordem dos cartoes: do mais usado para o menos usado, para que um bloco
# pequeno mostre primeiro o que mais importa
TIPOS_PALETA = ['maior', 'menor', '7', 'maj7', 'm7', 'power', 'sus2', 'sus4',
                'dim', 'aum', 'm7b5', 'dim7', '6', 'm6', '9']

MAX_NO_BRACO = 6          # uma cor distinta por acorde
MARGEM_ARRASTO = 6        # pixels de mouse antes do clique virar arrasto
LARGURA_JANELA = 4        # casas de uma regiao (mesma janela do CAGED)
MARGEM_BRACO = 14         # folga em volta do braco para aceitar a soltura


# ---------------------------------------------------------------------------
# CALCULOS PUROS (sem desenho, faceis de testar)
# ---------------------------------------------------------------------------

def _acordes():
    """O modulo do painel de acordes, importado so quando preciso."""
    from ui.blocks import painel_acordes
    return painel_acordes


def cifra_de(item):
    """Cifra sem a forma: 'C (A)' -> 'C'."""
    return item.get('cifra') or str(item.get('rotulo', '')).split(' (')[0]


def janela_caged(tonica, casa, num_casas=24):
    """
        Como funciona: Testa as cinco formas CAGED da tonica, em todas as
        oitavas que cabem no braco, e fica com a janela cujo centro esta mais
        perto da casa informada.
        Para que serve: Soltar um acorde no braco cair numa regiao que se toca
        de verdade, e nao numa faixa qualquer de casas.
        Onde e usada: alvo_da_soltura.

        Devolve (casa_inicial, casa_final, nome_da_forma).
    """
    pa = _acordes()
    melhor = None
    limite = max(0, int(num_casas) - 1)
    for shape in pa.SHAPES:
        solta = pa.CORDAS_SOLTAS[shape['corda_tonica']]
        base = (pa.semitons(solta, tonica) - shape['casa_tonica']) % 12
        for inicio in (base, base + 12, base + 24):
            if inicio > limite:
                continue
            chave = (abs(inicio + LARGURA_JANELA / 2 - casa), inicio)
            if melhor is None or chave < melhor[0]:
                melhor = (chave, (inicio, inicio + LARGURA_JANELA, shape['nome']))
    if melhor is None:
        inicio = max(0, min(limite, int(casa) - 2))
        return inicio, inicio + LARGURA_JANELA, ''
    return melhor[1]


def descrever(tonica, tipo, janela=None, forma=''):
    """Dicionario de um acorde no formato que o braco desenha."""
    pa = _acordes()
    cifra = pa.nome_do_acorde(tonica, tipo)
    rotulo = f'{cifra} ({forma})' if forma else cifra
    return {'rotulo': rotulo, 'cifra': cifra, 'tonica': tonica, 'tipo': tipo,
            'notas': pa.notas_do_acorde(tonica, tipo),
            'janela': tuple(janela) if janela else None,
            'cor': tuple(TEMA.acento), 'fixado': True}


def proxima_cor(lista):
    """A primeira cor de acorde que ainda nao esta no braco."""
    cores = _acordes().CORES_FIXADOS
    usadas = {tuple(item.get('cor') or ()) for item in lista}
    for cor in cores:
        if tuple(cor) not in usadas:
            return tuple(cor)
    return tuple(cores[len(lista) % len(cores)])


def _lista(estado):
    lista = getattr(estado, 'acordes_fixados', None)
    if lista is None:
        lista = []
        estado.acordes_fixados = lista
    return lista


def _sincronizar(estado):
    """O braco le acordes_no_braco; fora da aba ele e igual aos fixados."""
    estado.acordes_no_braco = list(_lista(estado))


def adicionar(estado, item):
    """
        Como funciona: Poe o acorde no braco com uma cor livre. O mesmo rotulo
        nao entra duas vezes; o acorde que estava no braco inteiro e
        substituido quando volta numa regiao. Passando do limite, sai o mais
        antigo.
        Para que serve: Ligar varios acordes ao mesmo tempo sem repetir cor.
        Onde e usada: Clique e soltura da paleta, soltura vinda da aba.
    """
    lista = _lista(estado)
    if any(a.get('rotulo') == item['rotulo'] for a in lista):
        return False
    cifra = cifra_de(item)
    for i, atual in enumerate(lista):
        if cifra_de(atual) == cifra and not atual.get('janela') and item.get('janela'):
            novo = dict(item, cor=atual.get('cor') or proxima_cor(lista))
            lista[i] = novo
            _sincronizar(estado)
            return True
    if len(lista) >= MAX_NO_BRACO:
        lista.pop(0)
    novo = dict(item, cor=proxima_cor(lista), fixado=True)
    lista.append(novo)
    _sincronizar(estado)
    return True


def mover(estado, indice, janela, forma=''):
    """Leva o acorde ja ligado para outra regiao, mantendo a cor."""
    lista = _lista(estado)
    if not 0 <= indice < len(lista):
        return False
    atual = lista[indice]
    cifra = cifra_de(atual)
    rotulo = f'{cifra} ({forma})' if forma else cifra
    if any(i != indice and a.get('rotulo') == rotulo for i, a in enumerate(lista)):
        return False
    lista[indice] = dict(atual, rotulo=rotulo, cifra=cifra,
                         janela=tuple(janela) if janela else None)
    _sincronizar(estado)
    return True


def remover(estado, indice):
    """Tira um acorde do braco pela posicao na lista."""
    lista = _lista(estado)
    if 0 <= indice < len(lista):
        lista.pop(indice)
        _sincronizar(estado)
        return True
    return False


def alternar(estado, tonica, tipo):
    """
        Como funciona: Se o acorde ja esta no braco (em qualquer regiao), tira
        todas as ocorrencias; se nao esta, liga no braco inteiro.
        Para que serve: Clique simples no cartao da paleta.
        Onde e usada: tratar_evento.
    """
    cifra = _acordes().nome_do_acorde(tonica, tipo)
    lista = _lista(estado)
    restantes = [a for a in lista if cifra_de(a) != cifra]
    if len(restantes) != len(lista):
        lista[:] = restantes
        _sincronizar(estado)
        return False
    adicionar(estado, descrever(tonica, tipo))
    return True


def limpar(estado):
    """Tira todos os acordes do braco."""
    _lista(estado)[:] = []
    estado.progressao_ativa = -1
    _sincronizar(estado)


def ligado(estado, tonica, tipo):
    """Cor do acorde quando ele esta no braco, ou None."""
    cifra = _acordes().nome_do_acorde(tonica, tipo)
    for item in _lista(estado):
        if cifra_de(item) == cifra:
            return item.get('cor')
    return None


# ---------------------------------------------------------------------------
# GEOMETRIA DO BRACO (a mesma de guitar_neck.desenhar_guitarra)
# ---------------------------------------------------------------------------

def rect_do_braco(estado):
    """Retangulo das casas do braco principal, sem a calha das cordas soltas."""
    alvo = getattr(estado, 'dragger_guitarra', None)
    if alvo is None:
        return None
    calha = int(max(26, min(44, alvo.largura * 0.028)))
    return pygame.Rect(int(alvo.x + calha), int(alvo.y),
                       max(1, int(alvo.largura - calha)), max(1, int(alvo.altura)))


def sobre_o_braco(estado, pos):
    """Verdadeiro quando o ponto esta no braco ou na folga em volta dele."""
    alvo = getattr(estado, 'dragger_guitarra', None)
    if alvo is None or pos is None:
        return False
    zona = pygame.Rect(int(alvo.x), int(alvo.y), int(alvo.largura), int(alvo.altura))
    return zona.inflate(MARGEM_BRACO * 2, MARGEM_BRACO * 2).collidepoint(pos)


def casa_em(estado, x):
    """Casa sob a coordenada x: 0 na calha e na pestana, N dentro da casa N."""
    rect = rect_do_braco(estado)
    if rect is None:
        return 0
    num_casas = max(1, int(getattr(estado, 'NUM_CASAS', 18)))
    if x < rect.x:
        return 0
    casa = int((x - rect.x) / (rect.width / num_casas)) + 1
    return max(0, min(num_casas, casa))


def alvo_da_soltura(estado, arrasto, pos=None):
    """
        Como funciona: Se o ponto esta sobre o braco, monta o acorde que seria
        posto ali: com a janela fixa que veio da aba (forma CAGED escolhida),
        ou com a forma CAGED mais perto da casa sob o mouse.
        Para que serve: A previa durante o arrasto e a soltura usam o mesmo
        calculo, entao o que se ve e o que fica.
        Onde e usada: tratar_evento e acordes_para_desenhar.
    """
    if not arrasto:
        return None
    pos = pos or arrasto.get('pos')
    if not sobre_o_braco(estado, pos):
        return None
    tonica, tipo = arrasto['tonica'], arrasto['tipo']
    if arrasto.get('janela_fixa'):
        ini, fim = arrasto['janela_fixa']
        forma = arrasto.get('forma', '')
    else:
        casa = casa_em(estado, pos[0])
        ini, fim, forma = janela_caged(tonica, casa, getattr(estado, 'NUM_CASAS', 18))

    if arrasto.get('origem') == 'ativo':
        # Acorde ja ligado: so a regiao muda, notas e cor ficam
        lista = _lista(estado)
        indice = arrasto.get('indice', -1)
        if not 0 <= indice < len(lista):
            return None
        atual = lista[indice]
        cifra = cifra_de(atual)
        return dict(atual, cifra=cifra, janela=(ini, fim),
                    rotulo=f'{cifra} ({forma})' if forma else cifra)
    return descrever(tonica, tipo, (ini, fim), forma)


def forma_de(item):
    """Nome da forma CAGED no rotulo: 'C (A)' -> 'A'."""
    rotulo = str(item.get('rotulo', ''))
    return rotulo.split('(')[-1].rstrip(')') if '(' in rotulo else ''


def tonica_de(item):
    """Tonica do acorde: a guardada, ou a nota marcada como R."""
    if item.get('tonica'):
        return item['tonica']
    for nota, grau in (item.get('notas') or {}).items():
        if grau == 'R':
            return nota
    return 'C'


def acordes_para_desenhar(estado):
    """
        Como funciona: Junta os acordes do braco com a previa do arrasto em
        curso (acorde novo ou acorde mudando de regiao) e devolve tambem o
        conjunto de rotulos em foco.
        Para que serve: O braco desenha de uma lista so, ja com a previa.
        Onde e usada: ui/blocks/guitar_neck.desenhar_guitarra.

        Devolve (lista, foco).
    """
    lista = [a for a in (getattr(estado, 'acordes_no_braco', None) or [])]
    foco = set(getattr(estado, 'acorde_em_foco', None) or ())
    arrasto = getattr(estado, 'arrasto_acorde', None)
    if arrasto and arrasto.get('ativo'):
        alvo = alvo_da_soltura(estado, arrasto)
        if alvo is not None:
            if arrasto.get('origem') == 'ativo':
                indice = arrasto.get('indice', -1)
                fixados = _lista(estado)
                if 0 <= indice < len(fixados):
                    antigo = fixados[indice]
                    lista = [a for a in lista if a is not antigo]
            else:
                alvo['cor'] = proxima_cor(lista)
            alvo['previa'] = True
            lista.append(alvo)
            foco = {alvo['rotulo']}
    rotulos = {a.get('rotulo') for a in lista}
    return lista, (foco & rotulos)


# ---------------------------------------------------------------------------
# ESTADO
# ---------------------------------------------------------------------------

def preparar(estado):
    """Campos da paleta no estado global, criados na primeira vez."""
    if not hasattr(estado, 'paleta_tonica'):
        estado.paleta_tonica = getattr(estado, 'tom_atual', 'C') or 'C'
    for nome in ('rects_paleta_tonicas', 'rects_paleta_tipos', 'rects_paleta_ativos'):
        if not hasattr(estado, nome):
            setattr(estado, nome, [])
    if not hasattr(estado, 'rect_paleta_limpar'):
        estado.rect_paleta_limpar = pygame.Rect(0, 0, 0, 0)
    if not hasattr(estado, 'arrasto_acorde'):
        estado.arrasto_acorde = None
    if not hasattr(estado, 'acorde_em_foco'):
        estado.acorde_em_foco = set()
    return estado


def _zerar_alvos(estado):
    estado.rects_paleta_tonicas = []
    estado.rects_paleta_tipos = []
    estado.rects_paleta_ativos = []
    estado.rect_paleta_limpar = pygame.Rect(0, 0, 0, 0)


def iniciar_arrasto(estado, tonica, tipo, pos, origem='paleta', indice=-1,
                    janela_fixa=None, forma='', cifra=None):
    """
        Como funciona: Guarda o acorde preso ao mouse. Ate o mouse andar
        MARGEM_ARRASTO pixels ainda e um clique; depois vira arrasto, com
        fantasma e previa no braco.
        Para que serve: Um arrasto so para a paleta, a faixa de ligados e a
        aba ACORDES.
        Onde e usada: tratar_evento e PainelAcordes.tratar_clique.
    """
    preparar(estado)
    if cifra is None:
        cifra = _acordes().nome_do_acorde(tonica, tipo)
    estado.arrasto_acorde = {'tonica': tonica, 'tipo': tipo, 'origem': origem,
                             'cifra': cifra,
                             'indice': indice, 'inicio': tuple(pos), 'pos': tuple(pos),
                             'ativo': False,
                             'janela_fixa': tuple(janela_fixa) if janela_fixa else None,
                             'forma': forma}
    return estado.arrasto_acorde


# ---------------------------------------------------------------------------
# DESENHO
# ---------------------------------------------------------------------------

_FONTES = {}


def _fonte(tamanho):
    if tamanho not in _FONTES:
        _FONTES[tamanho] = pygame.font.SysFont('Arial', tamanho, bold=True)
    return _FONTES[tamanho]


def _mouse(estado):
    return getattr(estado, 'mouse_workspace', (-9999, -9999))


def _desenhar_cartao(tela, rect, cifra, nome, cor, hover, fonte, fonte_sub):
    """Um cartao de acorde: cifra grande, nome do tipo quando cabe."""
    if cor is not None:
        fundo = ds.misturar(TEMA.superficie_alt, cor, 0.42)
        ds.superficie_translucida(tela, rect, ds.clarear(fundo, 0.08) if hover else fundo,
                                  240, ds.RAIO_SM, cor, 2)
        cor_texto = TEMA.texto
    else:
        fundo = ds.clarear(TEMA.superficie_alt, 0.10) if hover else TEMA.superficie_alt
        ds.superficie_translucida(tela, rect, fundo, 225, ds.RAIO_SM,
                                  TEMA.acento if hover else TEMA.borda, 1)
        cor_texto = TEMA.texto if hover else TEMA.texto_suave
    duas_linhas = rect.height >= fonte.get_height() + fonte_sub.get_height() + 6
    if duas_linhas:
        meio = rect.y + (rect.height - fonte.get_height() - fonte_sub.get_height()) // 2
        ds.texto_em(tela, cifra, fonte, (rect.centerx, meio), cor_texto,
                    ancora='midtop', largura_max=rect.width - 4)
        ds.texto_em(tela, nome, fonte_sub, (rect.centerx, meio + fonte.get_height()),
                    TEMA.texto_apagado, ancora='midtop', largura_max=rect.width - 4)
    else:
        ds.texto_em(tela, cifra, fonte, rect.center, cor_texto, ancora='center',
                    largura_max=rect.width - 4)
    if cor is not None:
        pygame.draw.circle(tela, ds.rgb(cor), (rect.right - 6, rect.y + 6), 3)


def _desenhar_faixa(tela, estado, area, fonte, fonte_sub):
    """Faixa de baixo: chips dos acordes ligados, ou a dica de uso."""
    from ui.components.blocos_extras import _cabe
    lista = _lista(estado)
    mouse = _mouse(estado)
    arrasto = getattr(estado, 'arrasto_acorde', None)
    if not lista:
        ds.texto_em(tela, _t('Clique: braco todo  ·  Arraste: numa regiao'),
                    fonte_sub, (area.x, area.centery), TEMA.texto_apagado,
                    ancora='midleft', largura_max=area.width)
        return

    largura_limpar = fonte_sub.size(_t('Limpar'))[0] + 14
    limpar = pygame.Rect(area.right - largura_limpar, area.y, largura_limpar, area.height)
    if _cabe(limpar, area) and len(lista) > 1:
        estado.rect_paleta_limpar = limpar
        ds.botao(tela, limpar, _t('Limpar'), fonte_sub, variante='secundario',
                 hover=limpar.collidepoint(mouse))
        direita = limpar.x - ds.ESPACO_XS
    else:
        direita = area.right

    x = area.x
    for indice, item in enumerate(lista):
        rotulo = item.get('rotulo', '')
        cor = item.get('cor') or TEMA.acento
        largura = fonte.size(rotulo)[0] + 34
        chip = pygame.Rect(x, area.y, largura, area.height)
        if chip.right > direita:
            resto = len(lista) - indice
            ds.texto_em(tela, f'+{resto}', fonte_sub, (x + 2, area.centery),
                        TEMA.texto_suave, ancora='midleft')
            break
        hover = chip.collidepoint(mouse)
        arrastado = (arrasto and arrasto.get('ativo') and arrasto.get('origem') == 'ativo'
                     and arrasto.get('indice') == indice)
        ds.superficie_translucida(tela, chip, cor, 70 if arrastado else (150 if hover else 105),
                                  ds.RAIO_PILULA, cor, 1)
        pygame.draw.circle(tela, ds.rgb(cor), (chip.x + 10, chip.centery), 4)
        ds.texto_em(tela, rotulo, fonte, (chip.x + 18, chip.centery), TEMA.texto,
                    ancora='midleft', largura_max=chip.width - 32)
        x_fechar = pygame.Rect(chip.right - 16, chip.y, 14, chip.height)
        ds.texto_em(tela, 'x', fonte_sub, x_fechar.center,
                    TEMA.alerta if hover else TEMA.texto_apagado, ancora='center')
        estado.rects_paleta_ativos.append((chip, indice))
        x = chip.right + ds.ESPACO_XS


def desenhar_bloco_paleta(tela, estado, fontes, configs=None, campo=None):
    """
        Como funciona: Tres faixas dentro do bloco: as doze tonicas, a grade de
        cartoes de acorde da tonica escolhida e a faixa dos acordes ligados.
        Encolhendo o bloco, somem primeiro os nomes dos tipos, depois os
        ultimos cartoes; tonicas e ligados ficam sempre.
        Para que serve: Ver e comparar acordes no braco sem abrir a aba.
        Onde e usada: Workspace, bloco arrastavel 'Acordes' do gaveteiro.
    """
    from ui.components.blocos_extras import _moldura, _grade, _cabe, _pilula
    preparar(estado)
    _zerar_alvos(estado)
    foco_anterior = getattr(estado, 'acorde_em_foco', set())
    estado.acorde_em_foco = set()

    pa = _acordes()
    tonica = estado.paleta_tonica if estado.paleta_tonica in pa.NOTAS else 'C'
    fonte = fontes['pequena']
    fonte_sub = _fonte(11)
    with _moldura(tela, estado, 'paleta_acordes', _t('Acordes no braco'),
                  fontes, configs) as area:
        if area is None:
            # Bloco guardado: nada em foco, mas o arrasto da faixa continua valendo
            arrasto = getattr(estado, 'arrasto_acorde', None)
            if arrasto and arrasto.get('origem') == 'ativo':
                estado.acorde_em_foco = foco_anterior
            return
        mouse = _mouse(estado)
        alt_texto = fonte.get_height()

        # --- Tonicas: uma linha de doze, ou duas de seis em bloco estreito
        colunas = 12 if area.width / 12 >= fonte.size('C#')[0] + 4 else 6
        linhas = 12 // colunas
        alt_pilula = alt_texto + 4
        rect_tonicas = pygame.Rect(area.x, area.y, area.width,
                                   alt_pilula * linhas + 3 * (linhas - 1))
        for (r, nota) in zip(_grade(rect_tonicas, 12, 14, alt_pilula - 2, gap=3,
                                    opcoes_colunas=(colunas,), altura_max=alt_pilula),
                             pa.NOTAS):
            if _cabe(r, area):
                estado.rects_paleta_tonicas.append((r, nota))
                _pilula(tela, r, nota, fonte_sub if r.width < 26 else fonte,
                        ativo=(nota == tonica))

        # --- Faixa dos ligados, presa ao rodape do bloco
        alt_faixa = max(fonte_sub.get_height() + 12, fonte.get_height() + 6)
        rect_faixa = pygame.Rect(area.x, area.bottom - alt_faixa, area.width, alt_faixa)
        if rect_faixa.y > rect_tonicas.bottom + ds.ESPACO_SM + 16:
            _desenhar_faixa(tela, estado, rect_faixa, fonte, fonte_sub)
            fundo_grade = rect_faixa.y - ds.ESPACO_SM
        else:
            fundo_grade = area.bottom

        # --- Cartoes: quantos couberem, na ordem de TIPOS_PALETA
        rect_grade = pygame.Rect(area.x, rect_tonicas.bottom + ds.ESPACO_SM, area.width,
                                 max(0, fundo_grade - rect_tonicas.bottom - ds.ESPACO_SM))
        largura_min = fonte.size('Cmaj7')[0] + 8
        quantos = len(TIPOS_PALETA)
        rects = []
        while quantos > 0:
            rects = _grade(rect_grade, quantos, largura_min, alt_texto + 6, gap=4,
                           opcoes_colunas=(8, 6, 5, 4, 3, 2), altura_max=46)
            if rects:
                break
            quantos -= 1
        for r, tipo in zip(rects, TIPOS_PALETA):
            if not _cabe(r, area):
                continue
            cor = ligado(estado, tonica, tipo)
            hover = r.collidepoint(mouse)
            cifra = pa.nome_do_acorde(tonica, tipo)
            if hover and cor is not None:
                estado.acorde_em_foco = {a['rotulo'] for a in _lista(estado)
                                         if cifra_de(a) == cifra}
            _desenhar_cartao(tela, r, cifra, _t(pa.TIPOS_ACORDE[tipo]['nome']),
                             cor, hover, fonte, fonte_sub)
            estado.rects_paleta_tipos.append((r, tipo))

        # Chip da faixa sob o mouse: so ele fica em evidencia no braco
        for chip, indice in estado.rects_paleta_ativos:
            if chip.collidepoint(mouse):
                estado.acorde_em_foco = {_lista(estado)[indice].get('rotulo')}

    arrasto = getattr(estado, 'arrasto_acorde', None)
    if arrasto and arrasto.get('origem') == 'ativo':
        indice = arrasto.get('indice', -1)
        if 0 <= indice < len(_lista(estado)):
            estado.acorde_em_foco = {_lista(estado)[indice].get('rotulo')}


def desenhar_arrasto(tela, estado, fontes):
    """
        Como funciona: Desenha o acorde preso ao mouse e, embaixo, para onde
        ele vai: a forma e as casas quando esta sobre o braco, ou a dica de
        soltar no braco.
        Para que serve: Mostrar o que acontece antes de soltar.
        Onde e usada: Fim de ui/renderizador_ui.desenhar_workspace.
    """
    arrasto = getattr(estado, 'arrasto_acorde', None)
    if not arrasto or not arrasto.get('ativo'):
        return
    fonte = fontes['pequena']
    fonte_sub = _fonte(11)
    pa = _acordes()
    cifra = arrasto.get('cifra') or pa.nome_do_acorde(arrasto['tonica'], arrasto['tipo'])
    alvo = alvo_da_soltura(estado, arrasto)
    if alvo is not None:
        ini, fim = alvo['janela']
        forma = forma_de(alvo)
        dica = (f"{_t('forma')} {forma}  ·  " if forma else '') + f"{_t('casas')} {ini}-{fim}"
        cor = TEMA.acento
        if arrasto.get('origem') == 'ativo':
            lista = _lista(estado)
            if 0 <= arrasto.get('indice', -1) < len(lista):
                cor = lista[arrasto['indice']].get('cor') or cor
        else:
            cor = proxima_cor(getattr(estado, 'acordes_no_braco', []) or [])
    else:
        dica = _t('Solte no braco')
        cor = TEMA.borda_forte

    x, y = arrasto['pos']
    largura = max(fonte.size(cifra)[0], fonte_sub.size(dica)[0]) + ds.ESPACO_LG
    rect = pygame.Rect(int(x + 14), int(y + 10), largura,
                       fonte.get_height() + fonte_sub.get_height() + 10)
    ds.sombra(tela, rect, ds.RAIO_MD, forca=80)
    ds.superficie_translucida(tela, rect, TEMA.superficie, 240, ds.RAIO_MD, cor, 2)
    ds.texto_em(tela, cifra, fonte, (rect.x + ds.ESPACO_SM, rect.y + 4), TEMA.texto)
    ds.texto_em(tela, dica, fonte_sub,
                (rect.x + ds.ESPACO_SM, rect.y + 6 + fonte.get_height()),
                TEMA.texto_suave if alvo is not None else TEMA.texto_apagado)


# ---------------------------------------------------------------------------
# EVENTOS
# ---------------------------------------------------------------------------

def _achar(rects, pos):
    for rect, valor in rects or []:
        if rect.width > 0 and rect.height > 0 and rect.collidepoint(pos):
            return valor
    return None


def _coberto(estado, pos):
    """Verdadeiro quando o ponto esta sob a coluna lateral ou a gaveta de baixo."""
    coluna = getattr(estado, 'rect_gaveteiro', None)
    if coluna is not None:
        from ui.components.gaveteiro import largura_atual
        if pos[0] <= largura_atual(estado):
            return True
    barra = getattr(estado, 'dragger_painel_inferior', None)
    if barra is None:
        return False
    if any(sec.get('expandido') for sec in getattr(estado, 'secoes_inferiores', [])):
        from ui.components.bottom_nav import altura_caixa
        topo = barra.y - altura_caixa(estado) - 10
        return pygame.Rect(barra.x, topo, barra.largura,
                           barra.y + barra.altura - topo).collidepoint(pos)
    return pygame.Rect(barra.x, barra.y, barra.largura, barra.altura).collidepoint(pos)


def _tela_cheia(estado):
    for atributo in ('tela_estudo_ativa', 'tela_jogo_ativa',
                     'tela_criacao_tab_ativa', 'tab_tela_cheia_ativa'):
        if getattr(estado, atributo, False):
            return True
    return False


def _soltar(estado, arrasto):
    """Aplica a soltura: acorde novo no braco ou acorde ligado mudando de regiao."""
    alvo = alvo_da_soltura(estado, arrasto)
    if alvo is None:
        return False
    if arrasto.get('origem') == 'ativo':
        return mover(estado, arrasto.get('indice', -1), alvo['janela'], forma_de(alvo))
    return adicionar(estado, alvo)


def tratar_evento(estado, evento):
    """
        Como funciona: Cuida do mouse da paleta e de todo arrasto de acorde.
        Apertar num cartao ou chip prende o acorde; mexendo, vira arrasto com
        previa no braco; soltando sobre o braco, o acorde fica naquela regiao.
        Sem mexer, e clique: cartao liga/desliga no braco todo, chip tira.
        Para que serve: Estudar varios acordes no braco com clique e arrasto.
        Onde e usada: core/controlador_eventos.processar, antes do gaveteiro.

        Devolve True quando consumiu o evento.
    """
    preparar(estado)
    if _tela_cheia(estado):
        estado.arrasto_acorde = None
        return False

    if evento.type == pygame.MOUSEMOTION:
        estado.mouse_workspace = evento.pos
        arrasto = estado.arrasto_acorde
        if not arrasto:
            return False
        arrasto['pos'] = tuple(evento.pos)
        x0, y0 = arrasto['inicio']
        if abs(evento.pos[0] - x0) + abs(evento.pos[1] - y0) >= MARGEM_ARRASTO:
            arrasto['ativo'] = True
        return True

    if evento.type == pygame.MOUSEBUTTONDOWN and getattr(evento, 'button', 0) == 1:
        estado.mouse_workspace = evento.pos
        if getattr(estado, 'drag_ativado', False) or _coberto(estado, evento.pos):
            return False
        pos = evento.pos

        nota = _achar(estado.rects_paleta_tonicas, pos)
        if nota is not None:
            estado.paleta_tonica = nota
            return True

        if estado.rect_paleta_limpar.width and estado.rect_paleta_limpar.collidepoint(pos):
            limpar(estado)
            return True

        indice = _achar(estado.rects_paleta_ativos, pos)
        if indice is not None:
            lista = _lista(estado)
            if 0 <= indice < len(lista):
                item = lista[indice]
                iniciar_arrasto(estado, tonica_de(item), item.get('tipo') or 'maior',
                                pos, origem='ativo', indice=indice,
                                cifra=cifra_de(item))
            return True

        tipo = _achar(estado.rects_paleta_tipos, pos)
        if tipo is not None:
            iniciar_arrasto(estado, estado.paleta_tonica, tipo, pos, origem='paleta')
            return True
        return False

    if evento.type == pygame.MOUSEBUTTONUP and getattr(evento, 'button', 0) == 1:
        arrasto = estado.arrasto_acorde
        if not arrasto:
            return False
        estado.arrasto_acorde = None
        if arrasto.get('ativo'):
            _soltar(estado, arrasto)
            return True
        origem = arrasto.get('origem')
        if origem == 'paleta':
            alternar(estado, arrasto['tonica'], arrasto['tipo'])
            return True
        if origem == 'ativo':
            remover(estado, arrasto.get('indice', -1))
            return True
        # Clique sem arrasto vindo da aba: a aba ja tratou no aperto
        return False

    return False


# ---------------------------------------------------------------------------
# PERFIL
# ---------------------------------------------------------------------------

_CHAVES_SALVAS = ('rotulo', 'cifra', 'tonica', 'tipo', 'notas', 'janela', 'cor')


def exportar(estado):
    """Acordes ligados prontos para JSON (tuplas viram listas)."""
    saida = []
    for item in _lista(estado):
        limpo = {k: item.get(k) for k in _CHAVES_SALVAS if item.get(k) is not None}
        for chave in ('janela', 'cor'):
            if chave in limpo:
                limpo[chave] = list(limpo[chave])
        saida.append(limpo)
    return saida


def importar(estado, dados):
    """Devolve ao braco os acordes salvos no perfil, ignorando o que vier torto."""
    lista = []
    for item in dados or []:
        if not isinstance(item, dict) or not item.get('rotulo') or not item.get('notas'):
            continue
        novo = dict(item, fixado=True)
        novo['janela'] = tuple(item['janela']) if item.get('janela') else None
        novo['cor'] = tuple(item.get('cor') or proxima_cor(lista))
        lista.append(novo)
    estado.acordes_fixados = lista[:MAX_NO_BRACO]
    _sincronizar(estado)
    return estado.acordes_fixados


# Nomes publicos usados pelo resto do programa
tratar_evento_paleta = tratar_evento
desenhar_arrasto_acorde = desenhar_arrasto
