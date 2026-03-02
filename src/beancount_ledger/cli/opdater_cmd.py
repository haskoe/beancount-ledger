"""CLI-kommando: `dkbean opdater` – opdatér posteringer for et givet år (T-38)."""

from __future__ import annotations

import click

from beancount_ledger.application.opdater_service import opdater
from beancount_ledger.cli.main import GlobalContext, cli, pass_global


@cli.command("opdater")
@pass_global
def opdater_cmd(ctx: GlobalContext) -> None:
    result = opdater(ctx.app_context)

    if result is None:
        return

    total = sum(result.values())
    if total == 0:
        click.echo(f"Ingen nye posteringer fundet for {ctx.app_context.current_state.current_year}.")
    else:
        for key, count in result.items():
            if count:
                click.echo(f"  {key}: {count} ny(e) postering(er)")
        click.echo(f"Opdatering af {ctx.app_context.current_state.current_year} færdig – {total} postering(er) i alt.")
