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

# Configuração da URL de Conexão
URL_CONEXAO = "postgresql://neondb_owner:npg_u8ogByLqHK2F@ep-soft-cake-acsaff4w.sa-east-1.aws.neon.tech/neondb?sslmode=require"

class GerenciadorDB:
    """
    Classe responsável pela gestão da conexão remota com o banco de dados PostgreSQL.
    Facilita a persistência de usuários, perfis e projetos na nuvem com segurança.
    """
    def __init__(self, url_conexao=URL_CONEXAO):
        self.url = url_conexao
        self.conexao = None

    def conectar(self):
        """Estabelece a conexão com o banco de dados."""
        if psycopg is None:
            print("Erro: Biblioteca 'psycopg' ou 'psycopg2' não encontrada.")
            return False
        
        try:
            self.conexao = psycopg.connect(self.url)
            return True
        except Exception as e:
            print(f"Erro ao conectar ao banco remoto: {e}")
            return False

    def fechar(self):
        """Fecha a conexão ativa."""
        if self.conexao:
            self.conexao.close()
            self.conexao = None

    def inicializar_estrutura(self):
        """Cria as tabelas e índices necessários caso não existam."""
        if not self.conectar():
            return

        try:
            with self.conexao.cursor() as cursor:
                # 1. Tabela de Usuários (login será o email)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        login VARCHAR(100) UNIQUE NOT NULL,
                        senha VARCHAR(255) NOT NULL,
                        telefone VARCHAR(20)
                    );
                ''')

                # 2. Tabela de Perfis
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS perfis (
                        id SERIAL PRIMARY KEY,
                        usuario_id INTEGER NOT NULL,
                        nome_perfil VARCHAR(100) NOT NULL,
                        configuracoes JSONB, 
                        CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
                    );
                ''')

                # 3. Tabela de Projetos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projetos (
                        id SERIAL PRIMARY KEY,
                        usuario_id INTEGER NOT NULL,
                        nome_projeto VARCHAR(255) NOT NULL,
                        dados_projeto TEXT, 
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_usuario_projeto FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
                    );
                ''')

                # Índices
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_projetos_nome ON projetos (nome_projeto);')
                
                self.conexao.commit()
                print("Estrutura do banco de dados verificada/criada com sucesso!")
        except Exception as e:
            print(f"Erro ao estruturar o banco: {e}")
            self.conexao.rollback()
        finally:
            self.fechar()

    # --- OPERAÇÕES DE AUTENTICAÇÃO ---

    def criar_usuario(self, login, senha, telefone=None):
        """Cria um novo usuário com senha criptografada."""
        if not self.conectar(): return None
        try:
            # Gerar hash da senha
            salt = bcrypt.gensalt()
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

            with self.conexao.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO usuarios (login, senha, telefone) VALUES (%s, %s, %s) RETURNING id;",
                    (login, senha_hash, telefone)
                )
                novo_id = cursor.fetchone()[0]
                self.conexao.commit()
                return {"id": novo_id, "email": login}
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            self.conexao.rollback()
            return None
        finally:
            self.fechar()

    def verificar_login(self, login, senha):
        """Verifica se as credenciais estão corretas."""
        if not self.conectar(): return None
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute("SELECT id, senha FROM usuarios WHERE login = %s;", (login,))
                resultado = cursor.fetchone()
                
                if resultado:
                    usuario_id, senha_hash = resultado
                    # Comparar senhas usando bcrypt
                    if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                        return {"id": usuario_id, "email": login}
            return None
        except Exception as e:
            print(f"Erro ao verificar login: {e}")
            return None
        finally:
            self.fechar()

    def deletar_conta(self, usuario_id):
        """Remove permanentemente a conta do usuário e todos os dados associados."""
        if not self.conectar(): return False
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute("DELETE FROM usuarios WHERE id = %s;", (usuario_id,))
                self.conexao.commit()
                return True
        except Exception as e:
            print(f"Erro ao deletar conta: {e}")
            self.conexao.rollback()
            return False
        finally:
            self.fechar()

    def salvar_perfil(self, usuario_id, nome_perfil, configuracoes_dict):
        """Salva ou atualiza configurações do perfil."""
        if not self.conectar(): return False
        try:
            config_json = json.dumps(configuracoes_dict)
            with self.conexao.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO perfis (usuario_id, nome_perfil, configuracoes) VALUES (%s, %s, %s);",
                    (usuario_id, nome_perfil, config_json)
                )
                self.conexao.commit()
                return True
        except Exception as e:
            print(f"Erro ao salvar perfil: {e}")
            return False
        finally:
            self.fechar()

if __name__ == '__main__':
    # Teste de inicialização
    db = GerenciadorDB()
    db.inicializar_estrutura()
