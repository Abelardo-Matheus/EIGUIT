# -*- coding: utf-8 -*-
"""Tela de autenticacao do EIGUIT Studio (CustomTkinter) com o novo design."""
import json
import os
from tkinter import messagebox

import customtkinter as ctk

from BD.gerenciador_remoto_db import GerenciadorDB
from config.design_system import PALETA_CLARA, PALETA_ESCURA, TEMA

FILE_CACHE = 'sessao_cache.json'


def _hex(cor):
    """Converte uma cor RGB do design system para o formato aceito pelo CTk."""
    return '#%02x%02x%02x' % (int(cor[0]), int(cor[1]), int(cor[2]))


class Paleta:
    """Cores da tela de login derivadas do design system, nos dois modos."""

    def __init__(self, modo):
        p = PALETA_ESCURA if modo == 'escuro' else PALETA_CLARA
        self.modo = modo
        self.fundo = _hex(p['fundo'])
        self.cartao = _hex(p['superficie'])
        self.campo = _hex(p['superficie_alt'])
        self.borda = _hex(p['borda'])
        self.texto = _hex(p['texto'])
        self.texto_suave = _hex(p['texto_suave'])
        self.texto_apagado = _hex(p['texto_apagado'])
        self.primaria = _hex(p['primaria'])
        self.primaria_clara = _hex(p['primaria_clara'])
        self.alerta = _hex(p['alerta'])
        self.verde = _hex(p['verde'])


class TelaAutenticacao(ctk.CTk):
    """
        Como funciona: Janela de login/registro construida com CustomTkinter,
        seguindo a mesma paleta e o mesmo espacamento do estudio.
        Para que serve: Autenticar o usuario antes de abrir o workspace.
        Onde e usada: Chamada por main.py no inicio da aplicacao.
    """

    LARGURA = 440
    ALTURA = 660

    def __init__(self, pular_cache=False):
        """
            Como funciona: Monta a janela, tenta reaproveitar a sessao em cache
            e exibe o formulario de login.
            Para que serve: Preparar o fluxo de autenticacao.
            Onde e usada: Instanciada por iniciar_fluxo_autenticacao.
        """
        super().__init__()
        self.cores = Paleta(TEMA.modo)
        ctk.set_appearance_mode('dark' if TEMA.escuro else 'light')
        ctk.set_default_color_theme('blue')

        self.title('EIGUIT Studio - Autenticacao')
        self.geometry(f'{self.LARGURA}x{self.ALTURA}')
        self.resizable(False, False)
        self.configure(fg_color=self.cores.fundo)

        self.db = GerenciadorDB()
        self.db.inicializar_estrutura()
        self.usuario_logado = None

        if not pular_cache and os.path.exists(FILE_CACHE):
            try:
                with open(FILE_CACHE, 'r', encoding='utf-8') as arq:
                    self.usuario_logado = json.load(arq)
                self.after(100, self.destroy)
                return
            except Exception:
                pass

        self._montar_cabecalho()
        self.frame = ctk.CTkFrame(self, fg_color=self.cores.cartao, corner_radius=16)
        self.frame.pack(pady=(0, 24), padx=24, fill='both', expand=True)
        self.mostrar_login()

    # ------------------------------------------------------------- estrutura
    def _montar_cabecalho(self):
        """Marca do produto no topo da janela."""
        topo = ctk.CTkFrame(self, fg_color='transparent')
        topo.pack(pady=(28, 18))

        logo = ctk.CTkLabel(
            topo, text='E', width=44, height=44, corner_radius=12,
            fg_color=self.cores.primaria, text_color='#ffffff',
            font=ctk.CTkFont(size=22, weight='bold'))
        logo.pack()

        ctk.CTkLabel(topo, text='EIGUIT Studio', text_color=self.cores.texto,
                     font=ctk.CTkFont(size=22, weight='bold')).pack(pady=(12, 2))
        ctk.CTkLabel(topo, text='Guitar Studio IA', text_color=self.cores.texto_apagado,
                     font=ctk.CTkFont(size=12)).pack()

    def limpar_frame(self):
        """
            Como funciona: Remove todos os widgets do cartao central.
            Para que serve: Alternar entre os formularios de login e registro.
            Onde e usada: Antes de montar cada formulario.
        """
        for widget in self.frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------- widgets
    def _titulo(self, texto, subtitulo=''):
        ctk.CTkLabel(self.frame, text=texto, text_color=self.cores.texto,
                     font=ctk.CTkFont(size=19, weight='bold')).pack(pady=(28, 2))
        if subtitulo:
            ctk.CTkLabel(self.frame, text=subtitulo,
                         text_color=self.cores.texto_apagado,
                         font=ctk.CTkFont(size=12)).pack(pady=(0, 6))

    def _campo(self, placeholder, mostrar=None):
        entrada = ctk.CTkEntry(
            self.frame, placeholder_text=placeholder, width=280, height=42,
            corner_radius=8, border_width=1, fg_color=self.cores.campo,
            border_color=self.cores.borda, text_color=self.cores.texto,
            placeholder_text_color=self.cores.texto_apagado,
            font=ctk.CTkFont(size=13))
        if mostrar is not None:
            entrada.configure(show=mostrar)
        entrada.pack(pady=7)
        return entrada

    def _botao_primario(self, texto, comando):
        botao = ctk.CTkButton(
            self.frame, text=texto, command=comando, width=280, height=44,
            corner_radius=8, fg_color=self.cores.primaria,
            hover_color=self.cores.primaria_clara, text_color='#ffffff',
            font=ctk.CTkFont(size=14, weight='bold'))
        botao.pack(pady=(18, 8))
        return botao

    def _botao_secundario(self, texto, comando):
        botao = ctk.CTkButton(
            self.frame, text=texto, command=comando, width=280, height=42,
            corner_radius=8, fg_color='transparent', border_width=1,
            border_color=self.cores.borda, text_color=self.cores.texto,
            hover_color=self.cores.campo, font=ctk.CTkFont(size=13))
        botao.pack(pady=6)
        return botao

    def _status(self):
        rotulo = ctk.CTkLabel(self.frame, text='', text_color=self.cores.alerta,
                              font=ctk.CTkFont(size=12), wraplength=280)
        rotulo.pack(pady=(4, 0))
        return rotulo

    def _avisar(self, mensagem, erro=True):
        """Mostra a mensagem no proprio formulario, sem popup."""
        if hasattr(self, 'lbl_status') and self.lbl_status.winfo_exists():
            self.lbl_status.configure(
                text=mensagem,
                text_color=self.cores.alerta if erro else self.cores.verde)

    # ------------------------------------------------------------ telas
    def mostrar_login(self):
        """
            Como funciona: Monta o formulario de entrada.
            Para que serve: Autenticar um usuario existente.
            Onde e usada: Abertura da janela e retorno do registro.
        """
        self.limpar_frame()
        self._titulo('Entrar', 'Acesse sua conta para continuar')

        self.entry_email = self._campo('Email')
        self.entry_senha = self._campo('Senha', mostrar='*')

        self.frame_checks = ctk.CTkFrame(self.frame, fg_color='transparent')
        self.frame_checks.pack(pady=(10, 2))

        estilo_check = dict(
            font=ctk.CTkFont(size=12), text_color=self.cores.texto_suave,
            fg_color=self.cores.primaria, hover_color=self.cores.primaria_clara,
            border_color=self.cores.borda, checkbox_width=18, checkbox_height=18)

        self.check_mostrar = ctk.CTkCheckBox(
            self.frame_checks, text='Mostrar senha', command=self.toggle_senha,
            **estilo_check)
        self.check_mostrar.pack(side='left', padx=8)

        self.var_lembrar = ctk.BooleanVar(value=True)
        self.check_lembrar = ctk.CTkCheckBox(
            self.frame_checks, text='Lembrar sessao', variable=self.var_lembrar,
            **estilo_check)
        self.check_lembrar.pack(side='left', padx=8)

        self.lbl_status = self._status()
        self.btn_login = self._botao_primario('Fazer login', self.acao_login)
        self.btn_registrar = self._botao_secundario('Criar conta', self.mostrar_registro)

        self.btn_esqueci = ctk.CTkButton(
            self.frame, text='Esqueci a senha', width=280, height=32,
            fg_color='transparent', hover=False,
            text_color=self.cores.texto_apagado, font=ctk.CTkFont(size=12),
            command=lambda: self._avisar('Recuperacao de senha em desenvolvimento.'))
        self.btn_esqueci.pack(pady=(6, 20))

        self.entry_email.bind('<Return>', lambda _e: self.entry_senha.focus_set())
        self.entry_senha.bind('<Return>', lambda _e: self.acao_login())
        self.entry_email.focus_set()

    def mostrar_registro(self):
        """
            Como funciona: Monta o formulario de criacao de conta.
            Para que serve: Registrar um novo usuario na nuvem.
            Onde e usada: Botao 'Criar conta' da tela de login.
        """
        self.limpar_frame()
        self._titulo('Criar conta', 'Leva menos de um minuto')

        self.entry_email = self._campo('Email')
        self.entry_senha = self._campo('Senha (minimo 6 caracteres)', mostrar='*')
        self.entry_senha_rep = self._campo('Repetir senha', mostrar='*')
        self.entry_tel = self._campo('Telefone (opcional)')

        self.lbl_status = self._status()
        self.btn_confirmar = self._botao_primario('Registrar', self.acao_registrar)
        self.btn_voltar = self._botao_secundario('Voltar', self.mostrar_login)

        self.entry_tel.bind('<Return>', lambda _e: self.acao_registrar())
        self.entry_email.focus_set()

    def toggle_senha(self):
        """
            Como funciona: Alterna entre senha mascarada e visivel.
            Para que serve: Conferir a digitacao da senha.
            Onde e usada: Checkbox 'Mostrar senha'.
        """
        self.entry_senha.configure(
            show='' if self.entry_senha.cget('show') == '*' else '*')

    # ------------------------------------------------------------ acoes
    def acao_login(self):
        """
            Como funciona: Valida os campos, consulta o banco e salva a sessao.
            Para que serve: Autenticar o usuario.
            Onde e usada: Botao 'Fazer login' e tecla Enter.
        """
        email = self.entry_email.get().strip()
        senha = self.entry_senha.get()
        if not email or not senha:
            self._avisar('Preencha email e senha.')
            return

        self.btn_login.configure(state='disabled', text='Entrando...')
        self.update_idletasks()
        try:
            usuario = self.db.verificar_login(email, senha)
        except Exception as e:
            self.btn_login.configure(state='normal', text='Fazer login')
            self._avisar(f'Falha de conexao: {e}')
            return

        if usuario:
            self.usuario_logado = usuario
            if self.var_lembrar.get():
                try:
                    with open(FILE_CACHE, 'w', encoding='utf-8') as arq:
                        json.dump(usuario, arq)
                except Exception:
                    pass
            self.destroy()
        else:
            self.btn_login.configure(state='normal', text='Fazer login')
            self._avisar('Email ou senha incorretos.')

    def acao_registrar(self):
        """
            Como funciona: Valida os campos e cria o usuario no banco remoto.
            Para que serve: Cadastrar uma nova conta.
            Onde e usada: Botao 'Registrar' e tecla Enter.
        """
        email = self.entry_email.get().strip()
        senha = self.entry_senha.get()
        senha_rep = self.entry_senha_rep.get()
        tel = self.entry_tel.get().strip()

        if not email or not senha or not senha_rep:
            self._avisar('Preencha os campos obrigatorios.')
            return
        if senha != senha_rep:
            self._avisar('As senhas nao coincidem.')
            return
        if len(senha) < 6:
            self._avisar('A senha deve ter pelo menos 6 caracteres.')
            return

        self.btn_confirmar.configure(state='disabled', text='Criando...')
        self.update_idletasks()
        try:
            resultado = self.db.criar_usuario(email, senha, tel)
        except Exception as e:
            self.btn_confirmar.configure(state='normal', text='Registrar')
            self._avisar(f'Falha de conexao: {e}')
            return

        if resultado:
            messagebox.showinfo('Sucesso',
                                'Conta criada com sucesso! Faca login para continuar.')
            self.mostrar_login()
        else:
            self.btn_confirmar.configure(state='normal', text='Registrar')
            self._avisar('Nao foi possivel criar a conta (email ja existe?).')


def iniciar_fluxo_autenticacao(pular_cache=False):
    """
        Como funciona: Abre a janela de autenticacao e devolve o usuario logado.
        Para que serve: Porta de entrada da aplicacao.
        Onde e usada: Chamada por main.py.
    """
    app = TelaAutenticacao(pular_cache)
    app.mainloop()
    return app.usuario_logado


if __name__ == '__main__':
    print(f'Logado como: {iniciar_fluxo_autenticacao()}')
