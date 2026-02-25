"""CLI-kommando: `beancount_ledger primo` – generer primo.beancount (T-37)."""

from __future__ import annotations

import click

from beancount_ledger.application.primo_service import PrimoBalanceError, generate_primo
from beancount_ledger.cli.main import GlobalContext, cli, pass_global


@cli.command("primo")
@pass_global
def primo_cmd(ctx: GlobalContext) -> None:
    """Generer (eller regenerer) primo.beancount fra primo.csv.

    Commit'er automatisk med "primo updated" medmindre --dry-run er sat.
    """
    root = ctx.resolve_root()

    if ctx.verbose:
        click.echo(f"primo: root={root}")

    if ctx.dry_run:
        click.echo(f"[dry-run] ville generere primo.beancount fra: {root / 'primo.csv'}")
        return

    try:
        count = generate_primo(root)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except PrimoBalanceError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"primo.beancount genereret – {count} postering(er) skrevet.")
