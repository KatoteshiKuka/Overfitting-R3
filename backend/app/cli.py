"""Comandi di manutenzione locale.

    uv run python -m app.cli seed [--reset]

Ricarica i dataset di `data/` nel database senza riavviare il server.
"""

import argparse
import sys

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.features.facilities.seed import seed_facilities


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Carica i dataset da data/ nel database")
    seed_parser.add_argument(
        "--reset", action="store_true", help="Svuota le tabelle prima di ricaricare"
    )

    args = parser.parse_args(argv)
    settings = get_settings()

    if args.command == "seed":
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            count = seed_facilities(db, settings.facilities_dir, reset=args.reset)
        print(f"Presidi caricati da {settings.facilities_dir}: {count}")
        if count == 0 and not args.reset:
            print("Il censimento era già popolato. Usa --reset per ricaricare da zero.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
