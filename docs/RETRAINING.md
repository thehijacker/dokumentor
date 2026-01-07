# Retraining and Scheduling

This document explains how to run the manual retrain script, example usage inside the container, and recommendations for scheduling retrains.

## Purpose
The repository includes a simple CLI script `scripts/retrain_all_users.py` that allows you to:

- Retrain models for all users who have learning records (default: minimum 3 records)
- Retrain models for a single user by ID
- Do a dry-run to see which users would be retrained

This script is intended for manual use or to be scheduled via cron / CI.

## Usage

From the repository root (inside the container):

```bash
# Retrain all users (default min-records = 3)
docker compose exec dokumentor python scripts/retrain_all_users.py

# Retrain a single user
docker compose exec dokumentor python scripts/retrain_all_users.py --user 123

# Dry-run to see actions without making changes
docker compose exec dokumentor python scripts/retrain_all_users.py --dry-run

# Change minimum records required
docker compose exec dokumentor python scripts/retrain_all_users.py --min-records 5
```

## Behavior notes

- The script looks for distinct `user_id` values present in the `learning_records` table and retrains users that have at least `--min-records` records (default 3).
- The application automatically triggers a retrain during normal usage after every N corrections (N = 10). The script provides a way to manually run retraining on demand for bulk maintenance.
- When there is exactly one distinct subcategory for a given category and user, the system will auto-assign that subcategory with high confidence to reduce missing-subcategory issues.

## Scheduling via cron (example)

Example: run hourly (adjust paths and docker-compose file location as needed):

```cron
0 * * * * cd /path/to/repo && docker compose exec -T dokumentor python scripts/retrain_all_users.py --min-records 3 >> /var/log/dokumentor_retrain.log 2>&1
```

Notes:
- Use `-T` with `docker compose exec` in non-interactive cron environments to avoid TTY errors.
- Redirect logs so you can review output and errors.
- Consider adding a lockfile or other guard to prevent concurrent runs if your scheduling may overlap.

## Safety recommendations

- Add `--dry-run` to test before enabling scheduling.
- Monitor `logs/app.log` for retrain-related messages and failures.
- If you plan frequent retrains, consider tracking `last_retrained_at` in the database and/or implementing a small lockfile mechanism to avoid overlapping runs.

## CI scheduling option

If you prefer a cloud-native approach, you can schedule retrains using a CI job (GitHub Actions, Jenkins, etc.) that runs the same command. The `scripts/retrain_all_users.py` script is designed to be run non-interactively and is suitable for CI execution.

---

For more details about AI learning and model thresholds, see `README.md` under the AI Learning section.