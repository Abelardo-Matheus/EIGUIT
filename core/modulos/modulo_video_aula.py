import customtkinter as ctk
try:
    from tkvideoplayer import TkinterVideo
except ImportError:
    try:
        from tkVideoPlayer import TkinterVideo
    except ImportError:
        raise ImportError("tkvideoplayer library not found")
import os
import multiprocessing

class JanelaPlayerVideo(ctk.CTkToplevel):
    def __init__(self, parent, video_path, titulo="Videoaula"):
        super().__init__(parent)
        
        self.title(titulo)
        
        # Tamanho mais compacto para a janela
        largura_janela = 900
        altura_janela = 650
        
        # Centraliza a janela na tela
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w // 2) - (largura_janela // 2)
        pos_y = (screen_h // 2) - (altura_janela // 2)
        
        self.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        
        # Habilita o redimensionamento da janela
        self.resizable(True, True)
        
        self.attributes("-topmost", True)
        self.focus_force() # Traz o foco para a janela imediatamente
        
        # Configuração de Grid para preenchimento total
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # Container do Vídeo sem bordas (border_width=0)
        self.video_container = ctk.CTkFrame(self, fg_color="black", corner_radius=0, border_width=0)
        self.video_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # O Player de Vídeo com scaled=True: Ele vai esticar para o tamanho real da janela
        self.video_player = TkinterVideo(master=self.video_container, scaled=True, padx=0, pady=0, borderwidth=0)
        self.video_player.pack(expand=True, fill="both")
        
        # Frame de Controles mais compacto e sem bordas
        self.frame_controles = ctk.CTkFrame(self, height=80, corner_radius=0, border_width=0)
        self.frame_controles.grid(row=1, column=0, sticky="ew")
        
        # --- BARRA DE NAVEGAÇÃO (SEEK BAR) ---
        self.frame_seek = ctk.CTkFrame(self.frame_controles, fg_color="transparent")
        self.frame_seek.pack(fill="x", padx=10, pady=(5, 0))
        
        self.lbl_tempo_atual = ctk.CTkLabel(self.frame_seek, text="00:00", font=("Roboto", 12))
        self.lbl_tempo_atual.pack(side="left", padx=5)
        
        self.slider_seek = ctk.CTkSlider(
            self.frame_seek, 
            from_=0, 
            to=100, 
            height=18,
            command=self.ao_navegar_slider
        )
        self.slider_seek.pack(side="left", fill="x", expand=True, padx=5)
        self.slider_seek.set(0)
        
        self.lbl_tempo_total = ctk.CTkLabel(self.frame_seek, text="00:00", font=("Roboto", 12))
        self.lbl_tempo_total.pack(side="left", padx=5)
        
        # Botões
        self.frame_botoes = ctk.CTkFrame(self.frame_controles, fg_color="transparent")
        self.frame_botoes.pack(fill="x", padx=10, pady=(2, 5))
        
        self.btn_play = ctk.CTkButton(self.frame_botoes, text="▶ Play", width=100, command=self.video_player.play, fg_color="#2ecc71")
        self.btn_play.pack(side="left", padx=10, pady=5)
        
        self.btn_pause = ctk.CTkButton(self.frame_botoes, text="⏸ Pause", width=100, command=self.video_player.pause, fg_color="#f39c12")
        self.btn_pause.pack(side="left", padx=5, pady=5)
        
        self.btn_fechar = ctk.CTkButton(self.frame_botoes, text="✖ Fechar Aula", width=120, command=self.fechar_aula, fg_color="#e74c3c")
        self.btn_fechar.pack(side="right", padx=10, pady=5)
        
        # Eventos do Player para atualizar a barra
        self.video_player.bind("<<Duration>>", self.ao_carregar_duracao)
        self.video_player.bind("<<SecondChanged>>", self.ao_mudar_segundo)
        self.video_player.bind("<<Ended>>", lambda e: self.slider_seek.set(self.slider_seek.cget("to")))

        if os.path.exists(video_path):
            self.video_player.load(video_path)
            self.video_player.play()
        
        self.protocol("WM_DELETE_WINDOW", self.fechar_aula)

    def formatar_tempo(self, segundos):
        mins = int(segundos // 60)
        segs = int(segundos % 60)
        return f"{mins:02d}:{segs:02d}"

    def ao_carregar_duracao(self, event):
        duracao = self.video_player.video_info()["duration"]
        self.slider_seek.configure(to=duracao)
        self.lbl_tempo_total.configure(text=self.formatar_tempo(duracao))

    def ao_mudar_segundo(self, event):
        tempo_atual = self.video_player.current_duration()
        self.slider_seek.set(tempo_atual)
        self.lbl_tempo_atual.configure(text=self.formatar_tempo(tempo_atual))

    def ao_navegar_slider(self, valor):
        self.video_player.seek(int(valor))
        self.lbl_tempo_atual.configure(text=self.formatar_tempo(valor))

    def fechar_aula(self):
        try: self.video_player.stop()
        except: pass
        self.destroy()
        if hasattr(self, 'fechar_callback'):
            self.fechar_callback()

# Variável global para rastrear o processo ativo (Singleton)
_processo_ativo = None

def _run_player(video_path, titulo):
    root = ctk.CTk()
    root.withdraw()
    player = JanelaPlayerVideo(root, video_path, titulo)
    player.fechar_callback = lambda: root.quit()
    root.mainloop()

def abrir_player_video_async(video_path, titulo="Videoaula"):
    """
    Lança o player de vídeo em um processo separado.
    Garante que apenas UMA janela esteja aberta por vez.
    """
    global _processo_ativo
    
    # Se já houver um processo rodando, tenta matá-lo antes de abrir o novo
    if _processo_ativo and _processo_ativo.is_alive():
        _processo_ativo.terminate()
        _processo_ativo.join()
        
    _processo_ativo = multiprocessing.Process(target=_run_player, args=(video_path, titulo))
    _processo_ativo.daemon = True
    _processo_ativo.start()

# Exemplo de como chamar (para fins de teste/referência):
# if __name__ == "__main__":
#     app = ctk.CTk()
#     janela = JanelaPlayerVideo(app, 'automacao_tutoriais/videos_exportados/tutorial_metronomo.mp4')
#     app.mainloop()
