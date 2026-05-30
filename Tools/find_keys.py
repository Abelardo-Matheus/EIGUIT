import json

def find_keys(obj, target_keys, path=''):
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'find keys'.
        Para que serve: Realiza as tarefas fundamentais de 'find keys' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'find keys'.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any((tk in k.lower() for tk in target_keys)):
                print(f"Found key '{k}' at path: {path}.{k}")
            find_keys(v, target_keys, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_keys(item, target_keys, f'{path}[{i}]')
with open('state_dump.json', 'r', encoding='utf-8') as f:
    state = json.load(f)
find_keys(state, ['measure', 'note', 'beat', 'fret', 'string', 'tab', 'data'])