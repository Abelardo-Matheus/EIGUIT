import numpy as np
import time

class DetectorPalhetadas:
    """
        Como funciona: Define a estrutura e estado do componente 'DetectorPalhetadas'.
        Para que serve: Atua como o modelo principal para instâncias de 'DetectorPalhetadas'.
        Onde é usada: Chamado a partir do módulo ou classe base de 'detector_palhetadas'.
    """

    def __init__(self):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'detector_palhetadas'.
        """
        self.limiar_volume = 0.05
        self.cooldown = 0.15
        self.ultimo_disparo = 0.0
        self.volume_atual = 0.0

    def processar_buffer(self, buffer_audio):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'processar buffer'.
            Para que serve: Realiza as tarefas fundamentais de 'processar buffer' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'processar buffer'.
        """
        if buffer_audio is None or len(buffer_audio) == 0:
            return False
        audio_float = np.array(buffer_audio, dtype=np.float32)
        if np.max(np.abs(audio_float)) > 1.0:
            audio_float = audio_float / 32768.0
        rms = np.sqrt(np.mean(audio_float ** 2))
        self.volume_atual = rms
        tempo_atual = time.time()
        if rms > self.limiar_volume and tempo_atual - self.ultimo_disparo > self.cooldown:
            self.ultimo_disparo = tempo_atual
            return True
        return False