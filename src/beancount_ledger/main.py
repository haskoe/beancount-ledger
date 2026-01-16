import argparse
from .opdater import handle_opdater
from .afstem import handle_afstem
from .godkend import handle_godkend
from .moms_luk import handle_moms_luk
from .status import handle_status


def main():
    # Parent parser for shared arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--firma", default="firma", help="Navn på firmaet (default: 'firma')"
    )
    # parent_parser.add_argument(
    #     "--periode", default="", help="Regnskabsperiode/år (default: '2021')"
    # )
    parent_parser.add_argument(
        "--enddate", default="", help="Slutdato for perioden (format: YYMMDD)"
    )

    parser = argparse.ArgumentParser(description="Ledger CLI - Dansk Bogføringssystem")
    subparsers = parser.add_subparsers(dest="command", help="Tilgængelige kommandoer")

    # Subcommand: opdater
    subparsers.add_parser(
        "opdater",
        parents=[parent_parser],
        help="Opdater beancount filer",
    )

    # Subcommand: afstem
    subparsers.add_parser(
        "afstem",
        parents=[parent_parser],
        help="Check at saldo på bankkontoer stemmer med beancount transaktioner",
    )

    # Subcommand: godkend
    subparsers.add_parser(
        "godkend", parents=[parent_parser], help="Godkend afstemning eller lukning"
    )
    # Subcommand: moms-luk
    subparsers.add_parser("moms-luk", parents=[parent_parser], help="Luk momsperiode")
    # Subcommand: status
    subparsers.add_parser(
        "status", parents=[parent_parser], help="Vis status/rapporter"
    )

    args = parser.parse_args()

    from context import LedgerContext

    ctx = LedgerContext(company_name=args.firma, enddate=args.enddate)

    if args.command == "afstem":
        handle_afstem(ctx)
    elif args.command == "godkend":
        handle_godkend(ctx)
    elif args.command == "moms-luk":
        handle_moms_luk(ctx)
    elif args.command == "status":
        handle_status(ctx)
    elif args.command == "opdater":
        handle_opdater(ctx)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
