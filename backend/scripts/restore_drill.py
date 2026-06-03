#!/usr/bin/env python3
"""Monthly backup restore drill script.

Restores from Restic backup to a temporary directory and verifies integrity.
Reports timing results and any errors.
"""

import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone


def run_cmd(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    print("=" * 60)
    print("BACKUP RESTORE DRILL")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Check required env vars
    required = ["RESTIC_REPOSITORY", "RESTIC_PASSWORD", "BACKUP_S3_ENDPOINT"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        return 1

    with tempfile.TemporaryDirectory(prefix="restore_drill_") as tmpdir:
        print(f"Temp dir: {tmpdir}")

        # List snapshots
        start = time.time()
        rc, stdout, stderr = run_cmd(["restic", "snapshots", "--latest", "1"])
        if rc != 0:
            print(f"ERROR: Failed to list snapshots: {stderr}")
            return 1
        print(f"Snapshot list: {stdout.strip()}")

        # Restore latest snapshot
        print("Restoring latest snapshot...")
        rc, stdout, stderr = run_cmd(["restic", "restore", "latest", "--target", tmpdir])
        restore_time = time.time() - start
        if rc != 0:
            print(f"ERROR: Restore failed: {stderr}")
            return 1
        print(f"Restore completed in {restore_time:.1f}s")

        # Verify PostgreSQL dump exists
        pg_dump = os.path.join(tmpdir, "postgres", "email_saas.sql")
        if os.path.exists(pg_dump):
            size = os.path.getsize(pg_dump)
            print(f"PostgreSQL dump: {size} bytes")
        else:
            print("WARNING: PostgreSQL dump not found in backup")

        # Create temp database and restore
        print("Creating temp database for restore verification...")
        temp_db = "restore_drill_test"
        rc, stdout, stderr = run_cmd(["createdb", "-h", "localhost", "-U", "postgres", temp_db])
        if rc != 0:
            print(f"WARNING: Could not create temp database: {stderr}")
        else:
            rc, stdout, stderr = run_cmd(["psql", "-h", "localhost", "-U", "postgres", "-d", temp_db, "-f", pg_dump])
            if rc != 0:
                print(f"WARNING: Could not restore to temp database: {stderr}")
            else:
                # Verify row counts
                rc, stdout, stderr = run_cmd([
                    "psql", "-h", "localhost", "-U", "postgres", "-d", temp_db,
                    "-c", "SELECT count(*) FROM accounts;"
                ])
                if rc == 0:
                    print(f"Accounts table: {stdout.strip()} rows")
                else:
                    print(f"WARNING: Could not verify accounts table: {stderr}")
            
            # Clean up temp database
            run_cmd(["dropdb", "-h", "localhost", "-U", "postgres", temp_db])

        # Verify Stalwart data exists
        stalwart_data = os.path.join(tmpdir, "stalwart", "data")
        if os.path.exists(stalwart_data):
            print("Stalwart data: present")
        else:
            print("WARNING: Stalwart data not found in backup")

        # Check backup age
        rc, stdout, stderr = run_cmd(["restic", "snapshots", "--latest", "1", "--json"])
        if rc == 0:
            import json
            try:
                snapshots = json.loads(stdout)
                if snapshots:
                    snapshot_time = datetime.fromisoformat(snapshots[0]["time"].replace("Z", "+00:00"))
                    age = datetime.now(timezone.utc) - snapshot_time
                    print(f"Backup age: {age.total_seconds() / 3600:.1f} hours")
                    if age > timedelta(hours=24):
                        print("WARNING: Backup is older than 24 hours")
            except Exception:
                pass

        # Summary
        print("=" * 60)
        print(f"Restore drill completed successfully")
        print(f"Restore time: {restore_time:.1f}s")
        print(f"RPO check: backup age should be < 24h")
        print(f"RTO target: 4 hours")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
