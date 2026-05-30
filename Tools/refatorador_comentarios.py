import os
import ast

def generate_docstring(name, is_class=False, module_name=''):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'generate docstring'.
        Para que serve: Realiza as tarefas fundamentais de 'generate docstring' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'generate docstring'.
    """
    if is_class:
        func_type = 'Classe'
        action = 'Representa a estrutura de'
    else:
        func_type = 'Função/Método'
        action = 'Executa a rotina de'
    name_clean = name.replace('_', ' ')
    doc = f'\n    Como funciona: {action} {name_clean} configurando seus atributos e estado.\n    Para que serve: Gerencia operações relacionadas a {name_clean}.\n    Onde é usada: Utilizada no fluxo do módulo {module_name}.\n    '
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
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    if isinstance(node.body[0].value.value, str):
                        node.body.pop(0)
                docstring = generate_docstring(node.name, isinstance(node, ast.ClassDef), module_name)
                doc_node = ast.Expr(value=ast.Constant(value='\n' + docstring + '\n'))
                node.body.insert(0, doc_node)
        new_source = ast.unparse(tree)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_source)
        print(f'Processado com sucesso: {filepath}')
        return True
    except Exception as e:
        print(f'Erro ao processar {filepath}: {e}')
        return False

def main():
    """
        Como funciona: Inicializa o ambiente Pygame, carrega as configurações do usuário, autentica o acesso e inicia o loop principal de eventos e renderização.
        Para que serve: Ponto de entrada do sistema que orquestra a inicialização e o ciclo de vida da aplicação.
        Onde é usada: Executado diretamente ao iniciar o software via main.py.
    """
    directories = ['Core', 'Modulos', 'Interface', 'Estudos', 'Jogos', 'DragDrop', 'AudioEngine']
    root_files = ['main.py']
    total_processed = 0
    for d in directories:
        for root, dirs, files in os.walk(d):
            if any((ign in root for ign in ['venv_novo', '.venv', '__pycache__', 'build', 'dist'])):
                continue
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    filepath = os.path.join(root, file)
                    if process_file(filepath):
                        total_processed += 1
    for file in root_files:
        if os.path.exists(file):
            if process_file(file):
                total_processed += 1
    print(f'Total de arquivos processados: {total_processed}')
if __name__ == '__main__':
    main()