import cv2
import numpy as np
import pyautogui
import mss
import time
import threading
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configurações de Coordenadas (Ajustar conforme o layout real)
# Use um script de debug para encontrar esses pontos na sua tela
COORDENADAS = {
    "menu_estudos": (100, 100),
    "roda_ciclo_centro": (400, 400),
    "nota_C": (400, 220), # Exemplo de nota na roda
    "construtor_sequencia": (800, 600),
    "btn_modo_tonal": (200, 150),
    "btn_limpar": (950, 650)
}

# Configurações de Vídeo
FPS = 30.0
SCREEN_SIZE = pyautogui.size()

console = Console()

class ScreenRecorder:
    """
    Thread responsável por capturar a tela e compilar o vídeo.
    """
    def __init__(self, monitor_index=1):
        self.recording = False
        self.frames = []
        self.thread = None
        self.sct = mss.mss()
        
        # Monitor 0 é o bouding box de todos os monitores.
        # Monitores 1, 2, etc são as telas individuais.
        # Se estiver gravando a tela errada, o usuário pode mudar o índice.
        try:
            self.monitor = self.sct.monitors[monitor_index]
            console.print(f"[bold blue]Capturando Monitor {monitor_index}:[/] {self.monitor['width']}x{self.monitor['height']} em {self.monitor['left']},{self.monitor['top']}")
        except IndexError:
            self.monitor = self.sct.monitors[1]
            console.print("[yellow]Aviso: Monitor solicitado não encontrado, usando Monitor 1.[/yellow]")

    def _record_loop(self):
        last_time = time.time()
        while self.recording:
            # Controle de FPS simples
            if time.time() - last_time >= 1.0 / FPS:
                # Captura a tela
                img = np.array(self.sct.grab(self.monitor))
                # Converte de BGRA para BGR (OpenCV padrão)
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                self.frames.append(frame)
                last_time = time.time()
            else:
                time.sleep(0.001)

    def start_recording(self):
        self.frames = []
        self.recording = True
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()

    def stop_and_save(self, filename):
        self.recording = False
        if self.thread:
            self.thread.join()
        
        if not self.frames:
            console.print("[bold red]Nenhum frame capturado![/bold red]")
            return

        # Define o codec e cria o objeto VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, FPS, (self.monitor['width'], self.monitor['height']))

        for frame in self.frames:
            out.write(frame)
        
        out.release()
        console.print(f"[bold green]Vídeo salvo:[/] {filename}")

class FantasmaApp:
    """
    Simula ações humanas no aplicativo.
    """
    def __init__(self):
        pyautogui.FAILSAFE = True # Mover mouse para o canto da tela interrompe o script

    def mover_suave(self, x, y, duration=1.2):
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)

    def clicar(self, x, y):
        self.mover_suave(x, y, duration=0.8)
        pyautogui.click()
        time.sleep(0.5)

    def arrastar(self, x1, y1, x2, y2):
        self.mover_suave(x1, y1, duration=1.0)
        pyautogui.mouseDown()
        time.sleep(0.3)
        pyautogui.moveTo(x2, y2, duration=1.5, tween=pyautogui.easeInOutQuad)
        time.sleep(0.2)
        pyautogui.mouseUp()
        time.sleep(0.5)

# Fila de Gravação de Tutoriais
FILA_TUTORIAIS = [
    {
        "nome": "tutorial_arrastar_escala",
        "label": "Tutorial 1: Arrastar Escala para o Braço",
        "acoes": [
            ("clicar", (1000, 50)), # Ativar Alfinete (Modo Edição)
            ("arrastar", (400, 650), (400, 300)), # Arrastar do painel inferior para o braço
        ]
    },
    {
        "nome": "tutorial_config_cores",
        "label": "Tutorial 2: Personalizar Cores e Alpha",
        "acoes": [
            ("clicar", (50, 20)), # Menu Arquivo/Config
            ("clicar", (200, 150)), # Aba Configurações
            ("arrastar", (300, 400), (500, 400)), # Mover slider de Alpha
        ]
    },
    {
        "nome": "tutorial_metronomo",
        "label": "Tutorial 3: Ajustar BPM e Compasso",
        "acoes": [
            ("clicar", (800, 50)), # Abrir Metrônomo
            ("clicar", (850, 120)), # Botão + BPM
            ("clicar", (850, 120)), 
            ("clicar", (800, 180)), # Trocar Compasso
        ]
    },
    {
        "nome": "tutorial_ciclo_quintas",
        "label": "Tutorial 4: Explorar Ciclo de Quintas",
        "acoes": [
            ("clicar", (500, 20)), # Menu Estudos
            ("clicar", (500, 100)), # Ciclo de Quintas
            ("mover", (400, 400)), # Mostrar a Roda
            ("clicar", (450, 300)), # Selecionar Nota G
        ]
    }
]

def executar_automacao():
    # Caminho absoluto para evitar confusão de diretórios
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_videos = os.path.join(base_dir, "videos_exportados")
    
    if not os.path.exists(path_videos):
        os.makedirs(path_videos)

    # Inicializa o gravador. Tente mudar o índice se gravar a tela errada.
    # Monitores comuns: 1 (Principal), 2 (Secundário)
    recorder = ScreenRecorder(monitor_index=1) 
    fantasma = FantasmaApp()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        total_tasks = len(FILA_TUTORIAIS)
        
        for idx, tutorial in enumerate(FILA_TUTORIAIS, 1):
            task_id = progress.add_task(f"🎬 Gravando {idx}/{total_tasks}: {tutorial['label']}...", total=None)
            
            output_path = os.path.join(path_videos, f"{tutorial['nome']}.mp4")
            
            # Inicia Gravação
            recorder.start_recording()
            time.sleep(1) # Delay inicial

            # Executa Ações
            for acao in tutorial["acoes"]:
                tipo = acao[0]
                params = acao[1:]
                
                if tipo == "clicar":
                    fantasma.clicar(*params[0])
                elif tipo == "arrastar":
                    fantasma.arrastar(*params[0], *params[1])
                elif tipo == "mover":
                    fantasma.mover_suave(*params[0])

            time.sleep(2) # Delay final para visualização
            
            # Finaliza e Salva
            recorder.stop_and_save(output_path)
            progress.remove_task(task_id)

    console.print("\n[bold green]✨ Todos os tutoriais foram gerados com sucesso![/bold green]")

if __name__ == "__main__":
    console.print("[bold blue]Iniciando Gerador de Vídeos de Tutorial[/bold blue]")
    console.print("[yellow]Certifique-se de que o aplicativo está aberto e visível no monitor principal.[/yellow]\n")
    
    # Listar monitores disponíveis para ajudar o usuário
    import mss
    with mss.mss() as sct:
        for i, m in enumerate(sct.monitors):
            console.print(f"Monitor {i}: {m['width']}x{m['height']} em {m['left']},{m['top']}")
    
    confirm = input("\nPressione ENTER para iniciar ou CTRL+C para cancelar...")
    
    try:
        executar_automacao()
    except KeyboardInterrupt:
        console.print("\n[bold red]Automação cancelada pelo usuário.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Erro durante a automacao:[/] {e}")
