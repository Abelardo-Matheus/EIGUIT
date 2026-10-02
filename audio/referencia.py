# -*- coding: utf-8 -*-
"""
Analisador IA - musica de referencia: biblioteca local (pasta de audios de
referencia + partituras que o EIGUIT ja conhece), importacao de arquivo,
pesquisa/download opcional (yt-dlp), separacao opcional da guitarra
(Demucs), cache, BPM, forma de onda e compassos do MIDI associado.

O MIDI nunca da o timbre: ele so serve para estrutura (compassos, BPM,
escolher o trecho). A referencia de timbre e SEMPRE audio.

Dependencias opcionais (detectadas na hora; sem elas o botao fica
desabilitado com a explicacao): yt_dlp + ffmpeg (pesquisa/download online),
demucs (separar a guitarra de uma mixagem), librosa (BPM mais preciso).

Arquivos:
    %APPDATA%/EIGUIT/analisador/referencias/        cache de downloads e stems
    %APPDATA%/EIGUIT/analisador/referencias.json    indice (titulo, artista, tipo...)
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata

import numpy as np

from audio import dispositivos as disp

EXTENSOES = ('.wav', '.flac', '.ogg', '.mp3', '.m4a', '.aiff', '.aif', '.opus', '.webm')
AVISO_DOWNLOAD = ('Baixar áudio da internet é responsabilidade sua: respeite os termos de uso da '
                  'plataforma e os direitos autorais. O arquivo fica só no seu computador, para estudo.')
PALAVRAS_ISOLADA = ('isolated guitar', 'guitar only', 'guitar track', 'stem', 'isolated', 'guitarra isolada',
                    'só guitarra', 'so guitarra', 'guitar isolated', 'bass only', 'isolated bass')
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pasta_cache():
    pasta = os.path.join(disp.pasta_dados(), 'referencias')
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _arquivo_indice():
    return os.path.join(disp.pasta_dados(), 'referencias.json')


def _normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', texto.lower()).strip()


def id_referencia(caminho):
    """Id estavel: sha1 do nome + tamanho + data (rapido, sem ler o arquivo todo)."""
    try:
        st = os.stat(caminho)
        chave = f'{os.path.abspath(caminho)}|{st.st_size}|{int(st.st_mtime)}'
    except OSError:
        chave = os.path.abspath(caminho)
    return hashlib.sha1(chave.encode('utf-8')).hexdigest()[:14]


# ===========================================================================
# INDICE E BIBLIOTECA LOCAL
# ===========================================================================

def ler_indice():
    try:
        with open(_arquivo_indice(), encoding='utf-8') as f:
            dados = json.load(f)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def gravar_indice(indice):
    try:
        with open(_arquivo_indice(), 'w', encoding='utf-8') as f:
            json.dump(indice, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def pastas_referencia():
    """Pasta de cache + pastas configuradas pelo usuario (indice['_pastas'])."""
    indice = ler_indice()
    pastas = [pasta_cache()] + [p for p in indice.get('_pastas', []) if os.path.isdir(p)]
    return list(dict.fromkeys(pastas))


def adicionar_pasta(pasta):
    indice = ler_indice()
    pastas = indice.setdefault('_pastas', [])
    if pasta and os.path.isdir(pasta) and pasta not in pastas:
        pastas.append(pasta)
        gravar_indice(indice)


def registrar(caminho, titulo=None, artista='', tipo='mix', origem='arquivo', url='', midi=None,
              bpm=None, extra=None):
    """Guarda (ou atualiza) a referencia no indice e devolve o registro."""
    indice = ler_indice()
    rid = id_referencia(caminho)
    antigo = indice.get(rid, {})
    reg = {
        'id': rid, 'caminho': os.path.abspath(caminho),
        'titulo': titulo or antigo.get('titulo') or os.path.splitext(os.path.basename(caminho))[0],
        'artista': artista or antigo.get('artista', ''),
        'tipo': tipo or antigo.get('tipo', 'mix'),          # 'isolado' | 'mix' | 'separado'
        'origem': origem, 'url': url or antigo.get('url', ''),
        'midi': midi if midi is not None else antigo.get('midi'),
        'bpm': bpm if bpm is not None else antigo.get('bpm'),
        'usado': time.time(), 'criado': antigo.get('criado', time.time()),
    }
    if extra:
        reg.update(extra)
    indice[rid] = reg
    gravar_indice(indice)
    return reg


def atualizar(rid, **campos):
    indice = ler_indice()
    if rid in indice:
        indice[rid].update(campos)
        gravar_indice(indice)
        return indice[rid]
    return None


def listar_biblioteca(busca='', incluir_partituras=True, usuario=None):
    """
        Como funciona: junta (1) as referencias do indice, (2) os arquivos de
        audio das pastas de referencia que ainda nao estao no indice e (3) as
        partituras da biblioteca do EIGUIT (so estrutura: aparecem marcadas
        'partitura' e pedem um audio para servir de timbre). Filtra por texto
        (titulo, artista, nome do arquivo), sem acento e sem caixa.
        Devolve lista de dicts ordenada pelo uso mais recente.
    """
    termos = _normalizar(busca).split()
    itens, vistos = [], set()
    indice = ler_indice()
    for rid, reg in indice.items():
        if rid.startswith('_') or not isinstance(reg, dict):
            continue
        reg = dict(reg)
        reg['existe'] = os.path.exists(reg.get('caminho', ''))
        itens.append(reg)
        vistos.add(os.path.abspath(reg.get('caminho', '')))
    for pasta in pastas_referencia():
        for raiz, _dirs, arquivos in os.walk(pasta):
            for nome in arquivos:
                if not nome.lower().endswith(EXTENSOES):
                    continue
                caminho = os.path.abspath(os.path.join(raiz, nome))
                if caminho in vistos:
                    continue
                vistos.add(caminho)
                itens.append({'id': id_referencia(caminho), 'caminho': caminho,
                              'titulo': os.path.splitext(nome)[0], 'artista': '', 'tipo': 'mix',
                              'origem': 'pasta', 'usado': 0, 'existe': True, 'midi': None})
    if incluir_partituras:
        try:
            from Estudos import biblioteca_partituras as bib
            biblioteca = bib.Biblioteca(usuario)
            for meta in biblioteca.listar():
                pasta = os.path.join(biblioteca.pasta, meta.get('id', ''))
                itens.append({'id': 'partitura_' + meta.get('id', ''), 'caminho': '',
                              'titulo': meta.get('titulo', ''), 'artista': '', 'tipo': 'partitura',
                              'origem': 'partitura', 'bpm': meta.get('bpm'), 'usado': meta.get('usado', 0),
                              'midi': os.path.join(pasta, 'original' + meta.get('ext', '.mid')),
                              'existe': False, 'partitura_id': meta.get('id')})
        except Exception:
            pass
    if termos:
        def casa(it):
            alvo = _normalizar(' '.join([it.get('titulo', ''), it.get('artista', ''),
                                         os.path.basename(it.get('caminho', '') or '')]))
            return all(t in alvo for t in termos)
        itens = [it for it in itens if casa(it)]
    return sorted(itens, key=lambda it: -(it.get('usado') or 0))


def importar_arquivo(caminho, tipo='mix', titulo=None, artista='', midi=None):
    """Registra um arquivo local (nao copia: usa o original)."""
    if not caminho or not os.path.exists(caminho):
        raise ValueError('Arquivo não encontrado.')
    if not caminho.lower().endswith(EXTENSOES):
        raise ValueError('Formato não suportado. Use MP3, WAV, FLAC ou OGG.')
    return registrar(caminho, titulo=titulo, artista=artista, tipo=tipo, origem='arquivo', midi=midi)


def escolher_arquivo(titulo='Escolha o áudio de referência', midi=False):
    """Janela de arquivo do sistema (tkinter), como o Estudo de Tempo faz."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        janela = tk.Tk()
        janela.withdraw()
        janela.attributes('-topmost', True)
        tipos = [('MIDI', '*.mid *.midi')] if midi else \
            [('Áudio', ' '.join('*' + e for e in EXTENSOES)), ('Todos', '*.*')]
        caminho = filedialog.askopenfilename(title=titulo, filetypes=tipos)
        janela.destroy()
        return caminho or ''
    except Exception:
        return ''


def escolher_pasta(titulo='Pasta com áudios de referência'):
    try:
        import tkinter as tk
        from tkinter import filedialog
        janela = tk.Tk()
        janela.withdraw()
        janela.attributes('-topmost', True)
        pasta = filedialog.askdirectory(title=titulo)
        janela.destroy()
        return pasta or ''
    except Exception:
        return ''


# ===========================================================================
# RECURSOS OPCIONAIS
# ===========================================================================

def caminho_ffmpeg():
    achado = shutil.which('ffmpeg')
    if achado:
        return achado
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def yt_dlp_disponivel():
    """(ok, mensagem)."""
    try:
        import yt_dlp  # noqa: F401
    except Exception:
        return False, ('Pesquisa online desativada: instale o yt-dlp ("pip install yt-dlp") para '
                       'pesquisar e baixar áudio. Você ainda pode importar arquivos do computador.')
    if caminho_ffmpeg() is None:
        return False, ('O yt-dlp está instalado, mas falta o ffmpeg para converter o áudio. Instale o '
                       'ffmpeg (ou "pip install imageio-ffmpeg") e tente de novo.')
    return True, ''


def _python_demucs():
    """Python que tem o demucs: o atual ou o venv do servico de transcricao."""
    candidatos = [sys.executable]
    base = os.path.join(_RAIZ, 'services', 'transcription', 'venv_ia')
    candidatos += [os.path.join(base, 'Scripts', 'python.exe'), os.path.join(base, 'bin', 'python')]
    for py in candidatos:
        if not py or not os.path.exists(py):
            continue
        if py == sys.executable:
            try:
                import importlib.util
                if importlib.util.find_spec('demucs') is not None:
                    return py
            except Exception:
                pass
            continue
        try:
            r = subprocess.run([py, '-c', 'import demucs'], capture_output=True, timeout=30)
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return None


_cache_demucs = {}


def demucs_disponivel():
    if 'py' not in _cache_demucs:
        _cache_demucs['py'] = _python_demucs()
    if _cache_demucs['py'] is None:
        return False, ('Separação desativada: instale o Demucs ("pip install demucs") ou rode o '
                       'serviço de transcrição (ele traz o Demucs no venv_ia).')
    return True, ''


# ===========================================================================
# PESQUISA E DOWNLOAD (yt-dlp, opcional, sem chave de API)
# ===========================================================================

def _parece_isolada(titulo):
    t = (titulo or '').lower()
    return any(p in t for p in PALAVRAS_ISOLADA)


def pesquisar_online(texto, limite=8, instrumento='guitarra', cancelar=None):
    """
        Como funciona: duas buscas 'ytsearch' do yt-dlp (sem baixar nada):
        a do texto + "isolated guitar/bass" e a do texto puro. Junta, tira
        repetidos e poe primeiro o que parece faixa isolada.
        Devolve lista de {titulo, canal, duracao, url, isolada}.
    """
    ok, msg = yt_dlp_disponivel()
    if not ok:
        raise RuntimeError(msg)
    import yt_dlp
    extra = 'isolated bass' if instrumento == 'baixo' else 'isolated guitar'
    consultas = [f'ytsearch{limite}:{texto} {extra}', f'ytsearch{limite}:{texto}']
    vistos, saida = set(), []
    opcoes = {'quiet': True, 'skip_download': True, 'extract_flat': True, 'no_warnings': True}
    for consulta in consultas:
        if cancelar is not None and cancelar.is_set():
            break
        try:
            with yt_dlp.YoutubeDL(opcoes) as ydl:
                info = ydl.extract_info(consulta, download=False)
        except Exception as erro:
            raise RuntimeError(f'Falha na pesquisa (sem internet?): {erro}')
        for e in (info or {}).get('entries') or []:
            url = e.get('url') or e.get('webpage_url') or ''
            if not url or url in vistos:
                continue
            if not url.startswith('http'):
                url = f'https://www.youtube.com/watch?v={e.get("id", url)}'
            vistos.add(url)
            saida.append({'titulo': e.get('title', ''), 'canal': e.get('channel') or e.get('uploader') or '',
                          'duracao': float(e.get('duration') or 0), 'url': url,
                          'isolada': _parece_isolada(e.get('title', ''))})
    saida.sort(key=lambda r: (not r['isolada'], r['duracao'] > 900))
    return saida


def baixar(url, titulo='', canal='', tipo=None, progresso=None, cancelar=None):
    """
        Baixa so o audio para o cache (WAV via ffmpeg). Se ja foi baixado,
        reaproveita. Devolve o registro da referencia.
    """
    ok, msg = yt_dlp_disponivel()
    if not ok:
        raise RuntimeError(msg)
    import yt_dlp
    indice = ler_indice()
    for reg in indice.values():
        if isinstance(reg, dict) and reg.get('url') == url and os.path.exists(reg.get('caminho', '')):
            return reg
    nome = hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]
    destino = os.path.join(pasta_cache(), nome)

    def gancho(d):
        if cancelar is not None and cancelar.is_set():
            raise RuntimeError('Download cancelado.')
        if progresso and d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            if total:
                progresso(0.9 * d.get('downloaded_bytes', 0) / total)
    opcoes = {'quiet': True, 'no_warnings': True, 'format': 'bestaudio/best', 'outtmpl': destino + '.%(ext)s',
              'noplaylist': True, 'progress_hooks': [gancho], 'ffmpeg_location': caminho_ffmpeg(),
              'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]}
    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as erro:
        raise RuntimeError(f'Não consegui baixar: {erro}')
    caminho = destino + '.wav'
    if not os.path.exists(caminho):
        achados = [f for f in os.listdir(pasta_cache()) if f.startswith(nome)]
        if not achados:
            raise RuntimeError('O download terminou, mas o arquivo de áudio não apareceu.')
        caminho = os.path.join(pasta_cache(), achados[0])
    if progresso:
        progresso(1.0)
    titulo = titulo or (info or {}).get('title', nome)
    tipo = tipo or ('isolado' if _parece_isolada(titulo) else 'mix')
    return registrar(caminho, titulo=titulo, artista=canal or (info or {}).get('channel', ''), tipo=tipo,
                     origem='download', url=url)


# ===========================================================================
# SEPARACAO (Demucs, opcional)
# ===========================================================================

def separar(reg, instrumento='guitarra', progresso=None, cancelar=None):
    """
        Como funciona: chama o Demucs (modelo de 6 fontes, que tem guitarra)
        num processo separado, le o progresso da saida e pode ser cancelado
        (mata o processo). Guarda o stem no cache e registra como 'separado'.
        Demora (minutos na CPU) e deixa artefatos: a interface avisa.
    """
    ok, msg = demucs_disponivel()
    if not ok:
        raise RuntimeError(msg)
    py = _cache_demucs['py']
    fonte = 'bass' if instrumento == 'baixo' else 'guitar'
    saida = os.path.join(pasta_cache(), 'stems')
    os.makedirs(saida, exist_ok=True)
    cmd = [py, '-m', 'demucs', '-n', 'htdemucs_6s', '--two-stems', fonte, '-o', saida, reg['caminho']]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding='utf-8', errors='ignore')
    ultima = ''
    try:
        for linha in iter(proc.stdout.readline, ''):
            ultima = linha.strip() or ultima
            if cancelar is not None and cancelar.is_set():
                proc.kill()
                raise RuntimeError('Separação cancelada.')
            m = re.search(r'(\d+)%\|', linha)
            if m and progresso:
                progresso(int(m.group(1)) / 100.0)
        proc.wait()
    finally:
        if proc.poll() is None:
            proc.kill()
    if proc.returncode != 0:
        raise RuntimeError(f'O Demucs falhou: {ultima}')
    base = os.path.splitext(os.path.basename(reg['caminho']))[0]
    stem = os.path.join(saida, 'htdemucs_6s', base, f'{fonte}.wav')
    if not os.path.exists(stem):
        raise RuntimeError('O Demucs terminou, mas o arquivo separado não foi encontrado.')
    novo = registrar(stem, titulo=f'{reg.get("titulo", base)} ({"baixo" if fonte == "bass" else "guitarra"} separada)',
                     artista=reg.get('artista', ''), tipo='separado', origem='demucs', url=reg.get('url', ''),
                     midi=reg.get('midi'), bpm=reg.get('bpm'), extra={'origem_id': reg.get('id')})
    return novo


# ===========================================================================
# AUDIO: carregar, BPM, forma de onda, compassos do MIDI
# ===========================================================================

def carregar_audio(caminho, sr_alvo=None):
    """(mono float64, sr). Reamostra se sr_alvo for dado."""
    from audio import analise_timbre as at
    x, sr = at.ler_audio(caminho)
    x = at.para_mono(x)
    if sr_alvo and int(sr_alvo) != int(sr):
        x = at.reamostrar(x, sr, sr_alvo)
        sr = int(sr_alvo)
    return x, sr


def detectar_bpm(x, sr):
    """
        BPM do trecho: librosa.beat se existir; senao autocorrelacao do
        envelope de ataques entre 60 e 200 BPM. Devolve (bpm, confianca).
    """
    try:
        import librosa
        tempo, _ = librosa.beat.beat_track(y=np.asarray(x, dtype=np.float32), sr=sr)
        bpm = float(np.atleast_1d(tempo)[0])
        if 40 < bpm < 260:
            return bpm, 0.7
    except Exception:
        pass
    from audio import analise_timbre as at
    xs = at.reamostrar(x, sr, 16000)
    hop = 256
    fl = at.fluxo_espectral(at.stft_mag(xs, 1024, hop))
    fl = fl - fl.mean()
    ac = np.correlate(fl, fl, mode='full')[fl.size - 1:]
    dt = hop / 16000.0
    lags = np.arange(ac.size) * dt
    faixa = (lags >= 60 / 200.0) & (lags <= 60 / 60.0)
    if not faixa.any() or ac[0] <= 0:
        return None, 0.0
    i = np.flatnonzero(faixa)[np.argmax(ac[faixa])]
    bpm = 60.0 / lags[i]
    # prefere a faixa 80-160 (dobro/metade)
    while bpm < 80:
        bpm *= 2
    while bpm > 170:
        bpm /= 2
    conf = float(np.clip(ac[i] / ac[0] * 2, 0, 1))
    return float(bpm), conf


def forma_de_onda(x, pontos=800):
    """Picos por fatia (0..1) para desenhar a forma de onda."""
    x = np.abs(np.asarray(x, dtype=np.float64))
    if x.size == 0:
        return np.zeros(pontos)
    fatias = np.array_split(x, pontos)
    picos = np.array([f.max() if f.size else 0.0 for f in fatias])
    return picos / (picos.max() or 1.0)


def compassos_do_midi(caminho_midi, deslocamento_s=0.0):
    """
        Como funciona: le o MIDI com o leitor do Estudo de Tempo (a mesma
        divisao em compassos/tempos) e converte o inicio de cada compasso
        para segundos pelo mapa de BPM. 'deslocamento_s' = onde o compasso 1
        comeca no audio da referencia.
        Devolve (lista de {numero, inicio_s, fim_s, formula, bpm}, bpm_inicial).
    """
    from fractions import Fraction
    from Estudos import leitor_partitura as lp
    p = lp.ler_midi(caminho_midi)
    mapa = sorted(p.mapa_bpm or [(Fraction(0), 120.0)])

    def segundos(q):
        t, q0, bpm = 0.0, Fraction(0), mapa[0][1]
        for inicio, novo in mapa[1:]:
            if inicio >= q:
                break
            t += float(inicio - q0) * 60.0 / bpm
            q0, bpm = inicio, novo
        return t + float(q - q0) * 60.0 / bpm
    compassos = []
    for i, c in enumerate(p.compassos):
        fim_q = p.compassos[i + 1].inicio if i + 1 < len(p.compassos) else \
            c.inicio + Fraction(c.num * 4, c.den)
        compassos.append({'numero': c.numero, 'inicio_s': segundos(c.inicio) + deslocamento_s,
                          'fim_s': segundos(fim_q) + deslocamento_s, 'formula': f'{c.num}/{c.den}',
                          'bpm': c.bpm, 'batidas': c.num})
    return compassos, float(mapa[0][1])


class TarefaFundo:
    """
        Como funciona: roda uma funcao numa thread, com progresso (0..1),
        mensagem, cancelamento (Event passado como 'cancelar') e resultado ou
        erro. A interface so le os campos a cada quadro.
        Para que serve: download, separacao, pesquisa, BPM e analise sem
        travar a tela.
    """

    def __init__(self, rotulo, funcao, *args, **kwargs):
        self.rotulo = rotulo
        self.progresso = 0.0
        self.mensagem = rotulo
        self.resultado = None
        self.erro = ''
        self.pronta = False
        self.cancelar_evento = threading.Event()
        self._funcao, self._args, self._kwargs = funcao, args, kwargs
        self._thread = threading.Thread(target=self._rodar, daemon=True)
        self._thread.start()

    def _rodar(self):
        try:
            self.resultado = self._funcao(*self._args, progresso=self._avancar,
                                          cancelar=self.cancelar_evento, **self._kwargs)
        except Exception as erro:
            self.erro = str(erro) or erro.__class__.__name__
        self.progresso = 1.0
        self.pronta = True

    def _avancar(self, p, mensagem=None):
        self.progresso = float(np.clip(p, 0, 1))
        if mensagem:
            self.mensagem = mensagem

    def cancelar(self):
        self.cancelar_evento.set()

    def aguardar(self, limite=60.0):
        self._thread.join(limite)
        return self.pronta
