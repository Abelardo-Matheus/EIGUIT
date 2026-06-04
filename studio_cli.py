import sys
import os

# Garantir que o diretório raiz está no path para importar Modulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
except ImportError:
    print("Erro: A biblioteca 'rich' não está instalada.")
    print("Por favor, instale-a usando: pip install rich")
    sys.exit(1)

from Modulos.modulo_estudio_teoria import TeoricoMusical

console = Console()

def mostrar_menu():
    console.clear()
    console.print(Panel("[bold cyan]EIGUIT - Estúdio de Teoria Musical[/bold cyan]", subtitle="v1.0", expand=False))
    console.print("\n[bold]Menu Principal:[/bold]")
    console.print("1. [green]Campo Harmônico Inteligente[/green]")
    console.print("0. [red]Sair[/red]")
    
    escolha = Prompt.ask("\nEscolha uma opção", choices=["1", "0"], default="1")
    return escolha

def campo_harmonico_inteligente():
    console.print("\n[bold yellow]Configuração do Campo Harmônico[/bold yellow]")
    tonica = Prompt.ask("Escolha o Tom Principal (Ex: G, C, D, A, E)", default="G").strip()
    
    campo = TeoricoMusical.obter_campo_harmonico(tonica)
    if not campo:
        console.print(f"\n[bold red]Erro:[/bold red] Tom [inverse]{tonica}[/inverse] não reconhecido ou inválido.")
        Prompt.ask("\nPressione Enter para tentar novamente")
        return

    # Tabela 1: O Cardápio (Os Graus)
    table1 = Table(title=f"\n[bold underline]Campo Harmônico de {tonica.upper()} Maior[/bold underline]", show_header=True, header_style="bold magenta")
    table1.add_column("Grau", style="dim", justify="center")
    table1.add_column("Acorde", style="bold yellow", justify="center")
    table1.add_column("Tipo", justify="center")
    table1.add_column("Função na Música", style="italic green")

    for item in campo:
        cor_tipo = "cyan" if item['tipo'] == "Maior" else ("orange3" if item['tipo'] == "Menor" else "red")
        table1.add_row(
            item['grau'],
            item['acorde'],
            f"[{cor_tipo}]{item['tipo']}[/{cor_tipo}]",
            item['funcao']
        )

    console.print(table1)

    # Tabela 2: Progressões Sugeridas
    progressoes = TeoricoMusical.obter_progressoes(tonica)
    table2 = Table(title="\n[bold underline]Progressões Sugeridas (Cards de Estudo)[/bold underline]", show_header=True, header_style="bold blue", border_style="bright_blue")
    table2.add_column("Nome da Progressão", style="bold white")
    table2.add_column("Estrutura (Graus)", style="dim", justify="center")
    table2.add_column("Acordes Práticos", style="bold green", justify="center")

    for p in progressoes:
        table2.add_row(p['nome'], p['graus'], p['acordes'])

    console.print(table2)
    console.print("\n[dim]Dica: Use estes acordes para compor ou treinar trocas rápidas.[/dim]")
    Prompt.ask("\nPressione Enter para voltar ao menu")

def main():
    try:
        while True:
            escolha = mostrar_menu()
            if escolha == "1":
                campo_harmonico_inteligente()
            elif escolha == "0":
                console.print("\n[yellow]Saindo do Estúdio. Bons treinos![/yellow]")
                break
    except KeyboardInterrupt:
        console.print("\n[yellow]Operação cancelada pelo usuário. Saindo...[/yellow]")

if __name__ == "__main__":
    main()
