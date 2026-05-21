# =============================================================================
# GUITAR STUDIO IA - Copyright (c) 2026 MATHEUS ABELARDO TREVENZOLI ARAUJO
# Módulo de Integração com Songsterr API (MIDI e Tablaturas)
# =============================================================================

import requests
import re
import json
import subprocess
import os

class SongsterrAPI:
    def __init__(self):
        self.session = requests.Session()
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.session.headers.update({
            'User-Agent': self.ua
        })
        self.resultados_busca = []
        self.carregando = False
        self.diretorio_midis = "Audios/Midis"
        if not os.path.exists(self.diretorio_midis):
            os.makedirs(self.diretorio_midis)

    def buscar_musicas(self, query):
        """
        Busca músicas no Songsterr usando scraping do estado JSON da página de busca.
        Usa curl.exe como fallback para lidar com o status 103 Early Hints que trava bibliotecas padrão.
        """
        if not query:
            return []
            
        self.carregando = True
        # Garante que a query esteja formatada para URL
        query_encoded = requests.utils.quote(query)
        url = f"https://www.songsterr.com/a/wa/search?pattern={query_encoded}"
        
        html_content = ""
        try:
            # Tenta com requests primeiro
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                html_content = response.text
            else:
                # Se falhar (ex: 103 Early Hints), tenta com curl.exe
                raise Exception(f"Status {response.status_code}")
        except Exception:
            try:
                cmd = ["curl.exe", "-L", "-s", "-A", self.ua, url]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                html_content = result.stdout
            except Exception as e:
                print(f"Erro fatal ao buscar no Songsterr: {e}")
                self.carregando = False
                return []
        
        try:
            # Extrai o estado JSON da página
            match = re.search(r'<script id="state" type="application/json">(.*?)</script>', html_content)
            if not match:
                self.carregando = False
                return []
            
            data = json.loads(match.group(1))
            # O caminho correto identificado na pesquisa do estado
            songs_list = data.get('songs', {}).get('songs', {}).get('list', [])
            
            self.resultados_busca = songs_list
            self.carregando = False
            return songs_list
        except Exception as e:
            print(f"Erro ao processar dados do Songsterr: {e}")
            self.carregando = False
            return []

    def obter_detalhes_completos(self, song_id):
        """
        Busca os detalhes completos da música (trilhas, afinações) usando a API de metadados.
        """
        self.carregando = True
        url = f"https://www.songsterr.com/api/meta/{song_id}"
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        try:
            # 1. Tenta com requests primeiro (esta API costuma ser mais amigável que a busca)
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.carregando = False
                return data
            else:
                # Se falhar (ex: 103 Early Hints), tenta com curl.exe
                cmd = ["curl.exe", "-L", "-s", "-A", ua, url]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if result.stdout:
                    data = json.loads(result.stdout)
                    self.carregando = False
                    return data
        except Exception as e:
            print(f"Erro ao obter metadados do song {song_id}: {e}")
        
        self.carregando = False
        return None

    def baixar_midi(self, revision_id, song_id=None):
        """
        Baixa o arquivo MIDI para a pasta local e retorna o caminho.
        Tenta diferentes padrões de URL conhecidos em 2026.
        """
        caminho_local = os.path.join(self.diretorio_midis, f"{revision_id}.mid")
        
        # Se já existe e é um MIDI válido
        if os.path.exists(caminho_local) and os.path.getsize(caminho_local) > 4:
            is_midi = False
            with open(caminho_local, 'rb') as f:
                if f.read(4) == b'MThd':
                    is_midi = True
            if is_midi: return caminho_local

        # Obtém metadados extras para auxiliar no download
        hash_v4 = None
        v_gen = None
        detalhes = self.obter_detalhes_revisao(revision_id)
        if detalhes:
            hash_v4 = detalhes.get('audioV4Midi')
            v_gen = detalhes.get('audioV4Generated')
            if not song_id:
                song_id = detalhes.get('songId')

        # Lista de padrões de URL (Songsterr vive mudando em 2026)
        urls_para_tentar = []
        
        # 1. Padrões baseados em Revision ID
        urls_para_tentar.append(f"https://www.songsterr.com/a/ra/player/song/{revision_id}.mid")
        if v_gen:
            urls_para_tentar.append(f"https://www.songsterr.com/a/ra/player/song/{revision_id}.mid?v={v_gen}")
        
        # 2. Padrões baseados em Song ID
        if song_id:
            urls_para_tentar.append(f"https://www.songsterr.com/a/ra/player/song/{song_id}.mid")
            urls_para_tentar.append(f"https://www.songsterr.com/a/ra/player/song/{song_id}/revision/{revision_id}.mid")
            if v_gen:
                urls_para_tentar.append(f"https://www.songsterr.com/a/ra/player/song/{song_id}.mid?v={v_gen}")

        # 3. Padrões baseados em Hash V4
        if hash_v4:
            urls_para_tentar.append(f"https://audio4-1.songsterr.com/v4/data/{hash_v4}.mid")
            if v_gen:
                urls_para_tentar.append(f"https://audio4-1.songsterr.com/v4/data/{hash_v4}.mid?v={v_gen}")
            urls_para_tentar.append(f"https://dqsljvtekg760.cloudfront.net/{hash_v4}.mid")

        ua_moderno = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        referer = f"https://www.songsterr.com/a/wsa/song-tab-s{song_id}" if song_id else "https://www.songsterr.com/"

        for url in urls_para_tentar:
            try:
                if os.path.exists(caminho_local):
                    try: os.remove(caminho_local)
                    except: pass
                
                print(f"[Songsterr] Tentando URL: {url}")
                # Adicionamos headers extras que o Songsterr as vezes exige em 2026
                cmd = [
                    "curl.exe", "-L", "-s", "-A", ua_moderno, 
                    "-H", f"Referer: {referer}",
                    "-H", "X-Songsterr-Client: web",
                    "-H", "Accept: */*",
                    url, "-o", caminho_local
                ]
                subprocess.run(cmd, check=True, timeout=15)
                
                if os.path.exists(caminho_local) and os.path.getsize(caminho_local) > 4:
                    is_midi = False
                    with open(caminho_local, 'rb') as f:
                        if f.read(4) == b'MThd':
                            is_midi = True
                    
                    if is_midi:
                        print(f"[Songsterr] Download concluído com sucesso!")
                        return caminho_local
                    else:
                        print(f"[Songsterr] Arquivo inválido baixado. Tentando próxima...")
            except Exception as e:
                print(f"[Songsterr] Falha na tentativa: {e}")
        
        return None

    def obter_detalhes_revisao(self, revision_id):
        """
        Obtém metadados detalhados de uma revisão específica via API interna.
        """
        url = f"https://www.songsterr.com/api/revision/{revision_id}"
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        try:
            cmd = ["curl.exe", "-L", "-s", "-A", ua, url]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if result.stdout:
                data = json.loads(result.stdout)
                self.carregando = False
                return data
        except Exception as e:
            print(f"Erro ao obter detalhes da revisão {revision_id}: {e}")
        self.carregando = False
        return None

    def gerar_link_midi(self, revision_id):
        """
        Tenta gerar o link para o arquivo MIDI (pode requerer assinatura Plus em 2026).
        """
        return f"https://www.songsterr.com/a/ra/player/song/{revision_id}.mid"
