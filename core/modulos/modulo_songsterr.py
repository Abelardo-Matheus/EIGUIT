import requests
import re
import json
import subprocess
import os

class SongsterrAPI:
    """
        Como funciona: Define a estrutura e estado do componente 'SongsterrAPI'.
        Para que serve: Atua como o modelo principal para instâncias de 'SongsterrAPI'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_songsterr'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_songsterr'.
        """
        self.session = requests.Session()
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.session.headers.update({'User-Agent': self.ua})
        self.resultados_busca = []
        self.carregando = False
        self.diretorio_midis = 'assets/audio/Midis'
        if not os.path.exists(self.diretorio_midis):
            os.makedirs(self.diretorio_midis)

    def buscar_musicas(self, query):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'buscar musicas'.
            Para que serve: Realiza as tarefas fundamentais de 'buscar musicas' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'buscar musicas'.
        """
        if not query:
            return []
        self.carregando = True
        query_encoded = requests.utils.quote(query)
        url = f'https://www.songsterr.com/a/wa/search?pattern={query_encoded}'
        html_content = ''
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                html_content = response.text
            else:
                raise Exception(f'Status {response.status_code}')
        except Exception:
            try:
                cmd = ['curl.exe', '-L', '-s', '-A', self.ua, url]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                html_content = result.stdout
            except Exception as e:
                print(f'Erro fatal ao buscar no Songsterr: {e}')
                self.carregando = False
                return []
        try:
            match = re.search('<script id="state" type="application/json">(.*?)</script>', html_content)
            if not match:
                self.carregando = False
                return []
            data = json.loads(match.group(1))
            songs_list = data.get('songs', {}).get('songs', {}).get('list', [])
            self.resultados_busca = songs_list
            self.carregando = False
            return songs_list
        except Exception as e:
            print(f'Erro ao processar dados do Songsterr: {e}')
            self.carregando = False
            return []

    def obter_detalhes_completos(self, song_id):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'detalhes completos'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_songsterr'.
        """
        self.carregando = True
        url = f'https://www.songsterr.com/api/meta/{song_id}'
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.carregando = False
                return data
            else:
                cmd = ['curl.exe', '-L', '-s', '-A', ua, url]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.stdout:
                    data = json.loads(result.stdout)
                    self.carregando = False
                    return data
        except Exception as e:
            print(f'Erro ao obter metadados do song {song_id}: {e}')
        self.carregando = False
        return None

    def baixar_midi(self, revision_id, song_id=None):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'baixar midi'.
            Para que serve: Realiza as tarefas fundamentais de 'baixar midi' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'baixar midi'.
        """
        caminho_local = os.path.join(self.diretorio_midis, f'{revision_id}.mid')
        if os.path.exists(caminho_local) and os.path.getsize(caminho_local) > 4:
            is_midi = False
            with open(caminho_local, 'rb') as f:
                if f.read(4) == b'MThd':
                    is_midi = True
            if is_midi:
                return caminho_local
        hash_v4 = None
        v_gen = None
        detalhes = self.obter_detalhes_revisao(revision_id)
        if detalhes:
            hash_v4 = detalhes.get('audioV4Midi')
            v_gen = detalhes.get('audioV4Generated')
            if not song_id:
                song_id = detalhes.get('songId')
        urls_para_tentar = []
        urls_para_tentar.append(f'https://www.songsterr.com/a/ra/player/song/{revision_id}.mid')
        if v_gen:
            urls_para_tentar.append(f'https://www.songsterr.com/a/ra/player/song/{revision_id}.mid?v={v_gen}')
        if song_id:
            urls_para_tentar.append(f'https://www.songsterr.com/a/ra/player/song/{song_id}.mid')
            urls_para_tentar.append(f'https://www.songsterr.com/a/ra/player/song/{song_id}/revision/{revision_id}.mid')
            if v_gen:
                urls_para_tentar.append(f'https://www.songsterr.com/a/ra/player/song/{song_id}.mid?v={v_gen}')
        if hash_v4:
            urls_para_tentar.append(f'https://audio4-1.songsterr.com/v4/data/{hash_v4}.mid')
            if v_gen:
                urls_para_tentar.append(f'https://audio4-1.songsterr.com/v4/data/{hash_v4}.mid?v={v_gen}')
            urls_para_tentar.append(f'https://dqsljvtekg760.cloudfront.net/{hash_v4}.mid')
        ua_moderno = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        referer = f'https://www.songsterr.com/a/wsa/song-tab-s{song_id}' if song_id else 'https://www.songsterr.com/'
        for url in urls_para_tentar:
            try:
                if os.path.exists(caminho_local):
                    try:
                        os.remove(caminho_local)
                    except:
                        pass
                print(f'[Songsterr] Tentando URL: {url}')
                cmd = ['curl.exe', '-L', '-s', '-A', ua_moderno, '-H', f'Referer: {referer}', '-H', 'X-Songsterr-Client: web', '-H', 'Accept: */*', url, '-o', caminho_local]
                subprocess.run(cmd, check=True, timeout=15)
                if os.path.exists(caminho_local) and os.path.getsize(caminho_local) > 4:
                    is_midi = False
                    with open(caminho_local, 'rb') as f:
                        if f.read(4) == b'MThd':
                            is_midi = True
                    if is_midi:
                        print(f'[Songsterr] Download concluído com sucesso!')
                        return caminho_local
                    else:
                        print(f'[Songsterr] Arquivo inválido baixado. Tentando próxima...')
            except Exception as e:
                print(f'[Songsterr] Falha na tentativa: {e}')
        return None

    def obter_detalhes_revisao(self, revision_id):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'detalhes revisao'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'modulo_songsterr'.
        """
        url = f'https://www.songsterr.com/api/revision/{revision_id}'
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        try:
            cmd = ['curl.exe', '-L', '-s', '-A', ua, url]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if result.stdout:
                data = json.loads(result.stdout)
                self.carregando = False
                return data
        except Exception as e:
            print(f'Erro ao obter detalhes da revisão {revision_id}: {e}')
        self.carregando = False
        return None

    def gerar_link_midi(self, revision_id):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'gerar link midi'.
            Para que serve: Realiza as tarefas fundamentais de 'gerar link midi' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'gerar link midi'.
        """
        return f'https://www.songsterr.com/a/ra/player/song/{revision_id}.mid'