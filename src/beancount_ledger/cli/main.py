"""CLI – Click group `beancount_ledger` med globale options."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click


from beancount_ledger.domain.settings import Settings
from beancount_ledger.application.app_context import AppContext
from beancount_ledger.domain.current import CurrentState


@dataclass
class GlobalContext:
    """Globale CLI-indstillinger videregivet til alle underkommandoer."""

    base_dir: Path
    cvr: str | None
    verbose: bool
    dry_run: bool
    app_context: AppContext

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
    from beancount_ledger.application.kontoplan_service import generate_kontoplan

    app_context = ctx_obj.app_context

    settings = Settings.from_yaml(app_context.settings_yaml)
    current_state = CurrentState.from_yaml(app_context.current_yaml)

    app_context = AppContext(root_path=app_context.root_path, settings=settings, current_state=current_state)
    ctx_obj.app_context = app_context

    generate_kontoplan(app_context.root_path)

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
        app_context=None,  # blive sat senere
    )
    if verbose:
        click.echo(f"base-dir : {ctx.obj.base_dir}")
        if cvr:
            click.echo(f"cvr      : {cvr}")
        if dry_run:
            click.echo("dry-run  : aktiveret")

    # Auto-initialisér first_year-mappe for alle kommandoer undtagen create
    ctx.obj.app_context = AppContext(root_path=ctx.obj.resolve_root(), settings=None, current_state=None)
    if ctx.invoked_subcommand not in (None, "create"):
        _auto_init_first_year(ctx.obj)
        


# ---------------------------------------------------------------------------
# Registrér underkommandoer (import udløser @cli.command-dekoratoren)
# ---------------------------------------------------------------------------
from beancount_ledger.cli import create_cmd as _create_cmd  # noqa: E402, F401
from beancount_ledger.cli import primo_cmd as _primo_cmd  # noqa: E402, F401
from beancount_ledger.cli import opdater_cmd as _opdater_cmd  # noqa: E402, F401
