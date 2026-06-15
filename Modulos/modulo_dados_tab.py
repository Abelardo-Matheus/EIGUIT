import json
import pygame
import threading
import time

class GerenciadorDadosTablatura:
    def __init__(self, bpm=120):
        self.bpm = bpm
        self.nome_musica = "Nova Música"
        # Matriz: 6 cordas x N tempos.
        self.grade = [["-" for _ in range(64)] for _ in range(6)]
        self.playing = False
        self.cursor_tempo = 0
        self.playback_thread = None
        self.on_note_trigger = None
        
        # Sistema de Seleção
        self.selecao_inicio = None # (corda, tempo)
        self.selecao_fim = None
        self.copia_buffer = None

    def adicionar_nota(self, corda, tempo, valor):
        self._garantir_capacidade(tempo)
        if 0 <= corda < 6:
            self.grade[corda][tempo] = str(valor)

    def _garantir_capacidade(self, tempo):
        """Aumenta a grade automaticamente se o tempo solicitado estiver fora do limite."""
        while tempo >= len(self.grade[0]):
            for c in range(6):
                self.grade[c].extend(["-" for _ in range(32)])

    def remover_nota(self, corda, tempo):
        if 0 <= corda < 6 and 0 <= tempo < len(self.grade[0]):
            self.grade[corda][tempo] = "-"

    def copiar_selecao(self, corda_ini, tempo_ini, corda_fim, tempo_fim):
        c1, c2 = min(corda_ini, corda_fim), max(corda_ini, corda_fim)
        t1, t2 = min(tempo_ini, tempo_fim), max(tempo_ini, tempo_fim)
        
        self.copia_buffer = []
        for c in range(c1, c2 + 1):
            linha = []
            for t in range(t1, t2 + 1):
                linha.append(self.grade[c][t])
            self.copia_buffer.append(linha)

    def colar_em(self, corda_alvo, tempo_alvo):
        if not self.copia_buffer: return
        
        for r_idx, linha in enumerate(self.copia_buffer):
            c_real = corda_alvo + r_idx
            if c_real >= 6: break
            for t_idx, valor in enumerate(linha):
                t_real = tempo_alvo + t_idx
                self.adicionar_nota(c_real, t_real, valor)

    def limpar_tablatura(self):
        self.grade = [["-" for _ in range(len(self.grade[0]))] for _ in range(6)]

    def preencher_da_ia(self, notas_ia):
        """Converte a lista de notas da IA para a grade da tablatura."""
        self.limpar_tablatura()
        
        # Midi notes das cordas (Standard Tuning)
        # e(64), B(59), G(55), D(50), A(45), E(40)
        pitch_cordas = [64, 59, 55, 50, 45, 40]
        
        for nota in notas_ia:
            p = round(nota['pitch'])
            # offset está em beats. 1 beat = 4 colunas (semicolcheias)
            tempo = int(nota['offset'] * 4)
            
            # Garantir que a grade tenha espaço
            self._garantir_capacidade(tempo)
            
            # Encontrar a melhor corda (procurar da mais aguda para a mais grave ou vice-versa?)
            # Geralmente prefere-se cordas mais graves para notas graves
            corda_escolhida = -1
            casa_escolhida = -1
            
            # Tentar encontrar a nota em qualquer corda (0 a 24)
            # Priorizamos a corda que resultar na menor casa >= 0
            melhor_casa = 99
            
            for idx, base_p in enumerate(pitch_cordas):
                casa = p - base_p
                if 0 <= casa <= 24:
                    if casa < melhor_casa:
                        melhor_casa = casa
                        corda_escolhida = idx
                        casa_escolhida = casa
            
            if corda_escolhida != -1:
                self.adicionar_nota(corda_escolhida, tempo, str(casa_escolhida))

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
