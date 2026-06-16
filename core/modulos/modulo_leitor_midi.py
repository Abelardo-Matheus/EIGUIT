import mido
import time

class LeitorTablaturaMIDI:
    def __init__(self):
        self.notas_por_tempo = []

    def carregar_arquivo(self, caminho_arquivo):
        """Carrega um arquivo MIDI e extrai eventos de notas."""
        try:
            mid = mido.MidiFile(caminho_arquivo)
            # No MIDI, notas são valores de 0 a 127. 
            # Precisamos mapear isso para Cordas e Casas.
            # Vamos assumir a afinação padrão E2, A2, D3, G3, B3, E4.
            self.notas_por_tempo = []
            
            tempo_acumulado = 0
            for msg in mid:
                tempo_acumulado += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    nota_info = self._mapear_nota_para_guitarra(msg.note)
                    self.notas_por_tempo.append({
                        "tempo": tempo_acumulado,
                        "nota": msg.note,
                        "corda": nota_info["corda"],
                        "casa": nota_info["casa"]
                    })
            
            print(f"MIDI carregado: {len(self.notas_por_tempo)} notas encontradas.")
            return self.notas_por_tempo
        except Exception as e:
            print(f"Erro ao ler MIDI: {e}")
            return []

    def _mapear_nota_para_guitarra(self, pitch):
        """Mapeia o pitch MIDI para a corda e casa mais provável."""
        # Notas base (MIDI pitch) para afinação padrão:
        # E2=40, A2=45, D3=50, G3=55, B3=59, E4=64
        base_cordas = [64, 59, 55, 50, 45, 40] # 1 a 6
        
        # Estratégia simples: escolhe a corda onde a casa fica entre 0 e 22
        for i, base in enumerate(base_cordas):
            casa = pitch - base
            if 0 <= casa <= 22:
                return {"corda": i + 1, "casa": casa}
        
        # Se não couber em nenhuma, tenta a corda mais próxima
        return {"corda": 6, "casa": max(0, pitch - 40)}

    def converter_para_grade_tab(self, duracao_quarta=0.5):
        """Converte as notas MIDI para o formato de grade do Criador de Tablaturas."""
        # Assume semicolcheia como unidade de grade
        semicolcheia = duracao_quarta / 4.0
        
        # Encontra o tempo máximo para definir o tamanho da grade
        if not self.notas_por_tempo:
            return [["-" for _ in range(64)] for _ in range(6)]
            
        max_tempo = max(n["tempo"] for n in self.notas_por_tempo)
        num_colunas = int(max_tempo / semicolcheia) + 2
        
        grade = [["-" for _ in range(num_colunas)] for _ in range(6)]
        
        for n in self.notas_por_tempo:
            col = int(n["tempo"] / semicolcheia)
            corda_idx = n["corda"] - 1
            if 0 <= corda_idx < 6 and 0 <= col < num_colunas:
                grade[corda_idx][col] = str(n["casa"])
                
        return grade

if __name__ == "__main__":
    # Teste rápido
    leitor = LeitorTablaturaMIDI()
    # Se houver um arquivo midi para teste:
    # notas = leitor.carregar_arquivo("assets/audio/Midis/Metallica-One-05-20-2026.mid")
    # grade = leitor.converter_para_grade_tab()
    # print(f"Grade gerada com {len(grade[0])} colunas.")
