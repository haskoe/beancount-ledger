"""CLI – Click group `beancount_ledger` med globale options."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click


@dataclass
class GlobalContext:
    """Globale CLI-indstillinger videregivet til alle underkommandoer."""

    base_dir: Path
    cvr: str | None
    verbose: bool
    dry_run: bool

    def resolve_root(self, cvr: str | None = None) -> Path:
        """Returnér firma-repoets rod.

        Hvis *cvr* (eller ``self.cvr``) er angivet, antages ``base_dir`` at
        være forældremappe og roden er ``base_dir / cvr``.  Ellers bruges
        ``base_dir`` direkte (bruger er allerede inde i firma-repoet).
        """
        effective_cvr = cvr or self.cvr
        return self.base_dir / effective_cvr if effective_cvr else self.base_dir


pass_global = click.make_pass_decorator(GlobalContext)


def _auto_init_first_year(ctx_obj: GlobalContext) -> None:
    """Indlæs settings.yaml og opret data/<first_year>/ hvis den mangler.

    Regenererer desuden kontoplan.beancount fra standardkontoplan.csv.
    Kaldes automatisk af alle kommandoer undtagen ``create``.
    Fejler lydløst hvis settings.yaml ikke eksisterer endnu.
    """
    from beancount_ledger.application.init_year import init_year
    from beancount_ledger.application.kontoplan_service import generate_kontoplan
    from beancount_ledger.infrastructure import company_layout
    from beancount_ledger.infrastructure.yaml_io import load_yaml

    root = ctx_obj.resolve_root()
    settings_path = company_layout.settings_yaml(root)
    if not settings_path.exists():
        return

    generate_kontoplan(root)

    try:
        data = load_yaml(settings_path)
    except Exception:
        return

    first_year = data.get("first_year")
    if not first_year or not isinstance(first_year, int):
        return

    year_dir = company_layout.data_dir(root, first_year)
    if year_dir.exists():
        return

    if ctx_obj.dry_run:
        click.echo(f"[dry-run] ville oprette data/{first_year}/ (first_year fra settings.yaml)")
        return

    created = init_year(root, first_year)
    if created and ctx_obj.verbose:
        click.echo(f"Årsmappe data/{first_year}/ oprettet (first_year fra settings.yaml).")


@click.group()
@click.option(
    "--cvr",
    default=None,
    metavar="CVR",
    help="8-cifret CVR-nummer. Kan udelades hvis settings.yaml indeholder cvr.",
)
@click.option(
    "--base-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    metavar="DIR",
    help="Sti til firma-repoets rod. Standard: nuværende arbejdsmappe.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Udskriv detaljeret information undervejs.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Simulér uden at skrive filer eller committe til git.",
)
@click.version_option(package_name="beancount_ledger")
@click.pass_context
def cli(
    ctx: click.Context,
    cvr: str | None,
    base_dir: Path | None,
    verbose: bool,
    dry_run: bool,
) -> None:
    """beancount_ledger – automatisk generering af Beancount regnskabsposteringer.

    Køres fra roden af et firma-repo, eller angiv --base-dir eksplicit.
    """
    ctx.obj = GlobalContext(
        base_dir=base_dir if base_dir is not None else Path.cwd(),
        cvr=cvr,
        verbose=verbose,
        dry_run=dry_run,
    )
    if verbose:
        click.echo(f"base-dir : {ctx.obj.base_dir}")
        if cvr:
            click.echo(f"cvr      : {cvr}")
        if dry_run:
            click.echo("dry-run  : aktiveret")

    # Auto-initialisér first_year-mappe for alle kommandoer undtagen create
    if ctx.invoked_subcommand not in (None, "create"):
        _auto_init_first_year(ctx.obj)


# ---------------------------------------------------------------------------
# Registrér underkommandoer (import udløser @cli.command-dekoratoren)
# ---------------------------------------------------------------------------
from beancount_ledger.cli import create_cmd as _create_cmd  # noqa: E402, F401
from beancount_ledger.cli import primo_cmd as _primo_cmd  # noqa: E402, F401

