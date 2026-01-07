#!/usr/bin/env python3
"""retrain_all_users.py

Usage:
  python scripts/retrain_all_users.py [--user USER_ID] [--min-records N] [--dry-run]

Description:
  Retrain models for users that have learning records. By default it will look
  for distinct users in the LearningRecord table and retrain models for users
  that have at least `--min-records` records (default 3). Use `--user` to
  retrain a single user. `--dry-run` will only print what would be done.

This is intended as a simple manual script you can schedule via cron or run
manually inside the container (e.g., `docker compose exec dokumentor python scripts/retrain_all_users.py`).
"""

import argparse
import sys
import os

# Ensure project root is on PYTHONPATH when running this script directly
# This makes imports like `from backend.database import ...` work whether the
# script is executed from the project root, via `docker compose exec`, or in CI.
here = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(here, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import get_db, LearningRecord
from backend.ai_processor import AIProcessor
from datetime import datetime


def main():
    p = argparse.ArgumentParser(description="Retrain AI models for users based on learning records")
    p.add_argument('--user', type=int, help='Retrain only this user id')
    p.add_argument('--min-records', type=int, default=3, help='Minimum learning records required to retrain (default: 3)')
    p.add_argument('--dry-run', action='store_true', help='Show what would be done without performing retrain')
    args = p.parse_args()

    db = get_db()

    try:
        if args.user:
            user_ids = [args.user]
        else:
            # Find all user_ids that have learning records
            rows = db.query(LearningRecord.user_id).distinct().all()
            user_ids = [r[0] for r in rows if r[0] is not None]

        if not user_ids:
            print('No users with learning records found.')
            return 0

        print(f'Found {len(user_ids)} user(s) with learning records: {user_ids}')

        for user_id in user_ids:
            count = db.query(LearningRecord).filter_by(user_id=user_id).count()
            print(f'User {user_id}: {count} learning record(s)')

            if count < args.min_records:
                print(f'  Skipping user {user_id}: requires at least {args.min_records} records')
                continue

            if args.dry_run:
                print(f'  [dry-run] Would retrain user {user_id} now')
                continue

            # Actually retrain for this user
            print(f'  Retraining models for user {user_id} (started at {datetime.utcnow().isoformat()}Z)')
            try:
                ai = AIProcessor(user_id=user_id)
                ai._retrain_models()
                print(f'  Finished retraining for user {user_id} (time: {datetime.utcnow().isoformat()}Z)')
            except Exception as e:
                print(f'  ERROR retraining user {user_id}: {e}')

        return 0

    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
