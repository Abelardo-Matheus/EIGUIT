# -*- coding: utf-8 -*-
"""
Analisador IA - Fase 3: detector de efeitos treinado LOCALMENTE.

Gera um conjunto de dados sintetico com o proprio motor de pedais
(combinacoes de efeitos e parametros sobre as guitarras base do projeto e,
se existirem, sobre as gravacoes limpas de calibracao do usuario), extrai o
perfil de timbre de cada exemplo e treina um classificador leve do
scikit-learn (floresta aleatoria multi-rotulo). O modelo fica em
audio/config_analise/modelo_efeitos.pkl e REFORCA os detectores por regras
(mistura das duas probabilidades, peso no config). Tudo offline.

Sem scikit-learn, reforcar() nao faz nada e a interface explica.

Rodar pelo terminal:
    python -m audio.treinar_detector --amostras 600
"""
import argparse
import os
import pickle
import time

import numpy as np

from audio import analise_timbre as at
from audio import efeitos_pedais as motor

ARQUIVO_MODELO = os.path.join(at.PASTA_CONFIG, 'modelo_efeitos.pkl')
# efeitos que o modelo aprende (ganho e EQ ja sao medidas continuas)
ROTULOS = ['compressor', 'gate', 'volume', 'wah', 'autowah', 'tremolo', 'chorus', 'flanger',
           'phaser', 'vibrato', 'delay', 'reverb', 'octaver', 'ring']
# faixas "musicais" de cada parametro (o dataset nao precisa de extremos absurdos)
FAIXAS = {
    'compressor': {'sustain': (0.4, 1.0), 'attack': (3, 40)},
    'gate': {'limiar': (-50, -30)},
    'volume': {'ataque': (0.25, 0.9)},
    'wah': {'pedal': (0.2, 0.8), 'q': (3, 9), 'auto': (0.8, 3.0)},
    'autowah': {'sens': (0.4, 0.9), 'q': (3, 9), 'resposta': (30, 150)},
    'tremolo': {'rate': (2.5, 9.0), 'depth': (0.4, 0.95), 'forma': (0.0, 0.8)},
    'chorus': {'rate': (0.3, 2.0), 'depth': (0.35, 0.9), 'mix': (0.4, 0.8)},
    'flanger': {'rate': (0.1, 0.8), 'depth': (0.5, 1.0), 'feedback': (0.3, 0.8)},
    'phaser': {'rate': (0.2, 2.0), 'depth': (0.5, 1.0), 'mix': (0.7, 1.0)},
    'vibrato': {'rate': (3.0, 8.0), 'depth': (0.2, 0.7)},
    'delay': {'time': (120, 800), 'feedback': (0.15, 0.6), 'mix': (0.2, 0.6)},
    'reverb': {'decay': (0.8, 5.0), 'mix': (0.2, 0.6)},
    'octaver': {'sub': (0.4, 0.9), 'seco': (0.6, 1.0)},
    'ring': {'freq': (80, 400), 'mix': (0.5, 1.0)},
}
GANHO = {'boost': ('ganho', 6, 18), 'overdrive': ('drive', 0.2, 0.8), 'distorcao': ('dist', 0.3, 0.9)}


def sklearn_disponivel():
    try:
        import sklearn  # noqa: F401
        return True, ''
    except Exception:
        return False, ('Detector treinado desativado: instale o scikit-learn ("pip install scikit-learn") '
                       'para treinar e usar o modelo local. As regras continuam funcionando.')


def _bases(sr, rng, extras=()):
    """Audios limpos para o dataset: guitarras humanizadas, DI do sampler e gravacoes do usuario."""
    import sys
    pasta_val = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_validacao')
    if pasta_val not in sys.path:
        sys.path.insert(0, pasta_val)
    import sinais_analisador as sa
    bases = []
    for chave in motor.ORDEM_BASES:
        for semente in (3, 7):
            bases.append(sa.base_humana(chave, 2, semente))
        bases.append(sa.base_di(chave, 2, 11))
    for caminho in extras:
        try:
            x, s = at.ler_audio(caminho)
            bases.append(at.reamostrar(at.para_mono(x), s, sr))
        except Exception:
            continue
    return bases


def gravacoes_do_usuario():
    """WAVs de calibracao guardados pelo Analisador (som limpo real do usuario)."""
    try:
        from audio import dispositivos as disp
        pasta = os.path.join(disp.pasta_dados(), 'perfis')
        return [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith('.wav')]
    except Exception:
        return []


def _exemplo(x, sr, rng):
    """Uma cadeia aleatoria (0-3 efeitos + ganho opcional) aplicada a um trecho de x."""
    from Estudos import curriculo_pedais as cur
    n = int(min(x.size, 6.0 * sr))
    ini = int(rng.integers(0, max(1, x.size - n)))
    trecho = x[ini:ini + n].copy()
    trecho *= rng.uniform(0.6, 1.0) / (np.max(np.abs(trecho)) or 1.0) * 0.5
    trecho += rng.standard_normal(trecho.size) * 10 ** (rng.uniform(-85, -65) / 20)
    ativos = list(rng.choice(ROTULOS, size=int(rng.choice([0, 1, 1, 2, 2, 3])), replace=False))
    cadeia = []
    if rng.random() < 0.5:
        pid = str(rng.choice(list(GANHO)))
        chave, lo, hi = GANHO[pid]
        cadeia.append((pid, {chave: rng.uniform(lo, hi)}))
    for pid in ativos:
        par = {k: rng.uniform(*v) for k, v in FAIXAS[pid].items()}
        cadeia.append((pid, par))
    ordem = ['wah', 'autowah', 'compressor', 'octaver', 'boost', 'overdrive', 'distorcao', 'ring', 'tremolo',
             'vibrato', 'chorus', 'phaser', 'flanger', 'volume', 'delay', 'reverb', 'gate']
    cadeia.sort(key=lambda it: ordem.index(it[0]))
    y = trecho
    for pid, par in cadeia:
        valores = cur.valores_padrao(cur.PEDAIS_POR_ID[pid])
        valores.update(par)
        y = motor.aplicar_efeito(y, sr, pid, valores)
        if y.ndim == 2:
            y = y.mean(axis=1)
    rotulo = np.array([1 if r in ativos else 0 for r in ROTULOS], dtype=np.int8)
    return y, rotulo


def vetor(medidas, efeitos, chaves_medidas):
    """Caracteristicas do classificador: medidas do perfil + scores das regras."""
    v = []
    for k in chaves_medidas:
        valor = medidas.get(k, {}).get('valor')
        v.append(np.nan if valor is None else float(valor))
    for r in ROTULOS:
        v.append(float(efeitos.get(r, {}).get('score', 0.0)))
    return np.array(v, dtype=np.float64)


def gerar_dataset(amostras=400, semente=0, progresso=None, cancelar=None):
    """Devolve (X, Y, chaves_medidas)."""
    global _desligar_reforco
    rng = np.random.default_rng(semente)
    sr = motor.SR_PADRAO
    bases = _bases(sr, rng, gravacoes_do_usuario())
    X, Y, chaves = [], [], None
    cfg = at.carregar_config('guitarra')
    for i in range(amostras):
        if cancelar is not None and cancelar.is_set():
            break
        y, rot = _exemplo(bases[int(rng.integers(0, len(bases)))], sr, rng)
        _desligar_reforco = True               # o dataset usa so as regras
        try:
            p = at.perfil_timbre(y, sr, cfg)
        finally:
            _desligar_reforco = False
        if chaves is None:
            chaves = sorted(k for k, m in p['medidas'].items() if isinstance(m.get('valor'), (int, float))
                            or m.get('valor') is None)
        X.append(vetor(p['medidas'], p['efeitos'], chaves))
        Y.append(rot)
        if progresso:
            progresso(0.85 * (i + 1) / amostras, f'Gerando exemplos ({i + 1}/{amostras})...')
    return np.array(X), np.array(Y), chaves


def treinar(amostras=400, semente=0, progresso=None, cancelar=None, salvar=True):
    """
        Como funciona: gera o dataset, separa 20% para teste, treina uma
        floresta aleatoria multi-rotulo (valores faltando viram a mediana) e
        mede a acuracia por efeito no teste. Salva o modelo no projeto.
        Devolve as metricas.
    """
    ok, msg = sklearn_disponivel()
    if not ok:
        raise RuntimeError(msg)
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    X, Y, chaves = gerar_dataset(amostras, semente, progresso, cancelar)
    if len(X) < 40:
        raise RuntimeError('Poucos exemplos para treinar.')
    rng = np.random.default_rng(semente + 1)
    idx = rng.permutation(len(X))
    corte = int(0.8 * len(X))
    tr, te = idx[:corte], idx[corte:]
    if progresso:
        progresso(0.9, 'Treinando o classificador...')
    modelo = make_pipeline(SimpleImputer(strategy='median'),
                           RandomForestClassifier(n_estimators=120, max_depth=14, min_samples_leaf=2,
                                                  random_state=semente, n_jobs=1))
    modelo.fit(X[tr], Y[tr])
    pred = modelo.predict(X[te])
    acertos = {r: float(np.mean(pred[:, i] == Y[te][:, i])) for i, r in enumerate(ROTULOS)}
    # comparacao justa: so as regras (score >= 0.6) no mesmo teste
    base = len(chaves)
    regras = {r: float(np.mean((X[te][:, base + i] >= 0.6) == Y[te][:, i])) for i, r in enumerate(ROTULOS)}
    metricas = {'amostras': int(len(X)), 'acuracia_modelo': acertos, 'acuracia_regras': regras,
                'media_modelo': float(np.mean(list(acertos.values()))),
                'media_regras': float(np.mean(list(regras.values()))), 'quando': time.time()}
    if salvar:
        modelo.fit(X, Y)                        # o modelo final usa todos os exemplos
        with open(ARQUIVO_MODELO, 'wb') as f:
            pickle.dump({'modelo': modelo, 'chaves': chaves, 'rotulos': ROTULOS,
                         'versao_sklearn': sklearn.__version__, 'metricas': metricas}, f)
        _cache.clear()
    if progresso:
        progresso(1.0, 'Modelo treinado')
    return metricas


_cache = {}
_desligar_reforco = False


def carregar_modelo():
    """O modelo salvo (ou None: sem arquivo, sem sklearn ou versao incompativel)."""
    if 'modelo' in _cache:
        return _cache['modelo']
    pacote = None
    if os.path.exists(ARQUIVO_MODELO) and sklearn_disponivel()[0]:
        try:
            import sklearn
            with open(ARQUIVO_MODELO, 'rb') as f:
                pacote = pickle.load(f)
            if pacote.get('versao_sklearn') != sklearn.__version__:
                pacote['aviso'] = (f'modelo treinado com scikit-learn {pacote.get("versao_sklearn")}; '
                                   f'instalado {sklearn.__version__} (treine de novo se der erro)')
        except Exception:
            pacote = None
    _cache['modelo'] = pacote
    return pacote


def reforcar(efeitos, medidas, cfg):
    """
        Mistura a probabilidade do modelo com o score das regras:
            score = (1 - peso) * regras + peso * modelo
        e refaz sim/nao/incerto com os mesmos limiares. Marca 'modelo' em
        cada detector reforcado. Sem modelo, nao faz nada.
    """
    if _desligar_reforco:
        return
    pacote = carregar_modelo()
    if not pacote:
        return
    peso = cfg.get('detectores', {}).get('modelo', {}).get('peso', 0.35)
    try:
        v = vetor(medidas, efeitos, pacote['chaves']).reshape(1, -1)
        probs = pacote['modelo'].predict_proba(v)
    except Exception:
        return
    for i, r in enumerate(pacote['rotulos']):
        if r not in efeitos:
            continue
        p = probs[i]
        prob = float(p[0, 1]) if p.shape[1] > 1 else float(p[0, 0] if pacote['modelo'].classes_[i][0] == 1 else 0)
        det = efeitos[r]
        det['modelo'] = prob
        score = (1 - peso) * det['score'] + peso * prob
        det['score'] = float(score)
        lim = cfg.get('detectores', {}).get(r, {})
        sim, nao = lim.get('limiar_sim', 0.6), lim.get('limiar_nao', 0.3)
        if det['presenca'] != 'incerto' or det.get('confianca', 0) > 0.25:
            if score >= sim:
                det['presenca'] = 'sim'
            elif score <= nao:
                det['presenca'] = 'nao'
            else:
                det['presenca'] = 'incerto'


def main():
    ap = argparse.ArgumentParser(description='Treina o detector de efeitos local do Analisador IA.')
    ap.add_argument('--amostras', type=int, default=400)
    ap.add_argument('--semente', type=int, default=0)
    args = ap.parse_args()
    t = time.time()
    m = treinar(args.amostras, args.semente,
                progresso=lambda p, msg='': print(f'\r{msg} {p * 100:5.1f}%', end='', flush=True))
    print(f'\nPronto em {time.time() - t:.0f} s. Acurácia média: modelo {m["media_modelo"]:.2f} x '
          f'regras {m["media_regras"]:.2f}')
    for r in ROTULOS:
        print(f'  {r:<11} modelo {m["acuracia_modelo"][r]:.2f}   regras {m["acuracia_regras"][r]:.2f}')
    print(f'Modelo salvo em {ARQUIVO_MODELO}')


if __name__ == '__main__':
    main()
