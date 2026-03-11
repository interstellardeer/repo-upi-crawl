import asyncio
import logging

import typer

from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = typer.Typer(help="UPI Repository Crawler CLI")


@app.command()
def crawl(
    year: int = typer.Option(None, "--year", "-y", help="Crawl papers from a specific year"),
    division: str = typer.Option(None, "--division", "-d", help="Crawl papers from a division code"),
    author: str = typer.Option(None, "--author", "-a", help="Crawl papers by an author (slug or name)"),
    all: bool = typer.Option(False, "--all", help="Full crawl of all years"),
    incremental: bool = typer.Option(False, "--incremental", help="Only crawl years/divisions that changed"),
    bootstrap_only: bool = typer.Option(False, "--bootstrap", help="Only sync reference tables (divisions, subjects, authors)"),
):
    """Crawl the UPI Repository and store papers in the local database."""
    from app.crawlers import orchestrator

    init_db()

    async def _run():
        if bootstrap_only:
            await orchestrator.bootstrap()
        elif year:
            await orchestrator.crawl_year(year)
        elif division:
            await orchestrator.crawl_division(division)
        elif author:
            await orchestrator.crawl_author(author)
        elif all:
            await orchestrator.crawl_all()
        else:
            # Default: incremental
            await orchestrator.crawl_incremental()

    asyncio.run(_run())
    typer.echo("Done.")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Enable auto-reload (dev mode)"),
):
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


@app.command()
def reset(force: bool = typer.Option(False, "--force", help="Skip confirmation prompt")):
    """Drop and recreate the database."""
    import os
    from app.config import settings

    if not force:
        confirm = typer.confirm(f"This will DELETE {settings.DB_PATH}. Are you sure?")
        if not confirm:
            raise typer.Abort()

    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)
        typer.echo(f"Deleted {settings.DB_PATH}")

    init_db()
    typer.echo("Database recreated.")


if __name__ == "__main__":
    app()
