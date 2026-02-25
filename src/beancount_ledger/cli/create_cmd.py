"""CLI-kommando: `beancount_ledger create` – opret et nyt firma-repo (T-36)."""

from __future__ import annotations

import datetime

import click

from beancount_ledger.application.create_company import create_company
from .main import cli, pass_global, GlobalContext


@cli.command("create")
@click.option(
    "--cvr",
    required=True,
    metavar="CVR",
    help="8-cifret CVR-nummer for det nye firma.",
)
@click.option(
    "--company-name",
    default="",
    metavar="NAVN",
    help="Firmanavn der skrives til settings.yaml.",
)
@click.option(
    "--first-year",
    default="",
    metavar="YYYY",
    help="Første regnskabsår. Standard: indeværende år.",
)
@pass_global
def create_cmd(
    ctx: GlobalContext,
    cvr: str,
) -> None:
    """Opret et nyt firma-repo med standard mappestruktur og konfigurationsfiler.

    Firma-repoets rod oprettes under BASE_DIR/<cvr>/ med mindre --base-dir
    allerede peger direkte på den ønskede rod.
    """
    # Brug CVR fra global option hvis --cvr ikke er givet her (umuligt, da
    # local --cvr er required, men vi harmoniserer alligevel).
    effective_cvr = cvr
    if not effective_cvr:
        raise click.UsageError("--cvr er påkrævet.")

    root = ctx.resolve_root(effective_cvr)

    if ctx.verbose:
        click.echo(f"Opretter firma-repo: {root}")
        click.echo(f"  cvr          : {effective_cvr}")

    if ctx.dry_run:
        click.echo("[dry-run] ville oprette firma-repo under: " + str(root))
        return

    create_company(
        root=root,
        cvr=effective_cvr,
    )

    click.echo(f"Firma-repo oprettet: {root}")
