import json
import pygame
import threading
import time

class GerenciadorDadosTablatura:
    def __init__(self, bpm=120):
        self.bpm = bpm
        self.nome_musica = "Nova Música"
        # Matriz: 6 cordas x N tempos. Cada célula é uma string (ex: "12", "5b", "-")
        # Começamos com 64 tempos (4 compassos em 4/4 com semicolcheias)
        self.grade = [["-" for _ in range(64)] for _ in range(6)]
        self.playing = False
        self.cursor_tempo = 0
        self.playback_thread = None
        self.on_note_trigger = None # Callback para o sintetizador

    def adicionar_nota(self, corda, tempo, valor):
        if 0 <= corda < 6 and 0 <= tempo < len(self.grade[0]):
            self.grade[corda][tempo] = str(valor)

    def remover_nota(self, corda, tempo):
        if 0 <= corda < 6 and 0 <= tempo < len(self.grade[0]):
            self.grade[corda][tempo] = "-"

    def limpar_tablatura(self):
        self.grade = [["-" for _ in range(len(self.grade[0]))] for _ in range(6)]

    def set_bpm(self, bpm):
        self.bpm = bpm

    def exportar_json(self, nome_arquivo):
        dados = {
            "bpm": self.bpm,
            "grade": self.grade
        }
        with open(nome_arquivo, 'w') as f:
            json.dump(dados, f)

    def importar_json(self, nome_arquivo):
        try:
            with open(nome_arquivo, 'r') as f:
                dados = json.load(f)
                self.bpm = dados.get("bpm", 120)
                self.grade = dados.get("grade", self.grade)
        except Exception as e:
            print(f"Erro ao carregar tablatura: {e}")

    def play(self, callback_nota):
        if not self.playing:
            self.playing = True
            self.on_note_trigger = callback_nota
            self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.playback_thread.start()

    def stop(self):
        self.playing = False
        self.cursor_tempo = 0

    def _playback_loop(self):
        # Cálculo do intervalo entre semicolcheias (1/16)
        # 60 / BPM = Batida por segundo (quarta)
        # Dividimos por 4 para ter a semicolcheia
        intervalo = (60.0 / self.bpm) / 4.0
        
        while self.playing and self.cursor_tempo < len(self.grade[0]):
            start_time = time.time()
            
            # Dispara as notas de todas as cordas no tempo atual
            for corda_idx in range(6):
                celula = self.grade[corda_idx][self.cursor_tempo]
                if celula != "-":
                    self._processar_e_tocar(corda_idx + 1, celula)
            
            self.cursor_tempo += 1
            
            # Controle de tempo preciso
            elapsed = time.time() - start_time
            sleep_time = max(0, intervalo - elapsed)
            time.sleep(sleep_time)
            
        self.playing = False
        self.cursor_tempo = 0

    def _processar_e_tocar(self, corda, celula):
        # Extrai número da casa e técnica
        import re
        match = re.match(r"(\d+)([a-zA-Z/]*)", celula)
        if match:
            casa = int(match.group(1))
            tecnica = match.group(2) if match.group(2) else None
            if self.on_note_trigger:
                self.on_note_trigger(corda, casa, tecnica)

if __name__ == "__main__":
    # Teste de lógica
    mgr = GerenciadorDadosTablatura(bpm=120)
    mgr.adicionar_nota(5, 0, "0") # E grave
    mgr.adicionar_nota(5, 4, "3") # G
    mgr.adicionar_nota(5, 8, "5b") # A com bend
    
    def mock_synth(c, cs, t):
        print(f"Tocando: Corda {c}, Casa {cs}, Técnica {t}")

    print("Iniciando Playback...")
    mgr.play(mock_synth)
    time.sleep(5)
    mgr.stop()
