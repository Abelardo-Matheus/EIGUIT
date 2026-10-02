# -*- coding: utf-8 -*-
"""
ANALISE DE IA > Analisador  (cartao "Analisador IA")

Compara o TIMBRE do seu preset (o som que sai da pedaleira) com o timbre da
guitarra (ou do baixo/violao) numa musica de referencia e diz o que falta,
o que sobra e o que esta diferente: ganho, EQ, compressao, modulacao,
ambiencia e os demais efeitos do estudo de Pedais. Nao confere notas.

Assistente em cinco etapas (a barra do topo navega entre elas):
    1 Audio        entrada (pedaleira) e canal, saida, taxa, buffer, medidor,
                   monitoramento e calibracao de latencia
    2 Instrumento  guitarra / violao / baixo, captador, afinacao e a
                   calibracao opcional do som limpo
    3 Musica       biblioteca local, importar arquivo, pesquisa online
                   opcional, tipo (isolado/mix), separacao, trecho, BPM, MIDI
    4 Gravacao     contagem, metronomo, repeticoes; toca a musica e grava a
                   pedaleira ao mesmo tempo; takes
    5 Resultado    indices, sugestoes (Falta/Sobra/Ajuste/Timbre base),
                   graficos, A/B, medidas, historico, preset sugerido
                   (Fase 2), o detector treinado localmente (Fase 3) e a
                   aba Pedaleira (le o preset da pedaleira, aplica as
                   sugestoes e salva o arquivo para importar; pedaleiras/)

Tudo que e pesado (listar/abrir dispositivo, gravar, baixar, separar,
analisar, buscar preset, treinar) roda em thread (audio/referencia.TarefaFundo
ou GravadorPlayAlong), com barra de progresso e Cancelar. Sem chave de API:
a unica rede e a pesquisa/download opcional de audio.

Integracao: segue o ciclo dos estudos (GerenciadorEstudos):
    desenhar(tela, estado, fontes, meio_x, meio_y, cam_x, cam_y)
    tratar_eventos(evento, pos, estado) -> bool
    parar()
Teclas: Espaco toca/para, A alterna A/B, Enter avanca, Esc sai.
"""
import math
import os
import sys
import time

import numpy as np
import pygame

from audio import analise_timbre as at
from audio import dispositivos as disp
from audio import gravacao_playalong as gp
from audio import referencia as refm
from audio import sugestoes_timbre as st
from config.design_system import TEMA, ds
from core.i18n import _t

ETAPAS = [('audio', 'Áudio'), ('instrumento', 'Instrumento'), ('musica', 'Música'),
          ('gravacao', 'Gravação'), ('resultado', 'Resultado')]
ABAS_RESULTADO = [('sugestoes', 'Sugestões'), ('graficos', 'Gráficos'), ('medidas', 'Medidas'),
                  ('historico', 'Histórico'), ('preset', 'Preset sugerido'), ('detector', 'Detector local'),
                  ('pedaleira', 'Pedaleira')]
COR_TIPO = {'falta': 'alerta', 'sobra': 'aviso', 'ajuste': 'primaria_clara', 'timbre': 'roxo'}
NOMES_CAPTADOR = [('single', 'Single-coil'), ('humbucker', 'Humbucker'), ('p90', 'P90'),
                  ('ativo', 'Ativo'), ('piezo', 'Piezo'), ('nenhum', 'Não sei')]


def _quebrar(texto, fonte, largura):
    palavras, linhas, atual = str(texto).split(' '), [], ''
    for p in palavras:
        teste = f'{atual} {p}'.strip()
        if fonte.size(teste)[0] <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def _paragrafo(tela, texto, fonte, x, y, largura, cor, max_linhas=None, entre=3):
    linhas = _quebrar(texto, fonte, largura)
    if max_linhas is not None and len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        linhas[-1] = ds.truncar(linhas[-1] + ' ...', fonte, largura)
    h = fonte.get_height() + entre
    for i, linha in enumerate(linhas):
        ds.texto_em(tela, linha, fonte, (x, y + i * h), cor)
    return y + len(linhas) * h


def _cor(nome):
    return getattr(TEMA, nome, TEMA.acento)


def _fmt_tempo(s):
    s = max(0.0, float(s))
    return f'{int(s // 60)}:{s % 60:04.1f}'


class AnalisadorIA:
    """
        Como funciona: guarda o estado das cinco etapas; a cada quadro desenha
        a etapa atual e registra os "alvos" clicaveis (rect, acao, dado); o
        clique procura o alvo e chama a acao. Tarefas longas ficam em
        self.tarefa (uma por vez) e o resultado e aplicado quando fica pronto.
        Para que serve: a area "Analisador IA".
        Onde e usada: core/modulos/modulos_estudos.GerenciadorEstudos.
    """

    def __init__(self):
        self.etapa = 0
        self.cfg = disp.carregar_config()
        self.cfg.restaurar_latencia()
        self.lista = None
        self.medidor = disp.MedidorEntrada()
        self.monitorar = False
        self.player = gp.ReprodutorAB()
        self.gravador = gp.GravadorPlayAlong()
        self.tarefa = None                      # (TarefaFundo, ao_terminar)
        self.aviso = ('', None, 0.0)
        self._fontes = {}
        self._alvos = []
        self._areas_rolagem = []
        self._clip_lista = None
        self.scroll = {}
        self.arrasto = None
        self._motor_pausado = None
        self._estado = None
        self._mouse = (0, 0)
        # instrumento
        self.perfil_guitarra = None
        self._carregar_perfil_guitarra()
        # musica
        self.busca = ''
        self.busca_foco = False
        self.itens = []
        self.online = []
        self.ref = None
        self.ref_audio = None
        self.ref_sr = 44100
        self.forma = None
        self.sel = [0.0, 1.0]
        self.bpm = None
        self.bpm_fonte = ''
        self.midi = None
        self.compassos = None
        self.desloc_midi = 0.0
        self.tocando_ref = False
        # gravacao
        self.opc = {'volume': 0.8, 'contagem': 1, 'metronomo': False, 'repeticoes': 2}
        self.takes = []
        self.take_sel = None
        # resultado
        self.analise = None
        self.analise_take = None
        self.aba = 'sugestoes'
        self.preset = None
        self.historico = []
        self.ab = 'ref'
        self.modelo_info = None
        self._pedaleira = None                  # aba "Pedaleira" (Analisador/painel_pedaleira.py)
        self._atualizar_itens()
        # recursos opcionais checados em segundo plano (o Demucs pode estar noutro venv)
        import threading
        threading.Thread(target=refm.demucs_disponivel, daemon=True).start()

    # ================================================================ util
    def _fonte(self, tamanho, negrito=True):
        chave = (tamanho, negrito)
        if chave not in self._fontes:
            self._fontes[chave] = pygame.font.SysFont('Arial', tamanho, bold=negrito)
        return self._fontes[chave]

    def avisar(self, texto, tipo='info', segundos=6.0):
        cor = {'erro': TEMA.alerta, 'ok': TEMA.verde, 'aviso': TEMA.aviso}.get(tipo, TEMA.acento)
        self.aviso = (texto, cor, time.time() + segundos)

    def _alvo(self, rect, acao, dado=None):
        self._alvos.append((pygame.Rect(rect), acao, dado))

    def _hover(self, rect):
        return pygame.Rect(rect).collidepoint(self._mouse)

    def _botao(self, tela, rect, texto, acao, dado=None, variante='secundario', ativo=False,
               habilitado=True, tamanho=12, cor=None):
        ds.botao(tela, rect, _t(texto), self._fonte(tamanho), variante=variante, ativo=ativo,
                 hover=habilitado and self._hover(rect), habilitado=habilitado, cor=cor)
        if habilitado:
            self._alvo(rect, acao, dado)
        return rect

    def _chips(self, tela, x, y, largura, opcoes, atual, acao, tamanho=11, cor=None):
        """Linha de chips (quebra linha se preciso). Devolve o y abaixo."""
        fonte = self._fonte(tamanho)
        x0 = x
        for valor, rotulo in opcoes:
            w = fonte.size(_t(rotulo))[0] + 22
            if x + w > x0 + largura:
                x = x0
                y += 30
            r = pygame.Rect(x, y, w, 26)
            ds.chip(tela, r, _t(rotulo), fonte, ativo=valor == atual, cor=cor)
            self._alvo(r, acao, valor)
            x += w + 6
        return y + 32

    def _cache(self, chave, funcao, validade=5.0):
        """Resultado guardado por alguns segundos (consultas ao PortAudio, imports opcionais...)."""
        memo = self.__dict__.setdefault('_memo_ui', {})
        agora = time.time()
        if chave not in memo or agora - memo[chave][0] > validade:
            memo[chave] = (agora, funcao())
        return memo[chave][1]

    def _ocupado(self):
        return self.tarefa is not None or self.gravador.estado == 'gravando'

    def _iniciar_tarefa(self, rotulo, funcao, ao_terminar, *args, **kwargs):
        if self.tarefa is not None:
            self.avisar('Espere a tarefa atual terminar (ou cancele).', 'aviso')
            return
        self.tarefa = (refm.TarefaFundo(rotulo, funcao, *args, **kwargs), ao_terminar)

    def _checar_tarefa(self):
        if self.tarefa is None:
            return
        t, ao_terminar = self.tarefa
        if not t.pronta:
            return
        self.tarefa = None
        if t.cancelar_evento.is_set():
            self.avisar(f'{t.rotulo}: cancelado.', 'aviso')
            return
        if t.erro:
            self.avisar(f'{t.rotulo}: {t.erro}', 'erro', 10)
            return
        try:
            ao_terminar(t.resultado)
        except Exception as erro:
            self.avisar(f'{t.rotulo}: {erro}', 'erro', 10)

    # ============================================================ ciclo
    def _pausar_motor_global(self, estado):
        """O afinador global segura a entrada: pausa enquanto o Analisador esta aberto."""
        motor = getattr(estado, 'motor_audio', None)
        if motor is not None and getattr(motor, 'ativo', False) and self._motor_pausado is None:
            try:
                motor.parar()
                self._motor_pausado = motor
            except Exception:
                pass

    def parar_audio(self):
        self.player.parar()
        self.tocando_ref = False
        self.medidor.parar()

    def parar(self):
        """Chamado ao sair: nada pode continuar tocando/gravando; o afinador volta."""
        self.parar_audio()
        self.gravador.cancelar()
        if self.tarefa is not None:
            self.tarefa[0].cancelar()
        disp.salvar_config(self.cfg)
        if self._motor_pausado is not None:
            try:
                self._motor_pausado.iniciar()
            except Exception:
                pass
            self._motor_pausado = None

    # ============================================================ etapa 1
    def atualizar_lista(self):
        self.lista = disp.listar_dispositivos()
        if self.lista.get('erro'):
            self.avisar(self.lista['erro'], 'erro', 10)
        problemas = disp.validar_config(self.cfg, self.lista) if not self.lista.get('erro') else []
        self._reiniciar_medidor()
        return problemas

    def _reiniciar_medidor(self):
        self.medidor.parar()
        if self.etapa != 0 or self.cfg.entrada_id is None or self._ocupado():
            return
        if not self.medidor.iniciar(self.cfg, monitorar=self.monitorar):
            if self.medidor.erro:
                self.avisar(self.medidor.erro, 'erro', 8)

    def escolher_entrada(self, item):
        self.cfg.entrada_id, self.cfg.entrada_nome = item['id'], item['nome']
        self.cfg.canais_entrada = item['canais_entrada']
        if self.cfg.canal_processado >= item['canais_entrada']:
            self.cfg.canal_processado = 0
        if self.cfg.canal_di is not None and self.cfg.canal_di >= item['canais_entrada']:
            self.cfg.canal_di = None
        taxas = disp.taxas_suportadas(item['id'], True, 1)
        if taxas and self.cfg.taxa not in taxas:
            self.cfg.taxa = 48000 if 48000 in taxas else taxas[0]
        self.cfg.restaurar_latencia()
        self._reiniciar_medidor()

    def escolher_saida(self, item):
        self.cfg.saida_id, self.cfg.saida_nome = item['id'], item['nome']
        self.cfg.restaurar_latencia()
        self._reiniciar_medidor()

    def calibrar(self, modo):
        if self.cfg.entrada_id is None or self.cfg.saida_id is None:
            self.avisar('Escolha a entrada e a saída antes de calibrar.', 'aviso')
            return
        self.medidor.parar()
        cfg = self.cfg

        def job(progresso, cancelar):
            cliques, tempos = disp.sinal_cliques(cfg.taxa, n=8 if modo == 'loopback' else 10,
                                                 intervalo=0.5 if modo == 'loopback' else 0.75)
            gravado, desloc = gp.BackendSoundDevice().executar(cliques, cfg, [cfg.canal_processado],
                                                               progresso, cancelar)
            return disp.medir_latencia(gravado[max(0, desloc):, 0], cfg.taxa, tempos, modo)

        def ok(res):
            ms, conf, texto = res
            if ms is None:
                self.avisar(f'Calibração falhou: {texto}', 'erro', 10)
            else:
                self.cfg.definir_latencia(ms)
                disp.salvar_config(self.cfg)
                self.avisar(f'Latência {ms:.0f} ms ({texto}; confiança {conf * 100:.0f}%). Salva para este '
                            'par de dispositivos.', 'ok' if conf > 0.5 else 'aviso', 10)
            self._reiniciar_medidor()
        self._iniciar_tarefa('Calibração de latência', job, ok)

    # ============================================================ etapa 2
    def _arquivo_perfil(self):
        pasta = os.path.join(disp.pasta_dados(), 'perfis')
        os.makedirs(pasta, exist_ok=True)
        return os.path.join(pasta, f'{self.cfg.instrumento}_{self.cfg.captador}')

    def _carregar_perfil_guitarra(self):
        import json
        try:
            with open(self._arquivo_perfil() + '.json', encoding='utf-8') as f:
                self.perfil_guitarra = json.load(f)
        except (OSError, ValueError):
            self.perfil_guitarra = None

    def calibrar_instrumento(self):
        if self.cfg.entrada_id is None:
            self.avisar('Configure a entrada na etapa 1 primeiro.', 'aviso')
            self.etapa = 0
            return
        cfg = self.cfg
        canal = cfg.canal_di if cfg.canal_di is not None else cfg.canal_processado
        base = self._arquivo_perfil()
        instrumento = cfg.instrumento
        self.medidor.parar()

        def job(progresso, cancelar):
            silencio = np.zeros((int(15 * cfg.taxa), 2), dtype=np.float32)
            gravado, desloc = gp.BackendSoundDevice().executar(silencio, cfg, [canal], progresso, cancelar)
            x = gravado[max(0, desloc):, 0]
            rms = float(np.sqrt(np.mean(x ** 2))) if x.size else 0.0
            if rms < 10 ** (-55 / 20):
                raise RuntimeError('Não chegou som: toque durante os 15 segundos (acordes e notas soltas).')
            at.salvar_wav(base + '.wav', x, cfg.taxa)
            perfil = at.perfil_timbre(x, cfg.taxa, at.carregar_config(instrumento), efeitos=False)
            import json
            with open(base + '.json', 'w', encoding='utf-8') as f:
                json.dump(perfil, f, ensure_ascii=False)
            return perfil

        def ok(perfil):
            self.perfil_guitarra = perfil
            self.avisar('Timbre base do instrumento salvo. Ele será usado para separar o que vem da '
                        'guitarra do que vem do preset.', 'ok', 8)
        self._iniciar_tarefa('Calibração do instrumento (toque 15 s com o som limpo)', job, ok)

    # ============================================================ etapa 3
    def _atualizar_itens(self):
        try:
            usuario = getattr(self._estado, 'usuario_id_logado', None)
            self.itens = refm.listar_biblioteca(self.busca, usuario=usuario)
        except Exception as erro:
            self.itens = []
            self.avisar(f'Biblioteca: {erro}', 'erro')

    def importar(self):
        caminho = refm.escolher_arquivo()
        if caminho:
            self._importar_caminho(caminho)

    def _importar_caminho(self, caminho):
        try:
            reg = refm.importar_arquivo(caminho, tipo='mix')
        except ValueError as erro:
            self.avisar(str(erro), 'erro')
            return
        self._atualizar_itens()
        self.selecionar(reg)

    def adicionar_pasta(self):
        pasta = refm.escolher_pasta()
        if pasta:
            refm.adicionar_pasta(pasta)
            self._atualizar_itens()
            self.avisar(f'Pasta adicionada: {pasta}', 'ok')

    def pesquisar_online(self):
        ok, msg = refm.yt_dlp_disponivel()
        if not ok:
            self.avisar(msg, 'aviso', 10)
            return
        if not self.busca.strip():
            self.avisar('Digite o nome da música (e do artista) para pesquisar.', 'aviso')
            return
        texto, instrumento = self.busca, self.cfg.instrumento

        def job(progresso, cancelar):
            return refm.pesquisar_online(texto, 8, instrumento, cancelar)

        def ok_(res):
            self.online = res
            self.scroll['lista'] = 0
            if not res:
                self.avisar('Nenhum resultado online.', 'aviso')
        self._iniciar_tarefa('Pesquisa online', job, ok_)

    def baixar(self, item):
        def job(progresso, cancelar):
            return refm.baixar(item['url'], item['titulo'], item['canal'],
                               'isolado' if item['isolada'] else None, progresso, cancelar)

        def ok(reg):
            self.online = []
            self._atualizar_itens()
            self.selecionar(reg)
        self._iniciar_tarefa('Baixando áudio', job, ok)

    def selecionar(self, item):
        if item.get('tipo') == 'partitura':
            self.midi = item.get('midi')
            self._carregar_midi()
            self.avisar('Partitura escolhida: ela dá os compassos e o BPM. Agora escolha (ou importe) o '
                        'ÁUDIO da música, que é de onde vem o timbre.', 'aviso', 10)
            return
        if not item.get('caminho') or not os.path.exists(item['caminho']):
            self.avisar('O arquivo dessa referência não existe mais.', 'erro')
            return
        self.parar_audio()
        reg = refm.registrar(item['caminho'], item.get('titulo'), item.get('artista', ''),
                             item.get('tipo', 'mix'), item.get('origem', 'arquivo'), item.get('url', ''),
                             item.get('midi') or self.midi, item.get('bpm'))

        def job(progresso, cancelar):
            progresso(0.2, 'Lendo o áudio...')
            x, sr = refm.carregar_audio(reg['caminho'])
            if x.size < sr:
                raise RuntimeError('O áudio tem menos de 1 segundo.')
            progresso(0.6, 'Detectando o BPM...')
            bpm, conf = refm.detectar_bpm(x[:int(60 * sr)], sr)
            return x, sr, bpm, conf

        def ok(res):
            x, sr, bpm, conf = res
            self.ref, self.ref_audio, self.ref_sr = reg, x, sr
            self.forma = refm.forma_de_onda(x, 900)
            dur = x.size / sr
            self.sel = [0.0, min(1.0, 20.0 / dur)]
            if reg.get('midi'):
                self.midi = reg['midi']
            if self.midi:
                self._carregar_midi()
            if not self.compassos:
                self.bpm = reg.get('bpm') or (round(bpm, 1) if bpm else None)
                self.bpm_fonte = 'detectado' if bpm else ''
            self.takes = []
            self.take_sel = None
            self.analise = None
            self.preset = None
            self.historico = st.listar_historico(reg['id'])
            self._atualizar_itens()
            self.avisar(f'Referência carregada: {reg["titulo"]} ({_fmt_tempo(dur)}). Escolha o trecho.', 'ok')
        self._iniciar_tarefa('Carregando referência', job, ok)

    def _carregar_midi(self):
        if not self.midi or not os.path.exists(self.midi):
            self.compassos = None
            return
        try:
            self.compassos, bpm = refm.compassos_do_midi(self.midi, self.desloc_midi)
            self.bpm, self.bpm_fonte = round(bpm, 1), 'MIDI'
            if self.ref:
                refm.atualizar(self.ref['id'], midi=self.midi, bpm=self.bpm)
        except Exception as erro:
            self.compassos = None
            self.avisar(f'Não consegui ler o MIDI: {erro}', 'erro')

    def associar_midi(self):
        caminho = refm.escolher_arquivo('Escolha o MIDI da música (estrutura, compassos e BPM)', midi=True)
        if caminho:
            self.midi = caminho
            self._carregar_midi()

    def mudar_tipo(self, tipo):
        if self.ref:
            self.ref = refm.atualizar(self.ref['id'], tipo=tipo) or self.ref

    def separar(self):
        ok, msg = refm.demucs_disponivel()
        if not ok:
            self.avisar(msg, 'aviso', 10)
            return
        reg, instrumento = self.ref, self.cfg.instrumento

        def job(progresso, cancelar):
            return refm.separar(reg, instrumento, progresso, cancelar)
        self._iniciar_tarefa('Separando a guitarra (Demucs, pode levar minutos)', job,
                             lambda novo: (self._atualizar_itens(), self.selecionar(novo)))

    def trecho(self):
        """(inicio_s, fim_s) da selecao."""
        if self.ref_audio is None:
            return 0.0, 0.0
        dur = self.ref_audio.size / self.ref_sr
        a, b = sorted(self.sel)
        return a * dur, b * dur

    def audio_trecho(self, sr=None):
        a, b = self.trecho()
        x = self.ref_audio[int(a * self.ref_sr):int(b * self.ref_sr)]
        if sr and int(sr) != int(self.ref_sr):
            x = at.reamostrar(x, self.ref_sr, sr)
        return x

    def selecionar_compassos(self, primeiro, ultimo):
        if not self.compassos or self.ref_audio is None:
            return
        dur = self.ref_audio.size / self.ref_sr
        primeiro = max(0, min(primeiro, len(self.compassos) - 1))
        ultimo = max(primeiro, min(ultimo, len(self.compassos) - 1))
        a = self.compassos[primeiro]['inicio_s']
        b = self.compassos[ultimo]['fim_s']
        self.sel = [float(np.clip(a / dur, 0, 1)), float(np.clip(b / dur, 0, 1))]

    def _compasso_em(self, t):
        if not self.compassos:
            return None
        for i, c in enumerate(self.compassos):
            if c['inicio_s'] <= t < c['fim_s']:
                return i
        return len(self.compassos) - 1 if t >= self.compassos[-1]['fim_s'] else 0

    def alternar_ref(self):
        if self.tocando_ref:
            self.player.parar()
            self.tocando_ref = False
            return
        if self.ref_audio is None:
            return
        self.player.carregar('trecho', self.audio_trecho(), self.ref_sr)
        self.tocando_ref = self.player.tocar('trecho', self.cfg.saida_id, loop=True)

    # ============================================================ etapa 4
    def gravar(self):
        if self.gravador.estado == 'gravando':
            self.gravador.cancelar()
            return
        problemas = disp.validar_config(self.cfg)
        if problemas:
            self.avisar(problemas[0], 'erro', 8)
            return
        if self.ref_audio is None:
            self.avisar('Escolha a música e o trecho (etapa 3).', 'aviso')
            return
        self.parar_audio()
        ref = self.audio_trecho(self.cfg.taxa)
        self.gravador.iniciar(ref, self.cfg, bpm=self.bpm, compassos_contagem=self.opc['contagem'],
                              batidas_compasso=(self.compassos[0]['batidas'] if self.compassos else 4),
                              metronomo=self.opc['metronomo'], repeticoes=self.opc['repeticoes'],
                              volume_musica=self.opc['volume'])

    def _checar_gravacao(self):
        if self.gravador.estado == 'pronto' and self.gravador.resultado is not None:
            take = self.gravador.resultado
            self.gravador.resultado = None
            self.gravador.estado = 'parado'
            take['numero'] = (max([t['numero'] for t in self.takes]) + 1) if self.takes else 1
            take['trecho'] = self.trecho()
            try:
                gp.salvar_take(take, self.ref['id'] if self.ref else None, take['numero'])
            except Exception:
                pass
            self.takes.append(take)
            self.take_sel = len(self.takes) - 1
            erros = [p for p in take['problemas'] if p[0] == 'erro']
            if erros:
                self.avisar(erros[0][1], 'erro', 10)
            elif take['problemas']:
                self.avisar(take['problemas'][0][1], 'aviso', 10)
            else:
                self.avisar(f'Take {take["numero"]} gravado. Ouça, grave outro ou vá para o Resultado.', 'ok')
        elif self.gravador.estado == 'erro':
            self.avisar(self.gravador.erro, 'erro', 10)
            self.gravador.estado = 'parado'

    def ouvir_take(self, i):
        take = self.takes[i]
        chave = f'take{i}'
        self.player.carregar(chave, take['audio'][:, 0], take['sr'])
        self.player.tocar(chave, self.cfg.saida_id, loop=False)

    def descartar_take(self, i):
        self.player.parar()
        self.takes.pop(i)
        if self.take_sel is not None and self.take_sel >= len(self.takes):
            self.take_sel = len(self.takes) - 1 if self.takes else None

    def take_valido(self):
        if self.take_sel is None or not self.takes:
            return None
        take = self.takes[self.take_sel]
        if any(p[0] == 'erro' for p in take['problemas']):
            return None
        return take

    # ============================================================ etapa 5
    def analisar(self):
        take = self.take_valido()
        if take is None:
            self.avisar('Grave (e escolha) uma tomada válida na etapa 4.', 'aviso')
            return
        separado = bool(self.ref and self.ref.get('tipo') == 'separado')
        instrumento, bpm = self.cfg.instrumento, self.bpm
        perfil_g, captador = self.perfil_guitarra, self.cfg.captador

        def job(progresso, cancelar):
            return st.analisar(take['referencia'], take['sr'], take['audio'][:, 0], take['sr'],
                               instrumento=instrumento, bpm=bpm, perfil_guitarra=perfil_g,
                               captador=captador if captador != 'nenhum' else None, separado=separado,
                               progresso=progresso, cancelar=cancelar)

        def ok(res):
            self.analise = res
            self.analise_take = take['numero']
            self.preset = None
            self.scroll['sugestoes'] = 0
            info = {'take': take['numero'], 'instrumento': instrumento, 'captador': captador}
            self.historico = st.salvar_historico(self.ref['id'] if self.ref else None, res['resultado'], info)
            self.player.carregar('ref', res['ref_preparada'] * 0.9 / (np.max(np.abs(res['ref_preparada'])) or 1),
                                 res['sr'])
            self.player.carregar('rec', res['rec_preparada'] * 0.9 / (np.max(np.abs(res['rec_preparada'])) or 1),
                                 res['sr'])
        self._iniciar_tarefa('Analisando o timbre', job, ok)

    def tocar_ab(self, qual):
        if self.analise is None:
            return
        if self.player.tocando and self.player.atual in ('ref', 'rec', 'preset', 'di'):
            if qual == self.player.atual:
                self.player.parar()
                return
            self.player.trocar(qual)
            self.ab = qual
            return
        self.player.tocar(qual, self.cfg.saida_id, loop=True)
        self.ab = qual

    def alternar_ab(self):
        if self.analise is None:
            return
        self.tocar_ab('rec' if self.ab == 'ref' else 'ref')

    def audio_limpo(self):
        """Som limpo do usuario para a Fase 2: canal DI do take ou a calibracao."""
        take = self.take_valido()
        if take is not None and take['audio'].ndim == 2 and take['audio'].shape[1] > 1:
            return take['audio'][:, 1], take['sr'], 'canal DI da tomada'
        wav = self._arquivo_perfil() + '.wav'
        if os.path.exists(wav):
            x, sr = at.ler_audio(wav)
            return at.para_mono(x), sr, 'calibração do instrumento'
        return None, None, ''

    def buscar_preset(self):
        if self.analise is None:
            return
        x, sr, origem = self.audio_limpo()
        if x is None:
            self.avisar('Para o preset sugerido é preciso o som limpo: grave com um canal DI (etapa 1) ou '
                        'faça a calibração do instrumento (etapa 2).', 'aviso', 10)
            return
        from audio import cadeia_pedais as cp
        perfil_ref, instrumento = self.analise['perfil_ref'], self.cfg.instrumento

        def job(progresso, cancelar):
            r = cp.buscar_preset(perfil_ref, x, sr, instrumento, progresso, cancelar)
            r['comparacao'] = st.comparar(perfil_ref, r['perfil'], at.carregar_config(instrumento))
            r['origem'] = origem
            return r

        def ok(r):
            self.preset = r
            self.player.carregar('preset', r['audio'] * 0.9 / (np.max(np.abs(r['audio'])) or 1), r['sr'])
            self.player.carregar('di', r['di'] * 0.9 / (np.max(np.abs(r['di'])) or 1), r['sr'])
            self.avisar('Preset sugerido pronto: ouça no seu som limpo e abra os pedais para ajustar.', 'ok')
        self._iniciar_tarefa('Buscando o preset (análise por síntese)', job, ok)

    def treinar_detector(self):
        from audio import treinar_detector as td
        ok, msg = td.sklearn_disponivel()
        if not ok:
            self.avisar(msg, 'aviso', 10)
            return

        def job(progresso, cancelar):
            return td.treinar(300, 0, progresso, cancelar)

        def ok_(metricas):
            self.modelo_info = None
            self.avisar(f'Detector treinado: acurácia {metricas["media_modelo"] * 100:.0f}% '
                        f'(regras sozinhas: {metricas["media_regras"] * 100:.0f}%).', 'ok', 10)
        self._iniciar_tarefa('Treinando o detector local', job, ok_)

    def abrir_pedal(self, pid, valores=None):
        """Leva para ESTUDOS > Pedais com o pedal aberto e os valores sugeridos."""
        estado = self._estado
        if estado is None or not pid:
            return
        self.player.parar()
        estado.pedido_pedal = {'id': pid, 'valores': dict(valores or {})}
        estado.voltar_analisador = True
        estado.estudo_ativo = 'Pedais de Efeito'

    def exportar(self):
        if self.analise is None:
            return
        res = self.analise['resultado']
        pasta = os.path.join(disp.pasta_dados(), 'relatorios')
        os.makedirs(pasta, exist_ok=True)
        titulo = (self.ref or {}).get('titulo', 'referencia')
        nome = ''.join(c if c.isalnum() else '_' for c in titulo)[:40] + time.strftime('_%Y%m%d_%H%M')
        a, b = self.trecho()
        info = {'Música': titulo, 'Trecho': f'{_fmt_tempo(a)} - {_fmt_tempo(b)}',
                'Instrumento': self.cfg.instrumento, 'Take': self.analise_take,
                'BPM': self.bpm or '-', 'Data': time.strftime('%d/%m/%Y %H:%M')}
        md = st.relatorio_markdown(res, 'Analisador IA - relatório de timbre', info)
        if self.preset:
            from audio import cadeia_pedais as cp
            md += '\n## Preset sugerido\n\n' + cp.descrever(self.preset['cadeia']) + '\n'
        caminho_md = os.path.join(pasta, nome + '.md')
        with open(caminho_md, 'w', encoding='utf-8') as f:
            f.write(md)
        caminho_pdf = os.path.join(pasta, nome + '.pdf')
        try:
            self._exportar_pdf(caminho_pdf, info)
        except Exception:
            caminho_pdf = None
        self.avisar(f'Relatório salvo em {caminho_md}' + (' (e PDF)' if caminho_pdf else ''), 'ok', 12)
        try:
            if sys.platform.startswith('win'):
                os.startfile(pasta)                         # type: ignore[attr-defined]
        except Exception:
            pass

    # ================================================================ desenho
    def desenhar(self, tela, estado, fontes, meio_x, meio_y, cam_x, cam_y):
        """
            Como funciona: aplica o que ficou pronto (tarefa, gravacao), zera
            os alvos e desenha barra de etapas, a etapa atual e o rodape.
            Para que serve: tela principal do Analisador.
            Onde e usada: GerenciadorEstudos, a cada quadro.
        """
        self._estado = estado
        self._pausar_motor_global(estado)
        self._checar_tarefa()
        self._checar_gravacao()
        if self.lista is None:
            self.atualizar_lista()
        self._mouse = pygame.mouse.get_pos()
        self._alvos = []
        self._areas_rolagem = []
        largura = getattr(estado, 'LARGURA_TELA', 1280)
        altura = getattr(estado, 'ALTURA_TELA', 720)
        area = pygame.Rect(int(cam_x + 40), int(cam_y + 56), int(largura - 80), int(altura - 130))
        self.area = area
        ds.painel(tela, area, None, None, acento=TEMA.acento, alpha=235)
        interno = area.inflate(-ds.ESPACO_XL * 2, -ds.ESPACO_LG * 2)
        y = self._desenhar_etapas(tela, interno)
        rodape = 44
        conteudo = pygame.Rect(interno.x, y + 8, interno.width, interno.bottom - y - 8 - rodape)
        desenho = [self._etapa_audio, self._etapa_instrumento, self._etapa_musica,
                   self._etapa_gravacao, self._etapa_resultado][self.etapa]
        clip = tela.get_clip()
        tela.set_clip(conteudo.clip(clip) if clip else conteudo)
        try:
            desenho(tela, conteudo)
        finally:
            tela.set_clip(clip)
        self._desenhar_rodape(tela, pygame.Rect(interno.x, interno.bottom - rodape + 6, interno.width, rodape - 6))
        if self.tarefa is not None:
            self._desenhar_tarefa(tela, area)

    def _desenhar_etapas(self, tela, r):
        fonte = self._fonte(13)
        ds.texto_em(tela, _t('Analisador IA'), self._fonte(20), (r.x, r.y), TEMA.acento)
        ds.texto_em(tela, _t('compare o timbre do seu preset com o da música'), self._fonte(11, False),
                    (r.x, r.y + 26), TEMA.texto_suave)
        n = len(ETAPAS)
        larg = min(170, (r.width - 360) // n)
        x = r.right - n * (larg + 6)
        for i, (chave, nome) in enumerate(ETAPAS):
            rr = pygame.Rect(x + i * (larg + 6), r.y + 4, larg, 34)
            atual = i == self.etapa
            feito = self._etapa_pronta(i)
            cor = TEMA.acento if atual else (TEMA.verde if feito else TEMA.borda)
            ds.superficie_translucida(tela, rr, ds.misturar(TEMA.superficie_alt, cor, 0.25 if atual else 0.08),
                                      235, ds.RAIO_MD, cor, 2 if atual else 1)
            rot = ds.texto_em(tela, f'{i + 1}  {_t(nome)}', fonte, rr.center,
                              TEMA.texto if atual else TEMA.texto_suave, ancora='center', largura_max=rr.width - 30)
            if feito and not atual:                  # marca de "feito" (desenhada: nem toda fonte tem o glifo)
                cx, cy = rot.x - 12, rr.centery
                pygame.draw.lines(tela, TEMA.verde, False, [(cx - 5, cy), (cx - 1, cy + 4), (cx + 6, cy - 5)], 3)
            if self._pode_ir(i):
                self._alvo(rr, 'etapa', i)
        return r.y + 48

    def _etapa_pronta(self, i):
        if i == 0:
            return self.cfg.entrada_id is not None and self.cfg.saida_id is not None
        if i == 1:
            return bool(self.cfg.instrumento)
        if i == 2:
            return self.ref_audio is not None and (self.trecho()[1] - self.trecho()[0]) >= 2.0
        if i == 3:
            return self.take_valido() is not None
        return self.analise is not None

    def _pode_ir(self, i):
        if self._ocupado():
            return False
        return all(self._etapa_pronta(k) for k in range(i))

    def ir_para(self, i):
        if not self._pode_ir(i):
            faltando = next(k for k in range(i) if not self._etapa_pronta(k))
            self.avisar(f'Complete a etapa {faltando + 1} ({ETAPAS[faltando][1]}) primeiro.', 'aviso')
            return
        self.parar_audio()
        self.etapa = i
        disp.salvar_config(self.cfg)
        if i == 0:
            self._reiniciar_medidor()
        if i == 4 and self.analise is None and self.take_valido() is not None:
            self.analisar()

    def _desenhar_rodape(self, tela, r):
        texto, cor, ate = self.aviso
        if texto and time.time() < ate:
            _paragrafo(tela, texto, self._fonte(12, False), r.x + 110, r.y + 2, r.width - 330, cor, max_linhas=2)
        if self.etapa > 0:
            self._botao(tela, pygame.Rect(r.x, r.y, 100, 32), '< Voltar', 'etapa', self.etapa - 1,
                        habilitado=not self._ocupado())
        if self.etapa < len(ETAPAS) - 1:
            pode = self._pode_ir(self.etapa + 1)
            self._botao(tela, pygame.Rect(r.right - 200, r.y, 200, 32),
                        f'{ETAPAS[self.etapa + 1][1]} >', 'etapa', self.etapa + 1, variante='primario',
                        habilitado=pode, tamanho=13)

    def _desenhar_tarefa(self, tela, area):
        t, _ = self.tarefa
        caixa = pygame.Rect(0, 0, min(620, area.width - 80), 116)
        caixa.center = area.center
        ds.sombra(tela, caixa)
        ds.superficie_translucida(tela, caixa, TEMA.superficie, 250, ds.RAIO_LG, TEMA.acento, 2)
        ds.texto_em(tela, _t(t.rotulo), self._fonte(15), (caixa.x + 20, caixa.y + 16), TEMA.texto,
                    largura_max=caixa.width - 40)
        ds.texto_em(tela, _t(t.mensagem), self._fonte(11, False), (caixa.x + 20, caixa.y + 40),
                    TEMA.texto_suave, largura_max=caixa.width - 40)
        barra = pygame.Rect(caixa.x + 20, caixa.y + 64, caixa.width - 160, 10)
        if t.progresso > 0:
            ds.trilho(tela, barra, t.progresso)
        else:                                   # indeterminado: faixa que anda
            ds.trilho(tela, barra, 0.0)
            f = (time.time() * 0.6) % 1.0
            pygame.draw.rect(tela, TEMA.acento, (barra.x + int(f * (barra.width - 60)), barra.y, 60, barra.height),
                             border_radius=5)
        self._botao(tela, pygame.Rect(caixa.right - 120, caixa.y + 54, 100, 30), 'Cancelar', 'cancelar_tarefa',
                    variante='perigo')

    # ------------------------------------------------------------ listas
    def _lista(self, tela, r, chave, itens, desenhar_item, altura_item=40, vazio=''):
        """Lista com rolagem (clip + barra), no mesmo estilo do estudo de Pedais."""
        ds.superficie_translucida(tela, r, TEMA.superficie_alt, 200, ds.RAIO_MD, TEMA.borda, 1)
        if not itens:
            if vazio:
                _paragrafo(tela, _t(vazio), self._fonte(12, False), r.x + 12, r.y + 12, r.width - 24,
                           TEMA.texto_apagado)
            return
        total = len(itens) * altura_item
        maximo = max(0, total - r.height + 8)
        self.scroll[chave] = max(0, min(self.scroll.get(chave, 0), maximo))
        self._areas_rolagem.append((r, chave, maximo))
        clip = tela.get_clip()
        tela.set_clip(r.clip(clip) if clip else r)
        self._clip_lista = r
        y = r.y + 4 - self.scroll[chave]
        try:
            for i, item in enumerate(itens):
                rr = pygame.Rect(r.x + 4, y, r.width - 16, altura_item - 4)
                if rr.bottom >= r.y and rr.y <= r.bottom:
                    desenhar_item(tela, rr, item, i)
                y += altura_item
        finally:
            tela.set_clip(clip)
            self._clip_lista = None
        if maximo > 0:
            ds.barra_rolagem(tela, r.right - 8, r.y + 2, r.height - 4, r.height / total,
                             self.scroll[chave] / maximo, largura=6)

    def _item_linha(self, tela, rr, titulo, sub, ativo, acao, dado, direita='', cor_direita=None):
        cor = TEMA.acento if ativo else TEMA.borda
        ds.superficie_translucida(tela, rr, ds.misturar(TEMA.superficie, TEMA.acento,
                                                        0.22 if ativo else (0.1 if self._hover(rr) else 0)),
                                  230, ds.RAIO_SM, cor, 1)
        ds.texto_em(tela, titulo, self._fonte(12), (rr.x + 10, rr.y + 4), TEMA.texto,
                    largura_max=rr.width - 20 - (110 if direita else 0))
        if sub:
            ds.texto_em(tela, sub, self._fonte(10, False), (rr.x + 10, rr.y + 20), TEMA.texto_apagado,
                        largura_max=rr.width - 20 - (110 if direita else 0))
        if direita:
            ds.texto_em(tela, direita, self._fonte(10), (rr.right - 10, rr.centery), cor_direita or TEMA.texto_suave,
                        ancora='midright', largura_max=110)
        vis = rr.clip(self._clip_lista) if self._clip_lista is not None else rr
        if vis.width > 0 and vis.height > 0:
            self._alvo(vis, acao, dado)

    # ============================================================ ETAPA 1
    def _etapa_audio(self, tela, r):
        ok, msg = self._cache('sd', disp.disponivel, 60.0)
        col = (r.width - ds.ESPACO_XL) // 2
        esq = pygame.Rect(r.x, r.y, col, r.height)
        dir_ = pygame.Rect(esq.right + ds.ESPACO_XL, r.y, r.width - col - ds.ESPACO_XL, r.height)
        f11 = self._fonte(11)
        if not ok:
            _paragrafo(tela, _t(msg), self._fonte(13, False), r.x, r.y, r.width, TEMA.alerta)
            return
        lista = self.lista or {'entradas': [], 'saidas': []}
        y = esq.y
        ds.rotulo_secao(tela, esq.x, y, _t('Entrada (a pedaleira)'), f11)
        self._botao(tela, pygame.Rect(esq.right - 130, y - 6, 130, 24), 'Atualizar lista', 'atualizar_lista',
                    tamanho=11)
        y += 22
        h_lista = max(90, (esq.height - 90) // 2)

        def item_ent(t, rr, it, i):
            sub = f"{it['api']} · {it['canais_entrada']} canal(is) · {it['taxa_padrao']} Hz"
            self._item_linha(t, rr, it['nome'], sub, it['nome'] == self.cfg.entrada_nome, 'entrada', it)
        self._lista(tela, pygame.Rect(esq.x, y, esq.width, h_lista), 'entradas', lista['entradas'], item_ent,
                    vazio='Nenhuma entrada encontrada. Conecte a pedaleira (USB) e clique em Atualizar lista.')
        y += h_lista + 14
        ds.rotulo_secao(tela, esq.x, y, _t('Saída (onde você ouve a música)'), f11)
        y += 22

        def item_sai(t, rr, it, i):
            sub = f"{it['api']} · {it['canais_saida']} canal(is)"
            self._item_linha(t, rr, it['nome'], sub, it['nome'] == self.cfg.saida_nome, 'saida', it)
        self._lista(tela, pygame.Rect(esq.x, y, esq.width, esq.bottom - y), 'saidas', lista['saidas'], item_sai,
                    vazio='Nenhuma saída encontrada.')

        # ---- coluna direita: canais, taxa, buffer, medidor, monitor, latencia
        y = dir_.y
        n = max(1, int(self.cfg.canais_entrada or 1))
        ds.rotulo_secao(tela, dir_.x, y, _t('Canal com o som do preset'), f11)
        y = self._chips(tela, dir_.x, y + 20, dir_.width, [(c, f'Canal {c + 1}') for c in range(n)],
                        self.cfg.canal_processado, 'canal_proc')
        ds.rotulo_secao(tela, dir_.x, y, _t('Canal DI limpo (opcional, para o preset sugerido)'), f11)
        y = self._chips(tela, dir_.x, y + 20, dir_.width,
                        [(None, 'Nenhum')] + [(c, f'Canal {c + 1}') for c in range(n) if c != self.cfg.canal_processado],
                        self.cfg.canal_di, 'canal_di')
        ds.rotulo_secao(tela, dir_.x, y, _t('Taxa de amostragem'), f11)
        taxas = self._cache(('taxas', self.cfg.entrada_id), lambda: disp.taxas_suportadas(
            self.cfg.entrada_id, True, 1), 60.0) if self.cfg.entrada_id is not None else []
        taxas = taxas or list(disp.TAXAS_COMUNS[:2])
        yy = self._chips(tela, dir_.x, y + 20, dir_.width // 2 - 10, [(t, f'{t / 1000:g} kHz') for t in taxas],
                         self.cfg.taxa, 'taxa')
        ds.rotulo_secao(tela, dir_.x + dir_.width // 2, y, _t('Buffer'), f11)
        y2 = self._chips(tela, dir_.x + dir_.width // 2, y + 20, dir_.width // 2,
                         [(b, str(b)) for b in (128, 256, 512, 1024)], self.cfg.buffer, 'buffer')
        y = max(yy, y2)

        # medidor
        ds.rotulo_secao(tela, dir_.x, y, _t('Nível de entrada'), f11)
        y += 20
        niveis = self.medidor.niveis() if self.medidor.ativo else []
        for c in range(min(n, 4)):
            barra = pygame.Rect(dir_.x + 70, y + 3, dir_.width - 160, 12)
            ds.texto_em(tela, f'{_t("Canal")} {c + 1}', self._fonte(10), (dir_.x, y + 1),
                        TEMA.texto if c == self.cfg.canal_processado else TEMA.texto_apagado)
            pico, rms, clip, fraco = niveis[c] if c < len(niveis) else (-90, -90, False, True)
            pct = np.clip((pico + 60) / 60, 0, 1)
            cor = TEMA.alerta if clip else (TEMA.aviso if pico > -6 else TEMA.verde)
            ds.trilho(tela, barra, pct, cor=cor)
            pct_rms = np.clip((rms + 60) / 60, 0, 1)
            x_rms = barra.x + int(barra.width * pct_rms)
            pygame.draw.line(tela, TEMA.texto, (x_rms, barra.y - 2), (x_rms, barra.bottom + 2), 2)
            estado_txt = 'CLIP!' if clip else ('fraco' if fraco and self.medidor.ativo else f'{pico:.0f} dB')
            ds.texto_em(tela, _t(estado_txt), self._fonte(10), (barra.right + 8, y + 1),
                        TEMA.alerta if clip else (TEMA.aviso if fraco else TEMA.texto_suave))
            y += 20
        if not self.medidor.ativo:
            ds.texto_em(tela, _t(self.medidor.erro or 'Escolha a entrada para ver o nível.'), self._fonte(10, False),
                        (dir_.x, y), TEMA.texto_apagado, largura_max=dir_.width)
            y += 16
        y += 6
        rr = pygame.Rect(dir_.x, y, 46, 24)
        ds.interruptor(tela, rr, self.monitorar)
        self._alvo(rr, 'monitor')
        ds.texto_em(tela, _t('Ouvir a entrada (monitoramento)'), self._fonte(12), (rr.right + 10, rr.centery),
                    TEMA.texto, ancora='midleft')
        y += 28
        y = _paragrafo(tela, _t('Pelo computador o monitoramento tem atraso: prefira a saída de fone da própria '
                                'pedaleira para tocar.'), self._fonte(10, False), dir_.x, y, dir_.width,
                       TEMA.texto_apagado) + 8

        # latencia
        ds.rotulo_secao(tela, dir_.x, y, _t('Latência de ida e volta'), f11)
        y += 22
        barra = pygame.Rect(dir_.x, y + 8, dir_.width - 120, ds.ALTURA_TRILHO)
        ds.slider(tela, barra, self.cfg.latencia_ms / 300.0, valor=f'{self.cfg.latencia_ms:.0f} ms',
                  fonte=self._fonte(12))
        self._alvo(barra.inflate(16, 22), 'latencia_slider', barra)
        y += 30
        meia = (dir_.width - 8) // 2
        self._botao(tela, pygame.Rect(dir_.x, y, meia, 28), 'Calibrar (cabo/loopback)', 'calibrar', 'loopback',
                    habilitado=not self._ocupado(), tamanho=11)
        self._botao(tela, pygame.Rect(dir_.x + meia + 8, y, meia, 28), 'Calibrar (tocar junto)', 'calibrar',
                    'tocar', habilitado=not self._ocupado(), tamanho=11)
        y += 34
        _paragrafo(tela, _t('Loopback: ligue a saída na entrada (ou aproxime o microfone da caixa) e a '
                            'aplicação mede o eco de 8 cliques. Tocar junto: palhete uma nota em cada clique. '
                            'O valor fica salvo para este par de dispositivos.'),
                   self._fonte(10, False), dir_.x, y, dir_.width, TEMA.texto_apagado)

    # ============================================================ ETAPA 2
    def _etapa_instrumento(self, tela, r):
        f11 = self._fonte(11)
        col = (r.width - ds.ESPACO_XL) // 2
        esq = pygame.Rect(r.x, r.y, col, r.height)
        dir_ = pygame.Rect(esq.right + ds.ESPACO_XL, r.y, r.width - col - ds.ESPACO_XL, r.height)
        y = esq.y
        ds.rotulo_secao(tela, esq.x, y, _t('Instrumento'), f11)
        y = self._chips(tela, esq.x, y + 20, esq.width, self._cache('instr', at.listar_instrumentos, 60.0),
                        self.cfg.instrumento,
                        'instrumento', tamanho=13)
        cfg_i = at.carregar_config(self.cfg.instrumento)
        faixa = cfg_i['bandas_macro']
        texto = ', '.join(f"{cfg_i['nomes_bandas'][k]} {a:g}-{b:g} Hz" for k, (a, b) in faixa.items())
        y = _paragrafo(tela, _t('Bandas usadas na análise: ') + texto, self._fonte(10, False), esq.x, y,
                       esq.width, TEMA.texto_apagado) + 12
        ds.rotulo_secao(tela, esq.x, y, _t('Tipo de captador (opcional)'), f11)
        y = self._chips(tela, esq.x, y + 20, esq.width, NOMES_CAPTADOR, self.cfg.captador, 'captador')
        ds.rotulo_secao(tela, esq.x, y, _t('Afinação'), f11)
        y = self._chips(tela, esq.x, y + 20, esq.width, [(a, a) for a in cfg_i['afinacoes']], self.cfg.afinacao,
                        'afinacao')
        _paragrafo(tela, _t('O captador e a afinação ajudam a não culpar o preset por diferenças que vêm da '
                            'guitarra (ex.: o brilho natural de um single-coil).'),
                   self._fonte(11, False), esq.x, y + 4, esq.width, TEMA.texto_suave)

        y = dir_.y
        ds.rotulo_secao(tela, dir_.x, y, _t('Calibração do instrumento (recomendada)'), f11)
        y += 22
        y = _paragrafo(tela, _t('Grave ~15 s do instrumento LIMPO, sem efeitos (desligue os pedais ou use o canal '
                                'DI): acordes e notas soltas. Esse timbre base separa o que vem da sua guitarra do '
                                'que vem do preset e é o som usado no "preset sugerido".'),
                       self._fonte(12, False), dir_.x, y, dir_.width, TEMA.texto_suave) + 10
        self._botao(tela, pygame.Rect(dir_.x, y, 240, 34), 'Gravar 15 s do som limpo', 'calibrar_instr',
                    variante='primario', habilitado=not self._ocupado() and self.cfg.entrada_id is not None)
        y += 46
        if self.perfil_guitarra:
            ds.texto_em(tela, _t('Timbre base salvo para este instrumento/captador:'), self._fonte(12),
                        (dir_.x, y), TEMA.verde)
            y += 22
            modelo = cfg_i.get('modelo_di_db') or {}
            desvio = st._desvio_guitarra(cfg_i, self.perfil_guitarra, None)
            for chave, nome in cfg_i['nomes_bandas'].items():
                d = desvio.get(chave)
                barra = pygame.Rect(dir_.x + 130, y + 3, dir_.width - 200, 10)
                ds.texto_em(tela, _t(nome), self._fonte(10), (dir_.x, y), TEMA.texto_suave)
                pygame.draw.line(tela, TEMA.borda, (barra.centerx, barra.y - 2), (barra.centerx, barra.bottom + 2), 1)
                if d is not None:
                    w = int(np.clip(d / 12.0, -1, 1) * barra.width / 2)
                    rect = pygame.Rect(min(barra.centerx, barra.centerx + w), barra.y, abs(w), barra.height)
                    pygame.draw.rect(tela, TEMA.acento if d >= 0 else TEMA.aviso, rect, border_radius=3)
                    ds.texto_em(tela, f'{d:+.0f} dB', self._fonte(10), (barra.right + 8, y), TEMA.texto_suave)
                y += 18
            if not modelo:
                ds.texto_em(tela, _t('(sem modelo de referência para este instrumento: vale só o captador)'),
                            self._fonte(10, False), (dir_.x, y + 4), TEMA.texto_apagado)
        else:
            ds.texto_em(tela, _t('Ainda sem calibração para este instrumento/captador.'), self._fonte(11, False),
                        (dir_.x, y), TEMA.texto_apagado)

    # ============================================================ ETAPA 3
    def _etapa_musica(self, tela, r):
        f11 = self._fonte(11)
        larg_esq = int(r.width * 0.42)
        esq = pygame.Rect(r.x, r.y, larg_esq, r.height)
        dir_ = pygame.Rect(esq.right + ds.ESPACO_XL, r.y, r.width - larg_esq - ds.ESPACO_XL, r.height)
        # ---- busca
        y = esq.y
        caixa = pygame.Rect(esq.x, y, esq.width - 90, 32)
        ds.caixa_texto(tela, caixa, self.busca, self._fonte(13, False), focado=self.busca_foco,
                       placeholder=_t('Título ou artista...'))
        self._alvo(caixa, 'foco_busca')
        self._botao(tela, pygame.Rect(caixa.right + 6, y, 84, 32), 'Buscar', 'buscar', variante='primario')
        y += 40
        ok_online, msg_online = self._cache('ytdlp', refm.yt_dlp_disponivel, 30.0)
        terco = (esq.width - 12) // 3
        self._botao(tela, pygame.Rect(esq.x, y, terco, 28), 'Importar arquivo', 'importar', tamanho=11)
        self._botao(tela, pygame.Rect(esq.x + terco + 6, y, terco, 28), 'Adicionar pasta', 'add_pasta', tamanho=11)
        self._botao(tela, pygame.Rect(esq.x + 2 * (terco + 6), y, terco, 28), 'Pesquisar online',
                    'online', habilitado=ok_online and not self._ocupado(), tamanho=11)
        y += 34
        if not ok_online:
            y = _paragrafo(tela, _t(msg_online), self._fonte(10, False), esq.x, y, esq.width, TEMA.texto_apagado,
                           max_linhas=2) + 4
        itens = [('online', it) for it in self.online] + [('local', it) for it in self.itens]

        def item(t, rr, par, i):
            tipo, it = par
            if tipo == 'online':
                dur = _fmt_tempo(it['duracao']) if it['duracao'] else ''
                sub = f"{it['canal']} · {dur}" + ('  · guitarra isolada' if it['isolada'] else '')
                self._item_linha(t, rr, it['titulo'], sub, False, 'baixar', it, 'baixar ↓',
                                 TEMA.verde if it['isolada'] else TEMA.acento)
            else:
                nomes = {'isolado': 'isolado', 'mix': 'mix completo', 'separado': 'separado (Demucs)',
                         'partitura': 'partitura (só estrutura)'}
                sub = ' · '.join(v for v in (it.get('artista'), nomes.get(it.get('tipo'), ''),
                                             'BPM %g' % it['bpm'] if it.get('bpm') else '') if v)
                ativo = self.ref is not None and it.get('id') == self.ref.get('id')
                self._item_linha(t, rr, it.get('titulo', ''), sub, ativo, 'escolher_ref', it,
                                 'MIDI' if it.get('tipo') == 'partitura' else '')
        self._lista(tela, pygame.Rect(esq.x, y, esq.width, esq.bottom - y - 42), 'lista', itens, item, 40,
                    vazio='Nada por aqui ainda. Importe um áudio (MP3, WAV, FLAC, OGG), adicione uma pasta '
                          'com áudios de referência ou pesquise online.')
        _paragrafo(tela, _t(refm.AVISO_DOWNLOAD), self._fonte(9, False), esq.x, esq.bottom - 36, esq.width,
                   TEMA.texto_apagado, max_linhas=3, entre=1)

        # ---- referencia escolhida
        y = dir_.y
        if self.ref is None or self.ref_audio is None:
            ds.cartao_vazio(tela, pygame.Rect(dir_.x, y, dir_.width, 90),
                            _t('Escolha a música de referência na lista (ou importe um arquivo).'), self._fonte(13))
            y += 104
            _paragrafo(tela, _t('Dica: a referência ideal é a guitarra isolada da música ("isolated guitar", '
                                'stem). Com a mixagem completa, os outros instrumentos atrapalham: use a '
                                'separação (Demucs) se estiver instalada. O MIDI da música é opcional e só serve '
                                'para escolher o trecho por compassos: timbre vem sempre do áudio.'),
                       self._fonte(11, False), dir_.x, y, dir_.width, TEMA.texto_suave)
            if self.midi:
                ds.texto_em(tela, _t('MIDI escolhido: ') + os.path.basename(self.midi), self._fonte(11),
                            (dir_.x, y + 90), TEMA.verde)
            return
        ds.texto_em(tela, self.ref.get('titulo', ''), self._fonte(16), (dir_.x, y), TEMA.texto,
                    largura_max=dir_.width - 150)
        self._botao(tela, pygame.Rect(dir_.right - 140, y - 2, 140, 28),
                    'Parar' if self.tocando_ref else 'Ouvir trecho', 'tocar_ref',
                    variante='perigo' if self.tocando_ref else 'primario', tamanho=12)
        y += 30
        ds.rotulo_secao(tela, dir_.x, y, _t('O áudio é'), f11)
        tipo = self.ref.get('tipo', 'mix')
        y = self._chips(tela, dir_.x + 90, y - 4, dir_.width - 90,
                        [('isolado', 'Instrumento isolado'), ('mix', 'Mix completo'), ('separado', 'Separado (Demucs)')],
                        tipo, 'tipo_ref')
        if tipo == 'mix':
            if 'py' in refm._cache_demucs:
                ok_d, msg_d = refm.demucs_disponivel()
            else:                                   # checado numa thread (pode abrir outro Python)
                ok_d, msg_d = False, 'Verificando se o Demucs está instalado...'
            self._botao(tela, pygame.Rect(dir_.x, y - 2, 250, 28), 'Separar a guitarra (Demucs)', 'separar',
                        habilitado=ok_d and not self._ocupado(), tamanho=11)
            _paragrafo(tela, _t(msg_d if not ok_d else 'Demora alguns minutos e pode deixar artefatos '
                                '(parecem reverb/chorus): a confiança dessas medidas é reduzida.'),
                       self._fonte(10, False), dir_.x + 260, y - 2, dir_.width - 260, TEMA.texto_apagado, max_linhas=2)
            y += 34
        # forma de onda + selecao
        onda = pygame.Rect(dir_.x, y + 4, dir_.width, 110)
        self._desenhar_onda(tela, onda)
        y = onda.bottom + 8
        a, b = self.trecho()
        dur_total = self.ref_audio.size / self.ref_sr
        chave_nivel = (id(self.ref_audio), round(a, 2), round(b, 2))
        if getattr(self, '_nivel_cache', (None,))[0] != chave_nivel and self.arrasto is None:
            trecho = self.audio_trecho()
            self._nivel_cache = (chave_nivel, at.lufs(trecho, self.ref_sr) if trecho.size > self.ref_sr * 0.5 else -70.0)
        nivel = getattr(self, '_nivel_cache', (None, -70.0))[1]
        info = f"{_t('Trecho')}: {_fmt_tempo(a)} → {_fmt_tempo(b)}  ({b - a:.1f} s de {_fmt_tempo(dur_total)})   " \
               f"{_t('Nível')}: {nivel:.0f} LUFS"
        ds.texto_em(tela, info, self._fonte(12), (dir_.x, y), TEMA.texto)
        y += 22
        _paragrafo(tela, _t('Arraste na forma de onda para escolher o trecho (ex.: só o riff do refrão). '
                            'Espaço toca/para.'), self._fonte(10, False), dir_.x, y, dir_.width, TEMA.texto_apagado)
        y += 22
        # BPM e MIDI
        ds.rotulo_secao(tela, dir_.x, y, _t('Andamento e estrutura'), f11)
        y += 22
        texto_bpm = f"BPM {self.bpm:g} ({_t(self.bpm_fonte)})" if self.bpm else _t('BPM não detectado')
        ds.texto_em(tela, texto_bpm, self._fonte(13), (dir_.x, y + 4), TEMA.texto)
        self._botao(tela, pygame.Rect(dir_.x + 190, y, 30, 26), '-', 'bpm', -1, tamanho=13)
        self._botao(tela, pygame.Rect(dir_.x + 224, y, 30, 26), '+', 'bpm', 1, tamanho=13)
        self._botao(tela, pygame.Rect(dir_.x + 270, y, 170, 26),
                    'Trocar MIDI' if self.midi else 'Associar MIDI', 'midi', tamanho=11)
        y += 36
        if self.compassos:
            i0 = self._compasso_em(a) or 0
            i1 = self._compasso_em(max(a, b - 1e-3)) or i0
            ds.texto_em(tela, f"{_t('Compassos')} {self.compassos[i0]['numero']} {_t('a')} "
                              f"{self.compassos[i1]['numero']} ({self.compassos[i0]['formula']})",
                        self._fonte(12), (dir_.x, y + 4), TEMA.texto)
            xx = dir_.x + 250
            for rot, dado in (('◀ início', (-1, 0)), ('início ▶', (1, 0)), ('◀ fim', (0, -1)), ('fim ▶', (0, 1))):
                self._botao(tela, pygame.Rect(xx, y, 76, 26), rot, 'compasso', dado, tamanho=10)
                xx += 80
            y += 32
            ds.texto_em(tela, f"{_t('Compasso 1 começa em')} {self.desloc_midi:.2f} s", self._fonte(11),
                        (dir_.x, y + 4), TEMA.texto_suave)
            xx = dir_.x + 250
            for rot, dado in (('-0,1 s', -0.1), ('-0,01', -0.01), ('+0,01', 0.01), ('+0,1 s', 0.1)):
                self._botao(tela, pygame.Rect(xx, y, 76, 26), rot, 'desloc_midi', dado, tamanho=10)
                xx += 80
            y += 32
        elif self.midi:
            ds.texto_em(tela, _t('MIDI sem compassos legíveis.'), self._fonte(11, False), (dir_.x, y), TEMA.aviso)

    def _desenhar_onda(self, tela, r):
        ds.superficie_translucida(tela, r, TEMA.superficie_alt, 225, ds.RAIO_SM, TEMA.borda, 1)
        if self.forma is None:
            return
        a, b = sorted(self.sel)
        xa, xb = r.x + int(a * r.width), r.x + int(b * r.width)
        pygame.draw.rect(tela, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.35), (xa, r.y, max(2, xb - xa), r.height))
        n = self.forma.size
        meio = r.centery
        for px in range(r.width):
            v = self.forma[int(px * n / r.width)]
            h = int(v * (r.height / 2 - 4))
            x = r.x + px
            cor = TEMA.acento if xa <= x <= xb else TEMA.texto_apagado
            pygame.draw.line(tela, cor, (x, meio - h), (x, meio + h), 1)
        if self.compassos:
            dur = self.ref_audio.size / self.ref_sr
            passo = max(1, len(self.compassos) // 40)
            for c in self.compassos[::passo]:
                x = r.x + int(c['inicio_s'] / dur * r.width)
                if r.x <= x <= r.right:
                    pygame.draw.line(tela, TEMA.borda, (x, r.y), (x, r.bottom), 1)
                    ds.texto_em(tela, str(c['numero']), self._fonte(9), (x + 2, r.y + 2), TEMA.texto_apagado)
        pygame.draw.line(tela, TEMA.texto, (xa, r.y), (xa, r.bottom), 2)
        pygame.draw.line(tela, TEMA.texto, (xb, r.y), (xb, r.bottom), 2)
        if self.tocando_ref and self.player.duracao_s() > 0:
            f = (self.player.posicao_s() % self.player.duracao_s()) / self.player.duracao_s()
            x = xa + int(f * (xb - xa))
            pygame.draw.line(tela, TEMA.aviso, (x, r.y), (x, r.bottom), 2)
        self._alvo(r, 'onda', r)

    # ============================================================ ETAPA 4
    def _etapa_gravacao(self, tela, r):
        f11 = self._fonte(11)
        col = int(r.width * 0.45)
        esq = pygame.Rect(r.x, r.y, col, r.height)
        dir_ = pygame.Rect(esq.right + ds.ESPACO_XL, r.y, r.width - col - ds.ESPACO_XL, r.height)
        y = esq.y
        a, b = self.trecho()
        ds.texto_em(tela, f"{(self.ref or {}).get('titulo', '')}  ·  {_fmt_tempo(a)} → {_fmt_tempo(b)}",
                    self._fonte(14), (esq.x, y), TEMA.texto, largura_max=esq.width)
        y += 28
        ds.rotulo_secao(tela, esq.x, y, _t('Volume da música'), f11)
        barra = pygame.Rect(esq.x, y + 26, esq.width - 70, ds.ALTURA_TRILHO)
        ds.slider(tela, barra, self.opc['volume'], valor=f"{self.opc['volume'] * 100:.0f}%", fonte=self._fonte(12))
        self._alvo(barra.inflate(16, 22), 'volume_slider', barra)
        y += 48
        ds.rotulo_secao(tela, esq.x, y, _t('Contagem de entrada'), f11)
        y = self._chips(tela, esq.x, y + 20, esq.width, [(0, 'Sem contagem'), (1, '1 compasso'), (2, '2 compassos')],
                        self.opc['contagem'], 'contagem')
        ds.rotulo_secao(tela, esq.x, y, _t('Repetir o trecho'), f11)
        y = self._chips(tela, esq.x, y + 20, esq.width, [(n, f'{n}x') for n in (1, 2, 3, 4)],
                        self.opc['repeticoes'], 'repeticoes')
        rr = pygame.Rect(esq.x, y, 46, 24)
        ds.interruptor(tela, rr, self.opc['metronomo'])
        self._alvo(rr, 'metronomo')
        ds.texto_em(tela, _t('Metrônomo durante a música'), self._fonte(12), (rr.right + 10, rr.centery),
                    TEMA.texto, ancora='midleft')
        y += 34
        texto_bpm = f"BPM {self.bpm:g}" if self.bpm else _t('BPM desconhecido: contagem a 120')
        ds.texto_em(tela, texto_bpm, self._fonte(12), (esq.x, y + 4), TEMA.texto_suave)
        self._botao(tela, pygame.Rect(esq.x + 190, y, 30, 26), '-', 'bpm', -1)
        self._botao(tela, pygame.Rect(esq.x + 224, y, 30, 26), '+', 'bpm', 1)
        y += 40
        gravando = self.gravador.estado == 'gravando'
        self._botao(tela, pygame.Rect(esq.x, y, esq.width, 48), '■ Parar' if gravando else '● Gravar tocando por cima',
                    'gravar', variante='perigo' if gravando else 'primario', tamanho=16,
                    habilitado=gravando or self.tarefa is None)
        y += 58
        if gravando:
            p = self.gravador.progresso
            ds.trilho(tela, pygame.Rect(esq.x, y, esq.width, 12), p)
            dur_cont = (self.opc['contagem'] * 4 * 60.0 / (self.bpm or 120.0))
            dur_total = dur_cont + (b - a) * self.opc['repeticoes']
            fase = _t('Contagem...') if p * dur_total < dur_cont else _t('Gravando: toque junto com a música!')
            ds.texto_em(tela, fase, self._fonte(14), (esq.x, y + 18), TEMA.alerta)
            y += 44
        _paragrafo(tela, _t('A música toca na saída escolhida e só o canal da pedaleira é gravado (nunca a '
                            'música). A latência calibrada é descontada no alinhamento. Toque o mesmo trecho: o '
                            'que importa aqui é o SOM, não se as notas estão certas.'),
                   self._fonte(11, False), esq.x, y, esq.width, TEMA.texto_apagado)

        # takes
        y = dir_.y
        ds.rotulo_secao(tela, dir_.x, y, _t('Tomadas (escolha uma para analisar)'), f11)
        y += 22

        def item(t, rr, take, i):
            ativo = i == self.take_sel
            erros = [p for p in take['problemas'] if p[0] == 'erro']
            avisos = [p for p in take['problemas'] if p[0] == 'aviso']
            estado_txt = 'com erro' if erros else ('com aviso' if avisos else 'ok')
            cor = TEMA.alerta if erros else (TEMA.aviso if avisos else TEMA.verde)
            dur = take['audio'].shape[0] / take['sr']
            sub = f"{dur:.1f} s · {len(take['canais'])} canal(is) · vazamento {take.get('vazamento', 0) * 100:.0f}%"
            larg_bot = 150
            linha = pygame.Rect(rr.x, rr.y, rr.width - larg_bot, rr.height)
            self._item_linha(t, linha, f"Take {take['numero']}", sub, ativo, 'escolher_take', i, estado_txt, cor)
            self._botao(t, pygame.Rect(rr.right - larg_bot + 6, rr.y + 6, 70, rr.height - 12), 'Ouvir',
                        'ouvir_take', i, tamanho=10)
            self._botao(t, pygame.Rect(rr.right - 70, rr.y + 6, 70, rr.height - 12), 'Descartar',
                        'descartar_take', i, variante='fantasma', tamanho=10)
        altura = max(120, int(dir_.height * 0.55))
        self._lista(tela, pygame.Rect(dir_.x, y, dir_.width, altura), 'takes', self.takes, item, 46,
                    vazio='Nenhuma tomada ainda: clique em Gravar e toque junto com a música.')
        y += altura + 10
        if self.take_sel is not None and self.takes:
            take = self.takes[self.take_sel]
            for nivel, texto in take['problemas']:
                y = _paragrafo(tela, ('✖ ' if nivel == 'erro' else '! ') + _t(texto), self._fonte(11, False),
                               dir_.x, y, dir_.width, TEMA.alerta if nivel == 'erro' else TEMA.aviso) + 4
            if not take['problemas']:
                ds.texto_em(tela, _t('Tomada ok: pronta para analisar.'), self._fonte(12), (dir_.x, y), TEMA.verde)

    # ============================================================ ETAPA 5
    def painel_pedaleira(self):
        if self._pedaleira is None:
            from Analisador.painel_pedaleira import PainelPedaleira
            self._pedaleira = PainelPedaleira(self)
        return self._pedaleira

    def _etapa_resultado(self, tela, r):
        if self.analise is None:
            if self.aba == 'pedaleira':
                # sem analise: so ver/conferir arquivos da pedaleira
                self._botao(tela, pygame.Rect(r.x, r.y, 160, 28), '< Resultado', 'aba', 'sugestoes', tamanho=11)
                self.painel_pedaleira().desenhar(tela, pygame.Rect(r.x, r.y + 38, r.width, r.height - 38))
                return
            ds.cartao_vazio(tela, pygame.Rect(r.x, r.y, r.width, 90),
                            _t('Ainda não há análise para esta tomada.'), self._fonte(14))
            self._botao(tela, pygame.Rect(r.centerx - 110, r.y + 110, 220, 40), 'Analisar agora', 'analisar',
                        variante='primario', habilitado=self.tarefa is None and self.take_valido() is not None,
                        tamanho=14)
            self._botao(tela, pygame.Rect(r.centerx - 110, r.y + 158, 220, 32), 'Pedaleira (ver/conferir preset)',
                        'aba', 'pedaleira', tamanho=11)
            return
        res = self.analise['resultado']
        col = max(300, int(r.width * 0.3))
        esq = pygame.Rect(r.x, r.y, col, r.height)
        dir_ = pygame.Rect(esq.right + ds.ESPACO_XL, r.y, r.width - col - ds.ESPACO_XL, r.height)
        self._resumo_resultado(tela, esq, res)
        # abas
        x, y = dir_.x, dir_.y
        fonte = self._fonte(12)
        for chave, nome in ABAS_RESULTADO:
            w = fonte.size(_t(nome))[0] + 24
            rr = pygame.Rect(x, y, w, 28)
            ds.chip(tela, rr, _t(nome), fonte, ativo=self.aba == chave)
            self._alvo(rr, 'aba', chave)
            x += w + 6
        corpo = pygame.Rect(dir_.x, y + 38, dir_.width, dir_.bottom - y - 38)
        {'sugestoes': self._aba_sugestoes, 'graficos': self._aba_graficos, 'medidas': self._aba_medidas,
         'historico': self._aba_historico, 'preset': self._aba_preset,
         'detector': self._aba_detector,
         'pedaleira': lambda t, c, _r: self.painel_pedaleira().desenhar(t, c)}[self.aba](tela, corpo, res)

    def _resumo_resultado(self, tela, r, res):
        y = r.y
        g = res['indice_geral']
        cor = TEMA.verde if (g or 0) >= 80 else (TEMA.aviso if (g or 0) >= 55 else TEMA.alerta)
        centro = (r.x + 62, y + 60)
        pygame.draw.circle(tela, TEMA.trilho, centro, 56, 10)
        if g is not None:
            # arco feito de pontos grossos (o draw.arc do pygame deixa falhas)
            passos = max(2, int(120 * g / 100.0))
            for k in range(passos + 1):
                ang = math.pi / 2 - 2 * math.pi * (g / 100.0) * k / passos
                p = (centro[0] + int(51 * math.cos(ang)), centro[1] - int(51 * math.sin(ang)))
                pygame.draw.circle(tela, cor, p, 5)
        ds.texto_em(tela, '-' if g is None else f'{g:.0f}', self._fonte(30), centro, TEMA.texto, ancora='center')
        ds.texto_em(tela, _t('compatibilidade'), self._fonte(10, False), (centro[0], centro[1] + 26),
                    TEMA.texto_apagado, ancora='center')
        _paragrafo(tela, _t(res['resumo']), self._fonte(12), r.x + 132, y + 10, r.width - 132, TEMA.texto,
                   max_linhas=5)
        y += 130
        for chave in st.CATEGORIAS:
            v = res['indices'].get(chave)
            ds.texto_em(tela, _t(st.NOMES_CATEGORIA[chave]), self._fonte(11), (r.x, y), TEMA.texto_suave)
            barra = pygame.Rect(r.x + 90, y + 3, r.width - 140, 10)
            ds.trilho(tela, barra, (v or 0) / 100.0,
                      cor=TEMA.verde if (v or 0) >= 80 else (TEMA.aviso if (v or 0) >= 55 else TEMA.alerta))
            ds.texto_em(tela, '-' if v is None else f'{v:.0f}', self._fonte(11), (r.right, y), TEMA.texto,
                        ancora='topright')
            y += 20
        y = _paragrafo(tela, _t('Índices são estimativas: 100 = mesmas medidas de timbre, não "som idêntico".'),
                       self._fonte(9, False), r.x, y + 2, r.width, TEMA.texto_apagado) + 8
        ds.rotulo_secao(tela, r.x, y, _t('Audição A/B (volumes igualados)'), self._fonte(11))
        y += 22
        meia = (r.width - 6) // 2
        tocando = self.player.tocando and self.player.atual in ('ref', 'rec')
        self._botao(tela, pygame.Rect(r.x, y, meia, 30), 'A: Original', 'ab', 'ref',
                    ativo=tocando and self.player.atual == 'ref', tamanho=12)
        self._botao(tela, pygame.Rect(r.x + meia + 6, y, meia, 30), 'B: Você', 'ab', 'rec',
                    ativo=tocando and self.player.atual == 'rec', tamanho=12)
        y += 36
        ds.texto_em(tela, _t('Tecla A alterna no mesmo ponto; clique de novo para parar.'), self._fonte(9, False),
                    (r.x, y), TEMA.texto_apagado)
        y += 18
        self._botao(tela, pygame.Rect(r.x, y, meia, 30), 'Nova tomada', 'etapa', 3, tamanho=11)
        self._botao(tela, pygame.Rect(r.x + meia + 6, y, meia, 30), 'Exportar relatório', 'exportar', tamanho=11)
        y += 40
        al = self.analise['alinhamento']
        ds.texto_em(tela, f"{_t('Alinhamento')}: {al['deslocamento_s'] * 1000:+.0f} ms "
                          f"({_t('confiança')} {al['confianca'] * 100:.0f}%)", self._fonte(10, False), (r.x, y),
                    TEMA.texto_apagado)
        y += 18
        for aviso in res['avisos'][:3]:
            if y > r.bottom - 30:
                break
            y = _paragrafo(tela, '• ' + _t(aviso), self._fonte(9, False), r.x, y, r.width, TEMA.texto_apagado,
                           max_linhas=3, entre=1) + 3

    def _aba_sugestoes(self, tela, r, res):
        grupos = []
        for tipo in st.TIPOS:
            for s_ in res['sugestoes']:
                if s_['tipo'] == tipo:
                    grupos.append(s_)
        if not grupos:
            ds.cartao_vazio(tela, pygame.Rect(r.x, r.y, r.width, 80),
                            _t('Nenhuma diferença importante: seu som está bem próximo do original!'),
                            self._fonte(13))
            return
        fonte_txt = self._fonte(11, False)

        def altura_item(s_):
            return 44 + len(_quebrar(_t(s_['texto']), fonte_txt, r.width - 190)) * (fonte_txt.get_height() + 2)
        alturas = [altura_item(s_) for s_ in grupos]
        total = sum(alturas) + 8 * len(alturas)
        maximo = max(0, total - r.height)
        self.scroll['sugestoes'] = max(0, min(self.scroll.get('sugestoes', 0), maximo))
        self._areas_rolagem.append((r, 'sugestoes', maximo))
        clip = tela.get_clip()
        tela.set_clip(r.clip(clip) if clip else r)
        y = r.y - self.scroll['sugestoes']
        tipo_ant = None
        for s_, h in zip(grupos, alturas):
            rr = pygame.Rect(r.x, y, r.width - 12, h)
            if rr.bottom > r.y and rr.y < r.bottom:
                cor = _cor(COR_TIPO[s_['tipo']])
                ds.superficie_translucida(tela, rr, ds.misturar(TEMA.superficie_alt, cor, 0.08), 230, ds.RAIO_MD,
                                          cor, 1)
                pygame.draw.rect(tela, cor, (rr.x, rr.y + 6, 4, rr.height - 12), border_radius=2)
                selo = ds.selo(tela, (rr.x + 12, rr.y + 8), _t(st.NOMES_TIPO[s_['tipo']]), self._fonte(9), cor)
                titulo = _t(s_['titulo']) + ('  ' + _t('(possível)') if s_['possivel'] else '')
                ds.texto_em(tela, titulo, self._fonte(13), (selo.right + 8, rr.y + 7), TEMA.texto,
                            largura_max=rr.width - selo.width - 190)
                _paragrafo(tela, _t(s_['texto']), fonte_txt, rr.x + 14, rr.y + 32, rr.width - 190, TEMA.texto_suave,
                           entre=2)
                barra = pygame.Rect(rr.right - 160, rr.y + 12, 70, 6)
                ds.trilho(tela, barra, s_['confianca'], cor=cor)
                ds.texto_em(tela, f"{s_['confianca'] * 100:.0f}%", self._fonte(9), (barra.right + 6, barra.y - 4),
                            TEMA.texto_apagado)
                if s_.get('pedal'):
                    bt = pygame.Rect(rr.right - 160, rr.y + 26, 150, 26)
                    vis = bt.clip(r)
                    ds.botao(tela, bt, _t('Abrir pedal ›'), self._fonte(10), variante='suave',
                             hover=self._hover(vis))
                    if vis.height > 0:
                        self._alvo(vis, 'abrir_pedal', (s_['pedal'], s_.get('valores')))
            y += h + 8
            tipo_ant = s_['tipo']
        tela.set_clip(clip)
        if maximo > 0:
            ds.barra_rolagem(tela, r.right - 6, r.y, r.height, r.height / total,
                             self.scroll['sugestoes'] / maximo, largura=6)

    # ------------------------------------------------------------ graficos
    def _grafico(self, tela, r, series, titulo, xlog=False, x_rotulos=None, y_faixa=None, unidade_y='dB'):
        """Linhas sobrepostas com grade simples (sem criar Surface)."""
        ds.superficie_translucida(tela, r, TEMA.superficie_alt, 215, ds.RAIO_SM, TEMA.borda, 1)
        ds.texto_em(tela, _t(titulo), self._fonte(11), (r.x + 8, r.y + 5), TEMA.texto)
        area = pygame.Rect(r.x + 44, r.y + 24, r.width - 56, r.height - 44)
        validas = [(np.asarray(xs, float), np.asarray(ys, float), c, n) for xs, ys, c, n in series
                   if xs is not None and len(xs) > 1 and len(ys) == len(xs)]
        if not validas:
            ds.texto_em(tela, _t('sem dados suficientes'), self._fonte(10, False), area.center, TEMA.texto_apagado,
                        ancora='center')
            return
        tx = (lambda v: np.log10(np.maximum(v, 1e-6))) if xlog else (lambda v: v)
        x0 = min(tx(xs).min() for xs, _, _, _ in validas)
        x1 = max(tx(xs).max() for xs, _, _, _ in validas)
        if y_faixa:
            y0, y1 = y_faixa
        else:
            y0 = min(np.nanmin(ys) for _, ys, _, _ in validas)
            y1 = max(np.nanmax(ys) for _, ys, _, _ in validas)
            y0, y1 = y0 - 2, y1 + 2
        if x1 <= x0 or y1 <= y0:
            return

        def px(x, y):
            return (area.x + int((tx(x) - x0) / (x1 - x0) * area.width),
                    area.bottom - int((np.clip(y, y0, y1) - y0) / (y1 - y0) * area.height))
        for k in range(5):
            yy = area.y + k * area.height // 4
            pygame.draw.line(tela, TEMA.borda, (area.x, yy), (area.right, yy), 1)
            valor = y1 - k * (y1 - y0) / 4
            ds.texto_em(tela, f'{valor:.0f}', self._fonte(9, False), (area.x - 4, yy), TEMA.texto_apagado,
                        ancora='midright')
        for valor, rotulo in (x_rotulos or []):
            x, _ = px(valor, y0)
            if area.x <= x <= area.right:
                pygame.draw.line(tela, TEMA.borda, (x, area.y), (x, area.bottom), 1)
                ds.texto_em(tela, rotulo, self._fonte(9, False), (x, area.bottom + 3), TEMA.texto_apagado,
                            ancora='midtop')
        lx = area.right
        for xs, ys, cor, nome in validas:
            passo = max(1, len(xs) // max(1, area.width))
            pontos = [px(x, y) for x, y in zip(xs[::passo], ys[::passo]) if np.isfinite(y)]
            if len(pontos) > 1:
                pygame.draw.lines(tela, cor, False, pontos, 2)
            rot = ds.texto_em(tela, _t(nome), self._fonte(10), (lx, r.y + 6), cor, ancora='topright')
            lx = rot.x - 12

    def _aba_graficos(self, tela, r, res):
        pr, pg = self.analise['perfil_ref'], self.analise['perfil_rec']
        cor_r, cor_g = TEMA.acento, TEMA.aviso
        h = (r.height - 16) // 2
        topo = pygame.Rect(r.x, r.y, r.width, h)
        hz = pr['curvas'].get('bandas_hz')
        rot_hz = [(f, lab) for f, lab in ((63, '63'), (125, '125'), (250, '250'), (500, '500'), (1000, '1k'),
                                          (2000, '2k'), (4000, '4k'), (8000, '8k')) if hz and hz[0] <= f <= hz[-1]]
        self._grafico(tela, topo, [(hz, pr['curvas'].get('ltas_db'), cor_r, 'Original'),
                                   (pg['curvas'].get('bandas_hz'), pg['curvas'].get('ltas_db'), cor_g, 'Você')],
                      'Espectro médio (EQ): dB por banda de 1/3 de oitava', xlog=True, x_rotulos=rot_hz)
        meia = (r.width - 10) // 2
        baixo = pygame.Rect(r.x, topo.bottom + 16, meia, r.bottom - topo.bottom - 16)

        def env(p):
            t, e = p['curvas'].get('env_t'), p['curvas'].get('env_db')
            if not t:
                return None, None
            e = np.array(e)
            return t, e - np.max(e)
        et, ee = env(pr)
        gt, ge = env(pg)
        self._grafico(tela, baixo, [(et, ee, cor_r, 'Original'), (gt, ge, cor_g, 'Você')],
                      'Envelope de energia (dinâmica)', y_faixa=(-50, 2),
                      x_rotulos=[(s_, f'{s_:g}s') for s_ in range(0, int((et or [0])[-1]) + 1,
                                                                   max(1, int((et or [0])[-1]) // 6 or 1))])
        dec = pygame.Rect(baixo.right + 10, baixo.y, r.right - baixo.right - 10, baixo.height)
        s1 = (pr['curvas'].get('decaimento_t'), pr['curvas'].get('decaimento_db'), cor_r, 'Original')
        s2 = (pg['curvas'].get('decaimento_t'), pg['curvas'].get('decaimento_db'), cor_g, 'Você')
        if s1[0] or s2[0]:
            self._grafico(tela, dec, [s1, s2], 'Decaimento depois de uma nota (reverb/delay)', y_faixa=(-60, 2),
                          x_rotulos=[(v, f'{v:g}s') for v in (0.5, 1.0, 1.5, 2.0)])
        else:
            self._grafico(tela, dec, [(pr['curvas'].get('eco_q'), pr['curvas'].get('eco_z'), cor_r, 'Original'),
                                      (pg['curvas'].get('eco_q'), pg['curvas'].get('eco_z'), cor_g, 'Você')],
                          'Ecos (delay): força por tempo', y_faixa=(-5, 120),
                          x_rotulos=[(v, f'{int(v * 1000)}ms') for v in (0.25, 0.5, 0.75, 1.0, 1.25)],
                          unidade_y='z')

    def _aba_medidas(self, tela, r, res):
        linhas = [m for m in res['tabela'] if m['referencia'] is not None or m['voce'] is not None]
        fonte = self._fonte(10, False)
        cab = pygame.Rect(r.x, r.y, r.width, 22)
        colunas = [(0, 'Medida'), (0.46, 'Original'), (0.60, 'Você'), (0.74, 'Diferença'), (0.88, 'Confiança')]
        for frac, nome in colunas:
            ds.texto_em(tela, _t(nome), self._fonte(10), (cab.x + int(frac * cab.width), cab.y + 4), TEMA.texto_suave)

        def item(t, rr, m, i):
            if i % 2 == 0:
                pygame.draw.rect(t, ds.misturar(TEMA.superficie_alt, TEMA.acento, 0.05), rr)
            fmt = lambda v: '-' if v is None else (f'{v:.2f}' if abs(v) < 100 else f'{v:.0f}')
            ds.texto_em(t, f"{_t(m['nome'])} ({m['unidade']})" if m['unidade'] else _t(m['nome']), fonte,
                        (rr.x + 4, rr.y + 3), TEMA.texto, largura_max=int(0.45 * rr.width))
            for frac, v in ((0.46, m['referencia']), (0.60, m['voce']), (0.74, m['diferenca'])):
                ds.texto_em(t, fmt(v), fonte, (rr.x + int(frac * rr.width), rr.y + 3), TEMA.texto)
            ds.texto_em(t, f"{m['confianca'] * 100:.0f}%", fonte, (rr.x + int(0.88 * rr.width), rr.y + 3),
                        TEMA.texto_apagado)
        self._lista(tela, pygame.Rect(r.x, r.y + 24, r.width, r.height - 24), 'medidas', linhas, item, 20)

    def _aba_historico(self, tela, r, res):
        hist = self.historico or []
        if not hist:
            ds.cartao_vazio(tela, pygame.Rect(r.x, r.y, r.width, 70), _t('Sem análises anteriores desta música.'),
                            self._fonte(12))
            return
        grafico = pygame.Rect(r.x, r.y, r.width, min(170, r.height // 2))
        ds.superficie_translucida(tela, grafico, TEMA.superficie_alt, 215, ds.RAIO_SM, TEMA.borda, 1)
        ds.texto_em(tela, _t('Compatibilidade por tentativa (ajuste o preset e grave de novo)'), self._fonte(11),
                    (grafico.x + 8, grafico.y + 5), TEMA.texto)
        ult = hist[-20:]
        area = pygame.Rect(grafico.x + 12, grafico.y + 26, grafico.width - 24, grafico.height - 46)
        w = max(6, area.width // max(1, len(ult)) - 6)
        for i, h in enumerate(ult):
            v = h.get('indice_geral') or 0
            alt = int(area.height * v / 100.0)
            barra = pygame.Rect(area.x + i * (w + 6), area.bottom - alt, w, alt)
            cor = TEMA.verde if v >= 80 else (TEMA.aviso if v >= 55 else TEMA.alerta)
            pygame.draw.rect(tela, cor, barra, border_radius=3)
            ds.texto_em(tela, f'{v:.0f}', self._fonte(9), (barra.centerx, barra.y - 12), TEMA.texto_suave,
                        ancora='midtop')
            ds.texto_em(tela, str(i + 1), self._fonte(9, False), (barra.centerx, area.bottom + 3), TEMA.texto_apagado,
                        ancora='midtop')

        def item(t, rr, h, i):
            quando = time.strftime('%d/%m %H:%M', time.localtime(h.get('quando', 0)))
            sub = ' · '.join(h.get('sugestoes', [])[:3])
            self._item_linha(t, rr, f"{quando}  —  {h.get('indice_geral') or 0:.0f}/100", sub, False, 'nada', None)
        self._lista(tela, pygame.Rect(r.x, grafico.bottom + 10, r.width, r.bottom - grafico.bottom - 10), 'historico',
                    list(reversed(hist)), item, 42)

    def _aba_preset(self, tela, r, res):
        from audio import cadeia_pedais as cp
        y = r.y
        x_limpo, _sr, origem = (None, None, '')
        if self.preset is None:
            _paragrafo(tela, _t('Análise por síntese: a aplicação aplica cadeias de pedais do motor ao SEU som '
                                'limpo e procura a cadeia e os knobs cujo timbre mais se aproxima da música. '
                                'Precisa do som limpo: o canal DI da tomada ou a calibração do instrumento.'),
                       self._fonte(12, False), r.x, y, r.width, TEMA.texto_suave)
            self._botao(tela, pygame.Rect(r.x, y + 70, 260, 36), 'Buscar preset sugerido', 'buscar_preset',
                        variante='primario', habilitado=self.tarefa is None, tamanho=13)
            return
        p = self.preset
        antes = res['indice_geral']
        depois = p['comparacao']['indice_geral']
        ds.texto_em(tela, f"{_t('Preset sugerido')}  ·  {_t('compatibilidade')} {antes:.0f} → {depois:.0f} "
                          f"({_t('no seu som limpo')}: {_t(p.get('origem', ''))})", self._fonte(13), (r.x, y), TEMA.texto,
                    largura_max=r.width)
        y += 28
        # cadeia desenhada como pedais
        x = r.x
        fonte = self._fonte(11)
        from Estudos import curriculo_pedais as cur
        for i, it in enumerate(p['cadeia']):
            pedal = cur.PEDAIS_POR_ID[it['id']]
            w = max(110, fonte.size(_t(pedal['nome']))[0] + 24)
            if x + w > r.right:
                x = r.x
                y += 70
            caixa = pygame.Rect(x, y, w, 60)
            pygame.draw.rect(tela, pedal['cor'], caixa, border_radius=8)
            pygame.draw.rect(tela, ds.escurecer(pedal['cor'], 0.35), caixa, 2, border_radius=8)
            ds.texto_em(tela, _t(pedal['nome']), fonte, (caixa.centerx, caixa.y + 8), ds.contraste_texto(pedal['cor']),
                        ancora='midtop', largura_max=w - 8)
            knobs = [f"{par['nome'].split(' (')[0][:6]} {cur.formatar_valor(par, it['params'][par['id']])}"
                     for par in pedal['parametros'][:2] if par['id'] in it['params']]
            ds.texto_em(tela, ' · '.join(knobs), self._fonte(9, False), (caixa.centerx, caixa.y + 30),
                        ds.contraste_texto(pedal['cor']), ancora='midtop', largura_max=w - 8)
            self._alvo(caixa, 'abrir_pedal', (it['id'], it['params']))
            if i < len(p['cadeia']) - 1:
                ds.texto_em(tela, '›', self._fonte(16), (caixa.right + 6, caixa.centery), TEMA.texto_apagado,
                            ancora='midleft')
            x += w + 22
        y += 72
        _paragrafo(tela, cp.descrever(p['cadeia']), self._fonte(10, False), r.x, y, r.width, TEMA.texto_suave,
                   max_linhas=3)
        y += 46
        terco = (r.width - 12) // 3
        tocando = self.player.tocando and self.player.atual in ('preset', 'di', 'ref')
        self._botao(tela, pygame.Rect(r.x, y, terco, 30), 'Ouvir o preset', 'ab', 'preset',
                    ativo=tocando and self.player.atual == 'preset', tamanho=11)
        self._botao(tela, pygame.Rect(r.x + terco + 6, y, terco, 30), 'Ouvir seu som limpo', 'ab', 'di',
                    ativo=tocando and self.player.atual == 'di', tamanho=11)
        self._botao(tela, pygame.Rect(r.x + 2 * (terco + 6), y, terco, 30), 'Ouvir o original', 'ab', 'ref',
                    ativo=tocando and self.player.atual == 'ref', tamanho=11)
        y += 40
        _paragrafo(tela, _t('Clique num pedal para abri-lo em ESTUDOS > Pedais já com esses valores. O motor '
                            'de pedais do EIGUIT não é a sua pedaleira: use o preset como ponto de partida e '
                            'ajuste de ouvido.'), self._fonte(10, False), r.x, y, r.width, TEMA.texto_apagado)
        y += 40
        for passo in p['passos'][:6]:
            ds.texto_em(tela, '• ' + passo, self._fonte(10, False), (r.x, y), TEMA.texto_apagado, largura_max=r.width)
            y += 15
        self._botao(tela, pygame.Rect(r.x, min(r.bottom - 30, y + 6), 200, 28), 'Buscar de novo', 'buscar_preset',
                    habilitado=self.tarefa is None, tamanho=11)

    def _aba_detector(self, tela, r, res):
        from audio import treinar_detector as td
        y = r.y
        ok, msg = self._cache('sklearn', td.sklearn_disponivel, 60.0)
        _paragrafo(tela, _t('Fase 3: um classificador leve (scikit-learn) treinado AQUI, com exemplos gerados '
                            'pelo próprio motor de pedais (e com a sua calibração, se houver). Ele reforça os '
                            'detectores por regras. Nada sai do computador.'),
                   self._fonte(12, False), r.x, y, r.width, TEMA.texto_suave)
        y += 60
        if not ok:
            _paragrafo(tela, _t(msg), self._fonte(12, False), r.x, y, r.width, TEMA.aviso)
            return
        pacote = td.carregar_modelo()
        if pacote:
            m = pacote.get('metricas', {})
            ds.texto_em(tela, f"{_t('Modelo ativo')}: {m.get('amostras', 0)} {_t('exemplos')} · "
                              f"{_t('acurácia')} {m.get('media_modelo', 0) * 100:.0f}% "
                              f"({_t('regras')}: {m.get('media_regras', 0) * 100:.0f}%)", self._fonte(12), (r.x, y),
                        TEMA.verde)
            y += 24
            if pacote.get('aviso'):
                ds.texto_em(tela, pacote['aviso'], self._fonte(10, False), (r.x, y), TEMA.aviso, largura_max=r.width)
                y += 18
            for rotulo in td.ROTULOS:
                a = m.get('acuracia_modelo', {}).get(rotulo)
                if a is None:
                    continue
                barra = pygame.Rect(r.x + 110, y + 3, 220, 8)
                ds.texto_em(tela, rotulo, self._fonte(10, False), (r.x, y), TEMA.texto_suave)
                ds.trilho(tela, barra, a)
                ds.texto_em(tela, f'{a * 100:.0f}%', self._fonte(10), (barra.right + 8, y), TEMA.texto_suave)
                y += 15
        else:
            ds.texto_em(tela, _t('Nenhum modelo treinado ainda: só as regras estão em uso.'), self._fonte(12),
                        (r.x, y), TEMA.texto_apagado)
            y += 24
        self._botao(tela, pygame.Rect(r.x, y + 10, 300, 34), 'Treinar detector local (~2 min)', 'treinar',
                    variante='primario', habilitado=self.tarefa is None, tamanho=12)

    # ------------------------------------------------------------ PDF
    def _exportar_pdf(self, caminho, info):
        """Uma pagina A4 (tema claro) com resumo, sugestoes e graficos, via PIL (como o Estudo de Tempo)."""
        from PIL import Image
        from config.design_system import PALETA_CLARA
        W, H = 1240, 1754
        modo, paleta = TEMA.modo, TEMA._paleta
        alvos, areas, scroll = self._alvos, self._areas_rolagem, dict(self.scroll)
        try:
            TEMA.modo, TEMA._paleta = 'claro', PALETA_CLARA
            pag = pygame.Surface((W, H))
            pag.fill((255, 255, 255))
            m = 60
            ds.texto_em(pag, 'Analisador IA - relatório de timbre', self._fonte(28), (m, m), TEMA.texto)
            y = m + 44
            for k, v in info.items():
                ds.texto_em(pag, f'{k}: {v}', self._fonte(14, False), (m, y), TEMA.texto_suave)
                y += 20
            y += 10
            res = self.analise['resultado']
            self._resumo_resultado(pag, pygame.Rect(m, y, 360, 520), res)
            self.scroll['sugestoes'] = 0
            self._aba_sugestoes(pag, pygame.Rect(m + 400, y, W - 2 * m - 400, 700), res)
            self._aba_graficos(pag, pygame.Rect(m, y + 730, W - 2 * m, H - y - 730 - m), res)
            ds.texto_em(pag, 'Os índices são estimativas. ' + st.AVISO_REFERENCIA, self._fonte(11, False),
                        (m, H - m + 10), TEMA.texto_apagado, largura_max=W - 2 * m)
            img = Image.frombytes('RGB', (W, H), pygame.image.tostring(pag, 'RGB'))
            img.save(caminho, 'PDF', resolution=150)
        finally:
            TEMA.modo, TEMA._paleta = modo, paleta
            self._alvos, self._areas_rolagem, self.scroll = alvos, areas, scroll

    # ================================================================ eventos
    def tratar_eventos(self, evento, pos, estado):
        """Ponto de entrada usado pelo GerenciadorEstudos."""
        self._estado = estado
        if evento.type == pygame.DROPFILE:
            caminho = getattr(evento, 'file', '')
            if caminho.lower().endswith(('.mid', '.midi')):
                self.midi = caminho
                self._carregar_midi()
            elif caminho.lower().endswith(refm.EXTENSOES):
                self.etapa = 2
                self._importar_caminho(caminho)
            return True
        if self.busca_foco and evento.type in (pygame.TEXTINPUT, pygame.KEYDOWN):
            return self._digitar(evento)
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_SPACE:
                if self.etapa == 2:
                    self.alternar_ref()
                elif self.etapa == 4:
                    if self.player.tocando:
                        self.player.parar()
                    else:
                        self.tocar_ab(self.ab)
                elif self.etapa == 3:
                    self.gravar()
                return True
            if evento.key == pygame.K_a and self.etapa == 4:
                self.alternar_ab()
                return True
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.etapa < len(ETAPAS) - 1:
                self.ir_para(self.etapa + 1)
                return True
            return False
        if evento.type == pygame.MOUSEWHEEL:
            return self._rolar(self._mouse, -evento.y * 50)
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button in (4, 5):
            return self._rolar(pos, -50 if evento.button == 4 else 50)
        if evento.type == pygame.MOUSEMOTION and self.arrasto:
            self._arrastar(pos)
            return True
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.arrasto:
            self._arrastar(pos)
            if self.arrasto[0] == 'onda' and self.compassos and self.ref_audio is not None:
                a, b = self.trecho()
                i0 = self._compasso_em(a) or 0
                i1 = self._compasso_em(max(a, b - 1e-3)) or i0
                self.selecionar_compassos(i0, i1)
            if self.arrasto[0] == 'onda' and self.tocando_ref:
                self.player.parar()
                self.tocando_ref = False
                self.alternar_ref()
            self.arrasto = None
            return True
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            return self.clicar(pos)
        return False

    def _rolar(self, pos, delta):
        for r, chave, maximo in reversed(self._areas_rolagem):
            if r.collidepoint(pos):
                self.scroll[chave] = max(0, min(maximo, self.scroll.get(chave, 0) + delta))
                return True
        return False

    def _digitar(self, ev):
        if ev.type == pygame.TEXTINPUT:
            if ev.text and not ev.text.isascii():
                self.busca += ev.text
            return True
        if ev.key == pygame.K_BACKSPACE:
            self.busca = self.busca[:-1]
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.busca_foco = False
            self._atualizar_itens()
        elif ev.key == pygame.K_ESCAPE:
            self.busca_foco = False
            return False                              # deixa o gerenciador tratar o Esc
        elif ev.unicode and ev.unicode.isprintable() and ev.unicode.isascii():
            self.busca += ev.unicode
        return True

    def _arrastar(self, pos):
        tipo = self.arrasto[0]
        if tipo == 'onda':
            r = self.arrasto[1]
            f = float(np.clip((pos[0] - r.x) / max(1, r.width), 0, 1))
            self.sel[1] = f
            if abs(self.sel[1] - self.sel[0]) < 1e-4:
                self.sel[1] = min(1.0, self.sel[0] + 1e-3)
        elif tipo == 'latencia':
            r = self.arrasto[1]
            self.cfg.definir_latencia(round(float(np.clip((pos[0] - r.x) / max(1, r.width), 0, 1)) * 300))
        elif tipo == 'volume':
            r = self.arrasto[1]
            self.opc['volume'] = round(float(np.clip((pos[0] - r.x) / max(1, r.width), 0, 1)), 2)

    def clicar(self, pos):
        alvo = None
        for rect, acao, dado in reversed(self._alvos):
            if rect.collidepoint(pos):
                alvo = (acao, dado, rect)
                break
        if self.busca_foco and (alvo is None or alvo[0] != 'foco_busca'):
            self.busca_foco = False
        if alvo is None:
            return False
        acao, dado, rect = alvo
        if self.tarefa is not None and acao != 'cancelar_tarefa':
            return True                               # a caixa de progresso "trava" a tela
        metodo = getattr(self, f'_acao_{acao}', None)
        if metodo is not None:
            metodo(dado, rect, pos)
        return True

    # ---- acoes (um metodo por acao registrada nos alvos)
    def _acao_nada(self, dado, rect, pos):
        pass

    def _acao_cancelar_tarefa(self, dado, rect, pos):
        if self.tarefa is not None:
            self.tarefa[0].cancelar()

    def _acao_etapa(self, dado, rect, pos):
        self.ir_para(dado)

    def _acao_atualizar_lista(self, dado, rect, pos):
        problemas = self.atualizar_lista()
        self.avisar(problemas[0] if problemas else 'Lista de dispositivos atualizada.',
                    'aviso' if problemas else 'ok')

    def _acao_entrada(self, dado, rect, pos):
        self.escolher_entrada(dado)

    def _acao_saida(self, dado, rect, pos):
        self.escolher_saida(dado)

    def _acao_canal_proc(self, dado, rect, pos):
        self.cfg.canal_processado = dado
        if self.cfg.canal_di == dado:
            self.cfg.canal_di = None
        self.medidor._canal_monitor = dado

    def _acao_canal_di(self, dado, rect, pos):
        self.cfg.canal_di = dado

    def _acao_taxa(self, dado, rect, pos):
        self.cfg.taxa = int(dado)
        self._reiniciar_medidor()

    def _acao_buffer(self, dado, rect, pos):
        self.cfg.buffer = int(dado)
        self._reiniciar_medidor()

    def _acao_monitor(self, dado, rect, pos):
        self.monitorar = not self.monitorar
        self._reiniciar_medidor()
        if self.monitorar:
            self.avisar('Monitoramento ligado: cuidado com microfonia e com o atraso do computador.', 'aviso')

    def _acao_latencia_slider(self, dado, rect, pos):
        self.arrasto = ('latencia', dado)
        self._arrastar(pos)

    def _acao_calibrar(self, dado, rect, pos):
        self.calibrar(dado)

    def _acao_instrumento(self, dado, rect, pos):
        self.cfg.instrumento = dado
        self._carregar_perfil_guitarra()

    def _acao_captador(self, dado, rect, pos):
        self.cfg.captador = dado
        self._carregar_perfil_guitarra()

    def _acao_afinacao(self, dado, rect, pos):
        self.cfg.afinacao = dado

    def _acao_calibrar_instr(self, dado, rect, pos):
        self.calibrar_instrumento()

    def _acao_foco_busca(self, dado, rect, pos):
        self.busca_foco = True

    def _acao_buscar(self, dado, rect, pos):
        self.online = []
        self._atualizar_itens()

    def _acao_importar(self, dado, rect, pos):
        self.importar()

    def _acao_add_pasta(self, dado, rect, pos):
        self.adicionar_pasta()

    def _acao_online(self, dado, rect, pos):
        self.pesquisar_online()

    def _acao_baixar(self, dado, rect, pos):
        self.baixar(dado)

    def _acao_escolher_ref(self, dado, rect, pos):
        self.selecionar(dado)

    def _acao_tipo_ref(self, dado, rect, pos):
        self.mudar_tipo(dado)

    def _acao_separar(self, dado, rect, pos):
        self.separar()

    def _acao_tocar_ref(self, dado, rect, pos):
        self.alternar_ref()

    def _acao_onda(self, dado, rect, pos):
        r = dado
        f = float(np.clip((pos[0] - r.x) / max(1, r.width), 0, 1))
        self.sel = [f, f]
        self.arrasto = ('onda', r)

    def _acao_bpm(self, dado, rect, pos):
        self.bpm = max(30.0, min(300.0, (self.bpm or 120.0) + dado))
        self.bpm_fonte = 'manual'

    def _acao_midi(self, dado, rect, pos):
        self.associar_midi()

    def _acao_compasso(self, dado, rect, pos):
        if not self.compassos:
            return
        a, b = self.trecho()
        i0 = self._compasso_em(a) or 0
        i1 = self._compasso_em(max(a, b - 1e-3)) or i0
        self.selecionar_compassos(i0 + dado[0], i1 + dado[1])

    def _acao_desloc_midi(self, dado, rect, pos):
        self.desloc_midi = round(max(0.0, self.desloc_midi + dado), 3)
        self._carregar_midi()

    def _acao_volume_slider(self, dado, rect, pos):
        self.arrasto = ('volume', dado)
        self._arrastar(pos)

    def _acao_contagem(self, dado, rect, pos):
        self.opc['contagem'] = dado

    def _acao_repeticoes(self, dado, rect, pos):
        self.opc['repeticoes'] = dado

    def _acao_metronomo(self, dado, rect, pos):
        self.opc['metronomo'] = not self.opc['metronomo']

    def _acao_gravar(self, dado, rect, pos):
        self.gravar()

    def _acao_escolher_take(self, dado, rect, pos):
        self.take_sel = dado

    def _acao_ouvir_take(self, dado, rect, pos):
        self.ouvir_take(dado)

    def _acao_descartar_take(self, dado, rect, pos):
        self.descartar_take(dado)

    def _acao_analisar(self, dado, rect, pos):
        self.analisar()

    def _acao_aba(self, dado, rect, pos):
        self.aba = dado

    def _acao_ab(self, dado, rect, pos):
        self.tocar_ab(dado)

    def _acao_abrir_pedal(self, dado, rect, pos):
        pid, valores = dado
        self.abrir_pedal(pid, valores)

    def _acao_exportar(self, dado, rect, pos):
        try:
            self.exportar()
        except Exception as erro:
            self.avisar(f'Não consegui exportar: {erro}', 'erro')

    def _acao_ped(self, dado, rect, pos):
        try:
            self.painel_pedaleira().acao(dado)
        except Exception as erro:
            self.avisar(f'Pedaleira: {erro}', 'erro', 10)

    def _acao_buscar_preset(self, dado, rect, pos):
        self.buscar_preset()

    def _acao_treinar(self, dado, rect, pos):
        self.treinar_detector()
