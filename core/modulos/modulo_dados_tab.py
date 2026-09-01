import json
import pygame
import threading
import time

class GerenciadorDadosTablatura:
    def __init__(self, bpm=120):
        self.bpm = bpm
        self.nome_musica = "Nova Música"
        # Dicionário de trilhas: { "instrumento": grade }
        # Começa menor para caber na tela inicialmente (~2 desenhos)
        self.trilhas = {
            "Guitarra": [["-" for _ in range(64)] for _ in range(6)],
            "Baixo": [["-" for _ in range(64)] for _ in range(4)], # 4 cordas
            "Voz": [["-" for _ in range(64)] for _ in range(6)],
            "Bateria": [["-" for _ in range(64)] for _ in range(6)]
        }
        self.instrumento_atual = "Guitarra"
        self.playing = False
        self.cursor_tempo = 0
        self.playback_thread = None
        self.on_note_trigger = None
        
        self.selecao_inicio = None
        self.selecao_fim = None
        self.copia_buffer = None

    def adicionar_colunas(self, qtd):
        """Adiciona uma quantidade específica de colunas no final de todas as trilhas."""
        for inst in self.trilhas:
            num_c = len(self.trilhas[inst])
            for c in range(num_c):
                self.trilhas[inst][c].extend(["-" for _ in range(qtd)])

    @property
    def grade(self):
        """Retorna a grade do instrumento atualmente selecionado."""
        return self.trilhas[self.instrumento_atual]

    @grade.setter
    def grade(self, valor):
        self.trilhas[self.instrumento_atual] = valor

    def alternar_instrumento(self, nome):
        if nome in self.trilhas:
            self.instrumento_atual = nome
            print(f"[TAB] Alternado para {nome}")

    def adicionar_nota(self, corda, tempo, valor):
        self._garantir_capacidade(tempo)
        num_cordas = len(self.grade)
        if 0 <= corda < num_cordas:
            if isinstance(valor, (int, str)) and str(valor).isdigit():
                valor = f"{valor}v100"
            self.grade[corda][tempo] = str(valor)

    def _garantir_capacidade(self, tempo):
        """Aumenta a grade de TODAS as trilhas se necessário."""
        for inst in self.trilhas:
            while tempo >= len(self.trilhas[inst][0]):
                num_c = len(self.trilhas[inst])
                for c in range(num_c):
                    self.trilhas[inst][c].extend(["-" for _ in range(64)])

    def preencher_da_ia(self, notas_ia, instrumento="Guitarra"):
        """Converte notas da IA para uma trilha específica."""
        # Se for "other", mapeamos para Guitarra por padrão
        mapeamento = {"other": "Guitarra", "vocals": "Voz", "bass": "Baixo", "drums": "Bateria"}
        inst_alvo = mapeamento.get(instrumento, "Guitarra")
        
        # Limpar apenas a trilha alvo
        num_c = len(self.trilhas[inst_alvo])
        self.trilhas[inst_alvo] = [["-" for _ in range(len(self.trilhas[inst_alvo][0]))] for _ in range(num_c)]
        
        pitch_cordas = [64, 59, 55, 50, 45, 40] if inst_alvo != "Baixo" else [43, 38, 33, 28] # G, D, A, E
        RESOLUCAO = 8 
        
        for nota in notas_ia:
            p = round(nota['pitch'])
            tempo_col = int(round(nota['offset'] * RESOLUCAO))
            duracao_cols = max(1, int(round(nota['duration'] * RESOLUCAO)))
            
            self._garantir_capacidade(tempo_col + duracao_cols)
            
            corda_escolhida = -1
            casa_escolhida = -1
            melhor_casa = 99
            
            for idx, base_p in enumerate(pitch_cordas):
                casa = p - base_p
                if 0 <= casa <= 22:
                    if casa < melhor_casa:
                        melhor_casa = casa
                        corda_escolhida = idx
                        casa_escolhida = casa
            
            if corda_escolhida != -1:
                val = str(casa_escolhida)
                if duracao_cols > 1: val += f"d{duracao_cols}"
                self.trilhas[inst_alvo][corda_escolhida][tempo_col] = val + "v100"


    def exportar_notas_txt(self, caminho_arquivo):
        """
        Converte a grade de tablatura em nomes de notas (E2, A3, etc) e salva em TXT.
        """
        # Notas base das cordas em Standard E (E2, A2, D3, G3, B3, E4)
        # Usamos índices MIDI: E2(40), A2(45), D3(50), G3(55), B3(59), E4(64)
        midi_base = [64, 59, 55, 50, 45, 40]
        nomes_notas = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(f"PROJETO: {self.nome_musica}\n")
                f.write(f"BPM: {self.bpm}\n")
                f.write("-" * 30 + "\n\n")
                
                num_cols = len(self.grade[0])
                for t in range(num_cols):
                    notas_no_tempo = []
                    for c_idx in range(6):
                        celula = self.grade[c_idx][t]
                        if celula != "-":
                            # Extrair apenas a casa
                            import re
                            match = re.match(r"(\d+)", str(celula))
                            if match:
                                casa = int(match.group(1))
                                midi_note = midi_base[c_idx] + casa
                                
                                nome = nomes_notas[midi_note % 12]
                                oitava = (midi_note // 12) - 1
                                notas_no_tempo.append(f"{nome}{oitava}")
                    
                    if notas_no_tempo:
                        f.write(f"Tempo {t:03d}: {' '.join(notas_no_tempo)}\n")
            return True
        except Exception as e:
            print(f"[EXPORT TXT] Erro: {e}")
            return False

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
        # Extrai número da casa, técnica e metadados (v=velocity, d=duration, ~=vibrato)
        import re
        match = re.match(r"(\d+)", celula)
        if match:
            casa = int(match.group(1))
            
            # Extrair volume/velocity (vXX)
            vol_match = re.search(r"v(\d+)", celula)
            volume = int(vol_match.group(1)) if vol_match else 100
            
            # Extrair duração (dXX)
            dur_match = re.search(r"d(\d+)", celula)
            dur_cols = int(dur_match.group(1)) if dur_match else 1
            
            # Extrair técnicas (b=bend, /=slide, ~=vibrato, h=hammer, p=pull)
            tecnicas = "".join(re.findall(r"[a-zA-Z/~]+", celula))
            # Limpa marcadores de metadados das técnicas
            tecnicas = tecnicas.replace('v', '').replace('d', '')
            
            if self.on_note_trigger:
                # O callback agora aceita volume e duração
                try:
                    self.on_note_trigger(corda, casa, tecnicas, dur_cols, volume)
                except TypeError:
                    # Fallback para o callback antigo se ainda não atualizado
                    self.on_note_trigger(corda, casa, tecnicas)


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
