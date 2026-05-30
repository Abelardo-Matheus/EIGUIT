import os
import ast

def parse_name(name):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'parse name'.
        Para que serve: Realiza as tarefas fundamentais de 'parse name' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'parse name'.
    """
    return name.replace('_', ' ').strip()

def generate_smart_docstring(name, is_class, module_name):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'generate smart docstring'.
        Para que serve: Realiza as tarefas fundamentais de 'generate smart docstring' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'generate smart docstring'.
    """
    clean_name = parse_name(name)
    como = f"Processa a lógica interna de '{clean_name}'."
    para = f"Realiza operações relativas a '{clean_name}' no sistema."
    name_lower = name.lower()
    if is_class:
        como = f"Define a estrutura e estado do componente '{name}'."
        para = f"Atua como o modelo principal para instâncias de '{clean_name}'."
        if 'estudo' in name_lower:
            para = 'Controla a lógica e interação da tela de estudo prático.'
        elif 'gerenciador' in name_lower or 'engine' in name_lower or 'processador' in name_lower:
            para = 'Orquestra recursos e o ciclo de vida do módulo.'
            como = f"Mantém instâncias ativas e delega tarefas aos submódulos de '{clean_name}'."
    elif name_lower == '__init__':
        como = 'Inicializa os atributos e o estado inicial da instância.'
        para = 'Prepara o objeto para ser utilizado no ciclo de vida da aplicação.'
    elif name_lower.startswith('desenhar'):
        como = 'Utiliza funções de renderização do Pygame para desenhar na tela.'
        para = f"Apresenta o elemento visual '{clean_name.replace('desenhar ', '')}' na interface gráfica."
    elif name_lower.startswith('tratar_clique') or name_lower.startswith('tratar_evento'):
        como = 'Verifica colisões e processa inputs do mouse/teclado.'
        para = 'Mapeia ações do usuário para atualizações de estado.'
    elif name_lower.startswith('obter_') or name_lower.startswith('get_'):
        como = 'Acessa e formata dados internos ou de configuração.'
        para = f"Retorna as informações solicitadas sobre '{clean_name.replace('obter ', '').replace('get ', '')}'."
    elif name_lower.startswith('atualizar'):
        como = 'Recalcula dimensões, estados e processa alterações temporais.'
        para = 'Garante que os dados e a interface reflitam as últimas mudanças.'
    elif name_lower.startswith('inicializar'):
        como = 'Prepara variáveis e limpa dados de sessões anteriores.'
        para = 'Configura o ambiente necessário para início de uma nova tarefa.'
    elif name_lower.startswith('carregar'):
        como = 'Lê dados de disco, banco de dados ou estado salvo.'
        para = 'Popula as estruturas em memória com as informações persistidas.'
    elif name_lower.startswith('salvar'):
        como = 'Serializa os dados em memória e envia para o armazenamento.'
        para = 'Persiste as alterações feitas pelo usuário no banco ou sistema de arquivos.'
    elif name_lower == 'main':
        como = 'Inicializa a janela do Pygame, carrega os módulos e inicia o loop principal.'
        para = 'Ponto de entrada que orquestra todo o fluxo do sistema.'
    doc = f"\nComo funciona: {como}\nPara que serve: {para}\nOnde é usada: Chamado a partir do módulo ou classe base de '{module_name}'.\n"
    return doc.strip()

def process_file(filepath):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'process file'.
        Para que serve: Realiza as tarefas fundamentais de 'process file' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'process file'.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        module_name = os.path.basename(filepath).replace('.py', '')
        modified = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                existing_doc = ast.get_docstring(node)
                needs_update = False
                if not existing_doc:
                    needs_update = True
                elif 'Gerencia operações relacionadas a' in existing_doc:
                    needs_update = True
                elif 'Como funciona:' not in existing_doc:
                    needs_update = True
                if needs_update:
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                        if isinstance(node.body[0].value.value, str):
                            node.body.pop(0)
                    docstring = generate_smart_docstring(node.name, isinstance(node, ast.ClassDef), module_name)
                    doc_node = ast.Expr(value=ast.Constant(value='\n' + docstring + '\n'))
                    node.body.insert(0, doc_node)
                    modified = True
        if modified:
            new_source = ast.unparse(tree)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_source)
            return True
        return False
    except Exception as e:
        print(f'Error processing {filepath}: {e}')
        return False
total = 0
for root, _, files in os.walk('.'):
    if any((ign in root for ign in ['venv_novo', '.venv', '__pycache__', 'build', 'dist', '.git'])):
        continue
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            if process_file(filepath):
                total += 1
print(f'Total files modified: {total}')