# Persistent local preview

Install Docker Engine and Docker Compose, then run from this checkout:

```sh
python3 scripts/setup.py
docker compose up --build -d
```

Open http://127.0.0.1:8102. Read the owner key from the private `.env` locally. Setup creates mode-0600 configuration and refuses to overwrite it. Never commit or share this file. The service runs with Waitress as UID 10001, a read-only root filesystem, dropped Linux capabilities and a writable named data volume. The port is bound only to localhost. `docker compose down` retains polls; `down -v` deletes the volume.

This is a local deployment preview. Public sharing requires a trusted HTTPS reverse proxy, protected backups and actual public-path testing, which remain pending. No email delivery, hosted demo or calendar synchronization is included.

## Backup

The database contains participant names, votes, hashed access credentials, proposed slots and finalized choices. Preserve `.env` separately for owner access. Stop the service for a simple consistent copy:

```sh
docker compose stop meet-vale
docker compose cp meet-vale:/data/meet.sqlite3 /tmp/meet-source.sqlite3
python3 scripts/backup.py /tmp/meet-source.sqlite3 ./meet-backup.sqlite3
rm /tmp/meet-source.sqlite3
docker compose start meet-vale
```

The backup utility uses SQLite's backup API, verifies integrity and refuses to overwrite a destination. It also supports a live SQLite source when run directly on the host. Keep dated backups outside this checkout and protect them as private data.

## Restore to a clean project

Use a separate clean checkout/Compose project and private `.env`. Create its empty volume, stop it, then restore. Leave the original volume intact until verification finishes.

```sh
docker compose up -d
docker compose stop meet-vale
docker compose cp ./meet-backup.sqlite3 meet-vale:/data/meet.sqlite3
docker compose run --rm --user 0 meet-vale python -c "import os; os.chown('/data/meet.sqlite3',10001,10001); os.chmod('/data/meet.sqlite3',0o600)"
docker compose start meet-vale
```

Verify owner access, existing invitations, participant edits, final choices and calendar exports before switching users to the restored instance. Restoring an older backup rolls back votes and finalization made after it; reconcile those changes first. Existing downloaded calendar files are not automatically updated or recalled.

## Reproduce acceptance

```sh
docker build -t meet-vale-acceptance:local .
python3 scripts/container_acceptance.py
```

The test creates isolated disposable containers and volumes, checks non-root execution, restarts with the same data, restores a backup into a clean volume, and verifies credentials, votes, frozen final choices and exact calendar bytes. It also checks new participant edits, finalization and poll creation after restore, then removes its own resources. An optional `pip_ca` build secret supports a trusted private certificate authority without disabling TLS verification.
