import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print

console = Console()

def fetch_news():
    """
    Fetches news articles based on a user-provided topic using NewsAPI.
    This version uses 'rich' for a better UI.
    """
    api_key = "44adb3cf9d2e45e4921fa93e8bc3f14b"
    
    console.print(Panel.fit("[bold cyan]News Search App[/bold cyan]", border_style="cyan"))
    
    topic = Prompt.ask("[bold green]Enter a topic to search for news[/bold green]", default="technology")
    
    if not topic.strip():
        console.print("[bold red]Topic cannot be empty.[/bold red]")
        return

    url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=relevancy&apiKey={api_key}"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Fetching most relevant news for '[bold yellow]{topic}[/bold yellow]'...", total=None)
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Network error occurred:[/bold red] {e}")
            return
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            return

    if data.get("status") == "ok":
        articles = data.get("articles", [])
        
        # Filter out removed articles and those with no description
        valid_articles = [
            a for a in articles 
            if a.get('title') != "[Removed]" and a.get('description')
        ]
        
        total_results = len(valid_articles)
        
        if not valid_articles:
            console.print(f"[yellow]No relevant articles found for '{topic}'.[/yellow]")
            return

        console.print(f"\n[bold]Found {data.get('totalResults')} results. Showing top 5 most relevant:[/bold]\n")
        
        # Display the top 5 articles using Panels for better readability
        for i, article in enumerate(valid_articles[:5], 1):
            title = article.get('title', 'No Title')
            source = article.get('source', {}).get('name', 'Unknown')
            date = article.get('publishedAt', 'Unknown')[:10]
            description = article.get('description', 'No description available.')
            link = article.get('url', '#')
            
            content = f"""[bold white]{title}[/bold white]
[cyan]Source: {source} | Date: {date}[/cyan]

[white]{description}[/white]

[dim]Read more: {link}[/dim]"""
            
            console.print(Panel(content, border_style="green", title=f"Article {i}", expand=False))
            console.print("") # Add spacing between panels

        console.print("\n[dim]Run the script again to search for another topic.[/dim]")
        
    else:
        console.print(f"[bold red]API Error:[/bold red] {data.get('code')} - {data.get('message')}")

if __name__ == "__main__":
    try:
        fetch_news()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
