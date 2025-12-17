#!/usr/bin/env python3
"""Backfill script to normalize DATE entities and populate Entity.normalized_value.

Usage:
  python scripts/backfill_normalized_dates.py [--dry-run] [--batch N]

This script will iterate over all Entity rows with label 'DATE' and no
`normalized_value`, attempt to parse the entity.text to an ISO date using
`src.utils.normalizers.normalize_date`, and write the ISO string back to the
database in batches.
"""
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import argparse
import logging
from src.db.connection import get_session
from src.models.database import Entity
from sqlmodel import select
from src.utils.normalizers import normalize_date


logger = logging.getLogger("backfill_normalized_dates")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run(dry_run: bool = False, batch: int = 200):
    db = next(get_session())

    stmt = select(Entity).where(Entity.label == "DATE")
    rows = db.exec(stmt).all()
    total = len(rows)
    logger.info(f"Found {total} DATE entities to inspect")

    processed = 0
    updated = 0
    for e in rows:
        processed += 1
        if e.normalized_value:
            continue
        iso = normalize_date(e.text)
        if iso:
            logger.debug(f"Parsed entity id={e.id} text={e.text!r} -> {iso}")
            if not dry_run:
                e.normalized_value = iso
                db.add(e)
                updated += 1

        if processed % batch == 0:
            if not dry_run:
                db.commit()
            logger.info(f"Processed {processed}/{total}, updated {updated} (dry_run={dry_run})")

    if not dry_run:
        db.commit()

    logger.info(f"Done. Processed {processed} entities, updated {updated} rows (dry_run={dry_run})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes to the DB")
    parser.add_argument("--batch", type=int, default=200, help="Commit batch size")
    args = parser.parse_args()

    run(dry_run=args.dry_run, batch=args.batch)


if __name__ == "__main__":
    main()
