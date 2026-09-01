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
                try:
                    response = requests.post(f"{self.base_url}/transcribe?instrument={instrumento}", files=files, timeout=30)
                except requests.exceptions.RequestException as e:
                    raise Exception(f"Erro de conexão ao enviar áudio: {e}")
            
            if response.status_code != 200:
                raise Exception(f"Erro no servidor (Status {response.status_code})")
            
            self.task_id = response.json().get("task_id")
            self.status = "processing"
            
            # 2. Polling (verificar status)
            import time
            while self.status == "processing":
                try:
                    status_resp = requests.get(f"{self.base_url}/status/{self.task_id}", timeout=10)
                    data = status_resp.json()
                except requests.exceptions.RequestException as e:
                    print(f"[IA WARNING] Falha temporária no polling: {e}")
                    time.sleep(5)
                    continue
                
                if data["status"] == "completed":
                    self.resultado = data["result"]["notes"]
                    self.bpm_detectado = data["result"].get("bpm", 120)
                    self.instrumento_usado = data["result"].get("instrument_used", "other")
                    self.status = "completed"
                    # Injetar na trilha específica da tablatura
                    self._converter_para_tablatura(self.resultado, estado_global, self.bpm_detectado, self.instrumento_usado)
                    break
                elif data["status"] == "failed":
                    self.status = "failed"
                    self.erro = data.get("error", "Erro desconhecido")
                    break
                
                time.sleep(3) # Polling a cada 3 segundos conforme solicitado
                
        except Exception as e:
            self.status = "failed"
            self.erro = str(e)
            print(f"[IA ERROR] {self.erro}")

    def _converter_para_tablatura(self, notas_json, estado_global, bpm=120, instrumento="other"):
        """Converte o formato de notas MIDI para colunas de tablatura do Guitar Studio."""
        # Atualiza o BPM no estado e no gerenciador
        estado_global.tab_bpm = bpm
        if hasattr(estado_global, 'tab_dados_gerenciador'):
            estado_global.tab_dados_gerenciador.bpm = bpm
            # Preenche a trilha específica
            estado_global.tab_dados_gerenciador.preencher_da_ia(notas_json, instrumento)
            
        print(f"[IA] Transcrição de {len(notas_json)} notas ({instrumento}) injetada na tablatura.")



