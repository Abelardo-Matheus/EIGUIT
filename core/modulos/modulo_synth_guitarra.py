import numpy as np
import pygame
import time

class SintetizadorGuitarra:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)
        
        # Frequências das cordas (Afinação padrão EADGBE)
        self.freq_cordas = {
            1: 329.63, # e (High E)
            2: 246.94, # B
            3: 196.00, # G
            4: 146.83, # D
            5: 110.00, # A
            6: 82.41   # E (Low E)
        }

    def _karplus_strong(self, frequency, duration):
        """Implementa o algoritmo Karplus-Strong para simular cordas dedilhadas."""
        num_samples = int(self.sample_rate * duration)
        # Tamanho do buffer de atraso
        L = int(self.sample_rate / frequency)
        
        # Inicializa o buffer com ruído branco
        delay_line = np.random.uniform(-1, 1, L).astype(np.float32)
        
        samples = np.zeros(num_samples, dtype=np.float32)
        
        # Filtro de média móvel para decaimento
        for i in range(num_samples):
            samples[i] = delay_line[0]
            # Média simples com o próximo elemento (filtro passa-baixas básico)
            avg = 0.996 * 0.5 * (delay_line[0] + delay_line[1])
            # Atualiza a linha de atraso
            delay_line = np.append(delay_line[1:], avg)
            
        return samples

    def calcular_frequencia(self, corda, casa):
        """Calcula a frequência da nota baseada na corda e na casa."""
        f_base = self.freq_cordas.get(corda, 82.41)
        return f_base * (2 ** (casa / 12.0))

    def gerar_som_nota(self, corda, casa, duracao=1.0, tecnica=None):
        """Gera o array de som para uma nota específica."""
        freq = self.calcular_frequencia(corda, casa)
        
        if tecnica == 'b': # Bend (sobe meio tom)
            samples = self._gerar_som_com_bend(freq, duracao)
        elif tecnica == 's': # Slide (exemplo simplificado)
            samples = self._gerar_som_com_slide(freq, freq * (2**(2/12)), duracao)
        else:
            samples = self._karplus_strong(freq, duracao)
            
        # Normalização e conversão para 16-bit PCM
        samples = (samples * 32767).astype(np.int16)
        return samples

    def _gerar_som_com_bend(self, freq_inicial, duracao):
        """Gera som com efeito de bend subindo meio tom."""
        num_samples = int(self.sample_rate * duracao)
        L_inicial = int(self.sample_rate / freq_inicial)
        freq_final = freq_inicial * (2**(1/12)) # Meio tom acima
        
        delay_line = np.random.uniform(-1, 1, L_inicial).astype(np.float32)
        samples = np.zeros(num_samples, dtype=np.float32)
        
        for i in range(num_samples):
            samples[i] = delay_line[0]
            # Interpolação de frequência (simplificada para o KS)
            progresso = i / num_samples
            freq_atual = freq_inicial + (freq_final - freq_inicial) * progresso
            L_atual = int(self.sample_rate / freq_atual)
            
            avg = 0.996 * 0.5 * (delay_line[0] + delay_line[1])
            
            # Ajuste dinâmico do buffer (muito simplificado)
            if len(delay_line) > L_atual:
                delay_line = np.append(delay_line[1:L_atual], avg)
            else:
                delay_line = np.append(delay_line[1:], avg)
                
        return samples

    def _gerar_som_com_slide(self, freq_ini, freq_fim, duracao):
        """Gera som com efeito de slide entre duas frequências."""
        # Implementação similar ao bend, mas com range maior
        return self._gerar_som_com_bend(freq_ini, duracao) # Simplificado para o protótipo

    def tocar_nota(self, corda, casa, tecnica=None):
        """Toca a nota imediatamente."""
        try:
            samples = self.gerar_som_nota(corda, casa, duracao=1.5, tecnica=tecnica)
            
            # Converte mono para estéreo se necessário
            if pygame.mixer.get_init()[2] == 2:
                samples = np.repeat(samples[:, np.newaxis], 2, axis=1)
                
            sound = pygame.sndarray.make_sound(samples)
            sound.play()
        except Exception as e:
            print(f"Erro ao tocar nota: {e}")

if __name__ == "__main__":
    # Teste rápido
    pygame.init()
    synth = SintetizadorGuitarra()
    print("Tocando nota de teste (Corda 6, Casa 0)...")
    synth.tocar_nota(6, 0)
    time.sleep(1)
    print("Tocando com Bend (Corda 3, Casa 7)...")
    synth.tocar_nota(3, 7, tecnica='b')
    time.sleep(2)
