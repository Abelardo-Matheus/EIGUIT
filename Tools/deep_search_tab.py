import re
import json

def search():
    """
        Como funciona: Executa o fluxo lógico necessário para a operação 'search'.
        Para que serve: Realiza as tarefas fundamentais de 'search' dentro do contexto do módulo.
        Onde é usada: Utilizado internamente para gerenciar comportamentos de 'search'.
    """
    with open('song_page.html', 'r', encoding='utf-8') as f:
        content = f.read()
    urls = re.findall('https://static\\.songsterr\\.com/[^\\"\\\'\\s]+\\.json', content)
    print(f'JSON URLs: {urls}')
    if 'measures' in content:
        print("Found 'measures' in HTML")
    match = re.search('<script id="state" type="application/json">(.*?)</script>', content)
    if match:
        state = json.loads(match.group(1))

        def find_tab_data(obj, path=''):
            """
                Como funciona: Executa o fluxo lógico necessário para a operação 'find tab data'.
                Para que serve: Realiza as tarefas fundamentais de 'find tab data' dentro do contexto do módulo.
                Onde é usada: Utilizado internamente para gerenciar comportamentos de 'find tab data'.
            """
            if isinstance(obj, dict):
                if 'f' in obj and 's' in obj and isinstance(obj['f'], (int, float)):
                    return [(path, obj)]
                results = []
                for k, v in obj.items():
                    results.extend(find_tab_data(v, f'{path}.{k}' if path else k))
                return results
            elif isinstance(obj, list):
                if len(obj) > 20 and isinstance(obj[0], dict) and ('f' in obj[0] or 'm' in obj[0]):
                    return [(path, 'Potential list of notes/measures')]
                results = []
                for i, item in enumerate(obj):
                    results.extend(find_tab_data(item, f'{path}[{i}]'))
                return results
            return []
        potential = find_tab_data(state)
        print(f'Potential tab data paths: {len(potential)}')
        for p in potential[:10]:
            print(f'  {p}')
if __name__ == '__main__':
    search()