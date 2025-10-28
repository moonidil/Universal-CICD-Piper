from rich.console import Console
from rich.table import Table



def pretty(detection):
    """Display detection results in a clean, formatted table."""
    console = Console()
    table = Table(title="Piper Detection Report")

    #set up table columns
    table.add_column("Key")
    table.add_column("Value")

    #add detection results with fallbacks for empty values
    table.add_row("Types", ", ".join(detection.get("types", [])) or "-")
    table.add_row("Framework", detection.get("framework") or "-")
    table.add_row("Deploy", detection.get("deploy") or "-")

    #print the formatted table
    console.print(table)
