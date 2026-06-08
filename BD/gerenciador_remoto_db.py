import os
import json
import bcrypt
try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    try:
        import psycopg2 as psycopg
        from psycopg2.extras import RealDictCursor as dict_row
    except ImportError:
        psycopg = None
URL_CONEXAO = 'postgresql://neondb_owner:npg_u8ogByLqHK2F@ep-soft-cake-acsaff4w.sa-east-1.aws.neon.tech/neondb?sslmode=require'

class GerenciadorDB:
    """
        Como funciona: Gerencia a conexão persistente com o banco de dados PostgreSQL e expõe métodos para operações CRUD.
        Para que serve: Prover uma interface unificada para persistência de dados (usuários, perfis, favoritos) na nuvem.
        Onde é usada: Instanciado no núcleo do sistema para suporte a dados remotos.
    """

    def __init__(self, url_conexao=URL_CONEXAO):
        """
            Como funciona: Inicializa os atributos e o estado inicial da instância.
            Para que serve: Prepara o objeto para ser utilizado no ciclo de vida da aplicação.
            Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_remoto_db'.
        """
        self.url = url_conexao
        self.conexao = None

    def conectar(self):
        """
            Como funciona: Estabelece uma conexão segura com o banco Neon PostgreSQL utilizando a biblioteca psycopg e a URL de configuração.
            Para que serve: Garantir acesso ao banco de dados remoto para operações de leitura e escrita.
            Onde é usada: Chamado internamente por quase todos os métodos do GerenciadorDB antes de executar queries.
        """
        if psycopg is None:
            print("Erro: Biblioteca 'psycopg' ou 'psycopg2' não encontrada.")
            return False
        try:
            self.conexao = psycopg.connect(self.url)
            return True
        except Exception as e:
            print(f'Erro ao conectar ao banco remoto: {e}')
            return False

    def fechar(self):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'fechar'.
            Para que serve: Realiza as tarefas fundamentais de 'fechar' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'fechar'.
        """
        if self.conexao:
            self.conexao.close()
            self.conexao = None

    def inicializar_estrutura(self):
        """
            Como funciona: Prepara variáveis e limpa dados de sessões anteriores.
            Para que serve: Configura o ambiente necessário para início de uma nova tarefa.
            Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_remoto_db'.
        """
        if not self.conectar():
            return
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS usuarios (\n                        id SERIAL PRIMARY KEY,\n                        login VARCHAR(100) UNIQUE NOT NULL,\n                        senha VARCHAR(255) NOT NULL,\n                        telefone VARCHAR(20)\n                    );\n                ')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS perfis (\n                        id SERIAL PRIMARY KEY,\n                        usuario_id INTEGER NOT NULL,\n                        nome_perfil VARCHAR(100) NOT NULL,\n                        configuracoes JSONB, \n                        CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,\n                        CONSTRAINT unique_usuario_perfil UNIQUE (usuario_id, nome_perfil)\n                    );\n                ')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS projetos (\n                        id SERIAL PRIMARY KEY,\n                        usuario_id INTEGER NOT NULL,\n                        nome_projeto VARCHAR(255) NOT NULL,\n                        dados_projeto TEXT, \n                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        CONSTRAINT fk_usuario_projeto FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE\n                    );\n                ')
                cursor.execute('\n                    CREATE TABLE IF NOT EXISTS favoritos (\n                        id SERIAL PRIMARY KEY,\n                        usuario_id INTEGER NOT NULL,\n                        song_id INTEGER NOT NULL,\n                        titulo VARCHAR(255),\n                        artista VARCHAR(255),\n                        CONSTRAINT fk_usuario_favorito FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,\n                        CONSTRAINT unique_user_song UNIQUE (usuario_id, song_id)\n                    );\n                ')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_projetos_nome ON projetos (nome_projeto);')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_favoritos_user ON favoritos (usuario_id);')
                self.conexao.commit()
                print('Estrutura do banco de dados verificada/criada com sucesso!')
        except Exception as e:
            print(f'Erro ao estruturar o banco: {e}')
            self.conexao.rollback()
        finally:
            self.fechar()

    def criar_usuario(self, login, senha, telefone=None):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'criar usuario'.
            Para que serve: Realiza as tarefas fundamentais de 'criar usuario' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'criar usuario'.
        """
        if not self.conectar():
            return None
        try:
            salt = bcrypt.gensalt()
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')
            with self.conexao.cursor() as cursor:
                cursor.execute('INSERT INTO usuarios (login, senha, telefone) VALUES (%s, %s, %s) RETURNING id;', (login, senha_hash, telefone))
                novo_id = cursor.fetchone()[0]
                self.conexao.commit()
                return {'id': novo_id, 'email': login}
        except Exception as e:
            print(f'Erro ao criar usuário: {e}')
            self.conexao.rollback()
            return None
        finally:
            self.fechar()

    def verificar_login(self, login, senha):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'verificar login'.
            Para que serve: Realiza as tarefas fundamentais de 'verificar login' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'verificar login'.
        """
        if not self.conectar():
            return None
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute('SELECT id, senha FROM usuarios WHERE login = %s;', (login,))
                resultado = cursor.fetchone()
                if resultado:
                    usuario_id, senha_hash = resultado
                    if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                        return {'id': usuario_id, 'email': login}
            return None
        except Exception as e:
            print(f'Erro ao verificar login: {e}')
            return None
        finally:
            self.fechar()

    def deletar_conta(self, usuario_id):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'deletar conta'.
            Para que serve: Realiza as tarefas fundamentais de 'deletar conta' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'deletar conta'.
        """
        if not self.conectar():
            return False
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute('DELETE FROM usuarios WHERE id = %s;', (usuario_id,))
                self.conexao.commit()
                return True
        except Exception as e:
            print(f'Erro ao deletar conta: {e}')
            self.conexao.rollback()
            return False
        finally:
            self.fechar()

    def salvar_perfil(self, usuario_id, nome_perfil, configuracoes_dict):
        """
            Como funciona: Serializa os dados em memória e envia para o armazenamento.
            Para que serve: Persiste as alterações feitas pelo usuário no banco ou sistema de arquivos.
            Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_remoto_db'.
        """
        if not self.conectar():
            return False
        try:
            config_json = json.dumps(configuracoes_dict)
            with self.conexao.cursor() as cursor:
                cursor.execute('\n                    INSERT INTO perfis (usuario_id, nome_perfil, configuracoes) \n                    VALUES (%s, %s, %s)\n                    ON CONFLICT (usuario_id, nome_perfil) \n                    DO UPDATE SET configuracoes = EXCLUDED.configuracoes;\n                    ', (usuario_id, nome_perfil, config_json))
                self.conexao.commit()
                return True
        except Exception as e:
            print(f'Erro ao salvar perfil: {e}')
            return False
        finally:
            self.fechar()

    def obter_favoritos(self, usuario_id):
        """
            Como funciona: Acessa e formata dados internos ou de configuração.
            Para que serve: Retorna as informações solicitadas sobre 'favoritos'.
            Onde é usada: Chamado a partir do módulo ou classe base de 'gerenciador_remoto_db'.
        """
        if not self.conectar():
            return []
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute('SELECT song_id, titulo, artista FROM favoritos WHERE usuario_id = %s;', (usuario_id,))
                rows = cursor.fetchall()
                return [{'songId': r[0], 'title': r[1], 'artist': r[2]} for r in rows]
        except Exception as e:
            print(f'Erro ao obter favoritos: {e}')
            return []
        finally:
            self.fechar()

    def adicionar_favorito(self, usuario_id, song_id, titulo, artista):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'adicionar favorito'.
            Para que serve: Realiza as tarefas fundamentais de 'adicionar favorito' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'adicionar favorito'.
        """
        if not self.conectar():
            return False
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute('\n                    INSERT INTO favoritos (usuario_id, song_id, titulo, artista)\n                    VALUES (%s, %s, %s, %s)\n                    ON CONFLICT (usuario_id, song_id) DO NOTHING;\n                    ', (usuario_id, song_id, titulo, artista))
                self.conexao.commit()
                return True
        except Exception as e:
            print(f'Erro ao adicionar favorito: {e}')
            return False
        finally:
            self.fechar()

    def remover_favorito(self, usuario_id, song_id):
        """
            Como funciona: Executa o fluxo lógico necessário para a operação 'remover favorito'.
            Para que serve: Realiza as tarefas fundamentais de 'remover favorito' dentro do contexto do módulo.
            Onde é usada: Utilizado internamente para gerenciar comportamentos de 'remover favorito'.
        """
        if not self.conectar():
            return False
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute('DELETE FROM favoritos WHERE usuario_id = %s AND song_id = %s;', (usuario_id, song_id))
                self.conexao.commit()
                return True
        except Exception as e:
            print(f'Erro ao remover favorito: {e}')
            return False
        finally:
            self.fechar()

    def salvar_projeto(self, usuario_id, nome, tipo, dados_json):
        """
        Salva ou atualiza um projeto (ex: tablatura) no banco de dados.
        """
        if not self.conectar():
            return False
        try:
            with self.conexao.cursor() as cursor:
                # Simplificado: verifica se já existe um projeto com esse nome para o usuário
                cursor.execute('SELECT id FROM projetos WHERE usuario_id = %s AND nome_projeto = %s;', (usuario_id, nome))
                resultado = cursor.fetchone()
                if resultado:
                    cursor.execute('UPDATE projetos SET dados_projeto = %s WHERE id = %s;', (dados_json, resultado[0]))
                else:
                    cursor.execute('INSERT INTO projetos (usuario_id, nome_projeto, dados_projeto) VALUES (%s, %s, %s);', (usuario_id, nome, dados_json))
                self.conexao.commit()
                return True
        except Exception as e:
            print(f'Erro ao salvar projeto: {e}')
            return False
        finally:
            self.fechar()
if __name__ == '__main__':
    db = GerenciadorDB()
    db.inicializar_estrutura()