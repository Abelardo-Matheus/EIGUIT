"""
Módulo de Pesquisa de Timbre (Tone Matching)
==============================================

Motor de busca por trás da sub-aba "Timbre" do EIGUIT (ver `nomes_sub_abas` em
`config/app_settings.py` / `core/constantes_ui.py`). Dado um par música + artista,
varre duas trilhas de fontes na internet — pessoas que já "timbraram" a música
(trilha A) e sites/fontes institucionais (trilha B) — e monta um pacote de
resultados brutos. A extração final dos parâmetros de timbre (amp, pedais, EQ)
e o cruzamento entre fontes ("a parte inteligente") é feita por IA a partir do
prompt gerado por `gerar_prompt_para_ia`: este módulo cuida da coleta, não da
interpretação, porque extrair parâmetros de texto livre exige compreensão de
linguagem, não regex.

Segue a metodologia da skill 'pesquisa-timbre-guitarra'. Sem chave de API: as
buscas usam DuckDuckGo (HTML "lite"), a API JSON pública do Reddit e a página
de busca do YouTube, no mesmo estilo de scraping via requests + regex já usado
em `modulo_songsterr.py`.
"""

import json
import re
import subprocess
import threading
import urllib.parse

import requests


class BuscaTimbre:
    """
        Como funciona: Orquestra buscas HTTP em múltiplas fontes (fóruns,
        vídeos, sites institucionais) para reunir material bruto sobre o
        timbre de uma música, com tentativa em cascata (várias fontes) e sem
        travar caso uma fonte falhe.
        Para que serve: É o motor de coleta de dados da sub-aba "Timbre" — junta
        a matéria-prima que depois é cruzada e transformada em uma receita de
        timbre (via IA, a partir de `gerar_prompt_para_ia`).
        Onde é usada: Instanciado em `EstadoGlobal` (mesmo padrão de
        `self.songsterr = SongsterrAPI()`) e chamado a partir do controlador de
        eventos quando o usuário pesquisa na aba "Timbre".
    """

    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

    # Trilha A — onde gente que já tentou reproduzir o timbre compartilha o que achou.
    SUBREDDITS_TRILHA_A = ['guitarpedals', 'guitareffects', 'Guitar', 'Helix', 'FractalAudio', 'kemper']
    SITES_TRILHA_A = [
        'thegearpage.net',
        'gearspace.com',
        'line6.com/customtone',
        'fractalaudio.com',
        'kemper-amps.com',
        'tonehunt.org',
    ]

    # Trilha B — fontes institucionais/autoritativas.
    SITES_TRILHA_B = [
        'equipboard.com',
        'premierguitar.com',
        'guitarworld.com',
        'musicradar.com',
        'ultimate-guitar.com',
    ]

    def __init__(self):
        """
            Como funciona: Prepara a sessão HTTP (com um User-Agent de
            navegador real, igual ao usado em `SongsterrAPI`) e o estado de
            progresso.
            Para que serve: Deixa a instância pronta para ser reaproveitada em
            várias buscas sem recriar a sessão a cada chamada.
            Onde é usada: Chamado uma vez, ao criar `EstadoGlobal`.
        """
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.UA})
        self.carregando = False
        self.erro = None
        self.ultimo_pacote = None

    # ------------------------------------------------------------------
    # Infra de busca resiliente (mesmo princípio do SongsterrAPI.baixar_midi:
    # tenta várias fontes/URLs antes de desistir).
    # ------------------------------------------------------------------

    def _get_resiliente(self, url, timeout=10):
        """
            Como funciona: Tenta buscar a URL via `requests`; se falhar
            (bloqueio, timeout, erro de rede), tenta de novo via `curl.exe`
            como fallback — mesmo padrão de `SongsterrAPI.buscar_musicas`.
            Para que serve: Evita que uma falha pontual de rede derrube a
            busca inteira de timbre.
            Onde é usada: Base de todos os métodos `_buscar_*` deste módulo.
        """
        try:
            resposta = self.session.get(url, timeout=timeout)
            if resposta.status_code == 200:
                return resposta.text
            raise Exception(f'Status {resposta.status_code}')
        except Exception:
            try:
                cmd = ['curl.exe', '-L', '-s', '-A', self.UA, url]
                resultado = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout + 5)
                return resultado.stdout
            except Exception as e:
                print(f'[Timbre] Falha ao buscar {url}: {e}')
                return ''

    def _buscar_duckduckgo(self, query, max_resultados=8):
        """
            Como funciona: Consulta o endpoint HTML "lite" do DuckDuckGo (não
            exige chave de API) e extrai título, link e trecho de cada
            resultado via regex, no mesmo estilo de parsing usado em
            `modulo_songsterr.py`.
            Para que serve: É a busca-coringa usada tanto para varrer sites
            institucionais (trilha B) quanto fóruns/exchanges específicos
            (trilha A), bastando compor a query com `site:dominio.com`.
            Onde é usada: Chamado por `buscar_trilha_pessoas` e
            `buscar_trilha_sites` para cada domínio/tema pesquisado.
        """
        url = f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}'
        html_content = self._get_resiliente(url)
        if not html_content:
            return []
        blocos = re.findall(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>',
            html_content,
            re.DOTALL,
        )
        limpar = lambda s: re.sub(r'<[^>]+>', '', s).strip()
        resultados = []
        for url_bruta, titulo_bruto, trecho_bruto in blocos[:max_resultados]:
            resultados.append({
                'url': url_bruta,
                'titulo': limpar(titulo_bruto),
                'trecho': limpar(trecho_bruto),
            })
        return resultados

    def _buscar_reddit(self, query, subreddits=None, max_resultados=6):
        """
            Como funciona: Tenta primeiro a API JSON pública do Reddit
            (`/search.json`); se vier vazia ou bloqueada, cai para uma busca
            `site:reddit.com` no DuckDuckGo — a mesma lógica de fallback em
            cascata usada em `_get_resiliente`.
            Para que serve: Cobre a parte de "pessoas que já timbraram" que
            mais aparece em posts de Reddit (r/guitarpedals, r/Helix etc.).
            Onde é usada: Chamado por `buscar_trilha_pessoas`.
        """
        subreddits = subreddits or self.SUBREDDITS_TRILHA_A
        alvo = '+'.join(subreddits)
        url = (
            f'https://www.reddit.com/r/{alvo}/search.json'
            f'?q={urllib.parse.quote(query)}&restrict_sr=on&sort=relevance&limit={max_resultados}'
        )
        bruto = self._get_resiliente(url)
        resultados = []
        try:
            dados = json.loads(bruto)
            for item in dados.get('data', {}).get('children', []):
                post = item.get('data', {})
                resultados.append({
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'titulo': post.get('title', ''),
                    'trecho': (post.get('selftext') or '')[:400],
                    'subreddit': post.get('subreddit', ''),
                })
        except Exception:
            pass
        if not resultados:
            resultados = self._buscar_duckduckgo(f'site:reddit.com {query}', max_resultados)
        return resultados

    def _buscar_youtube(self, query, max_resultados=6):
        """
            Como funciona: Faz o GET da página de busca do YouTube e extrai os
            pares (videoId, título) de dentro do JSON embutido `ytInitialData`,
            no mesmo espírito de `deep_search_tab.py` (extrair um bloco JSON
            embutido em HTML via regex).
            Para que serve: Cobre vídeos de "tone match" / "how to sound like
            X", que costumam ser a fonte mais concreta de pessoas comparando o
            timbre lado a lado.
            Onde é usada: Chamado por `buscar_trilha_pessoas`.
        """
        url = f'https://www.youtube.com/results?search_query={urllib.parse.quote(query)}'
        html_content = self._get_resiliente(url)
        if not html_content:
            return []
        pares = re.findall(
            r'"videoId":"([a-zA-Z0-9_-]{11})".*?"title":\{"runs":\[\{"text":"(.*?)"\}',
            html_content,
        )
        vistos = set()
        resultados = []
        for video_id, titulo in pares:
            if video_id in vistos:
                continue
            vistos.add(video_id)
            resultados.append({
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'titulo': titulo,
                'trecho': '',
            })
            if len(resultados) >= max_resultados:
                break
        return resultados

    # ------------------------------------------------------------------
    # As duas trilhas (ver seção 2 da skill 'pesquisa-timbre-guitarra')
    # ------------------------------------------------------------------

    def confirmar_musica(self, query, songsterr_api=None):
        """
            Como funciona: Reaproveita `SongsterrAPI.buscar_musicas` (passe a
            instância já criada em `EstadoGlobal.songsterr`, se houver) para
            achar o título/artista exatos antes de gastar buscas de timbre com
            um nome errado ou uma versão cover.
            Para que serve: É o passo 1 da skill de pesquisa de timbre — fixar
            o alvo antes de buscar.
            Onde é usada: Chamado no início de `montar_pacote_pesquisa`.
        """
        if songsterr_api is None:
            from core.modulos.modulo_songsterr import SongsterrAPI
            songsterr_api = SongsterrAPI()
        try:
            resultados = songsterr_api.buscar_musicas(query)
            return resultados[0] if resultados else None
        except Exception as e:
            print(f'[Timbre] Não foi possível confirmar a música via Songsterr: {e}')
            return None

    def buscar_trilha_pessoas(self, musica, artista):
        """
            Como funciona: Dispara, cada uma protegida por try/except (uma
            fonte falhando não derruba as outras), buscas no Reddit, no
            YouTube e nos sites/exchanges de preset da trilha A.
            Para que serve: Reúne o que "pessoas que já timbraram" essa
            música documentaram — vídeos de tone match, posts de fórum,
            presets compartilhados.
            Onde é usada: Chamado por `montar_pacote_pesquisa`.
        """
        alvo = f'{artista} {musica}'.strip()
        resultados = []

        try:
            resultados += [dict(r, fonte='reddit', tipo='forum') for r in self._buscar_reddit(f'{alvo} tone rig')]
        except Exception as e:
            print(f'[Timbre] Falha na trilha A (reddit): {e}')

        try:
            resultados += [dict(r, fonte='youtube', tipo='video') for r in self._buscar_youtube(f'how to sound like {alvo} tone')]
        except Exception as e:
            print(f'[Timbre] Falha na trilha A (youtube): {e}')

        for site in self.SITES_TRILHA_A:
            try:
                resultados += [dict(r, fonte=site, tipo='forum_ou_preset') for r in self._buscar_duckduckgo(f'site:{site} {alvo} tone')]
            except Exception as e:
                print(f'[Timbre] Falha na trilha A ({site}): {e}')

        return resultados

    def buscar_trilha_sites(self, musica, artista, album=None):
        """
            Como funciona: Roda a mesma busca `site:dominio.com` (via
            `_buscar_duckduckgo`) para cada domínio institucional da trilha B,
            também protegida por try/except por fonte.
            Para que serve: Reúne entrevistas, rig rundowns e páginas oficiais
            de gear que documentam o setup real do artista.
            Onde é usada: Chamado por `montar_pacote_pesquisa`.
        """
        alvo = f'{artista} {musica} {album or ""}'.strip()
        resultados = []
        for site in self.SITES_TRILHA_B:
            try:
                resultados += [dict(r, fonte=site, tipo='site') for r in self._buscar_duckduckgo(f'site:{site} {alvo} gear rig tone')]
            except Exception as e:
                print(f'[Timbre] Falha na trilha B ({site}): {e}')
        return resultados

    # ------------------------------------------------------------------
    # Orquestração
    # ------------------------------------------------------------------

    def montar_pacote_pesquisa(self, musica, artista, album=None, ao_vivo=None):
        """
            Como funciona: Executa o passo 1 (confirmar música) e as duas
            trilhas de busca (seção 2 da skill), e embrulha tudo num
            dicionário único — a matéria-prima que ainda precisa ser cruzada
            por IA.
            Para que serve: É o método principal deste módulo; chame ele (ou a
            versão assíncrona `buscar_timbre_async`) para pesquisar o timbre
            de uma música.
            Onde é usada: Chamado pelo controlador de eventos ao clicar em
            "Buscar" na aba Timbre, ou pela IA da aba Chat.
        """
        self.carregando = True
        self.erro = None
        try:
            pacote = {
                'musica_pedida': musica,
                'artista_pedido': artista,
                'album': album,
                'ao_vivo': ao_vivo,
                'musica_confirmada': self.confirmar_musica(f'{artista} {musica}'),
                'trilha_pessoas': self.buscar_trilha_pessoas(musica, artista),
                'trilha_sites': self.buscar_trilha_sites(musica, artista, album),
            }
            self.ultimo_pacote = pacote
            return pacote
        except Exception as e:
            self.erro = str(e)
            print(f'[Timbre] Erro ao montar pacote de pesquisa: {e}')
            return None
        finally:
            self.carregando = False

    def buscar_timbre_async(self, musica, artista, callback, album=None, ao_vivo=None):
        """
            Como funciona: Roda `montar_pacote_pesquisa` numa thread separada
            e chama `callback(pacote)` quando terminar, para não travar o
            loop de 60 FPS do Pygame (a busca faz várias chamadas HTTP em
            sequência).
            Para que serve: É a forma recomendada de disparar a busca a
            partir da UI — o controlador de eventos só precisa checar
            `self.carregando` para mostrar um spinner, igual ao padrão de
            `songsterr_search_active`.
            Onde é usada: Chamado a partir de `controlador_eventos.py` quando
            o usuário confirma a busca na aba Timbre.
        """
        def _tarefa():
            pacote = self.montar_pacote_pesquisa(musica, artista, album, ao_vivo)
            callback(pacote)

        thread = threading.Thread(target=_tarefa, daemon=True)
        thread.start()
        return thread

    # ------------------------------------------------------------------
    # Ponte para a IA (a parte "inteligente" — seções 3 a 6 da skill)
    # ------------------------------------------------------------------

    def gerar_prompt_para_ia(self, pacote):
        """
            Como funciona: Serializa o pacote bruto (trilha A + trilha B) e
            monta um prompt de texto que descreve, passo a passo, como cruzar
            as fontes e escrever a receita final — seguindo a skill
            'pesquisa-timbre-guitarra' (extrair os mesmos parâmetros de cada
            fonte, cruzar por confiança, entregar receita autêntica +
            prática).
            Para que serve: É o que a aba "Chat" (ou qualquer motor de IA que
            o EIGUIT vier a usar) deve receber para transformar os resultados
            brutos numa receita de timbre estruturada — este módulo não tenta
            extrair parâmetros de texto livre sozinho, porque isso exige
            compreensão de linguagem, não regex.
            Onde é usada: Chamado depois de `montar_pacote_pesquisa`, antes de
            enviar para o modelo de IA configurado no app.
        """
        if not pacote:
            return ''

        linhas = [
            f"Música: {pacote.get('musica_pedida')}",
            f"Artista: {pacote.get('artista_pedido')}",
        ]
        if pacote.get('album'):
            linhas.append(f"Álbum: {pacote['album']}")
        if pacote.get('ao_vivo') is not None:
            linhas.append('Contexto: timbre ao vivo' if pacote['ao_vivo'] else 'Contexto: timbre de estúdio')

        confirmada = pacote.get('musica_confirmada')
        if confirmada:
            linhas.append(f"Música confirmada no Songsterr: {confirmada.get('title', '')} — {confirmada.get('artist', '')}")

        linhas.append('\n--- Trilha A: pessoas que já tentaram reproduzir esse timbre ---')
        for r in pacote.get('trilha_pessoas', []):
            linhas.append(f"[{r.get('fonte')}/{r.get('tipo')}] {r.get('titulo')} — {r.get('url')}\n  {r.get('trecho', '')}")

        linhas.append('\n--- Trilha B: sites e fontes institucionais ---')
        for r in pacote.get('trilha_sites', []):
            linhas.append(f"[{r.get('fonte')}] {r.get('titulo')} — {r.get('url')}\n  {r.get('trecho', '')}")

        linhas.append(
            '\n--- Instrução ---\n'
            'Use a skill "pesquisa-timbre-guitarra": extraia guitarra, amplificador, '
            'cadeia de pedais e observações de mixagem de cada fonte acima, cruze o que '
            'concorda entre trilha A e trilha B (alta confiança) do que aparece numa '
            'fonte só (baixa confiança/disputado), e entregue duas receitas — autêntica '
            'e prática/aproximada — citando a fonte de cada afirmação.'
        )
        return '\n'.join(linhas)
