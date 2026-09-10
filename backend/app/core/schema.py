"""Allineamento dello schema del database locale.

Il database è un artefatto usa e getta: si ricostruisce interamente dai file in `data/`.
Quando qualcuno aggiunge una colonna a un modello, però, `create_all` non tocca le
tabelle già esistenti e chi ha un vecchio `.db` sul proprio PC si ritrova un
`no such column` al primo caricamento, dopo un semplice `git pull`.

Su un progetto normale la risposta sarebbe una migrazione. Qui il database non contiene
nulla che non si possa rigenerare in pochi secondi, quindi si rileva la differenza e si
ricostruisce: costa meno di una migrazione e non lascia nessuno bloccato.
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, inspect

from app.core.database import Base

logger = logging.getLogger(__name__)


def outdated_tables(engine: Engine) -> list[str]:
    """Tabelle esistenti a cui manca almeno una colonna prevista dai modelli."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    stale: list[str] = []
    for name, table in Base.metadata.tables.items():
        if name not in existing:
            continue
        actual = {column["name"] for column in inspector.get_columns(name)}
        missing = {column.name for column in table.columns} - actual
        if missing:
            logger.warning("Tabella '%s' obsoleta, colonne mancanti: %s", name, sorted(missing))
            stale.append(name)
    return stale


def ensure_schema(engine: Engine) -> bool:
    """Crea le tabelle mancanti e ricostruisce quelle disallineate.

    Ritorna `True` se qualcosa è stato ricostruito, così il chiamante sa che deve
    ricaricare i dati.
    """
    stale = outdated_tables(engine)
    if stale:
        logger.warning("Ricostruisco il database locale: %s", ", ".join(stale))
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
    return bool(stale)
