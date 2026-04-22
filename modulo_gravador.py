import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import threading
import os 

print("\n--- LISTA DE DISPOSITIVOS DE ÁUDIO ---")
print(sd.query_devices())

print("\n--- DISPOSITIVO PADRÃO ---")
print(sd.default.device)


class GravadorAudio:
    def __init__(self, device_id=None):
        # Configurações padrão de estúdio
        self.taxa_amostragem = 48000  
        self.canais = 1
        self.device_id = device_id
        # Estados
        self.gravando = False
        self.audio_dados = None       # Aqui ficará a matriz de áudio (Numpy Array)
        self.thread_gravacao = None

    def iniciar_gravacao(self, duracao_segundos=3):
        """Inicia a gravação sem travar a interface gráfica (Pygame)"""
        if self.gravando:
            print("Já existe uma gravação em andamento!")
            return

        self.gravando = True
        self.audio_dados = None
        
        # Cria uma linha de execução separada para não congelar a tela
        self.thread_gravacao = threading.Thread(target=self._gravar_bloqueante, args=(duracao_segundos,))
        self.thread_gravacao.start()

    def _gravar_bloqueante(self, duracao):
        """Função interna que realmente captura o áudio do microfone"""
        try:
            print(f"🎤 Gravando por {duracao} segundos no dispositivo [{self.device_id}]...")
            
            # --- NOVO: Adicionamos o parâmetro 'device' aqui ---
            gravacao = sd.rec(
                int(duracao * self.taxa_amostragem), 
                samplerate=self.taxa_amostragem, 
                channels=self.canais, 
                dtype='float32',
                device=self.device_id 
            )
            
            sd.wait() 
            
            self.audio_dados = gravacao
            print("✅ Gravação concluída com sucesso!")
            
        except Exception as e:
            print(f"\n❌ ERRO FATAL NO MICROFONE: {e}")
            self.audio_dados = None
            
        finally:
            self.gravando = False

    def salvar_wav(self, nome_arquivo="teste_ia.wav"):
        """Exporta o array de áudio para um arquivo .wav na mesma pasta do script"""
        if self.audio_dados is not None and not self.gravando:
            try:
                # Pega o caminho exato onde este arquivo .py está salvo
                pasta_do_script = os.path.dirname(os.path.abspath(__file__))
                caminho_completo = os.path.join(pasta_do_script, nome_arquivo)
                
                # Converte e salva
                audio_int16 = np.int16(self.audio_dados * 32767)
                write(caminho_completo, self.taxa_amostragem, audio_int16)
                
                # Agora ele vai te dizer EXATAMENTE onde salvou!
                print(f"💾 Áudio salvo com sucesso em: {caminho_completo}")
                
            except Exception as e:
                print(f"❌ Erro ao tentar salvar o arquivo: {e}")
        else:
            print("Nenhum áudio válido para salvar ou gravação ainda em andamento.")

    def obter_array_para_ia(self):
        """Retorna o áudio puro em formato Numpy para passar pelo Librosa/TensorFlow depois"""
        if not self.gravando and self.audio_dados is not None:
            # Achata a matriz de 2D (amostras, canais) para 1D (amostras,)
            return self.audio_dados.flatten()
        return None

# --- ÁREA DE TESTE BLINDADA ---
if __name__ == "__main__":
    import time
    
    print("\n--- LISTA DE DISPOSITIVOS DE ÁUDIO DISPONÍVEIS ---")
    # Isso vai imprimir todos os microfones e alto-falantes do seu PC
    print(sd.query_devices())
    print("-" * 50)
    
    # === MUDE ESTE NÚMERO ===
    # Olhe a lista impressa acima e coloque o número [ID] do seu microfone ou Behringer aqui.
    # Exemplo: se na lista estiver " 1 In 1 - Behringer...", mude o None para 1
    ID_DO_MEU_MICROFONE = 3 
    
    print("\nIniciando Sistema de Áudio...")
    # Passamos o ID escolhido para o gravador
    meu_gravador = GravadorAudio(device_id=ID_DO_MEU_MICROFONE)
    meu_gravador.iniciar_gravacao(duracao_segundos=3)
    
    tempo_decorrido = 0
    limite_timeout = 10 
    
    while meu_gravador.gravando and tempo_decorrido < limite_timeout:
        print(".", end="", flush=True)
        time.sleep(0.5)
        tempo_decorrido += 0.5
        
    print("\n")
    
    if meu_gravador.gravando:
        print("⚠️ O loop travou e foi forçado a parar pelo Timeout de segurança!")
        meu_gravador.gravando = False
        
    meu_gravador.salvar_wav()