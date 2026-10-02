# -*- coding: utf-8 -*-
"""
Analisador IA - dispositivos de audio: lista entradas e saidas, guarda a
configuracao escolhida, mede o nivel de entrada em tempo real (com aviso de
clipping e de sinal fraco), monitora a entrada e calibra a latencia.

Backend: sounddevice (PortAudio), o mesmo do GlobalAudioEngine. Sem ele (ou
sem PortAudio) tudo continua importando: disponivel() diz o motivo e a tela
mostra a mensagem em vez de travar.

Arquivos (por usuario, fora do projeto):
    %APPDATA%/EIGUIT/analisador/config_audio.json   ultima configuracao
    (latencia calibrada fica guardada por par entrada|saida)
"""
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import List, Optional

import numpy as np

try:
    import sounddevice as sd
    _ERRO_SD = ''
except (ImportError, OSError) as _erro:          # sem PortAudio ou sem a biblioteca
    sd = None
    _ERRO_SD = str(_erro)

TAXAS_COMUNS = (44100, 48000, 88200, 96000)
BUFFERS = (64, 128, 256, 512, 1024, 2048)


def pasta_dados():
    """%APPDATA%/EIGUIT/analisador (ou ~/.config/EIGUIT/analisador)."""
    base = os.environ.get('APPDATA') or os.path.join(os.path.expanduser('~'), '.config')
    pasta = os.path.join(base, 'EIGUIT', 'analisador')
    os.makedirs(pasta, exist_ok=True)
    return pasta


def disponivel():
    """(True, '') ou (False, mensagem amigavel) para a interface."""
    if sd is None:
        return False, ('Biblioteca de áudio (sounddevice/PortAudio) indisponível: instale com '
                       '"uv sync" ou "pip install sounddevice". Detalhe: ' + _ERRO_SD)
    return True, ''


# ===========================================================================
# LISTAGEM
# ===========================================================================

def listar_dispositivos():
    """
        Devolve {'entradas': [...], 'saidas': [...]}, cada item com id, nome,
        api (host API: MME, WASAPI, ASIO...), canais e taxa padrao.
        Nunca levanta excecao: sem backend, as listas vem vazias.
    """
    if sd is None:
        return {'entradas': [], 'saidas': [], 'erro': disponivel()[1]}
    try:
        apis = sd.query_hostapis()
        dispositivos = sd.query_devices()
    except Exception as erro:
        return {'entradas': [], 'saidas': [], 'erro': f'Não consegui listar os dispositivos: {erro}'}
    entradas, saidas = [], []
    for i, d in enumerate(dispositivos):
        try:
            api = apis[d['hostapi']]['name']
        except Exception:
            api = '?'
        item = {'id': i, 'nome': d['name'], 'api': api,
                'canais_entrada': int(d['max_input_channels']),
                'canais_saida': int(d['max_output_channels']),
                'taxa_padrao': int(d.get('default_samplerate') or 48000),
                'latencia_baixa_ms': 1000 * float(d.get('default_low_input_latency', 0) or 0)}
        if item['canais_entrada'] > 0:
            entradas.append(item)
        if item['canais_saida'] > 0:
            saidas.append(item)
    return {'entradas': entradas, 'saidas': saidas, 'erro': ''}


def taxas_suportadas(id_disp, entrada=True, canais=1):
    """Quais das taxas comuns o dispositivo aceita (testa com o PortAudio)."""
    if sd is None or id_disp is None:
        return []
    ok = []
    for taxa in TAXAS_COMUNS:
        try:
            if entrada:
                sd.check_input_settings(device=id_disp, channels=max(1, canais), samplerate=taxa)
            else:
                sd.check_output_settings(device=id_disp, channels=max(1, canais), samplerate=taxa)
            ok.append(taxa)
        except Exception:
            continue
    return ok


def achar_por_nome(nome, lista):
    """O id pode mudar quando se pluga/desplugua algo: acha pelo nome."""
    for item in lista:
        if item['nome'] == nome:
            return item
    return None


# ===========================================================================
# CONFIGURACAO
# ===========================================================================

@dataclass
class ConfigAudio:
    entrada_id: Optional[int] = None
    entrada_nome: str = ''
    saida_id: Optional[int] = None
    saida_nome: str = ''
    canais_entrada: int = 1                   # quantos canais o dispositivo tem
    canal_processado: int = 0                 # canal com o som do preset (0 = primeiro)
    canal_di: Optional[int] = None            # canal seco (DI), se a pedaleira mandar
    taxa: int = 48000
    buffer: int = 256
    latencia_ms: float = 0.0                  # ida e volta (calibrada ou manual)
    instrumento: str = 'guitarra'
    captador: str = 'nenhum'
    afinacao: str = 'Padrão (E)'
    latencias: dict = field(default_factory=dict)   # 'entrada|saida' -> ms

    def chave_latencia(self):
        return f'{self.entrada_nome}|{self.saida_nome}'

    def definir_latencia(self, ms):
        self.latencia_ms = float(ms)
        self.latencias[self.chave_latencia()] = float(ms)

    def restaurar_latencia(self):
        if self.chave_latencia() in self.latencias:
            self.latencia_ms = float(self.latencias[self.chave_latencia()])

    def canais_gravados(self):
        """Canais a gravar (processado e, se houver, o DI), sem repetir."""
        canais = [self.canal_processado]
        if self.canal_di is not None and self.canal_di != self.canal_processado:
            canais.append(self.canal_di)
        return canais


def _arquivo_config():
    return os.path.join(pasta_dados(), 'config_audio.json')


def carregar_config():
    """Ultima configuracao usada (ou a padrao)."""
    try:
        with open(_arquivo_config(), encoding='utf-8') as f:
            dados = json.load(f)
        campos = ConfigAudio.__dataclass_fields__
        return ConfigAudio(**{k: v for k, v in dados.items() if k in campos})
    except (OSError, ValueError, TypeError):
        return ConfigAudio()


def salvar_config(cfg):
    try:
        with open(_arquivo_config(), 'w', encoding='utf-8') as f:
            json.dump(asdict(cfg), f, ensure_ascii=False, indent=1)
        return True
    except OSError:
        return False


def validar_config(cfg, lista=None):
    """
        Confere se os dispositivos ainda existem (pelo nome), se os canais
        cabem e se a taxa e aceita. Corrige ids que mudaram. Devolve a lista
        de problemas em texto (vazia = tudo certo).
    """
    problemas = []
    ok, msg = disponivel()
    if not ok:
        return [msg]
    lista = lista or listar_dispositivos()
    ent = achar_por_nome(cfg.entrada_nome, lista['entradas']) if cfg.entrada_nome else None
    sai = achar_por_nome(cfg.saida_nome, lista['saidas']) if cfg.saida_nome else None
    if ent is None:
        problemas.append('Escolha o dispositivo de entrada (a pedaleira). O último usado não foi '
                         'encontrado: ele está conectado?')
    else:
        cfg.entrada_id = ent['id']
        cfg.canais_entrada = ent['canais_entrada']
        if cfg.canal_processado >= ent['canais_entrada']:
            problemas.append(f'O canal {cfg.canal_processado + 1} não existe nesse dispositivo '
                             f'(ele tem {ent["canais_entrada"]}).')
        if cfg.canal_di is not None and cfg.canal_di >= ent['canais_entrada']:
            cfg.canal_di = None
    if sai is None:
        problemas.append('Escolha o dispositivo de saída (onde você ouve a música).')
    else:
        cfg.saida_id = sai['id']
    if ent is not None and taxas_suportadas(ent['id'], True, 1) and \
            cfg.taxa not in taxas_suportadas(ent['id'], True, 1):
        problemas.append(f'A entrada não aceita {cfg.taxa} Hz. Taxas aceitas: '
                         f'{", ".join(str(t) for t in taxas_suportadas(ent["id"], True, 1))}.')
    return problemas


# ===========================================================================
# MEDIDOR DE NIVEL E MONITORAMENTO
# ===========================================================================

class MedidorEntrada:
    """
        Como funciona: abre a entrada com todos os canais do dispositivo; o
        callback so calcula pico e RMS de cada canal (sem alocar memoria). A
        interface le niveis() a cada quadro. Com monitorar=True, o canal
        processado vai para a saida (stream duplex se entrada e saida forem o
        mesmo dispositivo; senao, uma fila curta entre os dois streams).
        Para que serve: Etapa 1 (medidor, clipping, sinal fraco, monitor).
        Onde e usada: Analisador/analisador_ia.py.
    """

    LIMIAR_CLIP = 0.98
    LIMIAR_FRACO_DB = -45.0

    def __init__(self):
        self.stream = None
        self.stream_saida = None
        self.ativo = False
        self.erro = ''
        self.monitorando = False
        self._lock = threading.Lock()
        self._pico = np.zeros(1)
        self._rms = np.zeros(1)
        self._clip_ate = np.zeros(1)
        self._fila = None
        self._canal_monitor = 0

    def iniciar(self, cfg, monitorar=False):
        self.parar()
        ok, msg = disponivel()
        if not ok:
            self.erro = msg
            return False
        n = max(1, int(cfg.canais_entrada or 1))
        self._pico = np.zeros(n)
        self._rms = np.zeros(n)
        self._clip_ate = np.zeros(n)
        self._canal_monitor = cfg.canal_processado
        self.monitorando = bool(monitorar)
        try:
            if monitorar and cfg.entrada_id == cfg.saida_id:
                self.stream = sd.Stream(device=(cfg.entrada_id, cfg.saida_id), samplerate=cfg.taxa,
                                        blocksize=cfg.buffer, channels=(n, 2), dtype='float32',
                                        latency='low', callback=self._cb_duplex)
            else:
                self.stream = sd.InputStream(device=cfg.entrada_id, samplerate=cfg.taxa,
                                             blocksize=cfg.buffer, channels=n, dtype='float32',
                                             latency='low', callback=self._cb_entrada)
                if monitorar:
                    self._fila = _FilaCircular(int(cfg.taxa * 0.5))
                    self.stream_saida = sd.OutputStream(device=cfg.saida_id, samplerate=cfg.taxa,
                                                        blocksize=cfg.buffer, channels=2, dtype='float32',
                                                        latency='low', callback=self._cb_saida)
            self.stream.start()
            if self.stream_saida is not None:
                self.stream_saida.start()
            self.ativo = True
            self.erro = ''
            return True
        except Exception as erro:
            self.parar()
            self.erro = _mensagem_erro(erro, cfg)
            return False

    def _medir(self, dados):
        pico = np.max(np.abs(dados), axis=0)
        rms = np.sqrt(np.mean(dados * dados, axis=0))
        agora = time.time()
        with self._lock:
            m = min(pico.size, self._pico.size)
            self._pico[:m] = np.maximum(pico[:m], self._pico[:m] * 0.85)
            self._rms[:m] = rms[:m]
            self._clip_ate[:m] = np.where(pico[:m] >= self.LIMIAR_CLIP, agora + 1.5, self._clip_ate[:m])

    def _cb_entrada(self, indata, frames, tempo, status):
        self._medir(indata)
        if self._fila is not None:
            c = min(self._canal_monitor, indata.shape[1] - 1)
            self._fila.escrever(indata[:, c])

    def _cb_saida(self, outdata, frames, tempo, status):
        dados = self._fila.ler(frames) if self._fila is not None else np.zeros(frames, np.float32)
        outdata[:, 0] = dados
        outdata[:, 1] = dados

    def _cb_duplex(self, indata, outdata, frames, tempo, status):
        self._medir(indata)
        c = min(self._canal_monitor, indata.shape[1] - 1)
        outdata[:, 0] = indata[:, c]
        outdata[:, 1] = indata[:, c]

    def niveis(self):
        """[(pico_db, rms_db, clipou, fraco)] por canal, para o medidor da tela."""
        agora = time.time()
        with self._lock:
            pico, rms, clip = self._pico.copy(), self._rms.copy(), self._clip_ate.copy()
        saida = []
        for p, r, c in zip(pico, rms, clip):
            pdb = 20 * np.log10(p + 1e-9)
            rdb = 20 * np.log10(r + 1e-9)
            saida.append((float(pdb), float(rdb), bool(c > agora), bool(pdb < self.LIMIAR_FRACO_DB)))
        return saida

    def parar(self):
        for s in (self.stream, self.stream_saida):
            if s is not None:
                try:
                    s.stop()
                    s.close()
                except Exception:
                    pass
        self.stream = self.stream_saida = None
        self._fila = None
        self.ativo = False
        self.monitorando = False


class _FilaCircular:
    """Fila de amostras mono entre o callback de entrada e o de saida."""

    def __init__(self, tamanho):
        self.buf = np.zeros(tamanho, dtype=np.float32)
        self.escrita = 0
        self.leitura = 0
        self.lock = threading.Lock()

    def escrever(self, x):
        with self.lock:
            n = x.size
            i = np.arange(self.escrita, self.escrita + n) % self.buf.size
            self.buf[i] = x
            self.escrita += n
            if self.escrita - self.leitura > self.buf.size:
                self.leitura = self.escrita - self.buf.size

    def ler(self, n):
        with self.lock:
            disponivel = self.escrita - self.leitura
            saida = np.zeros(n, dtype=np.float32)
            k = min(n, disponivel)
            if k > 0:
                i = np.arange(self.leitura, self.leitura + k) % self.buf.size
                saida[:k] = self.buf[i]
                self.leitura += k
            return saida


def _mensagem_erro(erro, cfg=None):
    """Transforma erro do PortAudio numa frase que o usuario entende."""
    texto = str(erro)
    baixo = texto.lower()
    if 'invalid sample rate' in baixo or 'samplerate' in baixo:
        return (f'O dispositivo não aceita {getattr(cfg, "taxa", "?")} Hz. Troque a taxa de amostragem '
                '(44100 ou 48000 costumam funcionar).')
    if 'invalid number of channels' in baixo or 'channels' in baixo:
        return 'O dispositivo não tem esse número de canais. Confira o canal escolhido.'
    if 'unanticipated host error' in baixo or 'device unavailable' in baixo or 'invalid device' in baixo:
        return ('O dispositivo não respondeu: ele foi desconectado ou está em uso por outro programa '
                '(feche o software da pedaleira/DAW e clique em "Atualizar lista").')
    return f'Erro de áudio: {texto}'


# ===========================================================================
# CALIBRACAO DE LATENCIA
# ===========================================================================

def sinal_cliques(sr, n=8, intervalo=0.5, antes=0.5, depois=0.7):
    """Trem de cliques curtos (estereo float32) e os instantes de cada clique."""
    total = int((antes + n * intervalo + depois) * sr)
    x = np.zeros(total, dtype=np.float32)
    clique = np.sin(2 * np.pi * 2000 * np.arange(int(0.004 * sr)) / sr) * \
        np.hanning(int(0.004 * sr))
    tempos = []
    for k in range(n):
        i = int((antes + k * intervalo) * sr)
        x[i:i + clique.size] += 0.8 * clique
        tempos.append(i / sr)
    return np.stack([x, x], axis=1), np.array(tempos)


def medir_latencia(gravado, sr, tempos_cliques, modo='loopback'):
    """
        Como funciona:
          loopback -> correlacao cruzada do que voltou com o clique enviado
                      (cabo da saida na entrada, ou o microfone perto da caixa)
          tocar    -> o usuario palheta junto com cada clique; mede a
                      diferenca ate o ataque mais proximo (mediana).
        Devolve (latencia_ms ou None, confianca 0..1, texto).
    """
    x = np.asarray(gravado, dtype=np.float64)
    if x.ndim == 2:
        x = x[:, 0]
    if x.size == 0 or np.max(np.abs(x)) < 1e-4:
        return None, 0.0, 'Nada chegou na entrada durante a calibração (volume zero ou cabo solto).'
    from audio import analise_timbre as at
    if modo == 'loopback':
        ref = np.zeros_like(x)
        clique = np.sin(2 * np.pi * 2000 * np.arange(int(0.004 * sr)) / sr) * np.hanning(int(0.004 * sr))
        for t in tempos_cliques:
            i = int(t * sr)
            ref[i:i + clique.size] += clique
        n = 1 << int(np.ceil(np.log2(2 * x.size)))
        c = np.fft.irfft(np.fft.rfft(x, n) * np.conj(np.fft.rfft(ref, n)), n)
        maximo = int(0.6 * sr)
        c = np.abs(c[:maximo])
        lag = int(np.argmax(c))
        conf = float(np.clip((c[lag] / (np.median(c) + 1e-12) - 5) / 20, 0, 1))
        return 1000.0 * lag / sr, conf, f'eco do clique {1000.0 * lag / sr:.0f} ms depois'
    # modo tocar junto
    xs = at.reamostrar(x, sr, at.SR_ANALISE)
    ataques = at.picos_ataque(at.fluxo_espectral(at.stft_mag(xs, 1024, 128)), at.SR_ANALISE, 128)
    difs = []
    for t in tempos_cliques:
        depois = ataques[(ataques > t - 0.05) & (ataques < t + 0.45)]
        if depois.size:
            difs.append(depois[0] - t)
    if len(difs) < 3:
        return None, 0.0, 'Poucas palhetadas detectadas: toque uma nota forte em cada clique.'
    difs = np.array(difs)
    med = float(np.median(difs))
    espalho = float(np.median(np.abs(difs - med)))
    conf = float(np.clip(1 - espalho / 0.04, 0, 1) * min(1.0, len(difs) / 6))
    return max(0.0, 1000.0 * med), conf, f'{len(difs)} palhetadas, variação de ±{espalho * 1000:.0f} ms'
