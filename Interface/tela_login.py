import customtkinter as ctk
from tkinter import messagebox
import json
import os
from BD.gerenciador_remoto_db import GerenciadorDB

FILE_CACHE = "sessao_cache.json"

class TelaAutenticacao(ctk.CTk):
    def __init__(self, pular_cache=False):
        super().__init__()

        self.title("Guitar Studio IA - Autenticação")
        self.geometry("400x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.db = GerenciadorDB()
        self.db.inicializar_estrutura() 
        self.usuario_logado = None

        # Tenta carregar do cache primeiro (se não foi solicitado pular)
        if not pular_cache and os.path.exists(FILE_CACHE):
            try:
                with open(FILE_CACHE, "r") as f:
                    self.usuario_logado = json.load(f)
                # Se carregou com sucesso, nem mostra a tela
                self.after(100, self.destroy)
                return
            except:
                pass

        # Container principal
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.mostrar_login()

    def limpar_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def mostrar_login(self):
        self.limpar_frame()

        self.label = ctk.CTkLabel(self.frame, text="Entrar no Guitar Studio", font=("Roboto", 24))
        self.label.pack(pady=20)

        self.entry_email = ctk.CTkEntry(self.frame, placeholder_text="Email", width=250)
        self.entry_email.pack(pady=12)

        self.entry_senha = ctk.CTkEntry(self.frame, placeholder_text="Senha", show="*", width=250)
        self.entry_senha.pack(pady=12)

        # Container para checkboxes
        self.frame_checks = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.frame_checks.pack(pady=5)

        self.check_mostrar = ctk.CTkCheckBox(self.frame_checks, text="Mostrar Senha", command=self.toggle_senha, font=("Roboto", 12))
        self.check_mostrar.pack(side="left", padx=10)

        self.var_lembrar = ctk.BooleanVar(value=True)
        self.check_lembrar = ctk.CTkCheckBox(self.frame_checks, text="Lembrar Sessão", variable=self.var_lembrar, font=("Roboto", 12))
        self.check_lembrar.pack(side="left", padx=10)

        self.btn_login = ctk.CTkButton(self.frame, text="Fazer Login", command=self.acao_login, width=200)
        self.btn_login.pack(pady=20)

        self.btn_registrar = ctk.CTkButton(self.frame, text="Criar Conta", fg_color="transparent", border_width=2, command=self.mostrar_registro, width=200)
        self.btn_registrar.pack(pady=10)

        self.btn_esqueci = ctk.CTkButton(self.frame, text="Esqueci a Senha", fg_color="transparent", text_color="gray", hover=False, command=lambda: messagebox.showinfo("Info", "Funcionalidade em desenvolvimento."), width=200)
        self.btn_esqueci.pack(pady=10)

    def mostrar_registro(self):
        self.limpar_frame()

        self.label = ctk.CTkLabel(self.frame, text="Criar Nova Conta", font=("Roboto", 24))
        self.label.pack(pady=20)

        self.entry_email = ctk.CTkEntry(self.frame, placeholder_text="Email", width=250)
        self.entry_email.pack(pady=10)

        self.entry_senha = ctk.CTkEntry(self.frame, placeholder_text="Senha", show="*", width=250)
        self.entry_senha.pack(pady=10)

        self.entry_senha_rep = ctk.CTkEntry(self.frame, placeholder_text="Repetir Senha", show="*", width=250)
        self.entry_senha_rep.pack(pady=10)

        self.entry_tel = ctk.CTkEntry(self.frame, placeholder_text="Telefone (Opcional)", width=250)
        self.entry_tel.pack(pady=10)

        self.btn_confirmar = ctk.CTkButton(self.frame, text="Registrar", command=self.acao_registrar, width=200)
        self.btn_confirmar.pack(pady=20)

        self.btn_voltar = ctk.CTkButton(self.frame, text="Voltar", fg_color="gray", command=self.mostrar_login, width=200)
        self.btn_voltar.pack(pady=10)

    def toggle_senha(self):
        if self.entry_senha.cget("show") == "*":
            self.entry_senha.configure(show="")
        else:
            self.entry_senha.configure(show="*")

    def acao_login(self):
        email = self.entry_email.get()
        senha = self.entry_senha.get()

        if not email or not senha:
            messagebox.showwarning("Aviso", "Preencha todos os campos.")
            return

        usuario = self.db.verificar_login(email, senha)
        if usuario:
            self.usuario_logado = usuario
            
            # Salva no cache se solicitado
            if self.var_lembrar.get():
                try:
                    with open(FILE_CACHE, "w") as f:
                        json.dump(usuario, f)
                except:
                    pass
            
            self.destroy()
        else:
            messagebox.showerror("Erro", "Email ou senha incorretos.")

    def acao_registrar(self):
        email = self.entry_email.get()
        senha = self.entry_senha.get()
        senha_rep = self.entry_senha_rep.get()
        tel = self.entry_tel.get()

        if not email or not senha or not senha_rep:
            messagebox.showwarning("Aviso", "Preencha os campos obrigatórios.")
            return

        if senha != senha_rep:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return

        if len(senha) < 6:
            messagebox.showwarning("Aviso", "A senha deve ter pelo menos 6 caracteres.")
            return

        resultado = self.db.criar_usuario(email, senha, tel)
        if resultado:
            messagebox.showinfo("Sucesso", "Conta criada com sucesso! Faça login para continuar.")
            self.mostrar_login()
        else:
            messagebox.showerror("Erro", "Não foi possível criar a conta (Email já existe?).")

def iniciar_fluxo_autenticacao(pular_cache=False):
    app = TelaAutenticacao(pular_cache)
    app.mainloop()
    return app.usuario_logado

if __name__ == "__main__":
    user = iniciar_fluxo_autenticacao()
    print(f"Logado como: {user}")
