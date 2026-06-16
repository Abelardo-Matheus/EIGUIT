import requests
import threading
import os

class ClienteTranscricaoIA:
    """Cliente para comunicar o Pygame com o serviço de transcrição FastAPI."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.task_id = None
        self.status = "idle"  # idle, uploading, processing, completed, failed
        self.resultado = None
        self.erro = None

    def transcrever_arquivo(self, caminho_arquivo, estado_global, instrumento="other"):
        """Inicia o processo de transcrição em uma thread separada."""
        if not os.path.exists(caminho_arquivo):
            self.status = "failed"
            self.erro = "Arquivo não encontrado."
            return

        self.status = "uploading"
        self.resultado = None
        self.erro = None
        
        thread = threading.Thread(target=self._fluxo_transcricao, args=(caminho_arquivo, estado_global, instrumento))
        thread.daemon = True
        thread.start()

    def _fluxo_transcricao(self, caminho_arquivo, estado_global, instrumento):
        try:
            # 1. Upload
            with open(caminho_arquivo, 'rb') as f:
                files = {'file': f}
                # Passar o instrumento como parâmetro na URL
                response = requests.post(f"{self.base_url}/transcribe?instrument={instrumento}", files=files)
            
            if response.status_code != 200:
                raise Exception(f"Erro no servidor: {response.status_code}")
            
            self.task_id = response.json().get("task_id")
            self.status = "processing"
            
            # 2. Polling (verificar status)
            import time
            while self.status == "processing":
                status_resp = requests.get(f"{self.base_url}/status/{self.task_id}")
                data = status_resp.json()
                
                if data["status"] == "completed":
                    self.resultado = data["result"]["notes"]
                    self.status = "completed"
                    # Injetar na tablatura do estado global
                    self._converter_para_tablatura(self.resultado, estado_global)
                    break
                elif data["status"] == "failed":
                    self.status = "failed"
                    self.erro = data.get("error", "Erro desconhecido")
                    break
                
                time.sleep(2) # Espera 2 segundos antes de tentar de novo
                
        except Exception as e:
            self.status = "failed"
            self.erro = str(e)
            print(f"[IA ERROR] {self.erro}")

    def _converter_para_tablatura(self, notas_json, estado_global):
        """Converte o formato de notas MIDI para colunas de tablatura do Guitar Studio."""
        # Se estivermos no modo de criação, injetamos direto no gerenciador de dados da tablatura
        from ui.renderizador_ui import render_tab_maker
        if render_tab_maker and hasattr(render_tab_maker, 'dados'):
            render_tab_maker.dados.preencher_da_ia(notas_json)
            return

        # Fallback para o estado global se não houver renderizador ativo
        afincacao = [40, 45, 50, 55, 59, 64] 
        for nota in notas_json:
            pitch = int(nota['pitch'])
            coluna = [None] * 6
            for i in range(5, -1, -1):
                fret = pitch - afincacao[i]
                if 0 <= fret <= 22:
                    coluna[i] = str(fret)
                    break
            if any(coluna):
                estado_global.adicionar_coluna_ia(coluna)
