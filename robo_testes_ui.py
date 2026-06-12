import pyautogui
import time
import subprocess
import os
import datetime

# ==============================================================================
# ROBO DE TESTES UI - GUITAR STUDIO IA
# ==============================================================================

class RoboTestesUI:
    def __init__(self, imagem_referencia="1.png", log_file="bugs a ser resolvidos.txt"):
        self.imagem_referencia = imagem_referencia
        self.log_file = log_file
        self.resolucao = pyautogui.size()
        self.area_janela = None
        self.ancora = None
        
        # Garante que o arquivo de log existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"--- LOG DE BUGS GERADO EM {datetime.datetime.now()} ---\n")

    def registrar_log(self, acao, resultado, detalhes=""):
        data_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{data_hora}] AÇÃO: {acao} | RESULTADO: {resultado} | DETALHES: {detalhes}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg)
        print(msg.strip())

    def capturar_evidencia(self, nome_prefixo="evidencia_bug"):
        data_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{nome_prefixo}_{data_str}.png"
        pyautogui.screenshot(filename)
        return filename

    def localizar_janela(self):
        """Localiza a janela do programa usando a imagem 1.png."""
        self.registrar_log("Localizar Janela", "Iniciando", f"Buscando {self.imagem_referencia}")
        
        try:
            # Tenta localizar a imagem na tela
            posicao = pyautogui.locateOnScreen(self.imagem_referencia, confidence=0.8)
            if posicao:
                self.area_janela = posicao
                self.ancora = pyautogui.center(posicao)
                self.registrar_log("Localizar Janela", "SUCESSO", f"Janela encontrada em {self.ancora}")
                return True
            else:
                self.registrar_log("Localizar Janela", "FALHA", "Imagem 1.png não detectada na tela.")
                return False
        except Exception as e:
            self.registrar_log("Localizar Janela", "ERRO", str(e))
            return False

    def iniciar_programa(self, comando=["python", "main.py"]):
        """Inicia o programa principal."""
        self.registrar_log("Iniciar Programa", "Executando", " ".join(comando))
        try:
            processo = subprocess.Popen(comando)
            time.sleep(5) # Aguarda o programa carregar
            return processo
        except Exception as e:
            self.registrar_log("Iniciar Programa", "ERRO", str(e))
            return None

    def testar_clique_play(self):
        """Simula um clique no botão de Play (coordenada relativa à âncora)."""
        if not self.ancora: return
        
        # Exemplo: O botão play fica a +100px em X e +50px em Y do centro da 1.png
        # Você deve ajustar esses offsets conforme a sua UI real
        alvo_x = self.ancora.x + 100
        alvo_y = self.ancora.y + 50
        
        if self._coordenada_valida(alvo_x, alvo_y):
            self.registrar_log("Teste Clique Play", "Movendo", f"Para ({alvo_x}, {alvo_y})")
            pyautogui.moveTo(alvo_x, alvo_y, duration=0.5)
            pyautogui.click()
            time.sleep(1)
        else:
            self.registrar_log("Teste Clique Play", "FALHA", "Coordenada fora dos limites da tela.")

    def _coordenada_valida(self, x, y):
        return 0 <= x < self.resolucao.width and 0 <= y < self.resolucao.height

    def executar_suite_testes(self):
        self.registrar_log("Suite de Testes", "Iniciando", f"Resolução: {self.resolucao}")
        
        if self.localizar_janela():
            self.testar_clique_play()
            # Adicione mais testes aqui
            self.registrar_log("Suite de Testes", "CONCLUÍDA")
        else:
            evidencia = self.capturar_evidencia("falha_localizacao")
            self.registrar_log("Suite de Testes", "ABORTADA", f"Interface não encontrada. Veja {evidencia}")

if __name__ == "__main__":
    robo = RoboTestesUI()
    # Descomente para iniciar o programa automaticamente:
    # robo.iniciar_programa()
    
    print("O robô iniciará em 3 segundos. Prepare a janela do programa na tela!")
    time.sleep(3)
    robo.executar_suite_testes()
