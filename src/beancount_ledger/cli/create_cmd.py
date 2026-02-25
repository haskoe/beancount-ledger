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
    company_name: str,
    first_year: str,
) -> None:
    """Opret et nyt firma-repo med standard mappestruktur og konfigurationsfiler.

    Firma-repoets rod oprettes under BASE_DIR/<cvr>/ med mindre --base-dir
    allerede peger direkte på den ønskede rod.
    """
    # Brug CVR fra global option hvis --cvr ikke er givet her (umuligt, da
    # local --cvr er required, men vi harmoniserer alligevel).
    effective_cvr = cvr or ctx.cvr
    if not effective_cvr:
        raise click.UsageError("--cvr er påkrævet.")

    effective_first_year = int(first_year) if first_year else datetime.date.today().year

    root = ctx.resolve_root(effective_cvr)

    if ctx.verbose:
        click.echo(f"Opretter firma-repo: {root}")
        click.echo(f"  company-name : {company_name}")
        click.echo(f"  cvr          : {effective_cvr}")
        click.echo(f"  first-year   : {effective_first_year}")

    if ctx.dry_run:
        click.echo("[dry-run] ville oprette firma-repo under: " + str(root))
        return

    create_company(
        root=root,
        company_name=company_name,
        cvr=effective_cvr,
        first_year=effective_first_year,
    )

    click.echo(f"Firma-repo oprettet: {root}")
